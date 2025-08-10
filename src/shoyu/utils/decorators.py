import asyncio
import random
from collections.abc import Callable
from time import sleep
from typing import Any

from .._exceptions import CoreError, SearchFailedError

__all__ = ["retry", "async_retry"]


def retry(
    max_retries: int = 3,
    sleep_time: int | float = 0,
    raises_on_exception: bool = True,
    non_retry_exceptions: tuple[type[Exception], ...] = (),
    exponential_backoff: bool = False,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Decorator to retry a function call on exception, with optional exponential backoff.

    Args:
        max_retries (int): Maximum number of retries before giving up (default: 3).
        sleep_time (int | float): Base time to sleep between retries (default: 0).
        raises_on_exception (bool): If True, re-raises the exception after max retries (default: True).
        non_retry_exceptions (tuple[type[Exception], ...]): Exceptions that should not trigger a retry (default: ()).
        exponential_backoff (bool): If True, use exponential backoff for sleep time (default: False).

    Returns:
        Callable[[Callable[..., Any]], Callable[..., Any]]: Decorated function that retries on exception.

    Usage:
        @retry(max_retries=5, sleep_time=2)
        def flaky_func(...): ...

    Notes:
        - If non_retry_exceptions is provided, those exceptions will not trigger a retry.
        - If raises_on_exception is False, the last exception will be suppressed.
        - Exponential backoff multiplies sleep_time by 2^i for each retry.
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        def wrapper(*args, **kwargs):  # noqa: ANN202, ANN002, ANN003
            for i in range(max_retries):
                try:
                    result = func(*args, **kwargs)
                    return result
                except Exception as e:
                    if (
                        i == max_retries - 1
                        or (
                            non_retry_exceptions and isinstance(e, non_retry_exceptions)
                        )
                    ) and raises_on_exception:
                        if isinstance(e, CoreError):
                            raise
                        else:
                            raise SearchFailedError(str(e)) from e
                    if sleep_time:
                        if exponential_backoff:
                            backoff_time = sleep_time * (2 ** i) * random.uniform(0.7, 1.3)
                            sleep(backoff_time)
                        else:
                            sleep(sleep_time)

        return wrapper

    return decorator

def async_retry(
    max_retries: int = 3,
    sleep_time: int | float = 0,
    raises_on_exception: bool = True,
    non_retry_exceptions: tuple[type[Exception], ...] = (),
    exponential_backoff: bool = False,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Async decorator to retry an async function call on exception, with optional exponential backoff.

    Args:
        max_retries (int): Maximum number of retries before giving up (default: 3).
        sleep_time (int | float): Base time to sleep between retries in seconds (default: 0).
        raises_on_exception (bool): If True, re-raises the exception after max retries (default: True).
        non_retry_exceptions (tuple[type[Exception], ...]): Exceptions that should not trigger a retry (default: ()).
        exponential_backoff (bool): If True, use exponential backoff for sleep time (default: False).

    Returns:
        Callable[[Callable[..., Any]], Callable[..., Any]]: Decorated async function that retries on exception.

    Usage:
        @async_retry(max_retries=5, sleep_time=2)
        async def flaky_async_func(...): ...

    Notes:
        - If non_retry_exceptions is provided, those exceptions will not trigger a retry.
        - If raises_on_exception is False, the last exception will be suppressed.
        - Exponential backoff multiplies sleep_time by 2^i for each retry.
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        async def wrapper(*args, **kwargs):  # noqa: ANN202, ANN002, ANN003
            for i in range(max_retries):
                try:
                    result = await func(*args, **kwargs)
                    return result
                except Exception as e:
                    if (
                        i == max_retries - 1
                        or (
                            non_retry_exceptions and isinstance(e, non_retry_exceptions)
                        )
                    ) and raises_on_exception:
                        if isinstance(e, CoreError):
                            raise
                        else:
                            raise SearchFailedError(str(e)) from e
                    if sleep_time:
                        if exponential_backoff:
                            backoff_time = sleep_time * (2 ** i) * random.uniform(0.7, 1.3)
                            await asyncio.sleep(backoff_time)
                        else:
                            await asyncio.sleep(sleep_time)

        return wrapper

    return decorator
