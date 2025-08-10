import os
import shutil
import tempfile
from contextlib import ExitStack
from typing import Any

from tqdm import trange

from ..tor.process import launch_tor_daemon, terminate_process


def create_tor_pool(num_circuits: int, *, max_queries_per_identity: int = 15) -> tuple[Any, list, list, ExitStack]:
    """
    Create a pool of WebSearch and AsyncWebSearch instances sharing a single Tor daemon.

    Args:
        num_circuits (int): Number of search circuits (identities) to create.
        max_queries_per_identity (int): Query limit per circuit before identity rotation.

    Returns:
        tuple:
            - tor_process (subprocess.Popen): Handle to the launched Tor process.
            - sync_searches (list[WebSearch]): List of synchronous WebSearch instances.
            - async_searches (list[AsyncWebSearch]): List of asynchronous AsyncWebSearch instances.
            - stack (ExitStack): ExitStack for resource cleanup.

    Architecture:
        - Single Tor daemon with multiple isolated circuits.
        - Each circuit has unique SOCKS authentication.
        - Shared control port for identity rotation.
        - Automatic cleanup on context exit.

    Resource Management:
        - Temporary directory for Tor data (auto-removed on cleanup).
        - Graceful process termination and connection cleanup for all instances.

    Usage:
        Use the returned ExitStack as a context manager to ensure all resources are cleaned up:
            with create_tor_pool(...) as (tor_process, sync_searches, async_searches, stack):
                ...

    Raises:
        RuntimeError: If Tor daemon fails to launch or ports cannot be allocated.
    """
    stack = ExitStack()

    data_dir = tempfile.mkdtemp(prefix="tor_pool_")
    stack.callback(shutil.rmtree, data_dir, ignore_errors=True)

    from ..utils.network import find_free_port

    socks_port = find_free_port()
    control_port = find_free_port()

    tor_process = launch_tor_daemon(
        data_directory=data_dir,
        socks_port=socks_port,
        control_port=control_port,
    )
    stack.callback(terminate_process, tor_process)

    cookie_path = os.path.join(data_dir, "control_auth_cookie")

    from .async_search import AsyncWebSearch
    from .sync import WebSearch

    sync_searches = []
    async_searches = []

    for i in trange(num_circuits, desc="Initializing circuits"):
        circuit_id = f"circuit_{i:03d}"

        sync_search = WebSearch(
            socks_port=socks_port,
            control_port=control_port,
            identity=circuit_id,
            control_cookie_path=cookie_path,
            max_queries_per_identity=max_queries_per_identity,
        )
        sync_searches.append(sync_search)
        stack.callback(sync_search.close)

        async_search = AsyncWebSearch(
            socks_port=socks_port,
            control_port=control_port,
            identity=circuit_id,
            control_cookie_path=cookie_path,
            max_queries_per_identity=max_queries_per_identity,
        )
        async_searches.append(async_search)

    return tor_process, sync_searches, async_searches, stack
