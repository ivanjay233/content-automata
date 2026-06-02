"""Configuration management — submodule for loading sources.

Handles config loading from multiple sources with merge
semantics: defaults < file < env vars < explicit dict.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from content_automata.exceptions import ConfigurationError


def load_config_from_file(path: str | Path) -> Dict[str, Any]:
    """Load configuration from a YAML or JSON file.

    Args:
        path: Path to config file (.yaml, .yml, or .json).

    Returns:
        Parsed configuration dictionary.

    Raises:
        ConfigurationError: If the file cannot be loaded.
    """
    path = Path(path)
    if not path.exists():
        raise ConfigurationError(f"Config file not found: {path}", field="path")

    try:
        content = path.read_text()
        if path.suffix in (".yaml", ".yml"):
            data = yaml.safe_load(content) or {}
        elif path.suffix == ".json":
            data = json.loads(content)
        else:
            raise ConfigurationError(
                f"Unsupported config format: {path.suffix}",
                field="format",
            )
    except (yaml.YAMLError, json.JSONDecodeError) as e:
        raise ConfigurationError(f"Failed to parse config: {e}", field="syntax") from e

    return data


def load_config_from_env(prefix: str = "CAUTO_") -> Dict[str, Any]:
    """Load configuration from environment variables.

    Converts CAUTO_API_KEY -> api_key, CAUTO_RESEARCH_PROVIDER -> research.provider, etc.

    Args:
        prefix: Environment variable prefix.

    Returns:
        Configuration dictionary from environment.
    """
    config: Dict[str, Any] = {}
    nested: Dict[str, Any] = {}

    for key, value in os.environ.items():
        if not key.startswith(prefix):
            continue

        # Strip prefix and lowercase
        config_key = key[len(prefix):].lower()

        # Parse YAML-like values (numbers, booleans)
        parsed_value: Any = value
        if value.lower() in ("true", "yes", "1"):
            parsed_value = True
        elif value.lower() in ("false", "no", "0"):
            parsed_value = False
        else:
            try:
                if "." in value:
                    parsed_value = float(value)
                else:
                    parsed_value = int(value)
            except (ValueError, TypeError):
                parsed_value = value

        # Handle nested keys with underscore
        parts = config_key.split("_", 1)
        if len(parts) == 2:
            section, sub_key = parts
            if section not in nested:
                nested[section] = {}
            nested[section][sub_key] = parsed_value
        else:
            config[config_key] = parsed_value

    # Merge nested config
    config.update(nested)
    return config


def merge_configs(*configs: Dict[str, Any]) -> Dict[str, Any]:
    """Deep-merge multiple configuration dictionaries.

    Later configs override earlier ones. Nested dicts are merged recursively.

    Args:
        *configs: Configuration dictionaries to merge.

    Returns:
        Merged configuration dictionary.
    """
    merged: Dict[str, Any] = {}
    for cfg in configs:
        _deep_merge(merged, cfg)
    return merged


def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> None:
    """Recursively merge override into base.

    Args:
        base: Base dictionary (modified in place).
        override: Dictionary to merge in.
    """
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value


def validate_config(config: Dict[str, Any]) -> list[str]:
    """Validate configuration and return list of errors.

    Args:
        config: Configuration dictionary to validate.

    Returns:
        List of error messages. Empty if valid.
    """
    errors: list[str] = []

    # Check for required fields
    research_provider = config.get("research", {}).get("provider", "")
    if research_provider and research_provider not in ("tavily", "exa", ""):
        errors.append(f"Unknown research provider: '{research_provider}'")

    image_provider = config.get("image_generation", {}).get("provider", "")
    if image_provider and image_provider not in ("openai", "stability", ""):
        errors.append(f"Unknown image provider: '{image_provider}'")

    # Quality threshold
    qt = config.get("quality_threshold", 0.6)
    if not isinstance(qt, (int, float)) or qt < 0 or qt > 1:
        errors.append(f"quality_threshold must be between 0 and 1, got {qt}")

    # Output directory
    output_dir = config.get("output_dir", "./output")
    if not isinstance(output_dir, str):
        errors.append("output_dir must be a string path")

    return errors
