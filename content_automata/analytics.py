"""Content analytics — tracks word counts, trends, and usage statistics."""

from __future__ import annotations

import json
import logging
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from content_automata.history import RevisionHistory, RevisionEntry

logger = logging.getLogger(__name__)


@dataclass
class ContentStats:
    """Aggregated content production statistics."""

    total_runs: int = 0
    total_words: int = 0
    total_images: int = 0
    avg_word_count: float = 0.0
    most_productive_day: str = ""
    top_topics: List[str] = field(default_factory=list)
    words_by_day: Dict[str, int] = field(default_factory=dict)
    runs_by_day: Dict[str, int] = field(default_factory=dict)


class ContentAnalytics:
    """Analyzes content production patterns from revision history."""

    def __init__(self, config: Optional[Dict] = None):
        self._config = config or {}
        self._history = RevisionHistory(config)

    def compute_stats(self, days: int = 30) -> ContentStats:
        """Compute content production statistics over a period.

        Args:
            days: Number of days to analyze (default: 30).

        Returns:
            ContentStats with aggregated metrics.
        """
        stats = ContentStats()
        revisions = self._history.list_revisions(limit=1000)

        # Filter by date range
        cutoff = datetime.now() - timedelta(days=days)
        recent = [
            r for r in revisions
            if self._parse_timestamp(r.timestamp) >= cutoff
        ]

        stats.total_runs = len(recent)
        stats.total_words = sum(r.word_count for r in recent)
        stats.total_images = sum(r.num_images for r in recent)
        stats.avg_word_count = stats.total_words / max(stats.total_runs, 1)

        # Words by day
        day_words: Dict[str, int] = defaultdict(int)
        day_runs: Dict[str, int] = defaultdict(int)
        for r in recent:
            day = r.timestamp[:10] if r.timestamp else "unknown"
            day_words[day] += r.word_count
            day_runs[day] += 1

        stats.words_by_day = dict(day_words)
        stats.runs_by_day = dict(day_runs)

        # Most productive day
        if day_words:
            stats.most_productive_day = max(day_words, key=day_words.get)

        # Top topics
        topic_counts = Counter(r.topic for r in recent)
        stats.top_topics = [t for t, _ in topic_counts.most_common(5)]

        return stats

    def word_count_trend(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get word count trend data for charting.

        Args:
            days: Number of days.

        Returns:
            List of {date, words, runs} dicts.
        """
        stats = self.compute_stats(days)
        return [
            {"date": day, "words": words, "runs": stats.runs_by_day.get(day, 0)}
            for day, words in sorted(stats.words_by_day.items())
        ]

    def _parse_timestamp(self, ts: str) -> datetime:
        """Parse an ISO timestamp string."""
        try:
            return datetime.fromisoformat(ts)
        except (ValueError, TypeError):
            return datetime.min
