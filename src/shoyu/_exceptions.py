from __future__ import annotations

import logging
from typing import Any

from ._enums import ErrorCodes

logger = logging.getLogger(__name__)

__all__ = [
    "CoreError",
    "TorError",
    "TorConnectionError",
    "TorAuthenticationError",
    "TorCommandError",
    "SearchClientNotInitializedError",
    "SearchFailedError",
    "IdentityRotationFailedError",
    "UnexpectedResultTypeError",
    "PortBindFailedError",
    "ProcessTimeoutError",
    "ProcessLookupFailedError",
]

class CoreError(Exception):
    """
    A custom exception class for handling application-specific errors.

    This exception includes an error message, an error code, and optional details.
    It also logs the error upon initialization.

    Attributes:
        message (str): A descriptive error message.
        code (ErrorCodes): An enumerated error code representing the specific error type.
        details (dict[str, Any] | str | None): Additional details about the error.
    """

    message: str
    code: ErrorCodes
    details: dict[str, Any] | str | None

    def __init__(
        self,
        message: str,
        code: ErrorCodes,
        details: dict[str, Any] | str | None = None,
    ) -> None:
        """
        Initialize a CoreError instance with an error message, code, and optional details.

        The error is logged automatically when an instance is created.

        Args:
            message (str): The error message.
            code (ErrorCodes): A predefined error code representing the error type.
            details (dict[str, Any] | str | None, optional): Additional information about the error.
                Can be a dictionary, a string, or None. Defaults to None.
        """
        self.message = message
        self.code = code
        self.details = details

        logger.error(
            f"{self.__class__.__name__}: {message} [Code: {code}] Details: {details}"
        )

    def __str__(self) -> str:
        """
        Return a string representation of the error, including the message, code, and optional details.

        Returns:
            str: A formatted string describing the error.

        Example:
            >>> error = CoreError("Invalid input", ErrorCodes.INVALID_INPUT, {"field": "email"})
            >>> print(str(error))
            "CoreError: Invalid input [Code: INVALID_INPUT] Details: {'field': 'email'}"
        """
        detail_part = f" Details: {self.details}" if self.details else ""
        return f"{self.__class__.__name__}: {self.message} [Code: {self.code}]{detail_part}"

    def to_dict(self) -> dict[str, Any]:
        """
        Convert the CoreError instance into a dictionary format.

        This is useful for structured logging or returning errors in API responses.

        Returns:
            dict[str, Any]: A dictionary containing error details.

        Example:
            >>> error = CoreError("Access denied", ErrorCodes.PERMISSION_DENIED, "User lacks admin rights")
            >>> error.to_dict()
            {
                "error": "CoreError",
                "message": "Access denied",
                "code": "PERMISSION_DENIED",
                "details": "User lacks admin rights"
            }
        """
        return {
            "error": self.__class__.__name__,
            "message": self.message,
            "code": self.code,
            "details": self.details or {},
        }


class TorError(CoreError):
    def __init__(self, message: str, details: str | None = None) -> None:
        super().__init__(message, ErrorCodes.TOR_LAUNCH_FAILED, details)


class TorConnectionError(CoreError):
    def __init__(self, message: str, details: str | None = None) -> None:
        super().__init__(message, ErrorCodes.TOR_CONNECTION_FAILED, details)


class TorAuthenticationError(CoreError):
    def __init__(self, message: str, details: str | None = None) -> None:
        from ._enums import ErrorCodes

        super().__init__(message, ErrorCodes.TOR_AUTH_FAILED, details)


class TorCommandError(CoreError):
    def __init__(self, message: str, details: str | None = None) -> None:
        from ._enums import ErrorCodes

        super().__init__(message, ErrorCodes.TOR_COMMAND_FAILED, details)


class SearchClientNotInitializedError(CoreError):
    def __init__(self, message: str, details: str | None = None) -> None:
        from ._enums import ErrorCodes

        super().__init__(message, ErrorCodes.SEARCH_CLIENT_NOT_INITIALIZED, details)


class SearchFailedError(CoreError):
    def __init__(self, message: str, details: str | None = None) -> None:
        from ._enums import ErrorCodes

        super().__init__(message, ErrorCodes.SEARCH_FAILED, details)


class IdentityRotationFailedError(CoreError):
    def __init__(self, message: str, details: str | None = None) -> None:
        from ._enums import ErrorCodes

        super().__init__(message, ErrorCodes.IDENTITY_ROTATION_FAILED, details)


class UnexpectedResultTypeError(CoreError):
    def __init__(self, message: str, details: str | None = None) -> None:
        from ._enums import ErrorCodes

        super().__init__(message, ErrorCodes.UNEXPECTED_RESULT_TYPE, details)


class PortBindFailedError(CoreError):
    def __init__(self, message: str, details: str | None = None) -> None:
        from ._enums import ErrorCodes

        super().__init__(message, ErrorCodes.PORT_BIND_FAILED, details)


class ProcessTimeoutError(CoreError):
    def __init__(self, message: str, details: str | None = None) -> None:
        from ._enums import ErrorCodes

        super().__init__(message, ErrorCodes.PROCESS_TIMEOUT, details)


class ProcessLookupFailedError(CoreError):
    def __init__(self, message: str, details: str | None = None) -> None:
        from ._enums import ErrorCodes

        super().__init__(message, ErrorCodes.PROCESS_LOOKUP_FAILED, details)
