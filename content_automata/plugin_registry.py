"""Plugin architecture for pipeline stages.

Provides a plugin registration system for extending the
content-automata pipeline with custom stages, providers,
and hooks without modifying core code.
"""

from __future__ import annotations

import importlib
import inspect
import logging
import pkgutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Type

from content_automata.stages.base import StageContract

logger = logging.getLogger(__name__)


@dataclass
class PluginMetadata:
    """Metadata for a registered plugin."""

    name: str
    version: str
    description: str
    author: str = ""
    plugin_type: str = "stage"  # stage, provider, hook, extension
    dependencies: List[str] = field(default_factory=list)
    enabled: bool = True


@dataclass
class Hook:
    """A pipeline hook that runs at a specific lifecycle point."""

    name: str
    point: str  # before_stage, after_stage, on_error, on_complete
    handler: Callable
    priority: int = 0  # Lower = runs first
    stage_filter: Optional[str] = None  # Restrict to specific stage


class PluginRegistry:
    """Registry for pipeline plugins, stages, and hooks.

    Provides:
    - Plugin registration and discovery
    - Stage class registration (via StageContract subclasses)
    - Hook registration for lifecycle events
    - Plugin dependency management
    - Plugin enable/disable controls
    """

    def __init__(self, config: Optional[dict] = None):
        self._config = config or {}
        self._plugins: Dict[str, PluginMetadata] = {}
        self._stages: Dict[str, Type[StageContract]] = {}
        self._hooks: Dict[str, List[Hook]] = {
            "before_stage": [],
            "after_stage": [],
            "on_error": [],
            "on_complete": [],
            "before_pipeline": [],
            "after_pipeline": [],
        }
        self._providers: Dict[str, Dict[str, Type]] = {}
        self._extensions: Dict[str, Any] = {}

    # ── Stage Registration ──

    def register_stage(
        self,
        name: str,
        stage_class: Type[StageContract],
        metadata: Optional[PluginMetadata] = None,
    ) -> None:
        """Register a pipeline stage class.

        Args:
            name: Unique stage name.
            stage_class: StageContract subclass.
            metadata: Optional plugin metadata.

        Raises:
            TypeError: If stage_class doesn't extend StageContract.
        """
        if not issubclass(stage_class, StageContract):
            raise TypeError(
                f"Stage '{name}' must extend StageContract, "
                f"got {stage_class.__bases__}"
            )

        self._stages[name] = stage_class
        logger.info("Registered stage: %s (%s)", name, stage_class.__name__)

        if metadata:
            self._plugins[name] = metadata

    def unregister_stage(self, name: str) -> bool:
        """Unregister a stage by name.

        Args:
            name: Stage name to remove.

        Returns:
            True if removed, False if not found.
        """
        return self._stages.pop(name, None) is not None

    def get_stage(self, name: str) -> Optional[Type[StageContract]]:
        """Get a registered stage class.

        Args:
            name: Stage name.

        Returns:
            Stage class, or None if not found.
        """
        return self._stages.get(name)

    def list_stages(self) -> Dict[str, Type[StageContract]]:
        """List all registered stages.

        Returns:
            Dict of stage name -> StageContract class.
        """
        return dict(self._stages)

    def instantiate_stage(
        self,
        name: str,
        config: Optional[Dict[str, Any]] = None,
    ) -> Optional[StageContract]:
        """Create an instance of a registered stage.

        Args:
            name: Stage name.
            config: Configuration dict for the stage.

        Returns:
            StageContract instance, or None if not found.
        """
        stage_class = self._stages.get(name)
        if not stage_class:
            logger.warning("Stage '%s' not found in registry", name)
            return None

        instance = stage_class(config)
        return instance

    # ── Hook Registration ──

    def register_hook(
        self,
        hook: Hook,
        metadata: Optional[PluginMetadata] = None,
    ) -> None:
        """Register a pipeline lifecycle hook.

        Args:
            hook: Hook configuration.
            metadata: Optional plugin metadata.

        Raises:
            ValueError: If hook point is unknown.
        """
        if hook.point not in self._hooks:
            raise ValueError(
                f"Unknown hook point '{hook.point}'. "
                f"Valid: {list(self._hooks.keys())}"
            )

        self._hooks[hook.point].append(hook)
        self._hooks[hook.point].sort(key=lambda h: h.priority)
        logger.info(
            "Registered hook '%s' at point '%s' (priority=%d)",
            hook.name,
            hook.point,
            hook.priority,
        )

        if metadata:
            self._plugins[hook.name] = metadata

    def unregister_hook(self, name: str) -> bool:
        """Unregister a hook by name.

        Args:
            name: Hook name to remove.

        Returns:
            True if removed, False if not found.
        """
        for point, hooks in self._hooks.items():
            for i, hook in enumerate(hooks):
                if hook.name == name:
                    self._hooks[point].pop(i)
                    return True
        return False

    def get_hooks(self, point: str, stage_name: Optional[str] = None) -> List[Hook]:
        """Get hooks for a lifecycle point, optionally filtered by stage.

        Args:
            point: Lifecycle point name.
            stage_name: Optional stage name filter.

        Returns:
            List of matching Hook objects.
        """
        hooks = self._hooks.get(point, [])
        if stage_name:
            return [
                h for h in hooks
                if h.stage_filter is None or h.stage_filter == stage_name
            ]
        return hooks

    def run_hooks(
        self,
        point: str,
        stage_name: Optional[str] = None,
        **context: Any,
    ) -> None:
        """Execute hooks for a lifecycle point.

        Args:
            point: Lifecycle point name.
            stage_name: Optional stage name filter.
            **context: Context data passed to each hook handler.
        """
        hooks = self.get_hooks(point, stage_name)
        for hook in hooks:
            try:
                hook.handler(**context)
                logger.debug("Hook '%s' executed at '%s'", hook.name, point)
            except Exception as e:
                logger.error(
                    "Hook '%s' failed at '%s': %s",
                    hook.name,
                    point,
                    e,
                )

    # ── Provider Registration ──

    def register_provider(
        self,
        provider_type: str,
        provider_name: str,
        provider_class: Type,
        metadata: Optional[PluginMetadata] = None,
    ) -> None:
        """Register a provider implementation.

        Args:
            provider_type: Provider type (research, image_gen, etc.).
            provider_name: Provider name (openai, tavily, etc.).
            provider_class: Provider implementation class.
            metadata: Optional plugin metadata.
        """
        if provider_type not in self._providers:
            self._providers[provider_type] = {}

        self._providers[provider_type][provider_name] = provider_class
        logger.info(
            "Registered provider '%s' for type '%s'",
            provider_name,
            provider_type,
        )

        if metadata:
            self._plugins[provider_name] = metadata

    def get_provider(
        self,
        provider_type: str,
        provider_name: str,
    ) -> Optional[Type]:
        """Get a registered provider class.

        Args:
            provider_type: Provider type.
            provider_name: Provider name.

        Returns:
            Provider class, or None if not found.
        """
        providers = self._providers.get(provider_type, {})
        return providers.get(provider_name)

    def list_providers(self, provider_type: Optional[str] = None) -> Dict[str, List[str]]:
        """List all registered providers.

        Args:
            provider_type: Optional filter by type.

        Returns:
            Dict of provider_type -> list of provider names.
        """
        if provider_type:
            return {provider_type: list(self._providers.get(provider_type, {}).keys())}
        return {
            ptype: list(providers.keys())
            for ptype, providers in self._providers.items()
        }

    # ── Plugin Discovery ──

    def discover_plugins(self, plugin_dirs: Optional[List[str]] = None) -> int:
        """Auto-discover plugins from module paths.

        Scans for modules with 'plugin' in their name and
        looks for plugin registration calls.

        Args:
            plugin_dirs: Additional directories to scan.

        Returns:
            Number of plugins discovered.
        """
        discovered = 0

        # Scan the content_automata package itself
        import content_automata
        package = content_automata
        package_path = Path(package.__file__).parent

        # Also scan custom plugin directories
        scan_paths = [str(package_path)]
        if plugin_dirs:
            scan_paths.extend(plugin_dirs)

        for path in scan_paths:
            try:
                pkg_path = Path(path)
                if pkg_path.is_dir():
                    for item in pkg_path.iterdir():
                        if item.suffix == ".py" and "plugin" in item.stem.lower():
                            mod_name = f"content_automata.{item.stem}"
                            try:
                                importlib.import_module(mod_name)
                                discovered += 1
                                logger.info("Discovered plugin module: %s", mod_name)
                            except (ImportError, Exception) as e:
                                logger.debug("Failed to load plugin %s: %s", mod_name, e)
            except Exception as e:
                logger.warning("Error scanning plugins in %s: %s", path, e)

        return discovered

    def enable_plugin(self, name: str) -> bool:
        """Enable a registered plugin.

        Args:
            name: Plugin name.

        Returns:
            True if enabled, False if not found.
        """
        plugin = self._plugins.get(name)
        if plugin:
            plugin.enabled = True
            logger.info("Plugin enabled: %s", name)
            return True
        return False

    def disable_plugin(self, name: str) -> bool:
        """Disable a registered plugin.

        Args:
            name: Plugin name.

        Returns:
            True if disabled, False if not found.
        """
        plugin = self._plugins.get(name)
        if plugin:
            plugin.enabled = False
            logger.info("Plugin disabled: %s", name)
            return True
        return False

    def list_plugins(self, plugin_type: Optional[str] = None) -> Dict[str, PluginMetadata]:
        """List all registered plugins.

        Args:
            plugin_type: Optional filter by plugin type.

        Returns:
            Dict of plugin name -> PluginMetadata.
        """
        if plugin_type:
            return {
                name: meta
                for name, meta in self._plugins.items()
                if meta.plugin_type == plugin_type
            }
        return dict(self._plugins)


# Global plugin registry instance
_default_registry = PluginRegistry()


def get_registry() -> PluginRegistry:
    """Get the global plugin registry instance.

    Returns:
        The shared PluginRegistry instance.
    """
    return _default_registry
