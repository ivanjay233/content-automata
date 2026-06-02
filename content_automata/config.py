"""Configuration management — main module, delegates to submodules.

Provides backward-compatible imports from the old monolithic
config module while delegating to focused submodules:
- config_loader.py: Loading from file/env vars, merging, validation
- config_models.py: Data classes for configuration
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, Optional

from content_automata.config_loader import (
    load_config_from_env,
    load_config_from_file,
    merge_configs,
    validate_config,
)
from content_automata.config_models import (
    APIProviderConfig,
    PipelineConfig,
    StageConfig,
)

logger = logging.getLogger(__name__)


def load_config(
    path: Optional[str] = None,
    env_prefix: str = "CAUTO_",
    overrides: Optional[Dict[str, Any]] = None,
) -> PipelineConfig:
    """Load and merge configuration from all sources.

    Priority (highest wins): overrides > env vars > file > defaults

    Args:
        path: Optional path to config file.
        env_prefix: Environment variable prefix for env loading.
        overrides: Optional dict of explicit overrides.

    Returns:
        Merged PipelineConfig.
    """
    # Start from file if provided
    file_config: Dict[str, Any] = {}
    if path:
        path_obj = Path(path)
        if path_obj.exists():
            file_config = load_config_from_file(path_obj)
            logger.info("Loaded config from %s", path_obj)

    # Load env vars
    env_config = load_config_from_env(env_prefix)

    # Merge: file < env < overrides
    merged = merge_configs(file_config, env_config)
    if overrides:
        merged = merge_configs(merged, overrides)

    return PipelineConfig.from_dict(merged)


__all__ = [
    "load_config",
    "PipelineConfig",
    "APIProviderConfig",
    "StageConfig",
    "load_config_from_file",
    "load_config_from_env",
    "merge_configs",
    "validate_config",
]
