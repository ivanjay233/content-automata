"""Provider pattern — abstract API clients with common interface."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class ResearchProvider(ABC):
    """Abstract interface for research API providers."""

    @abstractmethod
    def search(self, query: str, max_results: int = 5) -> Tuple[List[str], Dict[str, Any]]:
        """Execute a search query.

        Args:
            query: Search query string.
            max_results: Maximum results to return.

        Returns:
            Tuple of (source_urls, raw_data).
        """
        ...


class ContentProvider(ABC):
    """Abstract interface for content generation providers."""

    @abstractmethod
    def generate_text(
        self, prompt: str, max_tokens: int = 1000, temperature: float = 0.7
    ) -> str:
        """Generate text from a prompt.

        Args:
            prompt: Text prompt.
            max_tokens: Maximum tokens in response.
            temperature: Creativity temperature (0.0-1.0).

        Returns:
            Generated text.
        """
        ...

    @abstractmethod
    def generate_image(
        self, prompt: str, aspect_ratio: str = "16:9", style: str = "standard"
    ) -> Dict[str, Any]:
        """Generate an image from a prompt.

        Args:
            prompt: Image description prompt.
            aspect_ratio: Target aspect ratio.
            style: Image style.

        Returns:
            Dict with url, width, height keys.
        """
        ...


class TavilyProvider(ResearchProvider):
    """Tavily search API provider."""

    def __init__(self, api_key: str = "", config: Optional[Dict] = None):
        self._api_key = api_key
        self._config = config or {}

    def search(self, query: str, max_results: int = 5) -> Tuple[List[str], Dict[str, Any]]:
        if not self._api_key:
            return [], {"error": "No API key configured"}
        import httpx
        response = httpx.post(
            "https://api.tavily.com/search",
            json={"query": query, "max_results": max_results, "include_answer": True},
            headers={"Authorization": f"Bearer {self._api_key}"},
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        sources = [r.get("url", "") for r in data.get("results", [])]
        return sources, data


class ExaProvider(ResearchProvider):
    """Exa search API provider."""

    def __init__(self, api_key: str = "", config: Optional[Dict] = None):
        self._api_key = api_key
        self._config = config or {}

    def search(self, query: str, max_results: int = 5) -> Tuple[List[str], Dict[str, Any]]:
        if not self._api_key:
            return [], {"error": "No API key configured"}
        import httpx
        response = httpx.post(
            "https://api.exa.ai/search",
            json={"query": query, "num_results": max_results},
            headers={"x-api-key": self._api_key},
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        sources = [r.get("url", "") for r in data.get("results", [])]
        return sources, data


class OpenAIProvider(ContentProvider):
    """OpenAI API provider for text and image generation."""

    def __init__(self, api_key: str = "", config: Optional[Dict] = None):
        self._api_key = api_key
        self._config = config or {}

    def generate_text(
        self, prompt: str, max_tokens: int = 1000, temperature: float = 0.7
    ) -> str:
        if not self._api_key:
            return f"[Simulated response for: {prompt[:80]}...]"
        import httpx
        response = httpx.post(
            "https://api.openai.com/v1/chat/completions",
            json={
                "model": "gpt-4",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": temperature,
            },
            headers={"Authorization": f"Bearer {self._api_key}"},
            timeout=60,
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]

    def generate_image(
        self, prompt: str, aspect_ratio: str = "16:9", style: str = "standard"
    ) -> Dict[str, Any]:
        size_map = {"1:1": "1024x1024", "16:9": "1792x1024", "9:16": "1024x1792"}
        size = size_map.get(aspect_ratio, "1024x1024")
        if not self._api_key:
            w, h = size.split("x")
            return {"url": f"https://via.placeholder.com/{size}.png", "width": int(w), "height": int(h)}
        import httpx
        response = httpx.post(
            "https://api.openai.com/v1/images/generations",
            json={"model": "dall-e-3", "prompt": prompt, "n": 1, "size": size, "quality": "standard"},
            headers={"Authorization": f"Bearer {self._api_key}"},
            timeout=60,
        )
        response.raise_for_status()
        data = response.json()["data"][0]
        w, h = size.split("x")
        return {"url": data["url"], "width": int(w), "height": int(h)}


class ProviderFactory:
    """Factory for creating API providers from configuration."""

    _research_providers: Dict[str, type[ResearchProvider]] = {
        "tavily": TavilyProvider,
        "exa": ExaProvider,
    }

    _content_providers: Dict[str, type[ContentProvider]] = {
        "openai": OpenAIProvider,
    }

    @classmethod
    def create_research(cls, provider_name: str, api_key: str = "", config: Optional[Dict] = None) -> ResearchProvider:
        """Create a research provider by name.

        Args:
            provider_name: Provider identifier.
            api_key: API key.
            config: Optional configuration.

        Returns:
            ResearchProvider instance.

        Raises:
            ValueError: If provider is unknown.
        """
        provider_cls = cls._research_providers.get(provider_name.lower())
        if not provider_cls:
            raise ValueError(f"Unknown research provider: {provider_name}. Available: {list(cls._research_providers.keys())}")
        return provider_cls(api_key=api_key, config=config)

    @classmethod
    def create_content(cls, provider_name: str, api_key: str = "", config: Optional[Dict] = None) -> ContentProvider:
        """Create a content provider by name.

        Args:
            provider_name: Provider identifier.
            api_key: API key.
            config: Optional configuration.

        Returns:
            ContentProvider instance.

        Raises:
            ValueError: If provider is unknown.
        """
        provider_cls = cls._content_providers.get(provider_name.lower())
        if not provider_cls:
            raise ValueError(f"Unknown content provider: {provider_name}. Available: {list(cls._content_providers.keys())}")
        return provider_cls(api_key=api_key, config=config)

    @classmethod
    def register_research(cls, name: str, provider_cls: type[ResearchProvider]) -> None:
        """Register a custom research provider.

        Args:
            name: Provider identifier.
            provider_cls: Provider class.
        """
        cls._research_providers[name.lower()] = provider_cls

    @classmethod
    def register_content(cls, name: str, provider_cls: type[ContentProvider]) -> None:
        """Register a custom content provider.

        Args:
            name: Provider identifier.
            provider_cls: Provider class.
        """
        cls._content_providers[name.lower()] = provider_cls
