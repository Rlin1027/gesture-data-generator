"""Metadata collection and output for batch generation."""

import csv
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional


@dataclass
class ImageMetadata:
    """Metadata for a single generated image."""
    id: str
    filename: str
    generated_at: str
    mode: str
    seed_image: str
    reference_image: Optional[str]
    prompt: str
    model: str
    batch_index: int
    index_in_batch: int
    output_format: str
    size_bytes: int
    dimensions: List[int]
    api_latency_ms: float
    optimization_ms: float
    success: bool = True
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "filename": self.filename,
            "generated_at": self.generated_at,
            "generation": {
                "mode": self.mode,
                "seed_image": self.seed_image,
                "reference_image": self.reference_image,
                "prompt": self.prompt,
                "model": self.model,
                "batch_index": self.batch_index,
                "index_in_batch": self.index_in_batch
            },
            "output": {
                "format": self.output_format,
                "size_bytes": self.size_bytes,
                "dimensions": self.dimensions
            },
            "timing": {
                "api_latency_ms": self.api_latency_ms,
                "optimization_ms": self.optimization_ms
            },
            "success": self.success,
            "error": self.error
        }

    def to_flat_dict(self) -> Dict[str, Any]:
        """Convert to flat dictionary for CSV output."""
        return {
            "id": self.id,
            "filename": self.filename,
            "generated_at": self.generated_at,
            "mode": self.mode,
            "seed_image": self.seed_image,
            "reference_image": self.reference_image or "",
            "prompt": self.prompt[:100] + "..." if len(self.prompt) > 100 else self.prompt,
            "model": self.model,
            "batch_index": self.batch_index,
            "index_in_batch": self.index_in_batch,
            "output_format": self.output_format,
            "size_bytes": self.size_bytes,
            "width": self.dimensions[0] if self.dimensions else 0,
            "height": self.dimensions[1] if len(self.dimensions) > 1 else 0,
            "api_latency_ms": self.api_latency_ms,
            "optimization_ms": self.optimization_ms,
            "success": self.success,
            "error": self.error or ""
        }


@dataclass
class JobSummary:
    """Summary statistics for a batch generation job."""
    job_name: str
    started_at: str
    completed_at: str
    config_file: str
    total_requested: int
    total_generated: int
    total_failed: int
    success_rate: float
    total_time_seconds: float
    avg_time_per_image_ms: float
    total_size_bytes: int
    avg_size_bytes: float
    output_format: str
    output_directory: str
    errors: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "job_name": self.job_name,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "config_file": self.config_file,
            "statistics": {
                "total_requested": self.total_requested,
                "total_generated": self.total_generated,
                "total_failed": self.total_failed,
                "success_rate": self.success_rate,
                "total_time_seconds": self.total_time_seconds,
                "avg_time_per_image_ms": self.avg_time_per_image_ms
            },
            "storage": {
                "total_size_mb": self.total_size_bytes / (1024 * 1024),
                "avg_size_kb": self.avg_size_bytes / 1024,
                "format": self.output_format
            },
            "output_directory": self.output_directory,
            "errors": self.errors
        }


class MetadataCollector:
    """
    Collects and manages metadata for batch generation jobs.

    Handles storing individual image metadata and generating
    summary statistics and output files.
    """

    def __init__(self, job_name: str, config_file: str = ""):
        """
        Initialize the metadata collector.

        Args:
            job_name: Name of the batch job
            config_file: Path to the configuration file used
        """
        self.job_name = job_name
        self.config_file = config_file
        self.started_at = datetime.utcnow().isoformat() + "Z"
        self.images: List[ImageMetadata] = []
        self._index_counter = 0

    def add_image(
        self,
        filename: str,
        mode: str,
        seed_image: str,
        prompt: str,
        model: str,
        batch_index: int,
        index_in_batch: int,
        output_format: str,
        size_bytes: int,
        dimensions: List[int],
        api_latency_ms: float,
        optimization_ms: float,
        reference_image: Optional[str] = None,
        success: bool = True,
        error: Optional[str] = None
    ) -> ImageMetadata:
        """
        Add metadata for a generated image.

        Returns:
            The created ImageMetadata object
        """
        self._index_counter += 1
        image_id = f"{self.job_name}_{self._index_counter:04d}"

        metadata = ImageMetadata(
            id=image_id,
            filename=filename,
            generated_at=datetime.utcnow().isoformat() + "Z",
            mode=mode,
            seed_image=seed_image,
            reference_image=reference_image,
            prompt=prompt,
            model=model,
            batch_index=batch_index,
            index_in_batch=index_in_batch,
            output_format=output_format,
            size_bytes=size_bytes,
            dimensions=dimensions,
            api_latency_ms=api_latency_ms,
            optimization_ms=optimization_ms,
            success=success,
            error=error
        )

        self.images.append(metadata)
        return metadata

    def add_error(
        self,
        batch_index: int,
        index_in_batch: int,
        error: str,
        mode: str,
        seed_image: str,
        prompt: str,
        model: str,
        reference_image: Optional[str] = None
    ) -> ImageMetadata:
        """Add metadata for a failed generation."""
        return self.add_image(
            filename="",
            mode=mode,
            seed_image=seed_image,
            prompt=prompt,
            model=model,
            batch_index=batch_index,
            index_in_batch=index_in_batch,
            output_format="",
            size_bytes=0,
            dimensions=[0, 0],
            api_latency_ms=0,
            optimization_ms=0,
            reference_image=reference_image,
            success=False,
            error=error
        )

    def get_summary(self, output_directory: str, output_format: str) -> JobSummary:
        """Generate summary statistics for the job."""
        completed_at = datetime.utcnow().isoformat() + "Z"

        successful = [img for img in self.images if img.success]
        failed = [img for img in self.images if not img.success]

        total_size = sum(img.size_bytes for img in successful)
        total_api_time = sum(img.api_latency_ms for img in successful)
        total_opt_time = sum(img.optimization_ms for img in successful)

        # Calculate total time from timestamps
        start = datetime.fromisoformat(self.started_at.replace("Z", "+00:00"))
        end = datetime.fromisoformat(completed_at.replace("Z", "+00:00"))
        total_seconds = (end - start).total_seconds()

        errors = [
            {
                "index": img.batch_index * 4 + img.index_in_batch,
                "batch_index": img.batch_index,
                "error": img.error
            }
            for img in failed
        ]

        return JobSummary(
            job_name=self.job_name,
            started_at=self.started_at,
            completed_at=completed_at,
            config_file=self.config_file,
            total_requested=len(self.images),
            total_generated=len(successful),
            total_failed=len(failed),
            success_rate=len(successful) / len(self.images) if self.images else 0,
            total_time_seconds=total_seconds,
            avg_time_per_image_ms=(total_api_time + total_opt_time) / len(successful) if successful else 0,
            total_size_bytes=total_size,
            avg_size_bytes=total_size / len(successful) if successful else 0,
            output_format=output_format,
            output_directory=output_directory,
            errors=errors
        )

    def save_json(self, output_path: Path, include_prompt: bool = True) -> None:
        """
        Save metadata as JSON file.

        Args:
            output_path: Path to save the JSON file
            include_prompt: Whether to include full prompt in output
        """
        data = []
        for img in self.images:
            img_dict = img.to_dict()
            if not include_prompt:
                img_dict["generation"]["prompt"] = "[redacted]"
            data.append(img_dict)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def save_csv(self, output_path: Path) -> None:
        """
        Save metadata as CSV file.

        Args:
            output_path: Path to save the CSV file
        """
        if not self.images:
            return

        output_path.parent.mkdir(parents=True, exist_ok=True)

        fieldnames = list(self.images[0].to_flat_dict().keys())

        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for img in self.images:
                writer.writerow(img.to_flat_dict())

    def save_summary(self, output_path: Path, output_directory: str, output_format: str) -> None:
        """
        Save job summary as JSON file.

        Args:
            output_path: Path to save the summary JSON
            output_directory: Output directory for the job
            output_format: Output image format
        """
        summary = self.get_summary(output_directory, output_format)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(summary.to_dict(), f, indent=2, ensure_ascii=False)

    def save_all(
        self,
        output_dir: Path,
        output_format: str,
        metadata_format: Literal["json", "csv", "both"] = "json",
        include_prompt: bool = True
    ) -> Dict[str, Path]:
        """
        Save all metadata files.

        Args:
            output_dir: Directory to save metadata files
            output_format: Image output format (for summary)
            metadata_format: Metadata output format
            include_prompt: Whether to include prompts in output

        Returns:
            Dictionary mapping file type to saved path
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        saved_files = {}

        # Save JSON if requested
        if metadata_format in ("json", "both"):
            json_path = output_dir / "metadata.json"
            self.save_json(json_path, include_prompt)
            saved_files["metadata_json"] = json_path

        # Save CSV if requested
        if metadata_format in ("csv", "both"):
            csv_path = output_dir / "metadata.csv"
            self.save_csv(csv_path)
            saved_files["metadata_csv"] = csv_path

        # Always save summary
        summary_path = output_dir / "summary.json"
        self.save_summary(summary_path, str(output_dir), output_format)
        saved_files["summary"] = summary_path

        return saved_files

    @property
    def success_count(self) -> int:
        """Get count of successful generations."""
        return sum(1 for img in self.images if img.success)

    @property
    def failure_count(self) -> int:
        """Get count of failed generations."""
        return sum(1 for img in self.images if not img.success)

    def __len__(self) -> int:
        return len(self.images)
