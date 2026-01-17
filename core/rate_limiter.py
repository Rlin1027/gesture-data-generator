"""Token bucket rate limiter for API request throttling."""

import threading
import time
from typing import Optional


class TokenBucketLimiter:
    """
    Token bucket rate limiter to ensure API requests stay within RPM limits.

    Uses the token bucket algorithm for smooth request distribution,
    avoiding burst traffic that could trigger rate limiting.

    Example:
        limiter = TokenBucketLimiter(rpm=60)
        for request in requests:
            limiter.acquire()  # Blocks if rate limit exceeded
            make_api_call(request)
    """

    def __init__(self, rpm: int = 60, burst_size: Optional[int] = None):
        """
        Initialize the rate limiter.

        Args:
            rpm: Maximum requests per minute allowed
            burst_size: Maximum tokens that can accumulate (defaults to rpm)
        """
        self.rpm = rpm
        self.burst_size = burst_size or rpm
        self.tokens = float(self.burst_size)
        self.last_refill = time.monotonic()
        self.lock = threading.Lock()

        # Calculate refill rate (tokens per second)
        self._refill_rate = rpm / 60.0

    def _refill(self) -> None:
        """Refill tokens based on elapsed time."""
        now = time.monotonic()
        elapsed = now - self.last_refill

        # Add tokens based on elapsed time
        new_tokens = elapsed * self._refill_rate
        self.tokens = min(self.burst_size, self.tokens + new_tokens)
        self.last_refill = now

    def acquire(self, tokens: int = 1, blocking: bool = True) -> bool:
        """
        Acquire tokens from the bucket.

        Args:
            tokens: Number of tokens to acquire (default: 1)
            blocking: If True, wait until tokens are available.
                     If False, return immediately with success/failure.

        Returns:
            True if tokens were acquired, False if non-blocking and unavailable
        """
        with self.lock:
            self._refill()

            if self.tokens >= tokens:
                self.tokens -= tokens
                return True

            if not blocking:
                return False

            # Calculate wait time needed
            tokens_needed = tokens - self.tokens
            wait_time = tokens_needed / self._refill_rate

        # Wait outside the lock
        time.sleep(wait_time)

        # Retry acquisition
        with self.lock:
            self._refill()
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            # Edge case: still not enough, recurse
            return self.acquire(tokens, blocking)

    def try_acquire(self, tokens: int = 1) -> bool:
        """
        Try to acquire tokens without blocking.

        Args:
            tokens: Number of tokens to acquire

        Returns:
            True if tokens were acquired, False otherwise
        """
        return self.acquire(tokens, blocking=False)

    @property
    def available_tokens(self) -> float:
        """Get current number of available tokens."""
        with self.lock:
            self._refill()
            return self.tokens

    def wait_time_for(self, tokens: int = 1) -> float:
        """
        Calculate wait time needed to acquire the specified tokens.

        Args:
            tokens: Number of tokens needed

        Returns:
            Seconds to wait (0 if tokens are available now)
        """
        with self.lock:
            self._refill()
            if self.tokens >= tokens:
                return 0.0
            tokens_needed = tokens - self.tokens
            return tokens_needed / self._refill_rate

    def reset(self) -> None:
        """Reset the limiter to full capacity."""
        with self.lock:
            self.tokens = float(self.burst_size)
            self.last_refill = time.monotonic()

    def __repr__(self) -> str:
        return (
            f"TokenBucketLimiter(rpm={self.rpm}, "
            f"burst_size={self.burst_size}, "
            f"available={self.available_tokens:.1f})"
        )
