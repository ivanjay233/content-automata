"""Dry-run mode — preview pipeline execution without side effects."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from content_automata.models import ContentBrief, ContentPackage, PipelineState

logger = logging.getLogger(__name__)


@dataclass
class DryRunAction:
    """A single action that would be performed in a real run."""

    stage: str
    action: str
    details: str
    side_effects: List[str] = field(default_factory=list)
    estimated_cost: str = ""


@dataclass
class DryRunReport:
    """Report of what a pipeline execution would do."""

    topic: str
    actions: List[DryRunAction] = field(default_factory=list)
    total_estimated_cost: str = "$0.00"
    api_calls: int = 0
    files_created: int = 0
    warnings: List[str] = field(default_factory=list)
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())


class DryRunMode:
    """Simulates pipeline execution and reports what would happen.

    Useful for previewing pipeline behavior before committing
    to actual API calls and file output.
    """

    def __init__(self, config: Optional[Dict] = None):
        self._config = config or {}

    def preview(self, brief: ContentBrief | Dict[str, Any]) -> DryRunReport:
        """Generate a dry-run report for a content brief.

        Args:
            brief: Content brief (dict or model) describing the content to generate.

        Returns:
            DryRunReport with all predicted actions and costs.
        """
        if isinstance(brief, dict):
            brief = ContentBrief(**brief)

        report = DryRunReport(topic=brief.topic)
        cfg = self._config

        # Research stage
        provider = cfg.get("research", {}).get("provider", "tavily")
        report.actions.append(DryRunAction(
            stage="research",
            action=f"Web research via {provider}",
            details=f"Topic: '{brief.topic}', Keywords: {brief.keywords}",
            side_effects=["External API call to research provider"],
            estimated_cost="$0.01-0.05",
        ))
        report.api_calls += 1

        # Copywriting stage
        variants = cfg.get("copywriting", {}).get("variants", ["blog", "social", "ad"])
        tone = brief.tone or cfg.get("copywriting", {}).get("default_tone", "professional")
        report.actions.append(DryRunAction(
            stage="copywriting",
            action=f"Content generation ({', '.join(variants)})",
            details=f"Tone: '{tone}', Format: {brief.format}",
            side_effects=["AI text generation API call"],
            estimated_cost="$0.01-0.10",
        ))
        report.api_calls += 1

        # Image generation stage
        img_provider = cfg.get("image_generation", {}).get("provider", "openai")
        aspect = cfg.get("image_generation", {}).get("default_aspect", "16:9")
        num_images = 2
        report.actions.append(DryRunAction(
            stage="image_gen",
            action=f"Generate {num_images} images via {img_provider}",
            details=f"Aspect ratio: {aspect}, Style: standard",
            side_effects=[f"AI image generation API call (x{num_images})"],
            estimated_cost=f"${0.04 * num_images:.2f}-${0.12 * num_images:.2f}",
        ))
        report.api_calls += num_images

        # Scheduling stage
        export_formats = cfg.get("scheduling", {}).get("export_formats", ["markdown"])
        report.actions.append(DryRunAction(
            stage="scheduling",
            action=f"Export content ({', '.join(export_formats)})",
            details=f"Output formats: {', '.join(export_formats)}",
            side_effects=[f"Create {len(export_formats)} output file(s)"],
            estimated_cost="$0.00",
        ))
        report.files_created = len(export_formats)

        # Cost estimation
        costs = {
            "tavily": 0.03,
            "openai_text": 0.02,
            "openai_image": 0.04,
            "stability_image": 0.04,
        }
        total = 0.0
        total += costs.get(provider, 0.03)
        total += costs.get("openai_text", 0.02)
        total += costs.get(f"{img_provider}_image", 0.04) * 2
        report.total_estimated_cost = f"${total:.2f}"

        # Warnings
        if not cfg.get("api_key"):
            report.warnings.append("No API key configured — pipeline will use simulated data")
        if not brief.keywords:
            report.warnings.append("No keywords specified — research may be less targeted")

        return report

    def to_markdown(self, report: DryRunReport) -> str:
        """Format a dry-run report as markdown.

        Args:
            report: The dry-run report to format.

        Returns:
            Markdown string representation.
        """
        lines = [
            f"# Dry Run Report: {report.topic}",
            "",
            f"*Generated at: {report.generated_at}*",
            "",
            "## Summary",
            "",
            f"- **API Calls:** {report.api_calls}",
            f"- **Files Created:** {report.files_created}",
            f"- **Estimated Cost:** {report.total_estimated_cost}",
            "",
        ]

        if report.warnings:
            lines.extend(["## Warnings", ""])
            for w in report.warnings:
                lines.append(f"- ⚠️  {w}")
            lines.append("")

        lines.extend(["## Actions", ""])
        for i, action in enumerate(report.actions, 1):
            lines.extend([
                f"### {i}. {action.stage}: {action.action}",
                "",
                f"- **Details:** {action.details}",
                f"- **Estimated Cost:** {action.estimated_cost}",
            ])
            if action.side_effects:
                for se in action.side_effects:
                    lines.append(f"- *{se}*")
            lines.append("")

        return "\n".join(lines)
