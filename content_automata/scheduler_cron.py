"""Scheduled publishing via cron expression support.

Provides cron-based scheduling for content publishing, including
cron expression parsing, next-run calculation, and schedule
validation for automated content distribution.
"""

from __future__ import annotations

import logging
import re
from calendar import monthrange
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# Standard cron field names and their ranges
CRON_FIELDS = {
    "minute": (0, 59),
    "hour": (0, 23),
    "day_of_month": (1, 31),
    "month": (1, 12),
    "day_of_week": (0, 6),  # 0=Sunday
}

CRON_PRESETS: Dict[str, str] = {
    "@every_minute": "* * * * *",
    "@hourly": "0 * * * *",
    "@daily": "0 0 * * *",
    "@weekly": "0 0 * * 0",
    "@monthly": "0 0 1 * *",
    "@weekdays": "0 9 * * 1-5",
    "@weekends": "0 10 * * 0,6",
    "@biweekly": "0 0 */14 * *",
}


@dataclass
class CronExpression:
    """Parsed cron expression with field values."""

    raw: str
    minute: str = "*"
    hour: str = "*"
    day_of_month: str = "*"
    month: str = "*"
    day_of_week: str = "*"
    preset_name: str = ""

    def is_valid(self) -> bool:
        """Check if the cron expression is valid.

        Returns:
            True if the expression parses and validates correctly.
        """
        try:
            validate_cron(self.raw)
            return True
        except ValueError:
            return False

    def next_run(self, after: Optional[datetime] = None) -> Optional[datetime]:
        """Calculate the next scheduled run time.

        Args:
            after: Reference time (defaults to now).

        Returns:
            The next datetime matching this cron schedule, or None.
        """
        return compute_next_cron_run(self.raw, after)

    def describe(self) -> str:
        """Generate a human-readable description of this schedule.

        Returns:
            English description of when content will publish.
        """
        return describe_cron(self.raw)


@dataclass
class PublishSchedule:
    """A scheduled content publish task."""

    cron: str
    template: str = "blog"
    topic_template: str = ""
    destinations: List[str] = field(default_factory=lambda: ["markdown"])
    enabled: bool = True
    next_run_at: Optional[datetime] = None
    last_run_at: Optional[datetime] = None
    metadata: Dict[str, str] = field(default_factory=dict)


class CronScheduler:
    """Manages cron-based content publishing schedules.

    Supports:
    - Standard 5-field cron expressions
    - Named presets (@daily, @weekly, etc.)
    - Next-run computation
    - Schedule validation
    - Human-readable descriptions
    """

    def __init__(self, config: Optional[dict] = None):
        self._config = config or {}
        self._schedules: Dict[str, PublishSchedule] = {}
        self._load_defaults()

    def _load_defaults(self) -> None:
        """Load default schedules from configuration."""
        schedules = self._config.get("schedules", {})
        for name, cfg in schedules.items():
            if isinstance(cfg, dict):
                self.add_schedule(
                    name=name,
                    cron=cfg.get("cron", "@daily"),
                    template=cfg.get("template", "blog"),
                    topic_template=cfg.get("topic_template", ""),
                    destinations=cfg.get("destinations", ["markdown"]),
                    enabled=cfg.get("enabled", True),
                    metadata=cfg.get("metadata", {}),
                )

    def add_schedule(
        self,
        name: str,
        cron: str,
        template: str = "blog",
        topic_template: str = "",
        destinations: Optional[List[str]] = None,
        enabled: bool = True,
        metadata: Optional[Dict[str, str]] = None,
    ) -> PublishSchedule:
        """Add a new publish schedule.

        Args:
            name: Unique schedule name.
            cron: Cron expression or preset name.
            template: Content template to use.
            topic_template: Dynamic topic template.
            destinations: Export destinations.
            enabled: Whether the schedule is active.
            metadata: Additional metadata.

        Returns:
            The created PublishSchedule.
        """
        resolved_cron = CRON_PRESETS.get(cron, cron)
        if not is_valid_cron(resolved_cron):
            raise ValueError(
                f"Invalid cron expression '{cron}'. "
                f"Use standard cron (5 fields) or presets: {list(CRON_PRESETS.keys())}"
            )

        schedule = PublishSchedule(
            cron=resolved_cron,
            template=template,
            topic_template=topic_template,
            destinations=destinations or ["markdown"],
            enabled=enabled,
            next_run_at=compute_next_cron_run(resolved_cron),
            metadata=metadata or {},
        )
        self._schedules[name] = schedule
        logger.info(
            "Added schedule '%s': %s (next: %s)",
            name,
            resolved_cron,
            schedule.next_run_at,
        )
        return schedule

    def remove_schedule(self, name: str) -> bool:
        """Remove a publish schedule.

        Args:
            name: Schedule name to remove.

        Returns:
            True if removed, False if not found.
        """
        return self._schedules.pop(name, None) is not None

    def get_schedule(self, name: str) -> Optional[PublishSchedule]:
        """Get a schedule by name.

        Args:
            name: Schedule name.

        Returns:
            The schedule, or None if not found.
        """
        return self._schedules.get(name)

    def list_schedules(self) -> Dict[str, PublishSchedule]:
        """List all registered schedules.

        Returns:
            Dictionary of schedule name -> PublishSchedule.
        """
        return dict(self._schedules)

    def due_schedules(
        self,
        at: Optional[datetime] = None,
    ) -> List[str]:
        """Find all schedules due to run.

        Args:
            at: Reference time (defaults to now).

        Returns:
            List of schedule names that are due.
        """
        now = at or datetime.now()
        due: List[str] = []
        for name, schedule in self._schedules.items():
            if not schedule.enabled:
                continue
            if schedule.next_run_at and schedule.next_run_at <= now:
                due.append(name)
        return due

    def mark_run(self, name: str, at: Optional[datetime] = None) -> None:
        """Mark a schedule as having been run.

        Args:
            name: Schedule name.
            at: Run timestamp (defaults to now).
        """
        schedule = self._schedules.get(name)
        if schedule:
            now = at or datetime.now()
            schedule.last_run_at = now
            schedule.next_run_at = compute_next_cron_run(schedule.cron, now)
            logger.info("Schedule '%s' run at %s, next at %s", name, now, schedule.next_run_at)


def is_valid_cron(expression: str) -> bool:
    """Validate a 5-field cron expression.

    Args:
        expression: The cron expression to validate.

    Returns:
        True if valid, False otherwise.
    """
    try:
        validate_cron(expression)
        return True
    except ValueError:
        return False


def validate_cron(expression: str) -> None:
    """Validate a cron expression, raising on invalid input.

    Args:
        expression: The cron expression to validate.

    Raises:
        ValueError: If the expression is invalid.
    """
    expression = expression.strip()

    # Check presets
    if expression in CRON_PRESETS:
        expression = CRON_PRESETS[expression]

    parts = expression.split()
    if len(parts) != 5:
        raise ValueError(
            f"Cron expression must have exactly 5 fields, got {len(parts)}: '{expression}'"
        )

    field_names = list(CRON_FIELDS.keys())
    for i, (part, (low, high)) in enumerate(zip(parts, CRON_FIELDS.values())):
        _validate_cron_field(part, low, high, field_names[i])


def _validate_cron_field(value: str, low: int, high: int, name: str) -> None:
    """Validate a single cron field value.

    Args:
        value: The field value string.
        low: Minimum valid value.
        high: Maximum valid value.
        name: Field name for error messages.

    Raises:
        ValueError: If the field value is invalid.
    """
    if value == "*":
        return

    # Handle comma-separated lists
    for part in value.split(","):
        part = part.strip()

        # Handle step values
        if "/" in part:
            base, step = part.split("/", 1)
            if not step.isdigit() or int(step) < 1:
                raise ValueError(f"Invalid step in cron field '{name}': '{part}'")
            if base == "*":
                continue
            part = base

        # Handle ranges
        if "-" in part:
            range_parts = part.split("-", 1)
            if len(range_parts) != 2:
                raise ValueError(f"Invalid range in cron field '{name}': '{part}'")
            start, end = range_parts
            if not start.isdigit() or not end.isdigit():
                raise ValueError(f"Non-numeric range in cron field '{name}': '{part}'")
            s, e = int(start), int(end)
            if s < low or e > high or s > e:
                raise ValueError(
                    f"Range {s}-{e} out of bounds for cron field '{name}' "
                    f"(valid: {low}-{high}): '{part}'"
                )
        elif part.isdigit():
            val = int(part)
            if val < low or val > high:
                raise ValueError(
                    f"Value {val} out of bounds for cron field '{name}' "
                    f"(valid: {low}-{high}): '{part}'"
                )
        else:
            raise ValueError(f"Invalid cron field '{name}': '{part}'")


def compute_next_cron_run(
    expression: str,
    after: Optional[datetime] = None,
) -> Optional[datetime]:
    """Compute the next datetime matching a cron expression.

    Args:
        expression: Cron expression or preset.
        after: Reference time (defaults to now).

    Returns:
        The next matching datetime, or None if no match found.
    """
    expression = CRON_PRESETS.get(expression, expression)

    if not is_valid_cron(expression):
        return None

    parts = expression.split()
    now = after or datetime.now()
    minute_pat, hour_pat, dom_pat, month_pat, dow_pat = parts

    # Start from the next minute
    candidate = now.replace(second=0, microsecond=0) + timedelta(minutes=1)

    # Check up to 4 years ahead
    max_checks = 365 * 24 * 60 * 4
    for _ in range(max_checks):
        if _matches_cron_field(candidate.minute, minute_pat, 0, 59) and \
           _matches_cron_field(candidate.hour, hour_pat, 0, 23) and \
           _matches_cron_field(candidate.day, dom_pat, 1, 31) and \
           _matches_cron_field(candidate.month, month_pat, 1, 12) and \
           _matches_cron_field(candidate.weekday(), dow_pat, 0, 6):
            return candidate
        candidate += timedelta(minutes=1)

    logger.warning("Could not find next cron run for '%s' within 4 years", expression)
    return None


def _matches_cron_field(value: int, pattern: str, low: int, high: int) -> bool:
    """Check if a value matches a cron field pattern.

    Args:
        value: The numeric value to check.
        pattern: The cron field pattern (*, range, step, list).
        low: Minimum valid value.
        high: Maximum valid value.

    Returns:
        True if the value matches the pattern.
    """
    if pattern == "*":
        return True

    for part in pattern.split(","):
        part = part.strip()

        step = 1
        if "/" in part:
            base, step_str = part.split("/", 1)
            step = int(step_str)
            part = base

        if part == "*":
            if value % step == 0:
                return True
            continue

        if "-" in part:
            start_str, end_str = part.split("-", 1)
            start, end = int(start_str), int(end_str)
            if start <= value <= end and (value - start) % step == 0:
                return True
        elif part.isdigit():
            if int(part) == value:
                return True

    return False


def describe_cron(expression: str) -> str:
    """Generate a human-readable description of a cron expression.

    Args:
        expression: Cron expression or preset.

    Returns:
        English description of the schedule.
    """
    expression = CRON_PRESETS.get(expression, expression)

    if expression == "* * * * *":
        return "Every minute"
    if expression == "0 * * * *":
        return "Every hour"
    if expression == "0 0 * * *":
        return "Daily at midnight"
    if expression == "0 0 * * 0":
        return "Weekly on Sunday"
    if expression == "0 0 1 * *":
        return "Monthly on the 1st"
    if expression == "0 9 * * 1-5":
        return "Weekdays at 9:00 AM"
    if expression == "0 10 * * 0,6":
        return "Weekends at 10:00 AM"

    try:
        parts = expression.split()
        minute, hour, dom, month, dow = parts
        desc_parts = []

        if minute != "*" or hour != "*":
            desc_parts.append(f"At {hour}:{minute.zfill(2)}" if hour != "*" else f"At minute {minute}")

        if dom != "*":
            desc_parts.append(f"on day {dom} of month")
        if month != "*":
            desc_parts.append(f"in month {month}")
        if dow != "*":
            day_names = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
            if dow.isdigit():
                desc_parts.append(f"on {day_names[int(dow)]}")
            elif "-" in dow:
                start, end = dow.split("-")
                desc_parts.append(f"{day_names[int(start)]} through {day_names[int(end)]}")
            else:
                desc_parts.append(f"on day {dow}")

        return ", ".join(desc_parts) if desc_parts else expression
    except Exception:
        return expression
