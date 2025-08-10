import asyncio
import os
import random
from itertools import cycle
from typing import Protocol, TypeVar, runtime_checkable

import aiohttp
from aiohttp_socks import ProxyConnector
from ddgs import DDGS

from .._enums import (
    ACCEPT_LANGUAGES,
    REFERERS,
    USER_AGENTS,
    Backend,
    Region,
    SafeSearch,
    TimeLimit,
)
from .._exceptions import SearchFailedError, UnexpectedResultTypeError
from ..config import config
from ..models import SearchResult
from ..tor.controller import (
    TorAuthenticationError,
    TorCommandError,
    TorConnectionError,
    TorError,
)
from ..utils.decorators import async_retry as retry
from ..utils.misc import generate_cookie_value
from .pool import create_tor_pool

__all__ = [
    "AsyncWebSearch",
    "BatchSearchMixin",
    "AsyncShoyu",
]


class AsyncWebSearch:
    """
    Native asynchronous web search with Tor integration.

    Provides DuckDuckGo search via Tor SOCKS proxy, with automatic identity rotation, per-circuit throttling, and randomized request headers.

    Args:
        socks_port (int): SOCKS proxy port for Tor.
        control_port (int): Tor control port for identity rotation.
        identity (str): Unique identifier for the Tor circuit.
        max_queries_per_identity (int): Maximum queries before rotating identity.
        control_cookie_path (str | None): Path to Tor control authentication cookie.

    Attributes:
        _socks_port (int): SOCKS proxy port.
        _control_port (int): Tor control port.
        _identity (str): Circuit identity.
        _max_queries (int): Query limit per identity.
        _query_counter (int): Number of queries issued on this identity.
        _cookie_path (str | None): Path to Tor control cookie.
        _last_request_time (float): Timestamp of last request for throttling.
        _session (aiohttp.ClientSession | None): HTTP session for requests.
        _tor_reader (asyncio.StreamReader | None): Tor control port reader.
        _tor_writer (asyncio.StreamWriter | None): Tor control port writer.

    Usage:
        Use as an async context manager or call search() directly.
    """

    _rotation_lock = asyncio.Lock()

    def __init__(
        self,
        *,
        socks_port: int,
        control_port: int,
        identity: str,
        max_queries_per_identity: int = 15,
        control_cookie_path: str | None = None,
    ) -> None:
        self._socks_port = socks_port
        self._control_port = control_port
        self._identity = identity
        self._max_queries = max_queries_per_identity
        self._query_counter = 0
        self._cookie_path = control_cookie_path

        self._last_request_time = 0.0  # For per-circuit throttling

        self._session: aiohttp.ClientSession | None = None
        self._tor_reader: asyncio.StreamReader | None = None
        self._tor_writer: asyncio.StreamWriter | None = None

    @retry(max_retries=3, sleep_time=1.0)
    async def search(
        self,
        query: str,
        *,
        region: Region = Region.WT_WT,
        safesearch: SafeSearch = SafeSearch.MODERATE,
        timelimit: TimeLimit = TimeLimit.NONE,
        backend: Backend = Backend.AUTO,
        max_results: int = 10,
    ) -> list[SearchResult]:
        """
        Perform an asynchronous DuckDuckGo search via Tor.

        Args:
            query (str): Search keywords.
            region (Region): Region code for search localization (default: WT_WT).
            safesearch (SafeSearch): Safe search filtering level (default: MODERATE).
            timelimit (TimeLimit): Restrict results to a time range (default: NONE).
            backend (Backend): Backend mode for search (default: AUTO).
            max_results (int): Maximum number of results to return (default: 10).

        Returns:
            list[SearchResult]: List of parsed search results.

        Raises:
            RuntimeError: On search failure or Tor errors.

        Notes:
            - Rotates identity after max_queries_per_identity.
            - Handles 403 errors by rotating identity and retrying.
            - Enforces per-circuit throttling and randomized delays.
        """
        if not self._session:
            await self._initialize_session()

        # Per-circuit throttling: enforce minimum interval between requests
        now = asyncio.get_event_loop().time()
        min_interval = config.MIN_OPERATION_DELAY
        if now - self._last_request_time < min_interval:
            await asyncio.sleep(min_interval - (now - self._last_request_time))
        self._last_request_time = asyncio.get_event_loop().time()

        try:
            proxy_url = f"socks5h://{self._identity}:pwd@127.0.0.1:{self._socks_port}"

            instance = DDGS(proxy=proxy_url)

            raw_results = list(
                instance.text(
                    query,
                    region=region.value,
                    safesearch=safesearch.value,
                    backend=backend.value,
                    max_results=max_results,
                )
            )

            results = [SearchResult.from_ddgs(result) for result in raw_results]

            self._query_counter += 1
            if self._query_counter >= self._max_queries:
                await self._rotate_identity()

            # Randomized delay between operations
            await asyncio.sleep(
                random.uniform(config.MIN_OPERATION_DELAY, config.MAX_OPERATION_DELAY)
            )

            return results

        except Exception as e:
            # 403-specific handling: rotate identity and increase delay
            error_message = str(e) or repr(e) or "Unknown error"
            if "403" in error_message:
                await self._rotate_identity()
                await asyncio.sleep(
                    random.uniform(
                        config.MIN_OPERATION_DELAY, config.MAX_OPERATION_DELAY
                    )
                    + 0.5
                )
            raise SearchFailedError(f"Async search failed: {error_message}") from e

    async def aclose(self) -> None:
        """
        Close all resources associated with this AsyncWebSearch instance.

        Closes the HTTP session and Tor control connection.
        """
        if self._session:
            await self._session.close()
            self._session = None

        if self._tor_writer:
            self._tor_writer.close()
            await self._tor_writer.wait_closed()
            self._tor_writer = None
            self._tor_reader = None

    async def _initialize_session(self) -> None:
        """
        Initialize the aiohttp session and connect to the Tor control port.

        Raises:
            TorConnectionError: If unable to connect to Tor control port.
        """
        proxy_url = f"socks5://{self._identity}:pwd@127.0.0.1:{self._socks_port}"
        connector = ProxyConnector.from_url(proxy_url)

        self._session = aiohttp.ClientSession(
            connector=connector, timeout=aiohttp.ClientTimeout(total=30, connect=5)
        )

        await self._connect_tor_control()

    async def _connect_tor_control(self) -> None:
        """
        Establish an asynchronous connection to the Tor control port and authenticate.

        Raises:
            TorConnectionError: If connection or authentication fails.
        """
        try:
            self._tor_reader, self._tor_writer = await asyncio.open_connection(
                "127.0.0.1", self._control_port
            )
            await self._authenticate_tor()
        except (TimeoutError, OSError) as e:
            raise TorConnectionError(f"Async Tor connection failed: {e}") from e

    async def _authenticate_tor(self) -> None:
        """
        Authenticate with the Tor control interface.

        Uses cookie-based authentication if available, otherwise null authentication.

        Raises:
            TorAuthenticationError: If authentication fails.
        """
        try:
            if self._cookie_path and os.path.exists(self._cookie_path):
                with open(self._cookie_path, "rb") as f:
                    cookie = f.read()
                cookie_hex = cookie.hex().upper()
                response = await self._send_tor_command(f"AUTHENTICATE {cookie_hex}")
            else:
                response = await self._send_tor_command("AUTHENTICATE")

            if not response.startswith("250"):
                raise TorAuthenticationError(f"Async auth failed: {response}")

        except (TimeoutError, OSError) as e:
            raise TorAuthenticationError(f"Async authentication error: {e}") from e

    async def _send_tor_command(self, command: str) -> str:
        """
        Send a command to the Tor control interface asynchronously.

        Args:
            command (str): Tor control protocol command.

        Returns:
            str: Response from Tor.

        Raises:
            TorConnectionError: If not connected to Tor.
            TorCommandError: If command transmission fails.
        """
        if not self._tor_writer or not self._tor_reader:
            raise TorConnectionError("Tor control not connected")

        try:
            self._tor_writer.write(f"{command}\r\n".encode())
            await self._tor_writer.drain()

            response = await self._tor_reader.readuntil(b"\r\n")
            return response.decode().strip()

        except (TimeoutError, OSError) as e:
            raise TorCommandError(f"Async command failed: {e}") from e

    async def _rotate_identity(self) -> None:
        """
        Rotate the Tor identity (build new circuits) for this search instance.

        Raises:
            TorCommandError: If the NEWNYM command fails.
            TorError: On other errors during identity rotation.
        """
        async with self._rotation_lock:
            try:
                response = await self._send_tor_command("SIGNAL NEWNYM")
                if not response.startswith("250"):
                    raise TorCommandError(f"NEWNYM failed: {response}")

                self._query_counter = 0

                if self._session:
                    await self._session.close()
                await self._initialize_session()

            except Exception as e:
                raise TorError(f"Async identity rotation failed: {e}") from e

    __call__ = search

    async def __aenter__(self) -> "AsyncWebSearch":
        """
        Enter async context manager.

        Returns:
            AsyncWebSearch: This instance.
        """
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object | None,
    ) -> None:
        """
        Exit async context manager, closing all resources.
        """
        await self.aclose()

    def __repr__(self) -> str:
        """
        Return a string representation of this AsyncWebSearch instance.
        """
        return (
            f"<AsyncWebSearch id={self._identity} "
            f"queries={self._query_counter}/{self._max_queries}>"
        )


@runtime_checkable
class AsyncShoyuProtocol(Protocol):
    async def search(
        self,
        query: str,
        *,
        region: Region = Region.WT_WT,
        safesearch: SafeSearch = SafeSearch.MODERATE,
        timelimit: TimeLimit = TimeLimit.NONE,
        backend: Backend = Backend.AUTO,
        max_results: int = 10,
    ) -> list[SearchResult]: ...


T = TypeVar("T", bound="AsyncShoyuProtocol")


class BatchSearchMixin:
    """
    Mixin providing batch search operations for efficient multi-query processing.

    Provides batch_search and search_with_retry utilities for any class implementing AsyncShoyuProtocol.
    """

    async def batch_search(
        self: "AsyncShoyuProtocol",
        queries: list[str],
        *,
        region: Region = Region.WT_WT,
        safesearch: SafeSearch = SafeSearch.MODERATE,
        timelimit: TimeLimit = TimeLimit.NONE,
        backend: Backend = Backend.AUTO,
        max_results: int = 10,
        max_concurrent: int = 5,
    ) -> dict[str, list[SearchResult]]:
        """
        Perform batch DuckDuckGo searches for multiple queries concurrently.

        Args:
            queries (list[str]): List of search keywords.
            region (Region): Region code for search localization (default: WT_WT).
            safesearch (SafeSearch): Safe search filtering level (default: MODERATE).
            timelimit (TimeLimit): Restrict results to a time range (default: NONE).
            backend (Backend): Backend mode for search (default: AUTO).
            max_results (int): Maximum number of results per query (default: 10).
            max_concurrent (int): Maximum number of concurrent searches (default: 5).

        Returns:
            dict[str, list[SearchResult]]: Mapping from query to list of results.

        Raises:
            RuntimeError: If an unexpected result type is encountered.

        Notes:
            - Each query is executed in parallel, up to max_concurrent at a time.
            - If a query fails, its result list will be empty.
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        results = {}

        async def search_single(query: str) -> tuple[str, list[SearchResult]]:
            async with semaphore:
                try:
                    search_results = await self.search(
                        query,
                        region=region,
                        safesearch=safesearch,
                        timelimit=timelimit,
                        backend=backend,
                        max_results=max_results,
                    )
                    return query, search_results
                except Exception:
                    return query, []

        tasks = [search_single(query) for query in queries]
        completed_results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in completed_results:
            if isinstance(result, tuple):
                query, search_results = result
                results[query] = search_results
            else:
                raise UnexpectedResultTypeError(
                    f"Unexpected result type: {type(result)}. Expected tuple."
                )

        return results

    async def search_with_retry(
        self: "AsyncShoyuProtocol",
        query: str,
        *,
        max_results: int = 10,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ) -> list[SearchResult]:
        """
        Perform a search with automatic retries on failure.

        Args:
            query (str): Search keywords.
            max_results (int): Maximum number of results (default: 10).
            max_retries (int): Maximum number of retry attempts (default: 3).
            retry_delay (float): Base delay between retries in seconds (default: 1.0).

        Returns:
            list[SearchResult]: List of search results.

        Raises:
            RuntimeError: If all retries fail.
        """
        last_exception = None

        for attempt in range(max_retries + 1):
            try:
                return await self.search(query, max_results=max_results)
            except Exception as e:
                last_exception = e
                if attempt < max_retries:
                    delay = retry_delay * (2**attempt) * random.uniform(0.8, 1.2)
                    await asyncio.sleep(delay)
                    continue
                break

        raise SearchFailedError(
            f"Search failed after {max_retries + 1} attempts: {last_exception}"
        ) from last_exception


class AsyncShoyu(BatchSearchMixin):
    """
    High-level asynchronous search interface with automatic load balancing and batch operations.

    Manages a pool of AsyncWebSearch circuits for concurrent, load-balanced search requests.

    Args:
        num_circuits (int): Number of Tor circuits to create (default: 3).
        max_queries_per_identity (int): Query limit per circuit before identity rotation (default: 15).

    Attributes:
        _tor_process: Handle to the Tor process.
        _async_searches (list[AsyncWebSearch]): Pool of async search instances.
        _stack (ExitStack): Resource cleanup stack.
        _circuit_pool: Iterator cycling through available circuits.

    Usage:
        Use as an async context manager or call search() directly.
    """

    def __init__(
        self, *, num_circuits: int = 3, max_queries_per_identity: int = 15
    ) -> None:
        self._tor_process, _, self._async_searches, self._stack = create_tor_pool(
            num_circuits=num_circuits,
            max_queries_per_identity=max_queries_per_identity,
        )
        self._circuit_pool = cycle(self._async_searches)

    async def search(
        self,
        query: str,
        *,
        region: Region = Region.WT_WT,
        safesearch: SafeSearch = SafeSearch.MODERATE,
        timelimit: TimeLimit = TimeLimit.NONE,
        backend: Backend = Backend.AUTO,
        max_results: int = 10,
    ) -> list[SearchResult]:
        """
        High-level async search interface with automatic load balancing.

        Args:
            query (str): Search keywords.
            region (Region): Region code for search localization (default: WT_WT).
            safesearch (SafeSearch): Safe search filtering level (default: MODERATE).
            timelimit (TimeLimit): Restrict results to a time range (default: NONE).
            backend (Backend): Backend mode for search (default: AUTO).
            max_results (int): Maximum number of results (default: 10).

        Returns:
            list[SearchResult]: List of parsed search results.
        """
        search_instance = next(self._circuit_pool)
        return await search_instance.search(
            query,
            region=region,
            safesearch=safesearch,
            timelimit=timelimit,
            backend=backend,
            max_results=max_results,
        )

    async def aclose(self) -> None:
        """
        Close all AsyncWebSearch circuits and cleanup resources.
        """
        for search in self._async_searches:
            await search.aclose()
        self._stack.close()

    __call__ = search

    async def __aenter__(self) -> "AsyncShoyu":
        """
        Enter async context manager.

        Returns:
            AsyncShoyu: This instance.
        """
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object | None,
    ) -> None:
        """
        Exit async context manager, closing all resources.
        """
        await self.aclose()

    def close(self) -> None:
        """
        Close all resources immediately (non-async).

        Note:
            Prefer using aclose() or async context manager for async cleanup.
        """
        self._stack.close()

    def __repr__(self) -> str:
        """
        Return a string representation of this AsyncShoyu instance.
        """
        return f"<AsyncShoyu circuits={len(self._async_searches)}>"
