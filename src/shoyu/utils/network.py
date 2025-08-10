import socket
import time

__all__ = ["find_free_port", "wait_for_port"]

def find_free_port() -> int:
    """
    Find and return an available TCP port on localhost.

    Returns:
        int: An available port number on 127.0.0.1.

    Raises:
        OSError: If unable to bind to any port.

    Usage:
        Used for dynamically allocating ports for Tor SOCKS/control interfaces.

    Notes:
        The port is immediately released after being found, so there is a small race condition
        if another process binds to the port before it is used.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]

def wait_for_port(port: int, timeout: int = 10) -> bool:
    """
    Wait for a TCP port to become available on localhost.

    Args:
        port (int): The port number to check.
        timeout (int): Maximum time to wait in seconds.

    Returns:
        bool: True if the port becomes available, False otherwise.
    """
    for _ in range(timeout):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as test_socket:
                test_socket.settimeout(1)
                result = test_socket.connect_ex(("127.0.0.1", port))
                if result == 0:
                    return True
        except OSError:
            pass
        time.sleep(1)
    return False
