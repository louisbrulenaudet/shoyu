import os
import socket

from .._exceptions import (
    TorAuthenticationError,
    TorCommandError,
    TorConnectionError,
    TorError,
)

__all__ = [
    "TorController",
]


class TorController:
    """
    Manual implementation of the Tor control protocol for identity rotation.

    Replaces stem.control.Controller with a lightweight implementation focused on identity rotation.

    Args:
        control_port (int): Tor control port number.
        cookie_path (str | None): Optional path to Tor authentication cookie.

    Attributes:
        _control_port (int): Tor control port number.
        _cookie_path (str | None): Path to Tor authentication cookie.
        _socket (socket.socket | None): TCP socket for control connection.
        _authenticated (bool): Authentication status flag.

    Usage:
        Use as a context manager or call connect/authenticate/new_identity directly.
    """

    def __init__(self, control_port: int, cookie_path: str | None = None) -> None:
        """
        Initialize Tor controller.

        Args:
            control_port (int): Tor control port.
            cookie_path (str | None): Optional path to authentication cookie.

        Security:
            Prefers cookie authentication over password.
        """
        self._control_port = control_port
        self._cookie_path = cookie_path
        self._socket: socket.socket | None = None
        self._authenticated = False

    def connect(self) -> None:
        """
        Establish connection to the Tor control port.

        Raises:
            TorConnectionError: If connection fails.

        Notes:
            Connection timeout set to 10 seconds for reliable startup.
        """
        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.settimeout(10.0)
            self._socket.connect(("127.0.0.1", self._control_port))

        except OSError as e:
            raise TorConnectionError(
                f"Failed to connect to Tor control port: {e}"
            ) from e

    def authenticate(self) -> None:
        """
        Authenticate with the Tor control interface.

        Raises:
            TorAuthenticationError: If authentication fails.

        Security:
            Uses cookie-based auth when available, falls back to null auth.
        """
        if not self._socket:
            raise TorConnectionError("Not connected to Tor")

        try:
            if self._cookie_path and os.path.exists(self._cookie_path):
                # Cookie-based authentication
                with open(self._cookie_path, "rb") as f:
                    cookie = f.read()
                cookie_hex = cookie.hex().upper()
                response = self._send_command(f"AUTHENTICATE {cookie_hex}")

            else:
                # Null authentication (no password)
                response = self._send_command("AUTHENTICATE")

            if not response.startswith("250"):
                raise TorAuthenticationError(f"Authentication failed: {response}")

            self._authenticated = True

        except OSError as e:
            raise TorAuthenticationError(f"Authentication error: {e}") from e

    def new_identity(self) -> None:
        """
        Request new Tor identity (circuit rotation).

        Raises:
            TorCommandError: If NEWNYM command fails.

        Notes:
            Forces Tor to build new circuits for subsequent connections.
        """
        if not self._authenticated:
            raise TorError("Not authenticated with Tor")

        response = self._send_command("SIGNAL NEWNYM")
        if not response.startswith("250"):
            raise TorCommandError(f"NEWNYM failed: {response}")

    def _send_command(self, command: str) -> str:
        """
        Send a command to the Tor control interface.

        Args:
            command (str): Tor control protocol command.

        Returns:
            str: Response from Tor.

        Raises:
            TorConnectionError: If not connected to Tor.
            TorCommandError: If command transmission fails.

        Protocol:
            Commands are CRLF-terminated, responses end with CRLF.
        """
        if not self._socket:
            raise TorConnectionError("Not connected to Tor")

        try:
            self._socket.send(f"{command}\r\n".encode())
            response = b""
            while True:
                chunk = self._socket.recv(1024)
                if not chunk:
                    break
                response += chunk
                if response.endswith(b"\r\n"):
                    break
            return response.decode().strip()
        except OSError as e:
            raise TorCommandError(f"Command failed: {e}") from e

    def close(self) -> None:
        """
        Close the Tor control connection.

        Performs graceful cleanup of socket resources.
        """
        if self._socket:
            try:
                self._socket.close()
            except OSError:
                pass  # Ignore errors during cleanup
            finally:
                self._socket = None
                self._authenticated = False

    def __enter__(self) -> "TorController":
        """
        Enter context manager, connecting and authenticating.

        Returns:
            TorController: This instance.
        """
        self.connect()
        self.authenticate()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object | None,
    ) -> None:
        """
        Exit context manager, closing the connection.
        """
        self.close()
