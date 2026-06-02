"""Content diff/comparison module for tracking changes between content versions.

Supports structural and semantic comparison of content packages,
drafts, and research results across pipeline runs.
"""

from __future__ import annotations

import difflib
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from content_automata.models import ContentPackage, Draft, ResearchResult

logger = logging.getLogger(__name__)


@dataclass
class DiffLine:
    """A single line in a diff output."""

    text: str
    kind: str = "equal"  # equal, added, removed, changed


@dataclass
class ContentDiff:
    """Structural diff between two content packages."""

    topic_changed: bool = False
    word_count_delta: int = 0
    sections_added: List[str] = field(default_factory=list)
    sections_removed: List[str] = field(default_factory=list)
    headline_changed: bool = False
    old_headline: str = ""
    new_headline: str = ""
    image_count_delta: int = 0
    research_points_added: List[str] = field(default_factory=list)
    research_points_removed: List[str] = field(default_factory=list)
    text_diff: List[DiffLine] = field(default_factory=list)
    similarity_score: float = 1.0
    version_a: str = ""
    version_b: str = ""


class ContentDiffer:
    """Compares two content packages or drafts and produces a structured diff.

    Supports:
    - Full content package comparison
    - Draft-level comparison
    - Research result comparison
    - Text-level unified diffs
    """

    def compare_packages(
        self,
        package_a: ContentPackage,
        package_b: ContentPackage,
    ) -> ContentDiff:
        """Compare two complete content packages.

        Args:
            package_a: First content package.
            package_b: Second content package.

        Returns:
            Structured ContentDiff between the packages.
        """
        diff = ContentDiff(
            version_a=package_a.version,
            version_b=package_b.version,
        )

        # Topic comparison
        diff.topic_changed = package_a.brief.topic != package_b.brief.topic

        # Word count delta
        diff.word_count_delta = (
            package_b.final.draft.word_count - package_a.final.draft.word_count
        )

        # Headline comparison
        old_head = package_a.final.draft.headline or ""
        new_head = package_b.final.draft.headline or ""
        if old_head != new_head:
            diff.headline_changed = True
            diff.old_headline = old_head
            diff.new_headline = new_head

        # Image count delta
        diff.image_count_delta = (
            len(package_b.final.visuals.images)
            - len(package_a.final.visuals.images)
        )

        # Research points comparison
        points_a = set(package_a.final.research.key_points)
        points_b = set(package_b.final.research.key_points)
        diff.research_points_added = sorted(points_b - points_a)
        diff.research_points_removed = sorted(points_a - points_b)

        # Text-level diff of blog posts
        text_a = package_a.final.draft.blog_post or ""
        text_b = package_b.final.draft.blog_post or ""
        diff.text_diff = self._compute_text_diff(text_a, text_b)

        # Similarity score
        diff.similarity_score = self._compute_similarity(text_a, text_b)

        return diff

    def compare_drafts(self, draft_a: Draft, draft_b: Draft) -> ContentDiff:
        """Compare two drafts directly.

        Args:
            draft_a: First draft.
            draft_b: Second draft.

        Returns:
            ContentDiff focused on draft-level changes.
        """
        diff = ContentDiff()
        diff.word_count_delta = draft_b.word_count - draft_a.word_count

        if draft_a.headline != draft_b.headline:
            diff.headline_changed = True
            diff.old_headline = draft_a.headline or ""
            diff.new_headline = draft_b.headline or ""

        text_a = draft_a.blog_post or ""
        text_b = draft_b.blog_post or ""
        diff.text_diff = self._compute_text_diff(text_a, text_b)
        diff.similarity_score = self._compute_similarity(text_a, text_b)

        return diff

    def compare_research(
        self,
        research_a: ResearchResult,
        research_b: ResearchResult,
    ) -> ContentDiff:
        """Compare two research results.

        Args:
            research_a: First research result.
            research_b: Second research result.

        Returns:
            ContentDiff focused on research-level changes.
        """
        diff = ContentDiff()
        diff.topic_changed = research_a.topic != research_b.topic

        points_a = set(research_a.key_points)
        points_b = set(research_b.key_points)
        diff.research_points_added = sorted(points_b - points_a)
        diff.research_points_removed = sorted(points_a - points_b)

        text_a = research_a.summary or ""
        text_b = research_b.summary or ""
        diff.text_diff = self._compute_text_diff(text_a, text_b)
        diff.similarity_score = self._compute_similarity(text_a, text_b)

        return diff

    def _compute_text_diff(
        self,
        text_a: str,
        text_b: str,
    ) -> List[DiffLine]:
        """Generate a line-level diff between two text blocks.

        Args:
            text_a: Original text.
            text_b: New text.

        Returns:
            List of DiffLine objects representing changes.
        """
        lines_a = text_a.splitlines(keepends=True)
        lines_b = text_b.splitlines(keepends=True)
        matcher = difflib.SequenceMatcher(None, lines_a, lines_b)
        result: List[DiffLine] = []

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "equal":
                for line in lines_a[i1:i2]:
                    result.append(DiffLine(text=line.rstrip("\n"), kind="equal"))
            elif tag == "replace":
                for line in lines_a[i1:i2]:
                    result.append(DiffLine(text=line.rstrip("\n"), kind="removed"))
                for line in lines_b[j1:j2]:
                    result.append(DiffLine(text=line.rstrip("\n"), kind="added"))
            elif tag == "delete":
                for line in lines_a[i1:i2]:
                    result.append(DiffLine(text=line.rstrip("\n"), kind="removed"))
            elif tag == "insert":
                for line in lines_b[j1:j2]:
                    result.append(DiffLine(text=line.rstrip("\n"), kind="added"))

        return result

    def _compute_similarity(self, text_a: str, text_b: str) -> float:
        """Compute a similarity ratio between two text blocks.

        Args:
            text_a: Original text.
            text_b: New text.

        Returns:
            Similarity score between 0.0 (completely different) and 1.0 (identical).
        """
        if not text_a and not text_b:
            return 1.0
        return difflib.SequenceMatcher(None, text_a, text_b).ratio()

    def render_unified_diff(self, diff: ContentDiff) -> str:
        """Render a ContentDiff as a human-readable unified diff string.

        Args:
            diff: The content diff to render.

        Returns:
            Formatted string showing changes.
        """
        lines: List[str] = []
        lines.append(f"--- Version: {diff.version_a}")
        lines.append(f"+++ Version: {diff.version_b}")
        lines.append("")

        if diff.topic_changed:
            lines.append("Topic changed")

        if diff.headline_changed:
            lines.append(f"Headline: '{diff.old_headline}' -> '{diff.new_headline}'")

        if diff.word_count_delta != 0:
            sign = "+" if diff.word_count_delta > 0 else ""
            lines.append(f"Word count: {sign}{diff.word_count_delta} words")

        if diff.image_count_delta != 0:
            sign = "+" if diff.image_count_delta > 0 else ""
            lines.append(f"Images: {sign}{diff.image_count_delta}")

        if diff.research_points_added:
            lines.append(f"Research points added: {diff.research_points_added}")
        if diff.research_points_removed:
            lines.append(f"Research points removed: {diff.research_points_removed}")

        lines.append(f"Similarity: {diff.similarity_score:.1%}")
        lines.append("")

        # Render text diff
        for dline in diff.text_diff:
            if dline.kind == "added":
                lines.append(f"+ {dline.text}")
            elif dline.kind == "removed":
                lines.append(f"- {dline.text}")
            elif dline.kind == "changed":
                lines.append(f"~ {dline.text}")
            else:
                lines.append(f"  {dline.text}")

        return "\n".join(lines)
