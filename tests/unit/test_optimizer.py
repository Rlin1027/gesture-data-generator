"""Unit tests for the ImageOptimizer."""

import io
import unittest

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from PIL import Image
from core.optimizer import (
    CompressionConfig,
    ImageOptimizer,
    OptimizationResult,
    OutputFormat,
)


class TestCompressionConfig(unittest.TestCase):
    """Tests for CompressionConfig dataclass."""

    def test_default_values(self):
        """Test default configuration values."""
        config = CompressionConfig()
        self.assertTrue(config.enabled)
        self.assertEqual(config.png_level, 6)
        self.assertEqual(config.webp_quality, 85)

    def test_custom_values(self):
        """Test custom configuration values."""
        config = CompressionConfig(enabled=False, png_level=9, webp_quality=50)
        self.assertFalse(config.enabled)
        self.assertEqual(config.png_level, 9)
        self.assertEqual(config.webp_quality, 50)

    def test_invalid_png_level(self):
        """Test validation of png_level range."""
        with self.assertRaises(ValueError):
            CompressionConfig(png_level=10)
        with self.assertRaises(ValueError):
            CompressionConfig(png_level=-1)

    def test_invalid_webp_quality(self):
        """Test validation of webp_quality range."""
        with self.assertRaises(ValueError):
            CompressionConfig(webp_quality=101)
        with self.assertRaises(ValueError):
            CompressionConfig(webp_quality=0)


class TestOptimizationResult(unittest.TestCase):
    """Tests for OptimizationResult dataclass."""

    def test_compression_ratio(self):
        """Test compression ratio calculation."""
        result = OptimizationResult(
            format="png",
            data=b"test",
            original_size=100,
            optimized_size=70
        )
        self.assertAlmostEqual(result.compression_ratio, 0.7, delta=0.01)

    def test_space_saved_percent(self):
        """Test space saved percentage calculation."""
        result = OptimizationResult(
            format="png",
            data=b"test",
            original_size=100,
            optimized_size=70
        )
        self.assertAlmostEqual(result.space_saved_percent, 30.0, delta=0.1)

    def test_zero_original_size(self):
        """Test handling of zero original size."""
        result = OptimizationResult(
            format="png",
            data=b"test",
            original_size=0,
            optimized_size=0
        )
        self.assertEqual(result.compression_ratio, 1.0)


class TestImageOptimizer(unittest.TestCase):
    """Tests for ImageOptimizer class."""

    def setUp(self):
        """Create test image."""
        self.test_image = Image.new("L", (320, 180), color=128)
        self.optimizer = ImageOptimizer()

    def test_default_config(self):
        """Test optimizer uses default config."""
        optimizer = ImageOptimizer()
        self.assertTrue(optimizer.config.enabled)

    def test_custom_config(self):
        """Test optimizer with custom config."""
        config = CompressionConfig(png_level=9)
        optimizer = ImageOptimizer(config)
        self.assertEqual(optimizer.config.png_level, 9)

    def test_optimize_png(self):
        """Test PNG optimization."""
        results = self.optimizer.optimize(self.test_image, OutputFormat.PNG)

        self.assertIn("png", results)
        self.assertIsInstance(results["png"], OptimizationResult)
        self.assertEqual(results["png"].format, "png")
        self.assertGreater(len(results["png"].data), 0)

    def test_optimize_webp(self):
        """Test WebP optimization."""
        results = self.optimizer.optimize(self.test_image, OutputFormat.WEBP)

        self.assertIn("webp", results)
        self.assertIsInstance(results["webp"], OptimizationResult)
        self.assertEqual(results["webp"].format, "webp")
        self.assertGreater(len(results["webp"].data), 0)

    def test_optimize_both(self):
        """Test both format optimization."""
        results = self.optimizer.optimize(self.test_image, OutputFormat.BOTH)

        self.assertIn("png", results)
        self.assertIn("webp", results)

    def test_optimize_string_format(self):
        """Test optimization with string format."""
        results = self.optimizer.optimize(self.test_image, "png")
        self.assertIn("png", results)

    def test_optimize_bytes(self):
        """Test optimization from bytes."""
        # Create image bytes
        buffer = io.BytesIO()
        self.test_image.save(buffer, format="PNG")
        image_bytes = buffer.getvalue()

        results = self.optimizer.optimize_bytes(image_bytes, OutputFormat.PNG)
        self.assertIn("png", results)

    def test_both_formats_produced(self):
        """Test that both formats are produced with valid data."""
        # Create a more complex image
        img = Image.new("RGB", (320, 180))
        for x in range(320):
            for y in range(180):
                img.putpixel((x, y), (x % 256, y % 256, (x + y) % 256))

        results = self.optimizer.optimize(img, OutputFormat.BOTH)

        # Both formats should be produced with valid data
        self.assertIn("png", results)
        self.assertIn("webp", results)
        self.assertGreater(results["png"].optimized_size, 0)
        self.assertGreater(results["webp"].optimized_size, 0)

    def test_estimate_savings(self):
        """Test storage savings estimation."""
        estimates = ImageOptimizer.estimate_savings(
            image_count=100,
            avg_size_kb=25,
            output_format=OutputFormat.BOTH
        )

        self.assertIn("original_mb", estimates)
        self.assertIn("png_mb", estimates)
        self.assertIn("webp_mb", estimates)
        self.assertLess(estimates["webp_mb"], estimates["png_mb"])

    def test_repr(self):
        """Test string representation."""
        repr_str = repr(self.optimizer)
        self.assertIn("ImageOptimizer", repr_str)
        self.assertIn("enabled=True", repr_str)


if __name__ == "__main__":
    unittest.main()
