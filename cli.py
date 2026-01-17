#!/usr/bin/env python3
"""
Command-line interface for batch gesture image generation.

Usage:
    python cli.py run config/job.yaml        # Execute batch job
    python cli.py validate config/job.yaml   # Validate config only
    python cli.py init --mode variation      # Create template config
    python cli.py status                     # View last job summary
"""

import sys
from pathlib import Path
from typing import Optional

import click

from config.schema import JobConfig, create_example_config, load_config, validate_config
from core.batch_processor import BatchProcessor


def print_banner():
    """Print the CLI banner."""
    click.echo(click.style("""
╔═══════════════════════════════════════════════════════════╗
║           Gesture Gen - Batch Generation CLI              ║
║              AI-Powered Dataset Generator                 ║
╚═══════════════════════════════════════════════════════════╝
""", fg="cyan"))


def print_config_summary(config: JobConfig, config_path: str):
    """Print a summary of the configuration."""
    estimate = BatchProcessor._format_time(config.estimate_time_seconds())

    click.echo(click.style("\n📋 任務配置:", fg="bright_white", bold=True))
    click.echo(f"   ├─ 名稱: {click.style(config.name, fg='cyan')}")
    click.echo(f"   ├─ 模式: {config.mode}")
    click.echo(f"   ├─ 生成數量: {config.generation.count} 張")
    click.echo(f"   ├─ 批次大小: {config.generation.batch_size}")
    click.echo(f"   ├─ 輸出格式: {config.output.format}")
    click.echo(f"   ├─ 輸出目錄: {config.output.directory}")
    click.echo(f"   ├─ API 速率: {config.api.rate_limit} RPM")
    click.echo(f"   └─ 預估時間: {estimate}")


@click.group()
@click.version_option(version="1.0.0", prog_name="gesture-gen")
def cli():
    """Gesture Gen - Batch image generation CLI tool."""
    pass


@cli.command()
@click.argument("config_file", type=click.Path(exists=True))
@click.option("--count", "-n", type=int, help="Override generation count")
@click.option("--format", "-f", "output_format", type=click.Choice(["png", "webp", "both"]),
              help="Override output format")
@click.option("--output", "-o", type=click.Path(), help="Override output directory")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt")
@click.option("--quiet", "-q", is_flag=True, help="Minimal output")
@click.option("--dry-run", is_flag=True, help="Simulate execution without API calls")
def run(
    config_file: str,
    count: Optional[int],
    output_format: Optional[str],
    output: Optional[str],
    yes: bool,
    quiet: bool,
    dry_run: bool
):
    """
    Execute a batch generation job.

    CONFIG_FILE: Path to the YAML configuration file.

    Examples:
        python cli.py run config/variation.yaml
        python cli.py run config/job.yaml --count 50 --format webp
        python cli.py run config/job.yaml --yes --quiet
    """
    if not quiet:
        print_banner()

    try:
        # Load and validate configuration
        config = load_config(config_file)
        config_path = Path(config_file)

        # Apply overrides
        if count is not None:
            config.generation.count = count
        if output_format is not None:
            config.output.format = output_format
        if output is not None:
            config.output.directory = output

        # Validate
        errors = config.validate(config_path.parent)
        if errors:
            click.echo(click.style("\n❌ 配置驗證失敗:", fg="red", bold=True))
            for error in errors:
                click.echo(f"   • {error}")
            sys.exit(1)

        # Show summary
        if not quiet:
            print_config_summary(config, config_file)

        # Confirm execution
        if not yes and not dry_run:
            click.echo()
            if not click.confirm(click.style("確認執行？", fg="yellow")):
                click.echo("已取消。")
                sys.exit(0)

        # Dry run mode
        if dry_run:
            click.echo(click.style("\n🔍 模擬執行模式 (不會呼叫 API)", fg="yellow"))
            click.echo(f"   將生成 {config.generation.count} 張圖片")
            click.echo(f"   預計需要 {config.get_total_batches()} 次 API 呼叫")
            click.echo(f"   輸出至: {config.output.directory}")
            sys.exit(0)

        # Execute batch job
        processor = BatchProcessor(config, str(config_path))

        if not quiet:
            click.echo()

        result = processor.run(show_progress=not quiet)

        # Print summary
        if not quiet:
            processor.print_summary(result)

        # Exit code based on result
        if not result.success:
            sys.exit(1)
        elif result.total_failed > 0:
            sys.exit(2)  # Partial success

    except FileNotFoundError as e:
        click.echo(click.style(f"\n❌ 找不到檔案: {e}", fg="red"))
        sys.exit(1)
    except Exception as e:
        click.echo(click.style(f"\n❌ 錯誤: {e}", fg="red"))
        if not quiet:
            import traceback
            click.echo(traceback.format_exc())
        sys.exit(1)


@cli.command()
@click.argument("config_file", type=click.Path(exists=True))
def validate(config_file: str):
    """
    Validate a configuration file without executing.

    CONFIG_FILE: Path to the YAML configuration file.

    Examples:
        python cli.py validate config/variation.yaml
    """
    print_banner()

    try:
        config_path = Path(config_file)
        errors = validate_config(config_file)

        if errors:
            click.echo(click.style("\n❌ 配置驗證失敗:", fg="red", bold=True))
            for error in errors:
                click.echo(f"   • {error}")
            sys.exit(1)
        else:
            config = load_config(config_file)
            click.echo(click.style("\n✅ 配置驗證通過", fg="green", bold=True))

            # Show validated config info
            click.echo(f"   ├─ 種子圖片: {config.input.seed_image}")
            if config.input.reference_image:
                click.echo(f"   ├─ 參考圖片: {config.input.reference_image}")
            click.echo(f"   ├─ 輸出目錄: {config.output.directory}")
            click.echo(f"   ├─ 預計生成: {config.generation.count} 張")
            click.echo(f"   └─ 預估時間: {BatchProcessor._format_time(config.estimate_time_seconds())}")

    except Exception as e:
        click.echo(click.style(f"\n❌ 錯誤: {e}", fg="red"))
        sys.exit(1)


@cli.command()
@click.option("--mode", "-m", type=click.Choice(["variation", "modification"]),
              default="variation", help="Generation mode")
@click.option("--output", "-o", type=click.Path(), default="config/my_job.yaml",
              help="Output path for the config file")
def init(mode: str, output: str):
    """
    Create a configuration file template.

    Examples:
        python cli.py init
        python cli.py init --mode modification --output config/style_transfer.yaml
    """
    print_banner()

    output_path = Path(output)

    if output_path.exists():
        if not click.confirm(f"檔案 {output} 已存在，要覆蓋嗎？"):
            click.echo("已取消。")
            sys.exit(0)

    try:
        create_example_config(output_path, mode)
        click.echo(click.style(f"\n✅ 已建立設定檔範本: {output}", fg="green", bold=True))
        click.echo(f"   模式: {mode}")
        click.echo("\n   下一步:")
        click.echo(f"   1. 編輯 {output} 設定您的參數")
        click.echo(f"   2. 執行 python cli.py validate {output} 驗證配置")
        click.echo(f"   3. 執行 python cli.py run {output} 開始生成")

    except Exception as e:
        click.echo(click.style(f"\n❌ 建立失敗: {e}", fg="red"))
        sys.exit(1)


@cli.command()
@click.option("--directory", "-d", type=click.Path(exists=True), default="./output",
              help="Output directory to check")
def status(directory: str):
    """
    View the status of the last completed job.

    Examples:
        python cli.py status
        python cli.py status --directory ./output/my_dataset
    """
    print_banner()

    import json
    from pathlib import Path

    output_dir = Path(directory)

    # Find the most recent summary.json
    summary_files = list(output_dir.rglob("summary.json"))

    if not summary_files:
        click.echo(click.style(f"\n⚠️  在 {directory} 找不到任務摘要", fg="yellow"))
        sys.exit(0)

    # Sort by modification time, get most recent
    latest_summary = max(summary_files, key=lambda p: p.stat().st_mtime)

    try:
        with open(latest_summary, "r", encoding="utf-8") as f:
            summary = json.load(f)

        click.echo(click.style("\n📊 最近任務摘要:", fg="bright_white", bold=True))
        click.echo(f"   ├─ 任務名稱: {summary.get('job_name', 'Unknown')}")
        click.echo(f"   ├─ 完成時間: {summary.get('completed_at', 'Unknown')}")

        stats = summary.get("statistics", {})
        click.echo(f"   ├─ 生成數量: {stats.get('total_generated', 0)}/{stats.get('total_requested', 0)}")
        click.echo(f"   ├─ 成功率: {stats.get('success_rate', 0)*100:.1f}%")
        click.echo(f"   ├─ 總耗時: {stats.get('total_time_seconds', 0):.1f} 秒")

        storage = summary.get("storage", {})
        click.echo(f"   ├─ 檔案格式: {storage.get('format', 'Unknown')}")
        click.echo(f"   ├─ 總大小: {storage.get('total_size_mb', 0):.2f} MB")

        click.echo(f"   └─ 摘要檔案: {latest_summary}")

        # Show errors if any
        errors = summary.get("errors", [])
        if errors:
            click.echo(click.style(f"\n⚠️  有 {len(errors)} 個錯誤:", fg="yellow"))
            for err in errors[:5]:
                click.echo(f"   • Index {err.get('index', '?')}: {err.get('error', 'Unknown')}")
            if len(errors) > 5:
                click.echo(f"   ... 還有 {len(errors) - 5} 個錯誤")

    except Exception as e:
        click.echo(click.style(f"\n❌ 讀取摘要失敗: {e}", fg="red"))
        sys.exit(1)


if __name__ == "__main__":
    cli()
