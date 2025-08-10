import random
import threading
import time
from itertools import cycle

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
from .._exceptions import SearchClientNotInitializedError, SearchFailedError
from ..config import config
from ..models import SearchResult
from ..tor.controller import TorController, TorError
from ..utils.decorators import retry
from ..utils.misc import generate_cookie_value
from .pool import create_tor_pool

__all__ = [
    "WebSearch",
    "Shoyu",
]


class WebSearch:
    """
    Synchronous web search with Tor proxy and identity rotation.

    Provides DuckDuckGo search via Tor SOCKS proxy, with automatic identity rotation,
    per-circuit throttling, and randomized request headers.

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
        _proxies (dict[str, str]): Proxy URIs for HTTP/HTTPS.
        _controller (TorController | None): Tor control interface.
        _ddgs (DDGS | None): DuckDuckGo search client.

    Usage:
        Use as a context manager or call search() directly.
    """

    _rotation_lock = threading.Lock()

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

        proxy_uri = f"socks5h://{identity}:pwd@127.0.0.1:{socks_port}"
        self._proxies: dict[str, str] = {"http": proxy_uri, "https": proxy_uri}

        self._controller: TorController | None = None
        self._ddgs: DDGS | None = None

        self._initialize_controller()
        self._initialize_ddgs()

    @retry(max_retries=3, sleep_time=1.0)
    def search(
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
        Perform a synchronous DuckDuckGo search via Tor.

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
        if not self._ddgs:
            raise SearchClientNotInitializedError("Search client not initialized")

        # Per-circuit throttling: enforce minimum interval between requests
        now = time.time()
        min_interval = config.MIN_OPERATION_DELAY
        if now - self._last_request_time < min_interval:
            time.sleep(min_interval - (now - self._last_request_time))
        self._last_request_time = time.time()

        try:
            raw_results = list(
                self._ddgs.text(
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
                self._rotate_identity()

            # Randomized delay between operations
            time.sleep(
                random.uniform(config.MIN_OPERATION_DELAY, config.MAX_OPERATION_DELAY)
            )

            return results

        except Exception as e:
            # 403-specific handling: rotate identity and increase delay
            if "403" in str(e):
                self._rotate_identity()
                time.sleep(
                    random.uniform(
                        config.MIN_OPERATION_DELAY, config.MAX_OPERATION_DELAY
                    )
                    + 0.5
                )
            raise SearchFailedError(f"Search failed for query '{query}': {e}") from e

    def close(self) -> None:
        """
        Close all resources associated with this WebSearch instance.

        Closes the DuckDuckGo client and Tor control connection.
        """
        if self._ddgs:
            self._ddgs = None

        if self._controller:
            try:
                self._controller.close()
            except Exception:
                pass
            finally:
                self._controller = None

    def _initialize_controller(self) -> None:
        """
        Initialize the TorController for identity rotation.

        Raises:
            TorError: If connection or authentication fails.
        """
        self._controller = TorController(
            control_port=self._control_port, cookie_path=self._cookie_path
        )
        self._controller.connect()
        self._controller.authenticate()

    def _initialize_ddgs(self) -> None:
        """
        Initialize the DuckDuckGo search client with randomized headers.
        """
        self._ddgs = DDGS(proxy=self._proxies.get("https"))

    def _rotate_identity(self) -> None:
        """
        Rotate the Tor identity (build new circuits) for this search instance.

        Raises:
            TorError: If identity rotation fails.
        """
        with self._rotation_lock:
            if not self._controller:
                raise TorError("Controller not available for rotation")

            try:
                self._controller.new_identity()
                self._query_counter = 0
                self._initialize_ddgs()
            except Exception as e:
                raise TorError(f"Identity rotation failed: {e}") from e

    __call__ = search

    def __enter__(self) -> "WebSearch":
        """
        Enter context manager.

        Returns:
            WebSearch: This instance.
        """
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object | None,
    ) -> None:
        """
        Exit context manager, closing all resources.
        """
        self.close()

    def __repr__(self) -> str:
        """
        Return a string representation of this WebSearch instance.
        """
        return (
            f"<WebSearch id={self._identity} "
            f"queries={self._query_counter}/{self._max_queries}>"
        )


class Shoyu:
    """
    High-level synchronous search interface with automatic load balancing.

    Manages a pool of WebSearch circuits for concurrent, load-balanced search requests.

    Args:
        num_circuits (int): Number of Tor circuits to create (default: 3).
        max_queries_per_identity (int): Query limit per circuit before identity rotation (default: 15).

    Attributes:
        _tor_process: Handle to the Tor process.
        _searches (list[WebSearch]): Pool of search instances.
        _stack (ExitStack): Resource cleanup stack.
        _circuit_pool: Iterator cycling through available circuits.

    Usage:
        Use as a context manager or call search() directly.
    """

    def __init__(
        self, *, num_circuits: int = 3, max_queries_per_identity: int = 15
    ) -> None:
        self._tor_process, self._searches, _, self._stack = create_tor_pool(
            num_circuits=num_circuits,
            max_queries_per_identity=max_queries_per_identity,
        )
        self._circuit_pool = cycle(self._searches)

    def search(
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
        High-level search interface with automatic load balancing.

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
        return search_instance.search(
            query,
            region=region,
            safesearch=safesearch,
            timelimit=timelimit,
            backend=backend,
            max_results=max_results,
        )

    def close(self) -> None:
        """
        Close all resources immediately.

        Note:
            Prefer using context manager for automatic cleanup.
        """
        self._stack.close()

    __call__ = search

    def __enter__(self) -> "Shoyu":
        """
        Enter context manager.

        Returns:
            Shoyu: This instance.
        """
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object | None,
    ) -> None:
        """
        Exit context manager, closing all resources.
        """
        self.close()

    def __repr__(self) -> str:
        """
        Return a string representation of this Shoyu instance.
        """
        return f"<Shoyu circuits={len(self._searches)}>"
