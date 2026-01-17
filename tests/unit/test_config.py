"""Unit tests for the configuration schema."""

import os
import tempfile
import unittest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import yaml
from config.schema import (
    ApiConfig,
    CompressionSettings,
    GenerationConfig,
    InputConfig,
    JobConfig,
    MetadataConfig,
    OutputConfig,
    create_example_config,
    load_config,
    validate_config,
)


class TestInputConfig(unittest.TestCase):
    """Tests for InputConfig validation."""

    def test_validate_missing_seed(self):
        """Test validation fails for missing seed image."""
        config = InputConfig(seed_image="nonexistent.png")
        errors = config.validate(Path("/tmp"))
        self.assertTrue(any("Seed image not found" in e for e in errors))

    def test_validate_with_existing_seed(self):
        """Test validation passes for existing seed image."""
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            temp_path = Path(f.name)
            try:
                config = InputConfig(seed_image=temp_path.name)
                errors = config.validate(temp_path.parent)
                self.assertEqual(len(errors), 0)
            finally:
                temp_path.unlink()


class TestGenerationConfig(unittest.TestCase):
    """Tests for GenerationConfig validation."""

    def test_valid_config(self):
        """Test valid configuration."""
        config = GenerationConfig(count=100, batch_size=4, prompt="test")
        errors = config.validate()
        self.assertEqual(len(errors), 0)

    def test_invalid_count(self):
        """Test validation fails for invalid count."""
        config = GenerationConfig(count=0, prompt="test")
        errors = config.validate()
        self.assertTrue(any("count" in e for e in errors))

    def test_invalid_batch_size(self):
        """Test validation fails for invalid batch size."""
        config = GenerationConfig(count=100, batch_size=5, prompt="test")
        errors = config.validate()
        self.assertTrue(any("batch_size" in e for e in errors))

    def test_empty_prompt(self):
        """Test validation fails for empty prompt."""
        config = GenerationConfig(count=100, prompt="")
        errors = config.validate()
        self.assertTrue(any("prompt" in e for e in errors))


class TestApiConfig(unittest.TestCase):
    """Tests for ApiConfig validation."""

    def test_missing_api_key(self):
        """Test validation fails when API key not set."""
        # Ensure env var is not set
        env_var = "TEST_MISSING_API_KEY"
        if env_var in os.environ:
            del os.environ[env_var]

        config = ApiConfig(key_env=env_var)
        errors = config.validate()
        self.assertTrue(any("not set" in e for e in errors))

    def test_with_api_key(self):
        """Test validation passes when API key is set."""
        env_var = "TEST_API_KEY"
        os.environ[env_var] = "test-key"

        try:
            config = ApiConfig(key_env=env_var)
            errors = config.validate()
            self.assertEqual(len(errors), 0)
        finally:
            del os.environ[env_var]

    def test_get_api_key(self):
        """Test getting API key from environment."""
        env_var = "TEST_GET_KEY"
        os.environ[env_var] = "my-secret-key"

        try:
            config = ApiConfig(key_env=env_var)
            self.assertEqual(config.get_api_key(), "my-secret-key")
        finally:
            del os.environ[env_var]


class TestCompressionSettings(unittest.TestCase):
    """Tests for CompressionSettings validation."""

    def test_valid_settings(self):
        """Test valid compression settings."""
        settings = CompressionSettings(png_level=6, webp_quality=85)
        errors = settings.validate()
        self.assertEqual(len(errors), 0)

    def test_invalid_png_level(self):
        """Test validation fails for invalid PNG level."""
        settings = CompressionSettings(png_level=10)
        errors = settings.validate()
        self.assertTrue(any("png_level" in e for e in errors))

    def test_invalid_webp_quality(self):
        """Test validation fails for invalid WebP quality."""
        settings = CompressionSettings(webp_quality=101)
        errors = settings.validate()
        self.assertTrue(any("webp_quality" in e for e in errors))


class TestOutputConfig(unittest.TestCase):
    """Tests for OutputConfig validation."""

    def test_valid_config(self):
        """Test valid output configuration."""
        config = OutputConfig()
        errors = config.validate()
        self.assertEqual(len(errors), 0)

    def test_invalid_format(self):
        """Test validation fails for invalid format."""
        config = OutputConfig(format="jpeg")  # Not supported
        errors = config.validate()
        self.assertTrue(any("format" in e for e in errors))

    def test_naming_without_index(self):
        """Test validation fails for naming without index."""
        config = OutputConfig(naming="{job_name}_{timestamp}")
        errors = config.validate()
        self.assertTrue(any("index" in e for e in errors))


class TestJobConfig(unittest.TestCase):
    """Tests for complete JobConfig validation."""

    def setUp(self):
        """Create a temporary seed image for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.seed_path = Path(self.temp_dir) / "seed.png"

        # Create a minimal valid PNG
        from PIL import Image
        img = Image.new("L", (10, 10))
        img.save(self.seed_path)

        # Set API key
        os.environ["TEST_JOB_API_KEY"] = "test-key"

    def tearDown(self):
        """Clean up temporary files."""
        self.seed_path.unlink()
        Path(self.temp_dir).rmdir()
        if "TEST_JOB_API_KEY" in os.environ:
            del os.environ["TEST_JOB_API_KEY"]

    def test_valid_job_config(self):
        """Test valid job configuration."""
        config = JobConfig(
            name="test_job",
            mode="variation",
            input=InputConfig(seed_image="seed.png"),
            generation=GenerationConfig(count=10, prompt="test"),
            api=ApiConfig(key_env="TEST_JOB_API_KEY"),
        )
        errors = config.validate(Path(self.temp_dir))
        self.assertEqual(len(errors), 0)

    def test_modification_requires_reference(self):
        """Test modification mode requires reference image."""
        config = JobConfig(
            name="test_job",
            mode="modification",
            input=InputConfig(seed_image="seed.png"),
            generation=GenerationConfig(count=10, prompt="test"),
            api=ApiConfig(key_env="TEST_JOB_API_KEY"),
        )
        errors = config.validate(Path(self.temp_dir))
        self.assertTrue(any("reference_image" in e for e in errors))

    def test_is_valid(self):
        """Test is_valid helper method."""
        config = JobConfig(
            name="test_job",
            mode="variation",
            input=InputConfig(seed_image="seed.png"),
            generation=GenerationConfig(count=10, prompt="test"),
            api=ApiConfig(key_env="TEST_JOB_API_KEY"),
        )
        self.assertTrue(config.is_valid(Path(self.temp_dir)))

    def test_get_total_batches(self):
        """Test batch count calculation."""
        config = JobConfig(
            name="test",
            mode="variation",
            input=InputConfig(seed_image="seed.png"),
            generation=GenerationConfig(count=10, batch_size=4, prompt="test"),
        )
        self.assertEqual(config.get_total_batches(), 3)  # ceil(10/4)

    def test_estimate_time(self):
        """Test time estimation."""
        config = JobConfig(
            name="test",
            mode="variation",
            input=InputConfig(seed_image="seed.png"),
            generation=GenerationConfig(count=60, batch_size=4, prompt="test"),
            api=ApiConfig(rate_limit=60),
        )
        # 60 images with batch_size 4 = 15 batches at 60 RPM = 15 seconds
        self.assertAlmostEqual(config.estimate_time_seconds(), 15, delta=1)


class TestConfigLoading(unittest.TestCase):
    """Tests for config file loading."""

    def test_load_config(self):
        """Test loading configuration from YAML file."""
        config_content = {
            "job": {"name": "test", "mode": "variation"},
            "input": {"seed_image": "test.png"},
            "generation": {"count": 100, "prompt": "test prompt"},
        }

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            yaml.dump(config_content, f)
            temp_path = f.name

        try:
            config = load_config(temp_path)
            self.assertEqual(config.name, "test")
            self.assertEqual(config.mode, "variation")
            self.assertEqual(config.generation.count, 100)
        finally:
            Path(temp_path).unlink()

    def test_load_nonexistent_config(self):
        """Test loading nonexistent config raises error."""
        with self.assertRaises(FileNotFoundError):
            load_config("/nonexistent/path/config.yaml")

    def test_create_example_config(self):
        """Test creating example configuration file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "example.yaml"
            create_example_config(output_path, mode="variation")

            self.assertTrue(output_path.exists())

            # Verify it can be loaded
            config = load_config(output_path)
            self.assertEqual(config.mode, "variation")


if __name__ == "__main__":
    unittest.main()
