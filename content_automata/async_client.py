"""Async support for API calls — async wrappers and utilities.

Provides async/await support for content-automata API calls,
including async HTTP clients, concurrent batch processing,
and async pipeline execution primitives.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Callable, Coroutine, Dict, List, Optional, TypeVar

import httpx

logger = logging.getLogger(__name__)

T = TypeVar("T")


class AsyncAPIClient:
    """Async HTTP client for API calls with timeout and retry support.

    Wraps httpx.AsyncClient with content-automata-specific
    defaults for timeout, retry, and error handling.
    """

    def __init__(
        self,
        base_url: str = "",
        api_key: str = "",
        timeout: float = 30.0,
        max_retries: int = 3,
        headers: Optional[Dict[str, str]] = None,
    ):
        """Initialize async API client.

        Args:
            base_url: Base URL for API requests.
            api_key: API key for authentication.
            timeout: Request timeout in seconds.
            max_retries: Maximum retry attempts.
            headers: Additional HTTP headers.
        """
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._timeout = timeout
        self._max_retries = max_retries
        self._extra_headers = headers or {}

        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the async HTTP client.

        Returns:
            Configured httpx.AsyncClient instance.
        """
        if self._client is None or self._client.is_closed:
            headers = {
                "User-Agent": "content-automata/0.1.0",
                "Accept": "application/json",
                **self._extra_headers,
            }
            if self._api_key:
                headers["Authorization"] = f"Bearer {self._api_key}"

            self._client = httpx.AsyncClient(
                base_url=self._base_url,
                headers=headers,
                timeout=self._timeout,
            )
        return self._client

    async def get(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Perform an async GET request.

        Args:
            path: URL path relative to base_url.
            params: Query parameters.

        Returns:
            Response JSON as dictionary.

        Raises:
            httpx.HTTPError: On request failure after retries.
        """
        client = await self._get_client()
        last_error: Optional[Exception] = None

        for attempt in range(self._max_retries):
            try:
                response = await client.get(path, params=params)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                last_error = e
                if e.response.status_code < 500:
                    raise  # Don't retry 4xx errors
                logger.warning(
                    "GET %s failed (attempt %d/%d): %s",
                    path,
                    attempt + 1,
                    self._max_retries,
                    e,
                )
                if attempt < self._max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
            except (httpx.TimeoutException, httpx.NetworkError) as e:
                last_error = e
                logger.warning(
                    "GET %s timeout/network error (attempt %d/%d): %s",
                    path,
                    attempt + 1,
                    self._max_retries,
                    e,
                )
                if attempt < self._max_retries - 1:
                    await asyncio.sleep(2 ** attempt)

        raise last_error or httpx.HTTPError(f"GET {path} failed after {self._max_retries} retries")

    async def post(
        self,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Perform an async POST request.

        Args:
            path: URL path relative to base_url.
            json: JSON body data.
            data: Form data.

        Returns:
            Response JSON as dictionary.
        """
        client = await self._get_client()
        last_error: Optional[Exception] = None

        for attempt in range(self._max_retries):
            try:
                response = await client.post(path, json=json, data=data)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                last_error = e
                if e.response.status_code < 500:
                    raise
                logger.warning(
                    "POST %s failed (attempt %d/%d): %s",
                    path,
                    attempt + 1,
                    self._max_retries,
                    e,
                )
                if attempt < self._max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
            except (httpx.TimeoutException, httpx.NetworkError) as e:
                last_error = e
                if attempt < self._max_retries - 1:
                    await asyncio.sleep(2 ** attempt)

        raise last_error or httpx.HTTPError(f"POST {path} failed after {self._max_retries} retries")

    async def close(self) -> None:
        """Close the HTTP client and release resources."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def __aenter__(self) -> "AsyncAPIClient":
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()


async def run_concurrently(
    tasks: List[Coroutine[Any, Any, T]],
    max_concurrent: int = 5,
    timeout: float = 60.0,
) -> List[T]:
    """Run multiple async tasks concurrently with a limit.

    Uses a semaphore to control concurrency.

    Args:
        tasks: List of async coroutines to execute.
        max_concurrent: Maximum concurrent tasks.
        timeout: Per-task timeout in seconds.

    Returns:
        List of results in task order.
    """
    semaphore = asyncio.Semaphore(max_concurrent)

    async def _run_with_limit(task: Coroutine[Any, Any, T]) -> T:
        async with semaphore:
            return await asyncio.wait_for(task, timeout=timeout)

    return await asyncio.gather(
        *(_run_with_limit(t) for t in tasks),
        return_exceptions=False,
    )


async def run_batch(
    processor: Callable[..., T],
    items: List[Any],
    batch_size: int = 10,
    delay: float = 0.1,
    **kwargs: Any,
) -> List[T]:
    """Process items in batches with a delay between batches.

    Args:
        processor: Async function to apply to each item.
        items: List of items to process.
        batch_size: Number of items per batch.
        delay: Delay in seconds between batches.
        **kwargs: Additional arguments passed to processor.

    Returns:
        List of results.
    """
    results: List[T] = []
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        batch_results = await run_concurrently(
            [processor(item, **kwargs) for item in batch],
        )
        results.extend(batch_results)
        if i + batch_size < len(items) and delay > 0:
            await asyncio.sleep(delay)
    return results


def sync_to_async(func: Callable[..., T]) -> Callable[..., Coroutine[Any, Any, T]]:
    """Convert a synchronous function to an async one using run_in_executor.

    Args:
        func: Synchronous function to wrap.

    Returns:
        Async function that runs the sync function in a thread pool.
    """
    async def wrapper(*args: Any, **kwargs: Any) -> T:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None,
            lambda: func(*args, **kwargs),
        )
    return wrapper
