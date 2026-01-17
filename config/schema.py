"""Configuration schema and validation for batch generation jobs."""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Union

import yaml


@dataclass
class InputConfig:
    """Input configuration for image sources."""
    seed_image: str
    reference_image: Optional[str] = None

    def validate(self, base_path: Path) -> List[str]:
        """Validate input configuration."""
        errors = []

        seed_path = base_path / self.seed_image
        if not seed_path.exists():
            errors.append(f"Seed image not found: {self.seed_image}")

        if self.reference_image:
            ref_path = base_path / self.reference_image
            if not ref_path.exists():
                errors.append(f"Reference image not found: {self.reference_image}")

        return errors


@dataclass
class GenerationConfig:
    """Generation parameters configuration."""
    count: int
    batch_size: int = 4
    prompt: str = ""
    model: str = "gemini-2.0-flash-exp-image-generation"

    def validate(self) -> List[str]:
        """Validate generation configuration."""
        errors = []

        if self.count < 1:
            errors.append(f"count must be at least 1, got {self.count}")
        if not 1 <= self.batch_size <= 4:
            errors.append(f"batch_size must be 1-4, got {self.batch_size}")
        if not self.prompt.strip():
            errors.append("prompt cannot be empty")

        return errors


@dataclass
class ApiConfig:
    """API configuration."""
    key_env: str = "GEMINI_API_KEY"
    rate_limit: int = 60
    retry_attempts: int = 3
    retry_delay: int = 5

    def validate(self) -> List[str]:
        """Validate API configuration."""
        errors = []

        if not os.environ.get(self.key_env):
            errors.append(f"Environment variable {self.key_env} not set")
        if self.rate_limit < 1:
            errors.append(f"rate_limit must be at least 1, got {self.rate_limit}")
        if self.retry_attempts < 0:
            errors.append(f"retry_attempts cannot be negative, got {self.retry_attempts}")
        if self.retry_delay < 0:
            errors.append(f"retry_delay cannot be negative, got {self.retry_delay}")

        return errors

    def get_api_key(self) -> str:
        """Get the API key from environment."""
        key = os.environ.get(self.key_env, "")
        if not key:
            raise ValueError(f"API key not found in environment variable: {self.key_env}")
        return key


@dataclass
class CompressionSettings:
    """Compression settings for output images."""
    enabled: bool = True
    png_level: int = 6
    webp_quality: int = 85

    def validate(self) -> List[str]:
        """Validate compression settings."""
        errors = []

        if not 0 <= self.png_level <= 9:
            errors.append(f"png_level must be 0-9, got {self.png_level}")
        if not 1 <= self.webp_quality <= 100:
            errors.append(f"webp_quality must be 1-100, got {self.webp_quality}")

        return errors


@dataclass
class OutputConfig:
    """Output configuration."""
    directory: str = "./output"
    format: Literal["png", "webp", "both"] = "png"
    compression: CompressionSettings = field(default_factory=CompressionSettings)
    naming: str = "{job_name}_{index:04d}_{timestamp}"

    def validate(self) -> List[str]:
        """Validate output configuration."""
        errors = []
        errors.extend(self.compression.validate())

        if self.format not in ("png", "webp", "both"):
            errors.append(f"format must be png, webp, or both, got {self.format}")

        # Validate naming template
        required_placeholders = ["{index"]
        for placeholder in required_placeholders:
            if placeholder not in self.naming:
                errors.append(f"naming template must contain {placeholder}")

        return errors


@dataclass
class MetadataConfig:
    """Metadata output configuration."""
    enabled: bool = True
    format: Literal["json", "csv", "both"] = "json"
    include_prompt: bool = True
    include_generation_time: bool = True

    def validate(self) -> List[str]:
        """Validate metadata configuration."""
        errors = []

        if self.format not in ("json", "csv", "both"):
            errors.append(f"metadata format must be json, csv, or both, got {self.format}")

        return errors


@dataclass
class JobConfig:
    """Complete job configuration."""
    name: str
    mode: Literal["variation", "modification"]
    input: InputConfig
    generation: GenerationConfig
    api: ApiConfig = field(default_factory=ApiConfig)
    output: OutputConfig = field(default_factory=OutputConfig)
    metadata: MetadataConfig = field(default_factory=MetadataConfig)

    def validate(self, base_path: Optional[Path] = None) -> List[str]:
        """
        Validate the complete job configuration.

        Args:
            base_path: Base path for resolving relative file paths

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        base = base_path or Path.cwd()

        # Validate job basics
        if not self.name.strip():
            errors.append("job name cannot be empty")
        if self.mode not in ("variation", "modification"):
            errors.append(f"mode must be variation or modification, got {self.mode}")

        # Validate modification mode requires reference image
        if self.mode == "modification" and not self.input.reference_image:
            errors.append("modification mode requires reference_image")

        # Validate all sections
        errors.extend(self.input.validate(base))
        errors.extend(self.generation.validate())
        errors.extend(self.api.validate())
        errors.extend(self.output.validate())
        errors.extend(self.metadata.validate())

        return errors

    def is_valid(self, base_path: Optional[Path] = None) -> bool:
        """Check if configuration is valid."""
        return len(self.validate(base_path)) == 0

    def get_output_path(self) -> Path:
        """Get the resolved output directory path."""
        return Path(self.output.directory)

    def get_total_batches(self) -> int:
        """Calculate total number of API batches needed."""
        from math import ceil
        return ceil(self.generation.count / self.generation.batch_size)

    def estimate_time_seconds(self) -> float:
        """Estimate total generation time in seconds."""
        batches = self.get_total_batches()
        # Assume ~1 second per request at rate limit
        seconds_per_batch = 60 / self.api.rate_limit
        return batches * seconds_per_batch


def load_config(config_path: Union[str, Path]) -> JobConfig:
    """
    Load configuration from a YAML file.

    Args:
        config_path: Path to the YAML configuration file

    Returns:
        Parsed JobConfig object

    Raises:
        FileNotFoundError: If config file doesn't exist
        ValueError: If config is invalid
    """
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(path, "r", encoding="utf-8") as f:
        raw_config = yaml.safe_load(f)

    return _parse_config(raw_config)


def _parse_config(raw: Dict[str, Any]) -> JobConfig:
    """Parse raw dictionary into JobConfig."""
    # Extract job basics
    job_section = raw.get("job", {})
    name = job_section.get("name", "unnamed_job")
    mode = job_section.get("mode", "variation")

    # Parse input
    input_section = raw.get("input", {})
    input_config = InputConfig(
        seed_image=input_section.get("seed_image", ""),
        reference_image=input_section.get("reference_image")
    )

    # Parse generation
    gen_section = raw.get("generation", {})
    generation_config = GenerationConfig(
        count=gen_section.get("count", 1),
        batch_size=gen_section.get("batch_size", 4),
        prompt=gen_section.get("prompt", ""),
        model=gen_section.get("model", "gemini-2.0-flash-exp-image-generation")
    )

    # Parse API
    api_section = raw.get("api", {})
    api_config = ApiConfig(
        key_env=api_section.get("key_env", "GEMINI_API_KEY"),
        rate_limit=api_section.get("rate_limit", 60),
        retry_attempts=api_section.get("retry_attempts", 3),
        retry_delay=api_section.get("retry_delay", 5)
    )

    # Parse output
    output_section = raw.get("output", {})
    compression_section = output_section.get("compression", {})
    compression_settings = CompressionSettings(
        enabled=compression_section.get("enabled", True),
        png_level=compression_section.get("png_level", 6),
        webp_quality=compression_section.get("webp_quality", 85)
    )
    output_config = OutputConfig(
        directory=output_section.get("directory", "./output"),
        format=output_section.get("format", "png"),
        compression=compression_settings,
        naming=output_section.get("naming", "{job_name}_{index:04d}_{timestamp}")
    )

    # Parse metadata
    meta_section = raw.get("metadata", {})
    metadata_config = MetadataConfig(
        enabled=meta_section.get("enabled", True),
        format=meta_section.get("format", "json"),
        include_prompt=meta_section.get("include_prompt", True),
        include_generation_time=meta_section.get("include_generation_time", True)
    )

    return JobConfig(
        name=name,
        mode=mode,
        input=input_config,
        generation=generation_config,
        api=api_config,
        output=output_config,
        metadata=metadata_config
    )


def validate_config(config_path: Union[str, Path]) -> List[str]:
    """
    Validate a configuration file without loading it fully.

    Args:
        config_path: Path to the YAML configuration file

    Returns:
        List of validation error messages (empty if valid)
    """
    try:
        config = load_config(config_path)
        base_path = Path(config_path).parent
        return config.validate(base_path)
    except FileNotFoundError as e:
        return [str(e)]
    except yaml.YAMLError as e:
        return [f"YAML parsing error: {e}"]
    except Exception as e:
        return [f"Configuration error: {e}"]


def create_example_config(
    output_path: Union[str, Path],
    mode: Literal["variation", "modification"] = "variation"
) -> None:
    """
    Create an example configuration file.

    Args:
        output_path: Path to write the example config
        mode: Generation mode for the example
    """
    example = {
        "job": {
            "name": "gesture_dataset_v1",
            "mode": mode
        },
        "input": {
            "seed_image": "./seeds/hand_pose_01.png"
        },
        "generation": {
            "count": 200,
            "batch_size": 4,
            "prompt": "Generate variation with different lighting and background",
            "model": "gemini-2.0-flash-exp-image-generation"
        },
        "api": {
            "key_env": "GEMINI_API_KEY",
            "rate_limit": 60,
            "retry_attempts": 3,
            "retry_delay": 5
        },
        "output": {
            "directory": "./output/dataset_v1",
            "format": "png",
            "compression": {
                "enabled": True,
                "png_level": 6,
                "webp_quality": 85
            },
            "naming": "{job_name}_{index:04d}_{timestamp}"
        },
        "metadata": {
            "enabled": True,
            "format": "json",
            "include_prompt": True,
            "include_generation_time": True
        }
    }

    if mode == "modification":
        example["input"]["reference_image"] = "./refs/style.png"

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(example, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
