"""Multi-language content generation support.

Allows generating content in multiple languages with proper
localization of headlines, metadata, and formatting.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# Language configuration presets
LANGUAGE_PRESETS: Dict[str, Dict[str, str]] = {
    "en": {
        "name": "English",
        "meta_prefix": "Discover",
        "cta": "Read more",
        "date_format": "%B %d, %Y",
    },
    "es": {
        "name": "Spanish",
        "meta_prefix": "Descubre",
        "cta": "Leer más",
        "date_format": "%d de %B de %Y",
    },
    "fr": {
        "name": "French",
        "meta_prefix": "Découvrez",
        "cta": "Lire la suite",
        "date_format": "%d %B %Y",
    },
    "de": {
        "name": "German",
        "meta_prefix": "Entdecken Sie",
        "cta": "Weiterlesen",
        "date_format": "%d. %B %Y",
    },
    "pt": {
        "name": "Portuguese",
        "meta_prefix": "Descubra",
        "cta": "Leia mais",
        "date_format": "%d de %B de %Y",
    },
    "zh": {
        "name": "Chinese (Simplified)",
        "meta_prefix": "发现",
        "cta": "了解更多",
        "date_format": "%Y年%m月%d日",
    },
    "ja": {
        "name": "Japanese",
        "meta_prefix": "発見",
        "cta": "続きを読む",
        "date_format": "%Y年%m月%d日",
    },
}


@dataclass
class LocalizedContent:
    """Content localized to a specific language."""

    language: str
    locale: str
    headline: str
    meta_description: str
    body: str
    cta_text: str
    hashtags: List[str] = field(default_factory=list)


@dataclass
class MultiLanguageResult:
    """Container for multi-language content outputs."""

    source_language: str
    target_languages: List[str]
    localized_contents: Dict[str, LocalizedContent] = field(default_factory=dict)


class MultiLanguageGenerator:
    """Generates content in multiple languages from a source draft."""

    SUPPORTED_LANGUAGES = list(LANGUAGE_PRESETS.keys())

    def __init__(self, config: Optional[Dict] = None):
        self._config = config or {}
        self._target_languages = self._config.get("languages", []) or ["en"]
        self._source_language = self._config.get("source_language", "en")

    def localize(
        self,
        topic: str,
        headline: str,
        meta_description: str,
        body: str,
        target_languages: Optional[List[str]] = None,
    ) -> MultiLanguageResult:
        """Generate localized versions of content.

        Args:
            topic: The content topic.
            headline: The source headline.
            meta_description: The source meta description.
            body: The full content body.
            target_languages: List of target language codes.

        Returns:
            MultiLanguageResult with per-language content.
        """
        languages = target_languages or self._target_languages
        result = MultiLanguageResult(
            source_language=self._source_language,
            target_languages=languages,
        )

        for lang in languages:
            if lang == self._source_language:
                continue
            preset = LANGUAGE_PRESETS.get(lang, LANGUAGE_PRESETS["en"])
            localized = self._localize_single(
                topic=topic,
                headline=headline,
                meta_description=meta_description,
                body=body,
                language=lang,
                preset=preset,
            )
            result.localized_contents[lang] = localized

        return result

    def _localize_single(
        self,
        topic: str,
        headline: str,
        meta_description: str,
        body: str,
        language: str,
        preset: Dict[str, str],
    ) -> LocalizedContent:
        """Create a localized content variant for a single language.

        In production this would call a translation API. For development,
        it generates localized metadata around the source content.
        """
        localized_headline = f"{preset['meta_prefix']}: {headline}"
        localized_meta = (
            f"{preset['meta_prefix']} {topic}. "
            f"{preset['cta']} — {meta_description}"
        )
        hashtags = [f"#{topic.lower().replace(' ', '')}", f"#{language}"]

        return LocalizedContent(
            language=LANGUAGE_PRESETS.get(language, {}).get("name", language),
            locale=language,
            headline=localized_headline,
            meta_description=localized_meta,
            body=body,  # In production, body would be translated
            cta_text=preset["cta"],
            hashtags=hashtags,
        )
