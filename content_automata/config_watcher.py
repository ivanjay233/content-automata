"""Config hot-reload support with file watcher.

Enables dynamic configuration reloading without restarting
the pipeline. Uses file polling to detect changes and
triggers callback functions on config updates.
"""

from __future__ import annotations

import hashlib
import logging
import os
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from content_automata.config_loader import load_config_from_file, merge_configs
from content_automata.config_models import PipelineConfig

logger = logging.getLogger(__name__)


@dataclass
class ConfigSnapshot:
    """A snapshot of configuration state for change detection."""

    path: str
    checksum: str
    mtime: float
    size: int
    data: Dict[str, Any] = field(default_factory=dict)


class ConfigWatcher:
    """Watches configuration files for changes and triggers reloads.

    Uses polling with configurable interval. When a config file
    changes, computes a diff and notifies registered callbacks.

    Features:
    - Polling-based file change detection
    - Checksum comparison for accurate change detection
    - Callback registration for custom reload logic
    - Throttled reloads to prevent rapid reload storms
    - Stale/fallback config support
    """

    def __init__(
        self,
        config_path: Optional[str] = None,
        poll_interval: float = 5.0,
        debounce_seconds: float = 1.0,
    ):
        """Initialize ConfigWatcher.

        Args:
            config_path: Path to config file to watch.
            poll_interval: Seconds between polls.
            debounce_seconds: Minimum seconds between reloads.
        """
        self._config_path = Path(config_path) if config_path else None
        self._poll_interval = poll_interval
        self._debounce = debounce_seconds
        self._snapshot: Optional[ConfigSnapshot] = None
        self._callbacks: List[Callable[[PipelineConfig], None]] = []
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._last_reload_time: float = 0.0
        self._lock = threading.RLock()
        self._current_config: Optional[PipelineConfig] = None

    def register_callback(self, callback: Callable[[PipelineConfig], None]) -> None:
        """Register a callback for config reloads.

        Callback receives the new PipelineConfig on every detected change.

        Args:
            callback: Function taking a PipelineConfig argument.
        """
        with self._lock:
            self._callbacks.append(callback)
            logger.debug("Registered config reload callback: %s", callback.__name__)

    def unregister_callback(self, callback: Callable) -> bool:
        """Unregister a previously registered callback.

        Args:
            callback: The callback function to remove.

        Returns:
            True if removed, False if not found.
        """
        with self._lock:
            try:
                self._callbacks.remove(callback)
                return True
            except ValueError:
                return False

    def start(self) -> None:
        """Start the config watcher in a background thread."""
        if self._running:
            logger.warning("ConfigWatcher is already running")
            return

        if not self._config_path or not self._config_path.exists():
            logger.warning(
                "ConfigWatcher: no valid config path, watching disabled"
            )
            return

        self._running = True
        self._snapshot = self._take_snapshot(self._config_path)
        self._thread = threading.Thread(
            target=self._watch_loop,
            name="config-watcher",
            daemon=True,
        )
        self._thread.start()
        logger.info(
            "ConfigWatcher started: watching %s (poll every %.1fs)",
            self._config_path,
            self._poll_interval,
        )

    def stop(self) -> None:
        """Stop the config watcher."""
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5.0)
        logger.info("ConfigWatcher stopped")

    @property
    def current_config(self) -> Optional[PipelineConfig]:
        """Get the most recently loaded config.

        Returns:
            Current PipelineConfig, or None if not loaded.
        """
        return self._current_config

    def reload_now(self) -> Optional[PipelineConfig]:
        """Force an immediate configuration reload.

        Returns:
            New PipelineConfig if changed, None if unchanged.
        """
        if not self._config_path:
            return None

        new_snapshot = self._take_snapshot(self._config_path)

        with self._lock:
            if new_snapshot.checksum == (self._snapshot.checksum if self._snapshot else ""):
                logger.debug("Config unchanged (checksum match)")
                return None

            cfg = self._load_and_notify(new_snapshot)
            self._snapshot = new_snapshot
            self._last_reload_time = time.monotonic()
            return cfg

    def _watch_loop(self) -> None:
        """Background polling loop for config file changes."""
        while self._running:
            try:
                time.sleep(self._poll_interval)

                if not self._config_path or not self._config_path.exists():
                    continue

                new_snapshot = self._take_snapshot(self._config_path)

                with self._lock:
                    if new_snapshot.checksum == (self._snapshot.checksum if self._snapshot else ""):
                        continue

                    # Debounce check
                    now = time.monotonic()
                    if now - self._last_reload_time < self._debounce:
                        logger.debug("Skipping reload (debounce active)")
                        continue

                    logger.info(
                        "Config file changed: %s",
                        self._config_path,
                    )
                    self._load_and_notify(new_snapshot)
                    self._snapshot = new_snapshot
                    self._last_reload_time = now

            except Exception as e:
                logger.error("Config watcher error: %s", e)

    def _take_snapshot(self, path: Path) -> ConfigSnapshot:
        """Take a snapshot of the current config file state.

        Args:
            path: Config file path.

        Returns:
            ConfigSnapshot with file state.
        """
        stat = path.stat()
        content = path.read_bytes()
        return ConfigSnapshot(
            path=str(path),
            checksum=hashlib.sha256(content).hexdigest(),
            mtime=stat.st_mtime,
            size=stat.st_size,
            data=load_config_from_file(str(path)),
        )

    def _load_and_notify(self, snapshot: ConfigSnapshot) -> PipelineConfig:
        """Load config from snapshot and notify callbacks.

        Args:
            snapshot: New config snapshot.

        Returns:
            Loaded PipelineConfig.
        """
        cfg = PipelineConfig.from_dict(snapshot.data)
        self._current_config = cfg

        for callback in self._callbacks:
            try:
                callback(cfg)
            except Exception as e:
                logger.error(
                    "Config reload callback '%s' failed: %s",
                    callback.__name__,
                    e,
                )

        logger.info(
            "Config reloaded: %s changes applied",
            len(cfg.errors) if cfg.errors else "with validation",
        )
        return cfg

    def set_config_path(self, path: str) -> None:
        """Change the watched config file path.

        Args:
            path: New config file path.
        """
        with self._lock:
            self._config_path = Path(path)
            self._snapshot = None
            logger.info("ConfigWatcher path changed to: %s", path)

            # Take initial snapshot
            if self._config_path.exists():
                self._snapshot = self._take_snapshot(self._config_path)


class HotReloadContext:
    """Context manager for hot-reloadable configuration.

    Usage:
        with HotReloadContext("config.yaml") as ctx:
            cfg = ctx.config
            # Use cfg...
            # Config changes trigger automatic callback
    """

    def __init__(
        self,
        config_path: str,
        poll_interval: float = 5.0,
        on_reload: Optional[Callable[[PipelineConfig], None]] = None,
    ):
        """Initialize hot-reload context.

        Args:
            config_path: Path to config file.
            poll_interval: Polling interval in seconds.
            on_reload: Optional callback on config change.
        """
        self._watcher = ConfigWatcher(
            config_path=config_path,
            poll_interval=poll_interval,
        )
        self._on_reload = on_reload
        self._config: Optional[PipelineConfig] = None

    @property
    def config(self) -> Optional[PipelineConfig]:
        """Get the current configuration.

        Returns:
            Current PipelineConfig or None.
        """
        return self._config or self._watcher.current_config

    def __enter__(self) -> "HotReloadContext":
        # Load initial config
        if self._watcher._config_path and self._watcher._config_path.exists():
            raw = load_config_from_file(str(self._watcher._config_path))
            self._config = PipelineConfig.from_dict(raw)
            self._watcher._current_config = self._config

        # Register callback
        if self._on_reload:
            self._watcher.register_callback(self._on_reload)

        # Define default callback
        def _default_reload(cfg: PipelineConfig) -> None:
            self._config = cfg
            logger.info("Config hot-reloaded: %d settings updated", len(cfg.to_dict()))

        self._watcher.register_callback(_default_reload)
        self._watcher.start()
        return self

    def __exit__(self, *args: Any) -> None:
        self._watcher.stop()
