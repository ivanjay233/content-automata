"""Progress tracking with Rich progress bars."""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from rich.console import Console
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)
from rich.table import Table
from rich.panel import Panel


class PipelineProgress:
    """Tracks pipeline execution progress with Rich visualizations."""

    STAGES = [
        ("research", "🔍 Researching", "Web research & topic analysis"),
        ("copywriting", "✍️  Writing", "Content generation & copywriting"),
        ("visuals", "🎨 Visuals", "Image generation & asset creation"),
        ("scheduling", "📅 Scheduling", "Formatting, export & scheduling"),
    ]

    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()
        self._progress: Optional[Progress] = None
        self._tasks: Dict[str, int] = {}
        self._start_time: float = 0.0
        self._current_stage: str = ""

    def start(self, topic: str) -> None:
        """Start progress tracking for a pipeline run.

        Args:
            topic: The content topic being processed.
        """
        self._start_time = time.time()
        self.console.print(Panel.fit(
            f"[bold cyan]content-automata[/bold cyan] — [white]{topic}[/white]",
            border_style="cyan",
        ))

        self._progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
            console=self.console,
        )

        self._progress.start()
        self._tasks = {}

        # Create task for each stage
        for i, (stage_id, label, _) in enumerate(self.STAGES):
            task_id = self._progress.add_task(
                f"[bold]{label}[/bold]",
                total=100,
                visible=False,
            )
            self._tasks[stage_id] = task_id

    def update_stage(self, stage: str, progress: float = 0.0, status: str = "") -> None:
        """Update progress for a specific stage.

        Args:
            stage: Stage identifier ('research', 'copywriting', 'visuals', 'scheduling').
            progress: Progress percentage (0-100).
            status: Optional status message.
        """
        if not self._progress or stage not in self._tasks:
            return

        task_id = self._tasks[stage]

        # Show the current stage
        self._progress.update(task_id, visible=True, completed=progress)

        if status:
            stage_index = next(
                i for i, (sid, _, _) in enumerate(self.STAGES) if sid == stage
            )
            self._progress.update(
                task_id,
                description=f"[bold]{self.STAGES[stage_index][1]}[/bold] — {status}",
            )

        self._current_stage = stage

    def complete_stage(self, stage: str) -> None:
        """Mark a stage as complete.

        Args:
            stage: Stage identifier.
        """
        self.update_stage(stage, progress=100.0, status="[green]✓ Complete[/green]")

    def finish(self, success: bool = True) -> None:
        """Finish progress tracking.

        Args:
            success: Whether the pipeline completed successfully.
        """
        if self._progress:
            self._progress.stop()

        elapsed = time.time() - self._start_time
        status = "[bold green]✓ Pipeline Complete![/bold green]" if success else "[bold red]✗ Pipeline Failed[/bold red]"
        self.console.print(f"{status} [dim]({elapsed:.1f}s)[/dim]")

    def show_summary(self, results: Dict[str, Any]) -> None:
        """Display a summary table of pipeline results.

        Args:
            results: Dictionary of pipeline results by stage.
        """
        table = Table(title="Pipeline Summary", show_header=True, header_style="bold cyan")
        table.add_column("Stage", style="bold")
        table.add_column("Status", style="green")
        table.add_column("Details")

        for stage_id, label, _ in self.STAGES:
            stage_result = results.get(stage_id, {})
            status = "✅" if stage_result.get("success") else "⬜"
            details = stage_result.get("details", "")
            table.add_row(label, status, details)

        self.console.print(table)

    @staticmethod
    def stage_label(stage: str) -> str:
        """Get the human-readable label for a stage."""
        labels = {
            "research": "Research",
            "copywriting": "Copywriting",
            "visuals": "Visuals",
            "scheduling": "Scheduling",
        }
        return labels.get(stage, stage)
