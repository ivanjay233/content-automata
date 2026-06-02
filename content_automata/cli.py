"""CLI interface for content-automata using Click."""

from __future__ import annotations

import json as json_lib
import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import print as rprint

from content_automata import ContentPipeline
from content_automata.history import RevisionHistory
from content_automata.templates import TemplateManager
from content_automata.dryrun import DryRunMode

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
@click.option("--json", "json_output", is_flag=True, default=False, help="Output in JSON format")
@click.option("--topic", "-t", default=None, help="Filter by topic")
@click.option("--limit", type=int, default=20, help="Number of entries to show")
def history(json_output, topic, limit):
    """Show pipeline run history."""
    hist = RevisionHistory()
    revisions = hist.list_revisions(limit=limit)

    if topic:
        revisions = [r for r in revisions if topic.lower() in r.topic.lower()]

    if not revisions:
        console.print("[yellow]No revision history found.[/yellow]")
        return

    if json_output:
        data = [
            {
                "version": r.version,
                "timestamp": r.timestamp,
                "topic": r.topic,
                "word_count": r.word_count,
                "tone": r.tone,
                "num_images": r.num_images,
                "export_formats": r.export_formats,
            }
            for r in revisions
        ]
        console.print(json_lib.dumps(data, indent=2))
        return

    console.print(Panel.fit(
        "[bold]content-automata[/bold] — Run History",
        border_style="cyan",
    ))

    table = Table(title=f"Last {len(revisions)} Runs")
    table.add_column("Version", style="bold")
    table.add_column("Date", style="dim")
    table.add_column("Topic")
    table.add_column("Words", justify="right")
    table.add_column("Images", justify="right")

    for rev in revisions:
        date_str = rev.timestamp[:10] if rev.timestamp else ""
        table.add_row(
            rev.version,
            date_str,
            rev.topic[:40],
            str(rev.word_count),
            str(rev.num_images),
        )

    console.print(table)


@cli.command()
@click.argument("topic_or_url", required=False)
@click.option("--json", "json_output", is_flag=True, default=False, help="Output in JSON format")
@click.option("--config", "-c", type=click.Path(exists=True), default=None, help="Config file path")
@click.option("--topic", "-t", default=None, help="Content topic")
@click.option("--url", "-u", default=None, help="URL to research")
@click.option("--tone", default="professional", help="Writing tone")
@click.option("--format", "export_format", default="markdown", help="Export format")
@click.option("--dry-run", "dry_run", is_flag=True, default=False, help="Preview without executing")
def run(topic_or_url, json_output, config, topic, url, tone, export_format, dry_run):
    """Run the full content pipeline."""
    # Resolve topic/url from positional arg
    if topic_or_url:
        if topic_or_url.startswith(("http://", "https://")):
            url = topic_or_url
        else:
            topic = topic_or_url

    if not topic and not url:
        console.print("[red]Error:[/red] Provide --topic or --url")
        sys.exit(1)

    if dry_run:
        _handle_dry_run(topic or url or "", json_output)
        return

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

        # Record history
        try:
            hist = RevisionHistory()
            hist.record(
                topic=result.brief.topic,
                summary=result.final.research.summary[:100],
                word_count=result.final.draft.word_count,
                tone=result.final.draft.tone,
                num_images=len(result.final.visuals.images),
                export_formats=[e.format for e in result.final.schedule.exports],
            )
        except Exception:
            pass  # Non-critical

        if json_output:
            data = {
                "topic": result.final.research.topic,
                "state": result.state.value,
                "completed_at": str(result.completed_at),
                "research_summary": result.final.research.summary,
                "key_points": result.final.research.key_points,
                "headline": result.final.draft.headline,
                "word_count": result.final.draft.word_count,
                "tone": result.final.draft.tone,
                "images": [{"url": img.url, "alt": img.alt_text} for img in result.final.visuals.images],
                "exports": [{"format": e.format, "file_path": e.file_path} for e in result.final.schedule.exports],
            }
            console.print(json_lib.dumps(data, indent=2))
            return

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


def _handle_dry_run(topic_or_url: str, json_output: bool):
    """Execute dry-run mode."""
    console.print(Panel.fit(
        "[bold yellow]content-automata[/bold yellow] — Dry Run Mode",
        border_style="yellow",
    ))

    dryrun = DryRunMode()
    brief = {"topic": topic_or_url}
    report = dryrun.preview(brief)

    if json_output:
        console.print(json_lib.dumps({
            "topic": report.topic,
            "api_calls": report.api_calls,
            "files_created": report.files_created,
            "estimated_cost": report.total_estimated_cost,
            "warnings": report.warnings,
            "actions": [
                {
                    "stage": a.stage,
                    "action": a.action,
                    "details": a.details,
                    "estimated_cost": a.estimated_cost,
                    "side_effects": a.side_effects,
                }
                for a in report.actions
            ],
        }, indent=2))
        return

    console.print(dryrun.to_markdown(report))


@cli.command()
@click.argument("action", type=click.Choice(["list", "show"]), default="list")
@click.argument("name", required=False)
def template(action, name):
    """Manage content templates (list, show)."""
    mgr = TemplateManager()

    if action == "list":
        console.print(Panel.fit(
            "[bold]content-automata[/bold] — Available Templates",
            border_style="magenta",
        ))
        table = Table(title="Templates")
        table.add_column("Name", style="bold")
        table.add_column("Label")
        table.add_column("Sections")
        table.add_column("Length", justify="right")

        for tpl in mgr.list_templates().values():
            table.add_row(
                tpl.name,
                tpl.label,
                ", ".join(tpl.sections[:3]) + ("..." if len(tpl.sections) > 3 else ""),
                str(tpl.suggested_length),
            )
        console.print(table)

    elif action == "show":
        if not name:
            console.print("[red]Error:[/red] Provide a template name to show")
            return

        tpl = mgr.get_template(name)
        if not tpl:
            console.print(f"[red]Template '{name}' not found.[/red]")
            return

        console.print(Panel.fit(
            f"[bold]{tpl.label}[/bold] — {tpl.description}",
            border_style="magenta",
        ))
        console.print(f"\n[bold]Sections:[/bold]")
        for s in tpl.sections:
            console.print(f"  • {s}")
        console.print(f"\n[bold]Fields:[/bold]")
        for f in tpl.fields:
            req = "[red]*[/red]" if f.required else ""
            opts = f" ({', '.join(f.options)})" if f.options else ""
            console.print(f"  • {f.label}{req}: {f.field_type}{opts}")
            if f.description:
                console.print(f"    [dim]{f.description}[/dim]")
        console.print(f"\n[bold]SEO Priority:[/bold] {tpl.seo_priority}")
        console.print(f"[bold]Suggested Length:[/bold] {tpl.suggested_length} words")


@cli.command()
@click.option("--config", "-c", type=click.Path(exists=True), default=None, help="Config file to validate")
def validate(config):
    """Validate pipeline configuration."""
    console.print(Panel.fit(
        "[bold]content-automata[/bold] — Config Validation",
        border_style="yellow",
    ))

    errors = []
    warnings = []

    if config:
        path = Path(config)
        if not path.exists():
            errors.append(f"Config file not found: {config}")
        else:
            import yaml
            try:
                with open(path) as f:
                    cfg = yaml.safe_load(f) or {}
                console.print(f"[green]✓[/green] Config file is valid YAML: {config}")
            except yaml.YAMLError as e:
                errors.append(f"Invalid YAML syntax: {e}")
    else:
        cfg = {}

    # Validate common fields
    research_providers = cfg.get("research", {}).get("provider", "tavily")
    valid_providers = ["tavily", "exa"]
    if research_providers not in valid_providers:
        warnings.append(f"Unknown research provider '{research_providers}'. Valid: {valid_providers}")

    img_providers = cfg.get("image_generation", {}).get("provider", "openai")
    valid_img_providers = ["openai", "stability"]
    if img_providers not in valid_img_providers:
        warnings.append(f"Unknown image provider '{img_providers}'. Valid: {valid_img_providers}")

    tones = cfg.get("copywriting", {}).get("default_tone", "professional")
    valid_tones = ["professional", "casual", "persuasive", "humorous", "authoritative"]
    if tones not in valid_tones:
        warnings.append(f"Unknown tone '{tones}'. Valid: {valid_tones}")

    aspects = cfg.get("image_generation", {}).get("default_aspect", "16:9")
    valid_aspects = ["1:1", "4:3", "16:9", "9:16", "3:2", "2:3"]
    if aspects not in valid_aspects:
        warnings.append(f"Unknown aspect ratio '{aspects}'. Valid: {valid_aspects}")

    formats = cfg.get("scheduling", {}).get("export_formats", ["markdown"])
    valid_formats = ["markdown", "html", "csv"]
    bad_formats = [f for f in formats if f not in valid_formats]
    if bad_formats:
        warnings.append(f"Unknown export formats: {bad_formats}. Valid: {valid_formats}")

    # Display results
    if errors:
        console.print("\n[bold red]Errors:[/bold red]")
        for e in errors:
            console.print(f"  [red]✗[/red] {e}")
    else:
        console.print("\n[bold green]✓ No errors![/bold green]")

    if warnings:
        console.print("\n[bold yellow]Warnings:[/bold yellow]")
        for w in warnings:
            console.print(f"  [yellow]⚠[/yellow] {w}")
    else:
        console.print("[green]No warnings.[/green]")

    console.print(f"\n[dim]Checked: provider, tone, aspect ratio, export formats[/dim]")


@cli.command()
@click.argument("query", required=False)
@click.option("--json", "json_output", is_flag=True, default=False, help="Output in JSON format")
@click.option("--limit", type=int, default=20, help="Max results")
def list_cmd(query, json_output, limit):
    """List available topics or show existing content."""
    hist = RevisionHistory()
    revisions = hist.list_revisions(limit=limit)

    if query:
        revisions = [r for r in revisions if query.lower() in r.topic.lower()]

    if not revisions:
        console.print("[yellow]No content found. Run 'cauto run --topic \"Your Topic\"' to generate content.[/yellow]")
        return

    if json_output:
        data = [
            {
                "version": r.version,
                "topic": r.topic,
                "timestamp": r.timestamp,
                "word_count": r.word_count,
            }
            for r in revisions
        ]
        console.print(json_lib.dumps(data, indent=2))
        return

    table = Table(title=f"Content ({len(revisions)} items)")
    table.add_column("#", style="dim")
    table.add_column("Version", style="bold cyan")
    table.add_column("Topic")
    table.add_column("Date")
    table.add_column("Words", justify="right")

    for i, rev in enumerate(revisions, 1):
        date_str = rev.timestamp[:10] if rev.timestamp else ""
        table.add_row(str(i), rev.version, rev.topic[:50], date_str, str(rev.word_count))

    console.print(table)


@cli.command()
@click.argument("version_or_topic", required=False)
@click.option("--latest", is_flag=True, default=False, help="Show latest revision")
@click.option("--json", "json_output", is_flag=True, default=False, help="Output in JSON format")
def show(version_or_topic, latest, json_output):
    """Show details of a specific content revision."""
    hist = RevisionHistory()

    revision = None
    if latest:
        revision = hist.get_latest()
    elif version_or_topic:
        # Try as version first
        revision = hist.get_revision(version_or_topic)
        # Try as topic search
        if not revision:
            revisions = hist.list_revisions(limit=100)
            matches = [r for r in revisions if version_or_topic.lower() in r.topic.lower()]
            if matches:
                revision = matches[0]
    else:
        revision = hist.get_latest()

    if not revision:
        console.print("[yellow]No revision found.[/yellow]")
        return

    if json_output:
        console.print(json_lib.dumps({
            "version": revision.version,
            "timestamp": revision.timestamp,
            "topic": revision.topic,
            "summary": revision.summary,
            "word_count": revision.word_count,
            "tone": revision.tone,
            "num_images": revision.num_images,
            "export_formats": revision.export_formats,
        }, indent=2))
        return

    console.print(Panel.fit(
        f"[bold]Revision: {revision.version}[/bold]",
        border_style="cyan",
    ))

    console.print(f"\n[bold]Topic:[/bold] {revision.topic}")
    console.print(f"[bold]Date:[/bold] {revision.timestamp}")
    console.print(f"[bold]Summary:[/bold] {revision.summary}")
    console.print(f"[bold]Word Count:[/bold] {revision.word_count}")
    console.print(f"[bold]Tone:[/bold] {revision.tone}")
    console.print(f"[bold]Images:[/bold] {revision.num_images}")
    console.print(f"[bold]Exports:[/bold] {', '.join(revision.export_formats)}")
