"""Content archive/restore functionality.

Provides snapshot-based archiving of content packages with
compression, metadata indexing, and restore capabilities
for content versioning and disaster recovery.
"""

from __future__ import annotations

import gzip
import json
import logging
import pickle
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from content_automata.models import ContentPackage

logger = logging.getLogger(__name__)


@dataclass
class ArchiveEntry:
    """Metadata for a single archived content package."""

    archive_id: str
    topic: str
    created_at: str
    word_count: int
    has_images: bool
    export_formats: List[str]
    size_bytes: int
    compressed: bool
    tags: List[str] = field(default_factory=list)
    notes: str = ""


@dataclass
class ArchiveIndex:
    """Index of all archive entries."""

    entries: Dict[str, ArchiveEntry] = field(default_factory=dict)
    total_count: int = 0
    total_size_bytes: int = 0
    last_updated: str = ""


class ContentArchive:
    """Manages archiving and restoration of content packages.

    Features:
    - Snapshot-based archiving with timestamps
    - Optional gzip compression
    - Metadata indexing for search
    - Full restore of archived packages
    - Batch archive operations
    - Archive listing with metadata
    """

    def __init__(self, archive_dir: Optional[str] = None):
        self._archive_dir = Path(archive_dir or "./archive")
        self._archive_dir.mkdir(parents=True, exist_ok=True)
        self._index_path = self._archive_dir / "index.json"
        self._index = self._load_index()

    def _load_index(self) -> ArchiveIndex:
        """Load the archive index from disk.

        Returns:
            The loaded ArchiveIndex, or a new one if not found.
        """
        if self._index_path.exists():
            try:
                data = json.loads(self._index_path.read_text())
                return ArchiveIndex(
                    entries={
                        k: ArchiveEntry(**v) for k, v in data.get("entries", {}).items()
                    },
                    total_count=data.get("total_count", 0),
                    total_size_bytes=data.get("total_size_bytes", 0),
                    last_updated=data.get("last_updated", ""),
                )
            except (json.JSONDecodeError, KeyError, TypeError) as e:
                logger.warning("Failed to load archive index: %s", e)
        return ArchiveIndex()

    def _save_index(self) -> None:
        """Persist the archive index to disk."""
        data = {
            "entries": {
                k: {
                    "archive_id": e.archive_id,
                    "topic": e.topic,
                    "created_at": e.created_at,
                    "word_count": e.word_count,
                    "has_images": e.has_images,
                    "export_formats": e.export_formats,
                    "size_bytes": e.size_bytes,
                    "compressed": e.compressed,
                    "tags": e.tags,
                    "notes": e.notes,
                }
                for k, e in self._index.entries.items()
            },
            "total_count": self._index.total_count,
            "total_size_bytes": self._index.total_size_bytes,
            "last_updated": datetime.now().isoformat(),
        }
        self._index_path.write_text(json.dumps(data, indent=2))

    def archive(
        self,
        package: ContentPackage,
        tags: Optional[List[str]] = None,
        notes: str = "",
        compress: bool = True,
    ) -> str:
        """Archive a content package.

        Args:
            package: The content package to archive.
            tags: Optional tags for categorization.
            notes: Optional notes about this archive.
            compress: Whether to gzip-compress the archive.

        Returns:
            The archive ID string.
        """
        archive_id = f"arc-{datetime.now().strftime('%Y%m%d%H%M%S-%f')}"
        topic = package.brief.topic
        word_count = package.final.draft.word_count
        has_images = len(package.final.visuals.images) > 0
        export_formats = [e.format for e in package.final.schedule.exports]

        # Serialize the package
        try:
            raw_data = pickle.dumps(package)
            raw_size = len(raw_data)
        except (pickle.PicklingError, TypeError) as e:
            logger.error("Failed to serialize package: %s", e)
            raise ValueError(f"Cannot archive package: {e}") from e

        # Optionally compress
        if compress and raw_size > 1024:
            compressed_data = gzip.compress(raw_data)
            archive_data = compressed_data
            actual_compressed = True
        else:
            archive_data = raw_data
            actual_compressed = False

        # Write archive file
        ext = ".arc.gz" if actual_compressed else ".arc"
        archive_path = self._archive_dir / f"{archive_id}{ext}"
        archive_path.write_bytes(archive_data)
        size_bytes = len(archive_data)

        # Update index
        entry = ArchiveEntry(
            archive_id=archive_id,
            topic=topic,
            created_at=datetime.now().isoformat(),
            word_count=word_count,
            has_images=has_images,
            export_formats=export_formats,
            size_bytes=size_bytes,
            compressed=actual_compressed,
            tags=tags or [],
            notes=notes,
        )
        self._index.entries[archive_id] = entry
        self._index.total_count = len(self._index.entries)
        self._index.total_size_bytes += size_bytes
        self._index.last_updated = datetime.now().isoformat()
        self._save_index()

        logger.info(
            "Archived '%s' as %s (%d bytes, compressed=%s)",
            topic,
            archive_id,
            size_bytes,
            actual_compressed,
        )
        return archive_id

    def restore(self, archive_id: str) -> Optional[ContentPackage]:
        """Restore an archived content package.

        Args:
            archive_id: The archive ID to restore.

        Returns:
            The restored ContentPackage, or None if not found.
        """
        entry = self._index.entries.get(archive_id)
        if not entry:
            logger.warning("Archive not found: %s", archive_id)
            return None

        # Try compressed first, then uncompressed
        archive_path = self._archive_dir / f"{archive_id}.arc.gz"
        if archive_path.exists():
            raw_data = gzip.decompress(archive_path.read_bytes())
        else:
            archive_path = self._archive_dir / f"{archive_id}.arc"
            if not archive_path.exists():
                logger.warning("Archive file not found: %s", archive_id)
                return None
            raw_data = archive_path.read_bytes()

        try:
            package: ContentPackage = pickle.loads(raw_data)
            logger.info("Restored archive '%s': topic='%s'", archive_id, package.brief.topic)
            return package
        except (pickle.UnpicklingError, EOFError, TypeError) as e:
            logger.error("Failed to restore archive '%s': %s", archive_id, e)
            return None

    def delete(self, archive_id: str) -> bool:
        """Delete an archived content package.

        Args:
            archive_id: The archive ID to delete.

        Returns:
            True if deleted, False if not found.
        """
        entry = self._index.entries.pop(archive_id, None)
        if not entry:
            return False

        # Remove files
        for ext in [".arc.gz", ".arc"]:
            path = self._archive_dir / f"{archive_id}{ext}"
            if path.exists():
                path.unlink()
                self._index.total_size_bytes -= entry.size_bytes
                break

        self._index.total_count = len(self._index.entries)
        self._index.last_updated = datetime.now().isoformat()
        self._save_index()
        logger.info("Deleted archive: %s", archive_id)
        return True

    def list_archives(
        self,
        tags: Optional[List[str]] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[ArchiveEntry]:
        """List archived content packages.

        Args:
            tags: Optional filter by tags.
            limit: Maximum number of entries to return.
            offset: Number of entries to skip.

        Returns:
            List of ArchiveEntry metadata objects.
        """
        entries = sorted(
            self._index.entries.values(),
            key=lambda e: e.created_at,
            reverse=True,
        )

        if tags:
            entries = [e for e in entries if any(t in e.tags for t in tags)]

        return entries[offset : offset + limit]

    def search(self, query: str) -> List[ArchiveEntry]:
        """Search archived content by topic or notes.

        Args:
            query: Search string to match against topics and notes.

        Returns:
            List of matching ArchiveEntry objects.
        """
        query_lower = query.lower()
        results = []
        for entry in self._index.entries.values():
            if query_lower in entry.topic.lower() or query_lower in entry.notes.lower():
                results.append(entry)
        return sorted(results, key=lambda e: e.created_at, reverse=True)

    def get_stats(self) -> Dict[str, Any]:
        """Get archive statistics.

        Returns:
            Dictionary with archive statistics.
        """
        return {
            "total_archives": self._index.total_count,
            "total_size_bytes": self._index.total_size_bytes,
            "total_size_human": self._format_bytes(self._index.total_size_bytes),
            "last_updated": self._index.last_updated,
            "archive_dir": str(self._archive_dir),
            "index_path": str(self._index_path),
        }

    @staticmethod
    def _format_bytes(size: int) -> str:
        """Format byte size for human readability.

        Args:
            size: Size in bytes.

        Returns:
            Human-readable size string.
        """
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"
