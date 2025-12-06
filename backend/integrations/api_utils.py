"""
Shared utilities for API clients.

Provides common functionality for error handling, retries, and rate limiting.
"""

import asyncio
import logging
from typing import Callable, TypeVar, Optional
from functools import wraps

logger = logging.getLogger(__name__)

T = TypeVar('T')


async def retry_with_backoff(
    func: Callable[..., T],
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    *args,
    **kwargs
) -> T:
    """
    Retry an async function with exponential backoff.
    
    Args:
        func: Async function to retry
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds before first retry
        backoff_factor: Multiplier for delay between retries
        *args: Positional arguments to pass to func
        **kwargs: Keyword arguments to pass to func
    
    Returns:
        Result from successful function call
    
    Raises:
        Exception: Last exception if all retries fail
    """
    delay = initial_delay
    last_exception = None
    
    for attempt in range(max_retries + 1):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            last_exception = e
            if attempt < max_retries:
                logger.warning(
                    f"Attempt {attempt + 1} failed: {e}. Retrying in {delay}s..."
                )
                await asyncio.sleep(delay)
                delay *= backoff_factor
            else:
                logger.error(f"All {max_retries + 1} attempts failed. Last error: {e}")
                raise
    
    # Should never reach here, but type checker needs it
    if last_exception:
        raise last_exception
    raise RuntimeError("Unexpected error in retry_with_backoff")


def handle_api_error(response, error_message: str = "API request failed"):
    """
    Handle API response errors and raise appropriate exceptions.
    
    Args:
        response: HTTP response object
        error_message: Custom error message prefix
    
    Raises:
        ValueError: If response indicates an error
    """
    if response.status_code >= 400:
        error_detail = f"{error_message}: {response.status_code}"
        try:
            error_body = response.json()
            if "message" in error_body:
                error_detail += f" - {error_body['message']}"
        except Exception:
            error_detail += f" - {response.text[:200]}"
        
        logger.error(error_detail)
        raise ValueError(error_detail)

