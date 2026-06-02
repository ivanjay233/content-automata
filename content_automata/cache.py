"""Content caching layer — reduces redundant API calls."""

from __future__ import annotations

import hashlib
import json
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """A single entry in the content cache."""

    key: str
    data: Any
    created_at: float
    ttl: int  # seconds
    hit_count: int = 0


class ContentCache:
    """Simple disk-based cache for content pipeline results.

    Caches research results, generated drafts, and image metadata
    to avoid redundant API calls on repeated runs.
    """

    def __init__(self, config: Optional[Dict] = None):
        self._config = config or {}
        self._cache_dir = Path(
            self._config.get("cache", {}).get("directory", "./.cache/content-automata")
        )
        self._default_ttl = self._config.get("cache", {}).get("default_ttl", 3600)  # 1 hour
        self._enabled = self._config.get("cache", {}).get("enabled", True)
        self._memory_cache: Dict[str, CacheEntry] = {}

        if self._enabled:
            self._cache_dir.mkdir(parents=True, exist_ok=True)

    def get(self, key: str) -> Optional[Any]:
        """Get a value from cache.

        Args:
            key: Cache key.

        Returns:
            Cached value or None if not found or expired.
        """
        if not self._enabled:
            return None

        # Check memory cache first
        if key in self._memory_cache:
            entry = self._memory_cache[key]
            if time.time() - entry.created_at < entry.ttl:
                entry.hit_count += 1
                logger.debug(f"Cache HIT (memory): {key[:50]}...")
                return entry.data
            else:
                del self._memory_cache[key]

        # Check disk cache
        cache_file = self._cache_dir / self._key_to_filename(key)
        if cache_file.exists():
            try:
                with open(cache_file) as f:
                    entry_data = json.load(f)
                if time.time() - entry_data["created_at"] < entry_data["ttl"]:
                    logger.debug(f"Cache HIT (disk): {key[:50]}...")
                    data = entry_data["data"]
                    # Store in memory for faster access next time
                    self._memory_cache[key] = CacheEntry(
                        key=key,
                        data=data,
                        created_at=entry_data["created_at"],
                        ttl=entry_data["ttl"],
                        hit_count=1,
                    )
                    return data
                else:
                    cache_file.unlink(missing_ok=True)
            except (json.JSONDecodeError, KeyError, OSError) as e:
                logger.warning(f"Cache read error: {e}")
                cache_file.unlink(missing_ok=True)

        logger.debug(f"Cache MISS: {key[:50]}...")
        return None

    def set(
        self,
        key: str,
        data: Any,
        ttl: Optional[int] = None,
    ) -> None:
        """Set a value in cache.

        Args:
            key: Cache key.
            data: Data to cache.
            ttl: Time-to-live in seconds (default: configured TTL).
        """
        if not self._enabled:
            return

        entry = CacheEntry(
            key=key,
            data=data,
            created_at=time.time(),
            ttl=ttl or self._default_ttl,
        )

        # Store in memory
        self._memory_cache[key] = entry

        # Store on disk
        try:
            cache_file = self._cache_dir / self._key_to_filename(key)
            with open(cache_file, "w") as f:
                json.dump({
                    "key": key,
                    "data": data,
                    "created_at": entry.created_at,
                    "ttl": entry.ttl,
                }, f)
        except OSError as e:
            logger.warning(f"Cache write error: {e}")

    def invalidate(self, key: str) -> None:
        """Invalidate a cache entry.

        Args:
            key: Cache key to invalidate.
        """
        self._memory_cache.pop(key, None)
        cache_file = self._cache_dir / self._key_to_filename(key)
        cache_file.unlink(missing_ok=True)

    def clear(self) -> None:
        """Clear all cached entries."""
        self._memory_cache.clear()
        for cache_file in self._cache_dir.glob("*.json"):
            cache_file.unlink(missing_ok=True)
        logger.info("Cache cleared")

    def stats(self) -> Dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dict with cache size, hit count, and memory entries.
        """
        disk_entries = list(self._cache_dir.glob("*.json"))
        memory_hits = sum(e.hit_count for e in self._memory_cache.values())
        return {
            "enabled": self._enabled,
            "disk_entries": len(disk_entries),
            "memory_entries": len(self._memory_cache),
            "memory_hits": memory_hits,
            "cache_dir": str(self._cache_dir),
            "default_ttl": self._default_ttl,
        }

    def _key_to_filename(self, key: str) -> str:
        """Convert a cache key to a safe filename."""
        hashed = hashlib.sha256(key.encode()).hexdigest()[:16]
        safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in key)[:40]
        return f"{safe_name}_{hashed}.json"
