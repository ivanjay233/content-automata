"""Configuration management with dependency injection support."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import yaml

logger = logging.getLogger(__name__)


@dataclass
class APIProviderConfig:
    """Configuration for a single API provider."""

    name: str
    api_key: str = ""
    base_url: str = ""
    timeout: int = 30
    max_retries: int = 3
    options: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StageConfig:
    """Configuration for a pipeline stage."""

    enabled: bool = True
    provider: str = ""
    options: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PipelineConfig:
    """Complete pipeline configuration with all stage settings."""

    api_key: str = ""
    api_providers: Dict[str, APIProviderConfig] = field(default_factory=dict)

    research: StageConfig = field(default_factory=lambda: StageConfig(provider="tavily"))
    copywriting: StageConfig = field(default_factory=lambda: StageConfig(provider="openai"))
    image_gen: StageConfig = field(default_factory=lambda: StageConfig(provider="openai"))
    scheduling: StageConfig = field(default_factory=lambda: StageConfig(provider="local"))

    languages: List[str] = field(default_factory=lambda: ["en"])
    quality_threshold: float = 0.6
    cache_enabled: bool = True
    dry_run: bool = False
    output_dir: str = "./output"
    verbose: bool = False

    @classmethod
    def from_file(cls, path: str | Path) -> "PipelineConfig":
        """Load configuration from a YAML or JSON file.

        Args:
            path: Path to config file (.yaml, .yml, or .json).

        Returns:
            Parsed PipelineConfig.
        """
        path = Path(path)
        if not path.exists():
            logger.warning(f"Config file not found: {path}")
            return cls()

        raw: Dict[str, Any] = {}
        try:
            content = path.read_text()
            if path.suffix in (".yaml", ".yml"):
                raw = yaml.safe_load(content) or {}
            elif path.suffix == ".json":
                raw = json.loads(content)
            else:
                raise ValueError(f"Unsupported config format: {path.suffix}")
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return cls()

        return cls.from_dict(raw)

    @classmethod
    def from_dict(cls, raw: Dict[str, Any]) -> "PipelineConfig":
        """Create config from a dictionary.

        Args:
            raw: Raw configuration dictionary.

        Returns:
            Parsed PipelineConfig.
        """
        config = cls()

        config.api_key = raw.get("api_key", config.api_key)
        config.languages = raw.get("languages", config.languages)
        config.quality_threshold = raw.get("quality_threshold", config.quality_threshold)
        config.cache_enabled = raw.get("cache", {}).get("enabled", config.cache_enabled)
        config.dry_run = raw.get("dry_run", config.dry_run)
        config.output_dir = raw.get("output_dir", config.output_dir)
        config.verbose = raw.get("verbose", config.verbose)

        # API providers
        providers = raw.get("api_providers", {})
        for name, provider_cfg in providers.items():
            if isinstance(provider_cfg, dict):
                config.api_providers[name] = APIProviderConfig(
                    name=name,
                    api_key=provider_cfg.get("api_key", ""),
                    base_url=provider_cfg.get("base_url", ""),
                    timeout=provider_cfg.get("timeout", 30),
                    max_retries=provider_cfg.get("max_retries", 3),
                    options=provider_cfg.get("options", {}),
                )

        # Stage configs
        research_cfg = raw.get("research", {})
        config.research = StageConfig(
            enabled=research_cfg.get("enabled", True),
            provider=research_cfg.get("provider", "tavily"),
            options=research_cfg,
        )

        copy_cfg = raw.get("copywriting", {})
        config.copywriting = StageConfig(
            enabled=copy_cfg.get("enabled", True),
            provider=copy_cfg.get("provider", "openai"),
            options=copy_cfg,
        )

        img_cfg = raw.get("image_generation", {})
        config.image_gen = StageConfig(
            enabled=img_cfg.get("enabled", True),
            provider=img_cfg.get("provider", "openai"),
            options=img_cfg,
        )

        sched_cfg = raw.get("scheduling", {})
        config.scheduling = StageConfig(
            enabled=sched_cfg.get("enabled", True),
            provider=sched_cfg.get("provider", "local"),
            options=sched_cfg,
        )

        return config

    def to_dict(self) -> Dict[str, Any]:
        """Convert config back to a dictionary.

        Returns:
            Dictionary representation.
        """
        return {
            "api_key": self.api_key,
            "languages": self.languages,
            "quality_threshold": self.quality_threshold,
            "cache_enabled": self.cache_enabled,
            "dry_run": self.dry_run,
            "output_dir": self.output_dir,
            "verbose": self.verbose,
            "research": {
                "enabled": self.research.enabled,
                "provider": self.research.provider,
                **self.research.options,
            },
            "copywriting": {
                "enabled": self.copywriting.enabled,
                "provider": self.copywriting.provider,
                **self.copywriting.options,
            },
            "image_generation": {
                "enabled": self.image_gen.enabled,
                "provider": self.image_gen.provider,
                **self.image_gen.options,
            },
            "scheduling": {
                "enabled": self.scheduling.enabled,
                "provider": self.scheduling.provider,
                **self.scheduling.options,
            },
        }
