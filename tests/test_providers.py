"""Tests for provider pattern and configuration."""

import pytest

from content_automata.providers import (
    ProviderFactory,
    TavilyProvider,
    ExaProvider,
    OpenAIProvider,
    ResearchProvider,
    ContentProvider,
)
from content_automata.config import PipelineConfig, StageConfig, APIProviderConfig


class TestProviderFactory:
    """Test ProviderFactory."""

    def test_create_tavily(self):
        provider = ProviderFactory.create_research("tavily")
        assert isinstance(provider, TavilyProvider)
        assert isinstance(provider, ResearchProvider)

    def test_create_exa(self):
        provider = ProviderFactory.create_research("exa")
        assert isinstance(provider, ExaProvider)
        assert isinstance(provider, ResearchProvider)

    def test_create_openai(self):
        provider = ProviderFactory.create_content("openai")
        assert isinstance(provider, OpenAIProvider)
        assert isinstance(provider, ContentProvider)

    def test_unknown_research_provider(self):
        with pytest.raises(ValueError):
            ProviderFactory.create_research("unknown_provider")

    def test_unknown_content_provider(self):
        with pytest.raises(ValueError):
            ProviderFactory.create_content("unknown_provider")

    def test_create_with_api_key(self):
        provider = ProviderFactory.create_research("tavily", api_key="test-key")
        assert provider._api_key == "test-key"

    def test_create_with_config(self):
        provider = ProviderFactory.create_content("openai", config={"custom": "value"})
        assert provider._config == {"custom": "value"}

    def test_register_custom_research(self):
        class CustomResearch(ResearchProvider):
            def search(self, query, max_results=5):
                return [], {}

        ProviderFactory.register_research("custom", CustomResearch)
        provider = ProviderFactory.create_research("custom")
        assert isinstance(provider, CustomResearch)

    def test_register_custom_content(self):
        class CustomContent(ContentProvider):
            def generate_text(self, prompt, max_tokens=1000, temperature=0.7):
                return "generated text"
            def generate_image(self, prompt, aspect_ratio="16:9", style="standard"):
                return {"url": "https://example.com/img.png", "width": 1024, "height": 1024}

        ProviderFactory.register_content("custom_content", CustomContent)
        provider = ProviderFactory.create_content("custom_content")
        assert isinstance(provider, CustomContent)


class TestProviderInstances:
    """Test specific provider instances."""

    def test_tavily_search_no_key(self):
        provider = TavilyProvider()
        sources, data = provider.search("test query")
        assert sources == []
        assert "error" in data

    def test_exa_search_no_key(self):
        provider = ExaProvider()
        sources, data = provider.search("test query")
        assert sources == []
        assert "error" in data

    def test_openai_generate_text_no_key(self):
        provider = OpenAIProvider()
        result = provider.generate_text("test prompt")
        assert "Simulated" in result
        assert "test prompt" in result

    def test_openai_generate_image_no_key(self):
        provider = OpenAIProvider()
        result = provider.generate_image("test prompt", "16:9")
        assert "placeholder.com" in result["url"]
        assert result["width"] == 1792


class TestPipelineConfig:
    """Test PipelineConfig."""

    def test_default_config(self):
        config = PipelineConfig()
        assert config.api_key == ""
        assert config.research.provider == "tavily"
        assert config.dry_run is False
        assert config.verbose is False

    def test_from_dict(self):
        raw = {
            "api_key": "test-key",
            "research": {"provider": "exa", "max_results": 15},
            "languages": ["en", "es"],
            "dry_run": True,
        }
        config = PipelineConfig.from_dict(raw)
        assert config.api_key == "test-key"
        assert config.research.provider == "exa"
        assert "es" in config.languages
        assert config.dry_run is True

    def test_from_dict_full(self):
        raw = {
            "api_key": "key123",
            "research": {"enabled": True, "provider": "tavily", "max_results": 10},
            "copywriting": {"default_tone": "casual", "variants": ["blog"]},
            "image_generation": {"provider": "stability", "default_aspect": "1:1"},
            "scheduling": {"export_formats": ["html"]},
            "quality_threshold": 0.8,
            "cache": {"enabled": False},
            "output_dir": "/custom/output",
            "verbose": True,
            "api_providers": {
                "openai": {"api_key": "oa-key", "timeout": 60},
            },
        }
        config = PipelineConfig.from_dict(raw)
        assert config.quality_threshold == 0.8
        assert config.cache_enabled is False
        assert config.output_dir == "/custom/output"
        assert config.verbose is True
        assert "openai" in config.api_providers
        assert config.api_providers["openai"].timeout == 60

    def test_to_dict_roundtrip(self):
        original = PipelineConfig(
            api_key="test",
            research=StageConfig(enabled=True, provider="exa"),
            languages=["en", "fr"],
        )
        as_dict = original.to_dict()
        restored = PipelineConfig.from_dict(as_dict)
        assert restored.api_key == "test"
        assert restored.research.provider == "exa"
        assert "fr" in restored.languages


class TestStageConfig:
    """Test StageConfig."""

    def test_defaults(self):
        cfg = StageConfig()
        assert cfg.enabled is True
        assert cfg.provider == ""
        assert cfg.options == {}

    def test_custom(self):
        cfg = StageConfig(enabled=False, provider="custom", options={"key": "value"})
        assert cfg.enabled is False
        assert cfg.options["key"] == "value"


class TestAPIProviderConfig:
    """Test APIProviderConfig."""

    def test_defaults(self):
        cfg = APIProviderConfig(name="test")
        assert cfg.api_key == ""
        assert cfg.base_url == ""
        assert cfg.timeout == 30
        assert cfg.max_retries == 3

    def test_custom(self):
        cfg = APIProviderConfig(
            name="openai",
            api_key="sk-xxx",
            base_url="https://custom.openai.com",
            timeout=120,
            max_retries=5,
            options={"model": "gpt-4"},
        )
        assert cfg.api_key == "sk-xxx"
        assert cfg.options["model"] == "gpt-4"
