"""CLI interface for content-automata using Click."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import print as rprint

from content_automata import ContentPipeline

console = Console()


@click.group()
@click.version_option(version="0.1.0", prog_name="cauto")
def cli():
    """content-automata — AI-powered content pipeline.

    Research → Copywriting → Image Generation → Scheduling
    """
    pass


@cli.command()
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True),
    default=None,
    help="Path to config YAML file",
)
def init(config: Optional[str]):
    """Initialize a new content-automata project."""
    console.print(Panel.fit(
        "[bold]content-automata[/bold] — Project Initialization",
        border_style="blue",
    ))

    # Create config if not exists
    config_path = Path(config or "config.yaml")
    if not config_path.exists():
        example = Path(__file__).parent.parent / "examples" / "config.yaml.example"
        if example.exists():
            import shutil
            shutil.copy(example, config_path)
            console.print(f"[green]✓[/green] Created config: {config_path}")
        else:
            config_path.write_text(
                "# content-automata configuration\n"
                "api_key: \"your-api-key-here\"\n"
                "research:\n"
                "  provider: \"tavily\"\n"
                "  max_results: 5\n"
                "copywriting:\n"
                "  default_tone: \"professional\"\n"
                "  variants: [\"blog\", \"social\", \"ad\"]\n"
                "image_generation:\n"
                "  provider: \"openai\"\n"
                "  default_aspect: \"16:9\"\n"
                "scheduling:\n"
                "  export_formats: [\"markdown\", \"html\", \"csv\"]\n"
            )
            console.print(f"[green]✓[/green] Created config: {config_path}")

    # Create output directory
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    console.print(f"[green]✓[/green] Created output directory: {output_dir}")

    console.print("\n[bold green]Ready![/bold green] Run [bold]cauto run --topic 'Your Topic'[/bold]")


@cli.command()
@click.option("--topic", "-t", default=None, help="Content topic")
@click.option("--url", "-u", default=None, help="URL to research")
@click.option("--config", "-c", type=click.Path(exists=True), default=None, help="Config file")
@click.option("--tone", default="professional", help="Writing tone")
@click.option("--format", "export_format", default="markdown", help="Export format")
def run(topic, url, config, tone, export_format):
    """Run the full content pipeline."""
    if not topic and not url:
        console.print("[red]Error:[/red] Provide --topic or --url")
        sys.exit(1)

    console.print(Panel.fit(
        "[bold]content-automata[/bold] — Pipeline Execution",
        border_style="green",
    ))

    # Initialize pipeline
    pipe = ContentPipeline(config=config or {})

    try:
        # Execute pipeline
        with console.status("[bold blue]Running content pipeline...") as status:
            if url:
                status.update(f"[bold blue]Researching URL: {url}")
                result = pipe.from_url(url, tone=tone)
            else:
                status.update(f"[bold blue]Researching topic: {topic}")
                result = pipe.from_topic(topic, tone=tone)

        # Display results
        console.print("\n[bold green]✓ Pipeline Complete![/bold green]\n")

        # Research summary
        console.print(Panel(
            result.final.research.summary,
            title="[bold]Research Summary[/bold]",
            border_style="blue",
        ))

        # Key points
        table = Table(title="Key Points", show_header=False)
        table.add_column("Point", style="cyan")
        for point in result.final.research.key_points[:5]:
            table.add_row(f"• {point}")
        console.print(table)

        # Draft info
        console.print(f"\n[bold]Headline:[/bold] {result.final.draft.headline or 'N/A'}")
        console.print(f"[bold]Word Count:[/bold] {result.final.draft.word_count}")
        console.print(f"[bold]Tone:[/bold] {result.final.draft.tone}")

        # Visuals
        if result.final.visuals.image_urls:
            console.print(f"\n[bold]Images Generated:[/bold] {len(result.final.visuals.image_urls)}")

        # Exports
        if result.final.schedule.exports:
            console.print(f"\n[bold]Exports:[/bold]")
            for exp in result.final.schedule.exports:
                if exp.file_path:
                    console.print(f"  [green]✓[/green] {exp.format}: {exp.file_path}")

        console.print(f"\n[dim]State: {result.state.value}[/dim]")

    except Exception as e:
        console.print(f"[red]Pipeline failed:[/red] {e}")
        sys.exit(1)


@cli.command()
@click.option("--format", "-f", "export_format", default="markdown", help="Export format")
@click.option("--file", "-i", type=click.Path(exists=True), default=None, help="Input content file")
@click.option("--date", "-d", default=None, help="Scheduled date (YYYY-MM-DD)")
def schedule(export_format, file, date):
    """Schedule content for publishing."""
    console.print(Panel.fit(
        "[bold]content-automata[/bold] — Content Scheduling",
        border_style="yellow",
    ))

    if file:
        console.print(f"[bold]Input:[/bold] {file}")
    console.print(f"[bold]Format:[/bold] {export_format}")
    if date:
        console.print(f"[bold]Date:[/bold] {date}")

    console.print("\n[yellow]Scheduling placeholder — integrate with Buffer, Hootsuite, or WordPress.[/yellow]")


@cli.command()
def status():
    """Check pipeline status."""
    console.print(Panel.fit(
        "[bold]content-automata[/bold] — Status",
        border_style="cyan",
    ))

    status_table = Table(title="Pipeline Status")
    status_table.add_column("Component", style="bold")
    status_table.add_column("Status", style="green")

    status_table.add_row("Package", f"v0.1.0")
    status_table.add_row("Python", f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    status_table.add_row("Config", "Not loaded (use 'cauto init' to create)")

    # Check installed packages
    for dep in ["httpx", "pyyaml", "rich", "click", "pydantic", "pillow"]:
        try:
            __import__(dep)
            status_table.add_row(dep, "✅ Installed")
        except ImportError:
            status_table.add_row(dep, "❌ Missing")

    console.print(status_table)


if __name__ == "__main__":
    cli()
