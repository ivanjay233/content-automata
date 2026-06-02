"""Configuration models — data classes for pipeline configuration.

Split from config.py for better organization.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from content_automata.config_loader import merge_configs, validate_config


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
    errors: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate config after initialization."""
        raw = self.to_dict()
        self.errors = validate_config(raw)

    @property
    def is_valid(self) -> bool:
        """Check if configuration is valid.

        Returns:
            True if no validation errors.
        """
        return len(self.errors) == 0

    @classmethod
    def from_file(cls, path: str | Any) -> "PipelineConfig":
        """Load configuration from a file.

        Args:
            path: Path to config file (.yaml, .yml, .json).

        Returns:
            Parsed PipelineConfig.
        """
        from content_automata.config_loader import load_config_from_file
        raw = load_config_from_file(str(path))
        return cls.from_dict(raw)

    @classmethod
    def from_env(cls, prefix: str = "CAUTO_") -> "PipelineConfig":
        """Load configuration from environment variables.

        Args:
            prefix: Environment variable prefix.

        Returns:
            PipelineConfig from environment.
        """
        from content_automata.config_loader import load_config_from_env
        raw = load_config_from_env(prefix)
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
        stage_mappings = [
            ("research", raw.get("research", {})),
            ("copywriting", raw.get("copywriting", {})),
            ("image_gen", raw.get("image_generation", {})),
            ("scheduling", raw.get("scheduling", {})),
        ]

        for attr, cfg in stage_mappings:
            if isinstance(cfg, dict):
                setattr(config, attr, StageConfig(
                    enabled=cfg.get("enabled", True),
                    provider=cfg.get("provider", getattr(config, attr).provider),
                    options=cfg,
                ))

        config.__post_init__()
        return config

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to a dictionary.

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
