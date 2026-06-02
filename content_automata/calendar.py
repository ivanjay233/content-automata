"""Content calendar and scheduling output."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class CalendarEntry:
    """A single entry in the content calendar."""

    date: str  # YYYY-MM-DD
    topic: str
    content_type: str  # blog, social, newsletter, ad
    status: str = "draft"  # draft, scheduled, published
    platform: str = "web"
    word_count: int = 0
    headline: str = ""
    hashtags: List[str] = field(default_factory=list)
    notes: str = ""


@dataclass
class ContentCalendar:
    """Monthly content calendar with daily entries."""

    month: str  # YYYY-MM
    year: int
    entries: List[CalendarEntry] = field(default_factory=list)
    total_items: int = 0

    def to_markdown(self) -> str:
        """Export calendar as markdown table."""
        lines = [
            f"# Content Calendar — {self.month}",
            "",
            f"Total items: {self.total_items}",
            "",
            "| Date | Topic | Type | Status | Platform |",
            "|------|-------|------|--------|----------|",
        ]
        for entry in sorted(self.entries, key=lambda e: e.date):
            lines.append(
                f"| {entry.date} | {entry.topic[:50]} | {entry.content_type} "
                f"| {entry.status} | {entry.platform} |"
            )
        return "\n".join(lines)

    def to_json(self) -> str:
        """Export calendar as JSON."""
        return json.dumps(
            {
                "month": self.month,
                "year": self.year,
                "total_items": self.total_items,
                "entries": [
                    {
                        "date": e.date,
                        "topic": e.topic,
                        "content_type": e.content_type,
                        "status": e.status,
                        "platform": e.platform,
                        "word_count": e.word_count,
                        "headline": e.headline,
                        "hashtags": e.hashtags,
                    }
                    for e in self.entries
                ],
            },
            indent=2,
        )


class CalendarPlanner:
    """Generates content calendars from topic lists."""

    CONTENT_MIX = {
        "monday": "blog",
        "tuesday": "social",
        "wednesday": "newsletter",
        "thursday": "social",
        "friday": "blog",
        "saturday": "social",
        "sunday": "ad",
    }

    def __init__(self, config: Optional[Dict] = None):
        self._config = config or {}
        self._content_mix = self._config.get("content_mix", self.CONTENT_MIX)

    def plan_month(
        self,
        topics: List[str],
        year: int | None = None,
        month: int | None = None,
        start_day: int = 1,
    ) -> ContentCalendar:
        """Plan a month of content from a list of topics.

        Args:
            topics: List of content topics to schedule.
            year: Calendar year (default: current year).
            month: Calendar month (default: next month).
            start_day: Day of month to start (default: 1).

        Returns:
            ContentCalendar with daily entries.
        """
        now = datetime.now()
        year = year or (now.year if now.month < 12 else now.year + 1)
        month = month or (now.month + 1 if now.month < 12 else 1)

        from calendar import monthrange
        _, days_in_month = monthrange(year, month)
        month_str = f"{year}-{month:02d}"

        calendar = ContentCalendar(month=month_str, year=year)
        topic_idx = 0

        for day in range(start_day, days_in_month + 1):
            date_str = f"{year}-{month:02d}-{day:02d}"
            weekday = datetime(year, month, day).strftime("%A").lower()
            content_type = self._content_mix.get(weekday, "social")

            # Cycle through topics
            topic = topics[topic_idx % len(topics)] if topics else "Untitled"
            topic_idx += 1

            entry = CalendarEntry(
                date=date_str,
                topic=topic,
                content_type=content_type,
                status="draft",
                platform="web",
            )
            calendar.entries.append(entry)

        calendar.total_items = len(calendar.entries)
        logger.info(f"Planned {calendar.total_items} items for {month_str}")
        return calendar
