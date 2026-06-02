"""Content revision history tracking."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class RevisionEntry:
    """A single revision entry."""

    version: str
    timestamp: str
    topic: str
    summary: str
    word_count: int
    tone: str
    num_images: int
    export_formats: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)


class RevisionHistory:
    """Tracks and stores content pipeline revision history.

    Maintains a local JSON-based history of all pipeline runs,
    with support for listing, viewing, and comparing revisions.
    """

    def __init__(self, config: Optional[Dict] = None):
        self._config = config or {}
        history_dir = self._config.get("history_dir", "./.content-automata/history")
        self._history_dir = Path(history_dir)
        self._history_dir.mkdir(parents=True, exist_ok=True)
        self._history_file = self._history_dir / "revisions.json"
        self._revisions: List[RevisionEntry] = []
        self._load()

    def record(
        self,
        topic: str,
        summary: str = "",
        word_count: int = 0,
        tone: str = "professional",
        num_images: int = 0,
        export_formats: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> RevisionEntry:
        """Record a new revision.

        Args:
            topic: Content topic.
            summary: Content summary.
            word_count: Word count.
            tone: Writing tone.
            num_images: Number of images generated.
            export_formats: Export formats used.
            metadata: Additional metadata.

        Returns:
            The created RevisionEntry.
        """
        version = f"v{len(self._revisions) + 1}.{datetime.now().strftime('%Y%m%d%H%M%S')}"
        entry = RevisionEntry(
            version=version,
            timestamp=datetime.now().isoformat(),
            topic=topic,
            summary=summary,
            word_count=word_count,
            tone=tone,
            num_images=num_images,
            export_formats=export_formats or [],
            metadata=metadata or {},
        )
        self._revisions.append(entry)
        self._save()
        logger.info(f"Recorded revision {version} for '{topic}'")
        return entry

    def list_revisions(self, limit: int = 20) -> List[RevisionEntry]:
        """List recent revisions.

        Args:
            limit: Maximum number of revisions to return.

        Returns:
            List of recent RevisionEntry objects.
        """
        return list(reversed(self._revisions[-limit:]))

    def get_revision(self, version: str) -> Optional[RevisionEntry]:
        """Get a specific revision by version string.

        Args:
            version: Version identifier (e.g., 'v1.20260602...').

        Returns:
            RevisionEntry or None.
        """
        for rev in self._revisions:
            if rev.version == version:
                return rev
        return None

    def get_latest(self) -> Optional[RevisionEntry]:
        """Get the most recent revision.

        Returns:
            Latest RevisionEntry or None.
        """
        return self._revisions[-1] if self._revisions else None

    def count(self) -> int:
        """Get total number of revisions.

        Returns:
            Revision count.
        """
        return len(self._revisions)

    def clear(self) -> None:
        """Clear all revision history."""
        self._revisions.clear()
        self._save()
        logger.info("Revision history cleared")

    def export_json(self) -> str:
        """Export revision history as JSON.

        Returns:
            JSON string of all revisions.
        """
        return json.dumps(
            [
                {
                    "version": r.version,
                    "timestamp": r.timestamp,
                    "topic": r.topic,
                    "summary": r.summary,
                    "word_count": r.word_count,
                    "tone": r.tone,
                    "num_images": r.num_images,
                    "export_formats": r.export_formats,
                }
                for r in self._revisions
            ],
            indent=2,
        )

    def _load(self) -> None:
        """Load revisions from disk."""
        if self._history_file.exists():
            try:
                data = json.loads(self._history_file.read_text())
                self._revisions = [RevisionEntry(**r) for r in data]
                logger.debug(f"Loaded {len(self._revisions)} revisions")
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"Failed to load revision history: {e}")

    def _save(self) -> None:
        """Save revisions to disk."""
        try:
            data = [
                {
                    "version": r.version,
                    "timestamp": r.timestamp,
                    "topic": r.topic,
                    "summary": r.summary,
                    "word_count": r.word_count,
                    "tone": r.tone,
                    "num_images": r.num_images,
                    "export_formats": r.export_formats,
                    "metadata": r.metadata,
                }
                for r in self._revisions
            ]
            self._history_file.write_text(json.dumps(data, indent=2))
        except OSError as e:
            logger.error(f"Failed to save revision history: {e}")
