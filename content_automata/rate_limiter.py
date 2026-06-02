"""API rate limiting handling for external provider calls.

Provides token-bucket and sliding-window rate limiters to
prevent hitting API rate limits across content-automata
providers. Includes configurable limits, backoff strategies,
and per-provider tracking.
"""

from __future__ import annotations

import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from threading import Lock
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """Configuration for a rate-limited API endpoint."""

    calls_per_minute: int = 60
    calls_per_hour: int = 1000
    burst_size: int = 10
    cooldown_seconds: float = 1.0
    max_retries: int = 3
    backoff_base: float = 1.0
    backoff_multiplier: float = 2.0
    backoff_max: float = 60.0


class TokenBucket:
    """Token bucket rate limiter.

    Tokens are added at a fixed rate. Each API call consumes
    one token. If no tokens are available, the call blocks
    or raises depending on configuration.
    """

    def __init__(self, rate: float, burst: int):
        """Initialize token bucket.

        Args:
            rate: Token refill rate per second.
            burst: Maximum token capacity (burst size).
        """
        self._rate = rate
        self._burst = burst
        self._tokens = float(burst)
        self._last_refill = time.monotonic()
        self._lock = Lock()

    def _refill(self) -> None:
        """Refill tokens based on elapsed time."""
        now = time.monotonic()
        elapsed = now - self._last_refill
        self._tokens = min(self._burst, self._tokens + elapsed * self._rate)
        self._last_refill = now

    def acquire(self, tokens: int = 1, block: bool = True, timeout: float = 30.0) -> bool:
        """Acquire tokens for an API call.

        Args:
            tokens: Number of tokens to consume.
            block: If True, block until tokens available.
            timeout: Maximum seconds to wait if blocking.

        Returns:
            True if tokens acquired, False if timeout.
        """
        deadline = time.monotonic() + timeout

        with self._lock:
            while True:
                self._refill()
                if self._tokens >= tokens:
                    self._tokens -= tokens
                    return True

                if not block:
                    return False

                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    return False

                # Sleep a bit and retry
                sleep_time = min(0.1, remaining)
                time.sleep(sleep_time)

    @property
    def available_tokens(self) -> float:
        """Get the current number of available tokens.

        Returns:
            Float number of tokens currently available.
        """
        with self._lock:
            self._refill()
            return self._tokens


class SlidingWindowCounter:
    """Sliding window rate limiter using a counter.

    Tracks API calls in a fixed window and resets periodically.
    Simpler than token bucket but effective for per-minute limits.
    """

    def __init__(self, max_calls: int, window_seconds: float = 60.0):
        """Initialize sliding window counter.

        Args:
            max_calls: Maximum calls allowed in the window.
            window_seconds: Window duration in seconds.
        """
        self._max_calls = max_calls
        self._window = window_seconds
        self._count = 0
        self._window_start = time.monotonic()
        self._lock = Lock()

    def allow(self) -> bool:
        """Check if a call is allowed.

        Returns:
            True if within the rate limit, False otherwise.
        """
        with self._lock:
            now = time.monotonic()
            if now - self._window_start >= self._window:
                self._count = 0
                self._window_start = now

            if self._count < self._max_calls:
                self._count += 1
                return True
            return False

    @property
    def remaining(self) -> int:
        """Get remaining calls allowed in this window.

        Returns:
            Integer number of remaining calls.
        """
        with self._lock:
            now = time.monotonic()
            if now - self._window_start >= self._window:
                return self._max_calls
            return max(0, self._max_calls - self._count)

    @property
    def reset_in(self) -> float:
        """Get seconds until the window resets.

        Returns:
            Float seconds until window reset.
        """
        with self._lock:
            elapsed = time.monotonic() - self._window_start
            return max(0.0, self._window - elapsed)


class RateLimiter:
    """Combined rate limiter with per-provider tracking.

    Supports multiple rate limiting strategies and provides
    a unified interface for API call management across
    different content-automata providers.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the rate limiter.

        Args:
            config: Optional configuration dictionary keyed by
                    provider name with RateLimitConfig values.
        """
        self._config: Dict[str, RateLimitConfig] = {}
        self._buckets: Dict[str, TokenBucket] = {}
        self._windows: Dict[str, SlidingWindowCounter] = {}
        self._lock = Lock()
        self._call_counts: Dict[str, int] = defaultdict(int)
        self._last_call_time: Dict[str, float] = {}
        self._error_counts: Dict[str, int] = defaultdict(int)

        if config:
            for provider, cfg in config.items():
                if isinstance(cfg, dict):
                    self._config[provider] = RateLimitConfig(**cfg)
                elif isinstance(cfg, RateLimitConfig):
                    self._config[provider] = cfg

    def register_provider(
        self,
        provider: str,
        config: Optional[RateLimitConfig] = None,
    ) -> None:
        """Register a provider with rate limiting.

        Args:
            provider: Provider name (e.g., 'openai', 'tavily').
            config: Rate limit configuration. Uses defaults if None.
        """
        cfg = config or RateLimitConfig()
        self._config[provider] = cfg
        self._buckets[provider] = TokenBucket(
            rate=cfg.calls_per_minute / 60.0,
            burst=cfg.burst_size,
        )
        self._windows[provider] = SlidingWindowCounter(
            max_calls=cfg.calls_per_minute,
            window_seconds=60.0,
        )
        logger.info(
            "Registered rate limiter for '%s': %d calls/min, burst=%d",
            provider,
            cfg.calls_per_minute,
            cfg.burst_size,
        )

    def acquire(self, provider: str, count: int = 1, block: bool = True) -> bool:
        """Acquire rate limit capacity for a provider call.

        Args:
            provider: Provider name.
            count: Number of tokens/calls to acquire.
            block: If True, wait until capacity available.

        Returns:
            True if capacity acquired, False if rate limited.
        """
        # Auto-register if not already
        if provider not in self._buckets:
            self.register_provider(provider)

        bucket = self._buckets[provider]
        window = self._windows[provider]

        # Check both limiters
        if not bucket.acquire(count, block=block):
            logger.warning("Token bucket exhausted for '%s'", provider)
            return False

        if not window.allow():
            logger.warning("Sliding window limit reached for '%s'", provider)
            return False

        with self._lock:
            self._call_counts[provider] += count
            self._last_call_time[provider] = time.monotonic()

        return True

    def wait_if_needed(self, provider: str) -> Optional[float]:
        """Wait the required cooldown before the next call.

        Args:
            provider: Provider name.

        Returns:
            Seconds waited, or None if not needed.
        """
        with self._lock:
            last_call = self._last_call_time.get(provider, 0.0)
            cfg = self._config.get(provider, RateLimitConfig())
            elapsed = time.monotonic() - last_call

            if elapsed < cfg.cooldown_seconds:
                wait_time = cfg.cooldown_seconds - elapsed
                time.sleep(wait_time)
                return wait_time

        return None

    def record_error(self, provider: str) -> int:
        """Record an API error for a provider.

        Increments the error counter and logs a warning.
        Used for adaptive backoff.

        Args:
            provider: Provider name.

        Returns:
            Current error count for the provider.
        """
        with self._lock:
            self._error_counts[provider] += 1
            count = self._error_counts[provider]
            logger.warning(
                "Rate limiter error count for '%s': %d",
                provider,
                count,
            )
            return count

    def record_success(self, provider: str) -> None:
        """Record a successful API call and reset error count.

        Args:
            provider: Provider name.
        """
        with self._lock:
            self._error_counts[provider] = 0

    def get_backoff_delay(self, provider: str) -> float:
        """Calculate backoff delay based on error count.

        Uses exponential backoff: base * multiplier^errors.

        Args:
            provider: Provider name.

        Returns:
            Delay in seconds before retrying.
        """
        cfg = self._config.get(provider, RateLimitConfig())
        with self._lock:
            errors = self._error_counts.get(provider, 0)

        delay = cfg.backoff_base * (cfg.backoff_multiplier ** errors)
        return min(delay, cfg.backoff_max)

    def reset(self, provider: Optional[str] = None) -> None:
        """Reset rate limiter state.

        Args:
            provider: Provider to reset, or None for all.
        """
        if provider:
            if provider in self._buckets:
                self._buckets[provider] = TokenBucket(
                    rate=self._config.get(provider, RateLimitConfig()).calls_per_minute / 60.0,
                    burst=self._config.get(provider, RateLimitConfig()).burst_size,
                )
                self._windows[provider] = SlidingWindowCounter(
                    max_calls=self._config.get(provider, RateLimitConfig()).calls_per_minute,
                    window_seconds=60.0,
                )
                self._call_counts[provider] = 0
                self._error_counts[provider] = 0
        else:
            self._buckets.clear()
            self._windows.clear()
            self._call_counts.clear()
            self._error_counts.clear()
            self._last_call_time.clear()

    def get_stats(self, provider: str) -> Dict[str, Any]:
        """Get rate limit statistics for a provider.

        Args:
            provider: Provider name.

        Returns:
            Dictionary of statistics.
        """
        bucket = self._buckets.get(provider)
        window = self._windows.get(provider)
        cfg = self._config.get(provider, RateLimitConfig())

        return {
            "provider": provider,
            "calls_per_minute_limit": cfg.calls_per_minute,
            "available_tokens": bucket.available_tokens if bucket else 0.0,
            "burst_size": cfg.burst_size,
            "window_remaining": window.remaining if window else 0,
            "window_reset_in": window.reset_in if window else 0.0,
            "total_calls": self._call_counts.get(provider, 0),
            "error_count": self._error_counts.get(provider, 0),
            "backoff_delay": self.get_backoff_delay(provider),
        }


# Global rate limiter instance
_default_limiter = RateLimiter()


def get_rate_limiter() -> RateLimiter:
    """Get the global rate limiter instance.

    Returns:
        The shared RateLimiter instance.
    """
    return _default_limiter


def rate_limited(
    provider: str,
    max_retries: Optional[int] = None,
) -> Callable:
    """Decorator for rate-limiting API calls.

    Args:
        provider: Provider name for rate limit tracking.
        max_retries: Maximum retry attempts (overrides config).

    Returns:
        Decorated function with rate limiting applied.
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            limiter = get_rate_limiter()
            cfg = limiter._config.get(provider, RateLimitConfig())
            retries = max_retries if max_retries is not None else cfg.max_retries
            last_error: Optional[Exception] = None

            for attempt in range(retries + 1):
                # Wait cooldown
                limiter.wait_if_needed(provider)

                # Acquire rate limit capacity
                if not limiter.acquire(provider, block=True):
                    delay = limiter.get_backoff_delay(provider)
                    logger.warning(
                        "Rate limited on '%s', backing off %.1fs (attempt %d/%d)",
                        provider,
                        delay,
                        attempt + 1,
                        retries + 1,
                    )
                    time.sleep(delay)
                    continue

                try:
                    result = func(*args, **kwargs)
                    limiter.record_success(provider)
                    return result
                except Exception as e:
                    last_error = e
                    limiter.record_error(provider)
                    delay = limiter.get_backoff_delay(provider)
                    logger.warning(
                        "API call failed for '%s' (attempt %d/%d): %s. "
                        "Backing off %.1fs",
                        provider,
                        attempt + 1,
                        retries + 1,
                        e,
                        delay,
                    )
                    if attempt < retries:
                        time.sleep(delay)

            raise last_error or RuntimeError(f"Rate limited call failed for '{provider}'")

        return wrapper
    return decorator
