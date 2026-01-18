<!-- Parent: ../AGENTS.md -->
# Configuration Module

## Purpose
Configuration management for the gesture generation system. Provides YAML-based configuration loading, validation, schema definitions, and application constants. Used by both the CLI batch processor and web application.

## Key Files
- `schema.py` - Dataclass-based configuration schema with full validation
  - `JobConfig` - Complete job configuration with nested configs
  - `InputConfig`, `GenerationConfig`, `ApiConfig`, `OutputConfig`, `MetadataConfig`
  - `load_config()` - Load and parse YAML configuration files
  - `validate_config()` - Validate configuration without full load
  - `create_example_config()` - Generate example configuration templates
- `constants.py` - Centralized application constants
  - Image dimensions: `IMAGE_WIDTH=320`, `IMAGE_HEIGHT=180`
  - Batch limits: `MAX_BATCH_SIZE=4`, `MIN_BATCH_SIZE=1`
  - Pagination: `MAX_PER_PAGE=50`, `DEFAULT_PER_PAGE=12`
  - File prefixes: `PREFIX_GENERATED`, `PREFIX_SEED`, `PREFIX_REFERENCE`
- `__init__.py` - Module initialization and exports

## Subdirectories
- `examples/` - Example YAML configuration files for reference
  - `modification.yaml` - Sample modification mode config
  - `variation.yaml` - Sample variation mode config

## For AI Agents

### Configuration Schema Structure
```python
JobConfig
├── name: str                    # Job identifier
├── mode: "variation" | "modification"
├── input: InputConfig
│   ├── seed_image: str          # Path to seed image
│   └── reference_image: Optional[str]
├── generation: GenerationConfig
│   ├── count: int               # Total images to generate
│   ├── batch_size: int          # 1-4 images per API call
│   ├── prompt: str
│   └── model: str
├── api: ApiConfig
│   ├── key_env: str             # Environment variable name
│   ├── rate_limit: int          # RPM limit
│   ├── retry_attempts: int
│   └── retry_delay: int
├── output: OutputConfig
│   ├── directory: str
│   ├── format: "png" | "webp" | "both"
│   ├── compression: CompressionSettings
│   └── naming: str              # Filename template
└── metadata: MetadataConfig
    ├── enabled: bool
    └── format: "json" | "csv" | "both"
```

### Working in This Module

- **Adding new config options**: Add to appropriate dataclass in `schema.py`, update `_parse_config()`, add validation in `validate()`
- **Adding constants**: Add to `constants.py`, import in other modules
- **Config validation**: Each dataclass has a `validate()` method returning `List[str]` of errors

### Usage Examples
```python
from config.schema import load_config, validate_config

# Load and validate
config = load_config("config/job.yaml")
errors = config.validate(base_path=Path.cwd())

# Access nested config
rpm = config.api.rate_limit
format = config.output.format
```

## Dependencies
- **External**: PyYAML for YAML parsing
- **Internal**: Used by `core/batch_processor.py`, `cli.py`
