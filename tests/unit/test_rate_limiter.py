"""Unit tests for the TokenBucketLimiter."""

import time
import threading
import unittest

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.rate_limiter import TokenBucketLimiter


class TestTokenBucketLimiter(unittest.TestCase):
    """Tests for TokenBucketLimiter class."""

    def test_initialization(self):
        """Test limiter initializes with correct values."""
        limiter = TokenBucketLimiter(rpm=60)
        self.assertEqual(limiter.rpm, 60)
        self.assertEqual(limiter.burst_size, 60)
        self.assertAlmostEqual(limiter.available_tokens, 60, delta=0.1)

    def test_custom_burst_size(self):
        """Test limiter with custom burst size."""
        limiter = TokenBucketLimiter(rpm=60, burst_size=10)
        self.assertEqual(limiter.rpm, 60)
        self.assertEqual(limiter.burst_size, 10)
        self.assertAlmostEqual(limiter.available_tokens, 10, delta=0.1)

    def test_acquire_tokens(self):
        """Test acquiring tokens reduces available count."""
        limiter = TokenBucketLimiter(rpm=60)
        initial = limiter.available_tokens

        limiter.acquire(1)
        self.assertAlmostEqual(limiter.available_tokens, initial - 1, delta=0.1)

    def test_try_acquire_success(self):
        """Test try_acquire returns True when tokens available."""
        limiter = TokenBucketLimiter(rpm=60)
        self.assertTrue(limiter.try_acquire(1))

    def test_try_acquire_failure(self):
        """Test try_acquire returns False when tokens unavailable."""
        limiter = TokenBucketLimiter(rpm=60, burst_size=2)
        # Consume all tokens
        limiter.acquire(2)
        # Should fail without blocking
        self.assertFalse(limiter.try_acquire(1))

    def test_token_refill(self):
        """Test tokens refill over time."""
        limiter = TokenBucketLimiter(rpm=600)  # 10 tokens per second
        limiter.acquire(5)

        initial = limiter.available_tokens
        time.sleep(0.1)  # Wait 100ms

        # Should have refilled approximately 1 token
        self.assertGreater(limiter.available_tokens, initial)

    def test_wait_time_for(self):
        """Test wait time calculation."""
        limiter = TokenBucketLimiter(rpm=60, burst_size=1)
        limiter.acquire(1)  # Empty the bucket

        wait_time = limiter.wait_time_for(1)
        # Should need to wait ~1 second for 1 token at 60 RPM
        self.assertGreater(wait_time, 0.5)
        self.assertLess(wait_time, 2.0)

    def test_reset(self):
        """Test reset restores full capacity."""
        limiter = TokenBucketLimiter(rpm=60, burst_size=10)
        limiter.acquire(10)  # Empty
        self.assertAlmostEqual(limiter.available_tokens, 0, delta=0.1)

        limiter.reset()
        self.assertAlmostEqual(limiter.available_tokens, 10, delta=0.1)

    def test_thread_safety(self):
        """Test limiter is thread-safe."""
        limiter = TokenBucketLimiter(rpm=6000, burst_size=100)  # Fast refill
        acquired = []

        def acquire_tokens():
            for _ in range(10):
                limiter.acquire(1)
                acquired.append(1)

        threads = [threading.Thread(target=acquire_tokens) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(acquired), 50)

    def test_repr(self):
        """Test string representation."""
        limiter = TokenBucketLimiter(rpm=60)
        repr_str = repr(limiter)
        self.assertIn("rpm=60", repr_str)
        self.assertIn("TokenBucketLimiter", repr_str)


if __name__ == "__main__":
    unittest.main()
