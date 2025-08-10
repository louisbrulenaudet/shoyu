import shutil
import subprocess

from .._exceptions import TorConnectionError, TorError
from ..utils.decorators import retry
from ..utils.network import wait_for_port
from ..utils.process_utils import terminate_process_tree

__all__= ["launch_tor_daemon", "terminate_process"]


@retry(max_retries=3, sleep_time=2, exponential_backoff=True)
def launch_tor_daemon(
    *, data_directory: str, socks_port: int, control_port: int
) -> subprocess.Popen:
    """
    Launch a Tor daemon subprocess with the specified configuration.

    Args:
        data_directory (str): Path to the Tor data directory (will be created if missing).
        socks_port (int): SOCKS proxy port for Tor.
        control_port (int): Control interface port for Tor.

    Returns:
        subprocess.Popen: Handle to the launched Tor process.

    Raises:
        RuntimeError: If Tor executable is not found, fails to launch, or fails to bind ports.

    Security Configuration:
        - IsolateSOCKSAuth: Separate circuits per auth credential.
        - CookieAuthentication: Secure file-based authentication.
        - MaxCircuitDirtiness: Regular circuit refresh (10 minutes).

    Notes:
        - Waits for the control port to become available before returning.
        - Cleans up the process if startup fails.
        - Designed for use with resource cleanup via terminate_process.
    """
    tor_executable = shutil.which("tor")

    if not tor_executable:
        raise TorError("Tor executable not found in PATH. Please install Tor.")

    tor_config = [
        tor_executable,
        "--DataDirectory",
        data_directory,
        "--SocksPort",
        str(socks_port),
        "--ControlPort",
        str(control_port),
        "--CookieAuthentication",
        "1",
        "--Log",
        "notice stderr",
        "--MaxCircuitDirtiness",
        "600",
    ]

    try:
        process = subprocess.Popen(
            tor_config,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True,
        )

        if process.poll() is not None:
            stdout, stderr = process.communicate()
            error_msg = stderr.strip() if stderr else "Unknown error"

            if stdout:
                error_msg += f"\nStdout: {stdout.strip()}"

            raise TorError(f"Tor daemon failed to start: {error_msg}")

        if wait_for_port(control_port, timeout=10):
            return process

        # If port did not become available, terminate process and raise error
        terminate_process_tree(process)
        stdout, stderr = process.communicate() if process.poll() is not None else ("", "")
        error_msg = "Tor startup timeout after 10s"
        if stderr:
            error_msg += f"\nStderr: {stderr.strip()}"
        if stdout:
            error_msg += f"\nStdout: {stdout.strip()}"
        raise TorConnectionError(error_msg)

    except (subprocess.SubprocessError, OSError) as e:
        raise TorError(f"Failed to launch Tor daemon: {e}") from e


def terminate_process(process: subprocess.Popen) -> None:
    """
    Gracefully terminate a subprocess and its children.

    Args:
        process (subprocess.Popen): Process to terminate.

    Usage:
        Use for cleaning up Tor daemon or other subprocesses started by this application.
    """
    terminate_process_tree(process)
