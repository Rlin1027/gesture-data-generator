"""Batch processing engine for bulk image generation."""

import io
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime
from math import ceil
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from PIL import Image
from tqdm import tqdm

from config.schema import JobConfig
from core.metadata import MetadataCollector
from core.optimizer import CompressionConfig, ImageOptimizer, OutputFormat
from core.rate_limiter import TokenBucketLimiter
from gemini_client import GeminiClient
from utils import process_image, TARGET_SIZE


@dataclass
class BatchResult:
    """Result of a batch generation job."""
    success: bool
    total_requested: int
    total_generated: int
    total_failed: int
    output_directory: str
    metadata_files: Dict[str, Path]
    elapsed_seconds: float
    error: Optional[str] = None


class BatchProcessor:
    """
    Batch processing engine for bulk image generation.

    Handles parallel execution, rate limiting, progress tracking,
    and metadata collection for large-scale image generation jobs.

    Example:
        config = load_config("config/job.yaml")
        processor = BatchProcessor(config)
        result = processor.run()
        print(f"Generated {result.total_generated} images")
    """

    def __init__(
        self,
        config: JobConfig,
        config_file: str = "",
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ):
        """
        Initialize the batch processor.

        Args:
            config: Job configuration
            config_file: Path to the configuration file (for metadata)
            progress_callback: Optional callback for progress updates
                              Signature: (current, total, status_message)
        """
        self.config = config
        self.config_file = config_file
        self.progress_callback = progress_callback

        # Initialize components
        self.rate_limiter = TokenBucketLimiter(rpm=config.api.rate_limit)
        self.optimizer = ImageOptimizer(
            CompressionConfig(
                enabled=config.output.compression.enabled,
                png_level=config.output.compression.png_level,
                webp_quality=config.output.compression.webp_quality
            )
        )
        self.metadata = MetadataCollector(config.name, config_file)

        # Load input images
        self._seed_image: Optional[Image.Image] = None
        self._reference_image: Optional[Image.Image] = None

        # Statistics
        self._start_time: float = 0
        self._success_count: int = 0
        self._failure_count: int = 0

    def _load_images(self, base_path: Path) -> None:
        """Load seed and reference images."""
        seed_path = base_path / self.config.input.seed_image
        with open(seed_path, "rb") as f:
            self._seed_image = process_image(f)

        if self.config.input.reference_image:
            ref_path = base_path / self.config.input.reference_image
            with open(ref_path, "rb") as f:
                self._reference_image = process_image(f)

    def _create_client(self) -> GeminiClient:
        """Create a Gemini client with configured API key."""
        api_key = self.config.api.get_api_key()
        return GeminiClient(api_key, self.config.generation.model)

    def _generate_single(
        self,
        client: GeminiClient,
        batch_idx: int,
        idx_in_batch: int
    ) -> Tuple[Optional[Image.Image], float, Optional[str]]:
        """
        Generate a single image with retry logic.

        Returns:
            Tuple of (image, api_latency_ms, error_message)
        """
        last_error = None

        for attempt in range(self.config.api.retry_attempts + 1):
            try:
                # Wait for rate limit
                self.rate_limiter.acquire()

                start_time = time.monotonic()

                if self.config.mode == "variation":
                    result = client.generate_variation(
                        self._seed_image,
                        self.config.generation.prompt
                    )
                else:
                    result = client.modify_gesture(
                        self._seed_image,
                        self._reference_image,
                        self.config.generation.prompt
                    )

                latency_ms = (time.monotonic() - start_time) * 1000

                if result is not None:
                    return result, latency_ms, None

                last_error = "Model returned None (no image generated)"

            except Exception as e:
                last_error = str(e)

                # Check if we should retry
                if attempt < self.config.api.retry_attempts:
                    time.sleep(self.config.api.retry_delay)
                    continue

        return None, 0, last_error

    def _process_batch(
        self,
        client: GeminiClient,
        batch_idx: int,
        batch_size: int,
        output_dir: Path,
        pbar: Optional[tqdm] = None
    ) -> List[Dict[str, Any]]:
        """
        Process a single batch of images.

        Returns:
            List of result dictionaries
        """
        results = []

        for idx_in_batch in range(batch_size):
            global_idx = batch_idx * self.config.generation.batch_size + idx_in_batch + 1

            # Generate image
            image, api_latency, error = self._generate_single(
                client, batch_idx, idx_in_batch
            )

            if error:
                # Record failure
                self.metadata.add_error(
                    batch_index=batch_idx,
                    index_in_batch=idx_in_batch,
                    error=error,
                    mode=self.config.mode,
                    seed_image=self.config.input.seed_image,
                    prompt=self.config.generation.prompt,
                    model=self.config.generation.model,
                    reference_image=self.config.input.reference_image
                )
                self._failure_count += 1

                results.append({
                    "success": False,
                    "error": error,
                    "index": global_idx
                })

            else:
                # Optimize and save image
                opt_start = time.monotonic()
                optimized = self.optimizer.optimize(
                    image,
                    OutputFormat(self.config.output.format)
                    if self.config.output.format != "both"
                    else OutputFormat.BOTH
                )
                opt_time_ms = (time.monotonic() - opt_start) * 1000

                # Generate filename
                timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
                base_filename = self.config.output.naming.format(
                    job_name=self.config.name,
                    index=global_idx,
                    timestamp=timestamp
                )

                # Save each format
                saved_files = []
                for fmt, result in optimized.items():
                    filename = f"{base_filename}.{fmt}"
                    filepath = output_dir / "images" / filename

                    filepath.parent.mkdir(parents=True, exist_ok=True)
                    with open(filepath, "wb") as f:
                        f.write(result.data)

                    saved_files.append(filename)

                    # Record metadata for primary format
                    if fmt == self.config.output.format or self.config.output.format == "both":
                        self.metadata.add_image(
                            filename=filename,
                            mode=self.config.mode,
                            seed_image=self.config.input.seed_image,
                            prompt=self.config.generation.prompt,
                            model=self.config.generation.model,
                            batch_index=batch_idx,
                            index_in_batch=idx_in_batch,
                            output_format=fmt,
                            size_bytes=result.optimized_size,
                            dimensions=[image.width, image.height],
                            api_latency_ms=api_latency,
                            optimization_ms=opt_time_ms,
                            reference_image=self.config.input.reference_image
                        )

                self._success_count += 1
                results.append({
                    "success": True,
                    "files": saved_files,
                    "index": global_idx
                })

            # Update progress
            if pbar:
                pbar.update(1)
                pbar.set_postfix({
                    "成功": self._success_count,
                    "失敗": self._failure_count
                })

            if self.progress_callback:
                total = self.config.generation.count
                current = self._success_count + self._failure_count
                self.progress_callback(
                    current,
                    total,
                    f"處理中: {global_idx}/{total}"
                )

        return results

    def run(self, show_progress: bool = True) -> BatchResult:
        """
        Execute the batch generation job.

        Args:
            show_progress: Whether to show progress bar

        Returns:
            BatchResult with job statistics
        """
        self._start_time = time.monotonic()
        self._success_count = 0
        self._failure_count = 0

        try:
            # Validate configuration
            base_path = Path(self.config_file).parent if self.config_file else Path.cwd()
            errors = self.config.validate(base_path)
            if errors:
                return BatchResult(
                    success=False,
                    total_requested=0,
                    total_generated=0,
                    total_failed=0,
                    output_directory="",
                    metadata_files={},
                    elapsed_seconds=0,
                    error=f"Configuration errors: {'; '.join(errors)}"
                )

            # Load images
            self._load_images(base_path)

            # Create output directory
            output_dir = Path(self.config.output.directory)
            output_dir.mkdir(parents=True, exist_ok=True)
            (output_dir / "images").mkdir(exist_ok=True)

            # Create client
            client = self._create_client()

            # Calculate batches
            total_images = self.config.generation.count
            batch_size = self.config.generation.batch_size
            total_batches = ceil(total_images / batch_size)

            # Process batches with progress bar
            pbar = None
            if show_progress:
                pbar = tqdm(
                    total=total_images,
                    desc=f"🎨 {self.config.name}",
                    unit="張",
                    ncols=80
                )

            try:
                for batch_idx in range(total_batches):
                    # Calculate actual batch size (last batch may be smaller)
                    remaining = total_images - (batch_idx * batch_size)
                    current_batch_size = min(batch_size, remaining)

                    self._process_batch(
                        client,
                        batch_idx,
                        current_batch_size,
                        output_dir,
                        pbar
                    )

            finally:
                if pbar:
                    pbar.close()

            # Save metadata
            metadata_files = self.metadata.save_all(
                output_dir,
                self.config.output.format,
                self.config.metadata.format,
                self.config.metadata.include_prompt
            )

            elapsed = time.monotonic() - self._start_time

            return BatchResult(
                success=True,
                total_requested=total_images,
                total_generated=self._success_count,
                total_failed=self._failure_count,
                output_directory=str(output_dir),
                metadata_files=metadata_files,
                elapsed_seconds=elapsed
            )

        except Exception as e:
            elapsed = time.monotonic() - self._start_time
            return BatchResult(
                success=False,
                total_requested=self.config.generation.count,
                total_generated=self._success_count,
                total_failed=self._failure_count,
                output_directory=str(self.config.output.directory),
                metadata_files={},
                elapsed_seconds=elapsed,
                error=str(e)
            )

    def estimate_time(self) -> Dict[str, Any]:
        """
        Estimate job completion time.

        Returns:
            Dictionary with time estimates
        """
        total_images = self.config.generation.count
        rpm = self.config.api.rate_limit

        # Estimate based on rate limit
        seconds_per_request = 60 / rpm
        total_seconds = total_images * seconds_per_request

        return {
            "total_images": total_images,
            "rate_limit_rpm": rpm,
            "estimated_seconds": total_seconds,
            "estimated_minutes": total_seconds / 60,
            "estimated_formatted": self._format_time(total_seconds)
        }

    @staticmethod
    def _format_time(seconds: float) -> str:
        """Format seconds as human-readable time."""
        if seconds < 60:
            return f"{seconds:.0f} 秒"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f} 分鐘"
        else:
            hours = seconds / 3600
            return f"{hours:.1f} 小時"

    def print_summary(self, result: BatchResult) -> None:
        """Print a summary of the batch result."""
        if result.success:
            print(f"\n✅ 完成！")
            print(f"   ├─ 總生成: {result.total_generated}/{result.total_requested} "
                  f"({result.total_generated/result.total_requested*100:.1f}%)")
            print(f"   ├─ 失敗: {result.total_failed}")
            print(f"   ├─ 輸出目錄: {result.output_directory}")
            if "summary" in result.metadata_files:
                print(f"   ├─ 摘要: {result.metadata_files['summary']}")
            print(f"   └─ 耗時: {self._format_time(result.elapsed_seconds)}")
        else:
            print(f"\n❌ 任務失敗")
            print(f"   ├─ 錯誤: {result.error}")
            print(f"   ├─ 已生成: {result.total_generated}")
            print(f"   └─ 耗時: {self._format_time(result.elapsed_seconds)}")
