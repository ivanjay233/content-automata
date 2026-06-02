"""Image generation stage — creates visuals from content."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from content_automata.models import ContentBrief, Draft, VisualAsset, VisualsResult

logger = logging.getLogger(__name__)


class ImageGenerator:
    """Generates matching visuals using AI image APIs.

    Supports multiple providers with configurable aspect ratios
    and style preferences.
    """

    SUPPORTED_ASPECT_RATIOS = ["1:1", "4:3", "16:9", "9:16", "3:2", "2:3"]
    SUPPORTED_PROVIDERS = ["openai", "stability"]

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self._config = config or {}
        self._provider = self._config.get("image_generation", {}).get(
            "provider", "openai"
        )
        self._default_aspect = self._config.get("image_generation", {}).get(
            "default_aspect", "16:9"
        )
        self._api_key = (
            self._config.get("api_key")
            or self._config.get("image_generation", {}).get("api_key")
            or ""
        )
        logger.info(
            f"ImageGenerator initialized: provider='{self._provider}', "
            f"aspect='{self._default_aspect}'"
        )

    def generate(
        self, draft: Draft, brief: ContentBrief
    ) -> VisualsResult:
        """Generate images matching the content draft.

        Args:
            draft: The content draft to base visuals on.
            brief: The content brief with formatting preferences.

        Returns:
            A VisualsResult containing generated image assets.
        """
        aspect = self._get_aspect_ratio(brief)
        topic = brief.topic
        headline = draft.headline or topic

        logger.info(f"Generating visuals for '{topic}' ({aspect})")

        # Create image prompts from content
        prompts = self._generate_prompts(topic, headline, draft.blog_post)

        # Generate images
        images: List[VisualAsset] = []
        for prompt in prompts:
            if self._api_key:
                asset = self._call_api(prompt, aspect)
            else:
                asset = self._simulate_image(prompt, aspect)
            images.append(asset)

        result = VisualsResult(
            images=images,
            image_urls=[img.url for img in images],
            primary_image=images[0] if images else None,
        )

        logger.info(f"Generated {len(images)} visual(s)")
        return result

    def _generate_prompts(
        self, topic: str, headline: str, blog_post: Optional[str]
    ) -> List[str]:
        """Generate image prompts from content."""
        prompts = [
            f"Professional illustration representing {topic}, "
            f"modern design style, clean composition, "
            f"suitable for a blog header, 4K quality",
            f"Abstract visual concept for {headline}, "
            f"with business and technology elements, "
            f"professional color palette, minimalist style",
        ]
        if blog_post:
            # Extract a key concept for a third image
            prompts.append(
                f"Data visualization style image related to {topic}, "
                f"showing growth and innovation, "
                f"modern infographic aesthetic, clean lines"
            )
        return prompts

    def _get_aspect_ratio(self, brief: ContentBrief) -> str:
        """Determine aspect ratio from brief or config.

        Returns:
            A valid aspect ratio string from SUPPORTED_ASPECT_RATIOS.
            Falls back to default if the requested ratio is invalid.
        """
        requested = (
            brief.custom_instructions or self._default_aspect
            if brief.custom_instructions and ":" in brief.custom_instructions
            else self._default_aspect
        )
        if requested not in self.SUPPORTED_ASPECT_RATIOS:
            logger.warning(
                f"Invalid aspect ratio '{requested}' requested, "
                f"falling back to '{self._default_aspect}'. "
                f"Valid options: {self.SUPPORTED_ASPECT_RATIOS}"
            )
            return self._default_aspect
        return requested

    def _call_api(self, prompt: str, aspect: str) -> VisualAsset:
        """Call the AI image generation API."""
        if self._provider == "stability":
            return self._call_stability(prompt, aspect)
        return self._call_openai(prompt, aspect)

    def _call_openai(self, prompt: str, aspect: str) -> VisualAsset:
        """Generate image via OpenAI DALL-E API."""
        import httpx

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        size_map = {
            "1:1": "1024x1024",
            "16:9": "1792x1024",
            "9:16": "1024x1792",
            "4:3": "1024x768",
            "3:2": "1024x683",
            "2:3": "683x1024",
        }
        size = size_map.get(aspect, "1024x1024")

        payload = {
            "model": "dall-e-3",
            "prompt": prompt,
            "n": 1,
            "size": size,
            "quality": "standard",
        }

        response = httpx.post(
            "https://api.openai.com/v1/images/generations",
            json=payload,
            headers=headers,
            timeout=60,
        )
        response.raise_for_status()
        data = response.json()

        url = data["data"][0]["url"]
        return VisualAsset(
            url=url,
            prompt=prompt,
            aspect_ratio=aspect,
            alt_text=f"AI-generated illustration: {prompt[:100]}",
            width=int(size.split("x")[0]),
            height=int(size.split("x")[1]),
        )

    def _call_stability(self, prompt: str, aspect: str) -> VisualAsset:
        """Generate image via Stability AI API."""
        import httpx

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        aspect_map = {
            "1:1": "1:1",
            "16:9": "16:9",
            "9:16": "9:16",
            "4:3": "4:3",
            "3:2": "3:2",
            "2:3": "2:3",
        }
        aspect_ratio = aspect_map.get(aspect, "16:9")

        payload = {
            "text_prompts": [{"text": prompt, "weight": 1.0}],
            "cfg_scale": 7,
            "height": 1024,
            "width": 1024,
            "samples": 1,
            "steps": 30,
            "aspect_ratio": aspect_ratio,
        }

        response = httpx.post(
            "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image",
            json=payload,
            headers=headers,
            timeout=60,
        )
        response.raise_for_status()
        data = response.json()

        url = data["artifacts"][0].get("url", "https://example.com/generated.png")
        return VisualAsset(
            url=url,
            prompt=prompt,
            aspect_ratio=aspect,
            alt_text=f"AI-generated illustration: {prompt[:100]}",
            width=1024,
            height=1024,
        )

    def _simulate_image(self, prompt: str, aspect: str) -> VisualAsset:
        """Simulate image generation for development/testing."""
        dims = {"1:1": (1024, 1024), "16:9": (1920, 1080), "9:16": (1080, 1920)}
        w, h = dims.get(aspect, (1024, 1024))

        return VisualAsset(
            url=f"https://via.placeholder.com/{w}x{h}.png?text={prompt[:50].replace(' ', '+')}",
            prompt=prompt,
            aspect_ratio=aspect,
            alt_text=f"AI-generated illustration: {prompt[:100]}",
            width=w,
            height=h,
        )
