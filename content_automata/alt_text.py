"""Image alt-text generation from content analysis."""

from __future__ import annotations

import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class AltTextGenerator:
    """Generates descriptive alt text for images based on content context.

    Produces accessible, SEO-friendly alt text descriptions that
    summarize the visual content in the context of the surrounding text.
    """

    def __init__(self, config: Optional[Dict] = None):
        self._config = config or {}
        self._max_length = self._config.get("alt_text_max_length", 125)

    def generate(
        self,
        topic: str,
        headline: str,
        content_snippet: str | None = None,
        image_prompt: str | None = None,
    ) -> str:
        """Generate alt text for an image.

        Args:
            topic: The content topic.
            headline: The content headline/title.
            content_snippet: Optional nearby text for context.
            image_prompt: Optional image generation prompt for reference.

        Returns:
            A descriptive alt text string.
        """
        parts = []

        if image_prompt:
            # Extract key descriptive elements from prompt
            cleaned = self._clean_prompt(image_prompt)
            if cleaned:
                parts.append(cleaned[:80])

        if not parts and headline:
            parts.append(f"Illustration of {headline.lower()}")

        if content_snippet:
            context = self._extract_context(content_snippet)
            if context:
                parts.append(context)

        if not parts:
            parts.append(f"Visual representation of {topic}")

        alt_text = " — ".join(parts)
        return alt_text[:self._max_length]

    def generate_bulk(
        self,
        topic: str,
        headline: str,
        prompts: List[str],
        content: str | None = None,
    ) -> List[str]:
        """Generate alt text for multiple images.

        Args:
            topic: The content topic.
            headline: The content headline.
            prompts: List of image generation prompts.
            content: Optional full content body.

        Returns:
            List of alt text strings.
        """
        return [
            self.generate(topic, headline, content, prompt)
            for prompt in prompts
        ]

    def _clean_prompt(self, prompt: str) -> str:
        """Clean up a generation prompt for use as alt text."""
        # Remove style/size descriptors not appropriate for alt text
        noise_terms = [
            "4k", "8k", "hd", "high resolution", "professional",
            "modern design", "clean composition", "minimalist style",
            "professional color palette",
        ]
        cleaned = prompt
        for term in noise_terms:
            cleaned = cleaned.replace(term, "").replace("  ", " ")
        return cleaned.strip().strip(",")

    def _extract_context(self, content: str) -> str | None:
        """Extract relevant context from surrounding content."""
        # Get first meaningful sentence
        sentences = [s.strip() for s in content.split(".") if s.strip()]
        for sentence in sentences[:3]:
            if len(sentence) > 20 and len(sentence) < 150:
                return sentence.strip()
        return None
