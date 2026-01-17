"""Image optimization module for compression and format conversion."""

import io
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional, Union

from PIL import Image


class OutputFormat(Enum):
    """Supported output formats."""
    PNG = "png"
    WEBP = "webp"
    BOTH = "both"


@dataclass
class CompressionConfig:
    """Configuration for image compression."""
    enabled: bool = True
    png_level: int = 6  # 0-9, higher = more compression
    webp_quality: int = 85  # 1-100, higher = better quality

    def __post_init__(self):
        """Validate compression settings."""
        if not 0 <= self.png_level <= 9:
            raise ValueError(f"png_level must be 0-9, got {self.png_level}")
        if not 1 <= self.webp_quality <= 100:
            raise ValueError(f"webp_quality must be 1-100, got {self.webp_quality}")


@dataclass
class OptimizationResult:
    """Result of image optimization."""
    format: str
    data: bytes
    original_size: int
    optimized_size: int

    @property
    def compression_ratio(self) -> float:
        """Calculate compression ratio (0-1, lower is better)."""
        if self.original_size == 0:
            return 1.0
        return self.optimized_size / self.original_size

    @property
    def space_saved_percent(self) -> float:
        """Calculate percentage of space saved."""
        return (1 - self.compression_ratio) * 100


class ImageOptimizer:
    """
    Image optimizer for compression and format conversion.

    Supports PNG compression and WebP conversion for reducing
    file sizes while maintaining acceptable quality.

    Example:
        optimizer = ImageOptimizer(CompressionConfig(png_level=6))
        results = optimizer.optimize(image, format=OutputFormat.BOTH)
        for fmt, result in results.items():
            print(f"{fmt}: {result.space_saved_percent:.1f}% saved")
    """

    def __init__(self, config: Optional[CompressionConfig] = None):
        """
        Initialize the optimizer.

        Args:
            config: Compression configuration (uses defaults if not provided)
        """
        self.config = config or CompressionConfig()

    def _get_image_bytes(self, image: Image.Image) -> int:
        """Get the uncompressed size estimate of an image."""
        # Estimate based on dimensions and mode
        width, height = image.size
        channels = len(image.getbands())
        return width * height * channels

    def _compress_png(self, image: Image.Image) -> bytes:
        """
        Compress image as PNG.

        Args:
            image: PIL Image to compress

        Returns:
            Compressed PNG bytes
        """
        buffer = io.BytesIO()

        # Ensure image is in a PNG-compatible mode
        if image.mode == "RGBA":
            save_image = image
        elif image.mode == "LA":
            save_image = image.convert("RGBA")
        elif image.mode == "L":
            save_image = image
        else:
            save_image = image.convert("RGB")

        save_image.save(
            buffer,
            format="PNG",
            optimize=self.config.enabled,
            compress_level=self.config.png_level if self.config.enabled else 6
        )

        return buffer.getvalue()

    def _compress_webp(self, image: Image.Image) -> bytes:
        """
        Compress image as WebP.

        Args:
            image: PIL Image to compress

        Returns:
            Compressed WebP bytes
        """
        buffer = io.BytesIO()

        # WebP supports RGB, RGBA, and grayscale
        if image.mode not in ("RGB", "RGBA", "L"):
            if image.mode == "LA":
                save_image = image.convert("RGBA")
            else:
                save_image = image.convert("RGB")
        else:
            save_image = image

        save_image.save(
            buffer,
            format="WEBP",
            quality=self.config.webp_quality if self.config.enabled else 85,
            method=6 if self.config.enabled else 4  # Higher method = better compression
        )

        return buffer.getvalue()

    def optimize(
        self,
        image: Image.Image,
        output_format: Union[OutputFormat, str] = OutputFormat.PNG
    ) -> Dict[str, OptimizationResult]:
        """
        Optimize an image with compression.

        Args:
            image: PIL Image to optimize
            output_format: Desired output format(s)

        Returns:
            Dictionary mapping format name to OptimizationResult
        """
        if isinstance(output_format, str):
            output_format = OutputFormat(output_format.lower())

        # Estimate original size
        original_size = self._get_image_bytes(image)

        results = {}

        if output_format in (OutputFormat.PNG, OutputFormat.BOTH):
            png_data = self._compress_png(image)
            results["png"] = OptimizationResult(
                format="png",
                data=png_data,
                original_size=original_size,
                optimized_size=len(png_data)
            )

        if output_format in (OutputFormat.WEBP, OutputFormat.BOTH):
            webp_data = self._compress_webp(image)
            results["webp"] = OptimizationResult(
                format="webp",
                data=webp_data,
                original_size=original_size,
                optimized_size=len(webp_data)
            )

        return results

    def optimize_bytes(
        self,
        image_bytes: bytes,
        output_format: Union[OutputFormat, str] = OutputFormat.PNG
    ) -> Dict[str, OptimizationResult]:
        """
        Optimize an image from bytes.

        Args:
            image_bytes: Raw image bytes
            output_format: Desired output format(s)

        Returns:
            Dictionary mapping format name to OptimizationResult
        """
        image = Image.open(io.BytesIO(image_bytes))
        return self.optimize(image, output_format)

    @staticmethod
    def estimate_savings(
        image_count: int,
        avg_size_kb: float = 25,
        output_format: OutputFormat = OutputFormat.PNG,
        png_level: int = 6,
        webp_quality: int = 85
    ) -> Dict[str, float]:
        """
        Estimate storage savings for a batch of images.

        Args:
            image_count: Number of images
            avg_size_kb: Average uncompressed size in KB
            output_format: Output format
            png_level: PNG compression level
            webp_quality: WebP quality setting

        Returns:
            Dictionary with estimated sizes in MB
        """
        total_original_mb = image_count * avg_size_kb / 1024

        # Empirical compression ratios (approximate)
        png_ratio = 0.72 - (png_level * 0.02)  # ~28-40% savings
        webp_ratio = 0.32 + (webp_quality - 85) * 0.005  # ~60-70% savings

        estimates = {
            "original_mb": total_original_mb,
        }

        if output_format in (OutputFormat.PNG, OutputFormat.BOTH):
            estimates["png_mb"] = total_original_mb * png_ratio
            estimates["png_saved_mb"] = total_original_mb * (1 - png_ratio)

        if output_format in (OutputFormat.WEBP, OutputFormat.BOTH):
            estimates["webp_mb"] = total_original_mb * webp_ratio
            estimates["webp_saved_mb"] = total_original_mb * (1 - webp_ratio)

        return estimates

    def __repr__(self) -> str:
        return (
            f"ImageOptimizer(enabled={self.config.enabled}, "
            f"png_level={self.config.png_level}, "
            f"webp_quality={self.config.webp_quality})"
        )
