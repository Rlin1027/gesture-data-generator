<!-- Parent: ../AGENTS.md -->
# Configuration Examples

## Purpose
Example YAML configuration files demonstrating batch generation job setups. Use these as templates when creating new batch jobs via the CLI.

## Key Files
- `variation.yaml` - Example configuration for variation mode
  - Generates variations of a seed image with different backgrounds/lighting
  - Keeps the hand pose, changes environment
- `modification.yaml` - Example configuration for modification mode
  - Transforms seed image based on a reference gesture
  - Requires both seed and reference images

## For AI Agents

### Using Example Configs
```bash
# Copy and customize
cp config/examples/variation.yaml config/my_job.yaml
# Edit with your parameters
vim config/my_job.yaml
# Validate
python cli.py validate config/my_job.yaml
# Run
python cli.py run config/my_job.yaml
```

### Example Structure
```yaml
job:
  name: "my_dataset"
  mode: "variation"  # or "modification"

input:
  seed_image: "./path/to/seed.png"
  reference_image: "./path/to/ref.png"  # modification only

generation:
  count: 100
  batch_size: 4
  prompt: "Your prompt here"
  model: "gemini-2.0-flash-exp-image-generation"

api:
  key_env: "GEMINI_API_KEY"
  rate_limit: 60

output:
  directory: "./output/my_dataset"
  format: "png"  # png | webp | both

metadata:
  enabled: true
  format: "json"  # json | csv | both
```

## Dependencies
- **Internal**: Used as reference for `config/schema.py` validation
