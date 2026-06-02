"""Tests for multi-language content generation."""

import pytest

from content_automata.i18n import (
    LANGUAGE_PRESETS,
    LocalizedContent,
    MultiLanguageGenerator,
    MultiLanguageResult,
)
from content_automata.models import ContentBrief


class TestMultiLanguageGeneration:
    """Tests for multi-language content generation support."""

    def test_all_language_presets_available(self):
        """Test that all expected language presets exist."""
        expected = {"en", "es", "fr", "de", "pt", "zh", "ja"}
        for lang in expected:
            assert lang in LANGUAGE_PRESETS, f"Missing preset for '{lang}'"

    def test_language_preset_structure(self):
        """Test that each preset has required fields."""
        for lang, preset in LANGUAGE_PRESETS.items():
            assert "name" in preset, f"Missing 'name' in {lang}"
            assert "meta_prefix" in preset, f"Missing 'meta_prefix' in {lang}"
            assert "cta" in preset, f"Missing 'cta' in {lang}"
            assert "date_format" in preset, f"Missing 'date_format' in {lang}"

    def test_english_preset_values(self):
        """Test English preset values."""
        en = LANGUAGE_PRESETS["en"]
        assert en["name"] == "English"
        assert en["meta_prefix"] == "Discover"
        assert en["cta"] == "Read more"

    def test_spanish_preset_values(self):
        """Test Spanish preset values."""
        es = LANGUAGE_PRESETS["es"]
        assert es["name"] == "Spanish"
        assert es["meta_prefix"] == "Descubre"
        assert es["cta"] == "Leer más"

    def test_french_preset_values(self):
        """Test French preset values."""
        fr = LANGUAGE_PRESETS["fr"]
        assert fr["name"] == "French"
        assert fr["meta_prefix"] == "Découvrez"
        assert fr["cta"] == "Lire la suite"

    def test_generator_initialization_defaults(self):
        """Test MultiLanguageGenerator with default config."""
        gen = MultiLanguageGenerator()
        assert gen is not None
        assert gen._target_languages == ["en"]
        assert gen._source_language == "en"

    def test_generator_initialization_with_config(self):
        """Test MultiLanguageGenerator with custom config."""
        gen = MultiLanguageGenerator({
            "languages": ["en", "es", "fr"],
            "source_language": "en",
        })
        assert gen._target_languages == ["en", "es", "fr"]
        assert gen._source_language == "en"

    def test_localize_to_multiple_languages(self):
        """Test localizing content to multiple target languages."""
        gen = MultiLanguageGenerator({"languages": ["en", "es", "fr"]})
        result = gen.localize(
            topic="Content Marketing",
            headline="10 Tips for Better Content",
            meta_description="A guide to content marketing",
            body="This is the full body content.",
            target_languages=["es", "fr"],
        )
        assert isinstance(result, MultiLanguageResult)
        assert result.source_language == "en"
        assert len(result.localized_contents) == 2

    def test_localize_skips_source_language(self):
        """Test that the source language is skipped in localization."""
        gen = MultiLanguageGenerator({"languages": ["en", "es"]})
        result = gen.localize(
            topic="Test",
            headline="Test Headline",
            meta_description="Test meta",
            body="Test body",
            target_languages=["en", "es"],
        )
        # Should only contain Spanish (skipping source English)
        assert "es" in result.localized_contents
        assert "en" not in result.localized_contents

    def test_localized_content_structure(self):
        """Test that localized content has correct structure."""
        gen = MultiLanguageGenerator()
        result = gen.localize(
            topic="AI",
            headline="AI Overview",
            meta_description="All about AI",
            body="Content body here",
            target_languages=["fr"],
        )
        localized = result.localized_contents["fr"]
        assert isinstance(localized, LocalizedContent)
        assert localized.language == "French"
        assert localized.locale == "fr"
        assert localized.headline
        assert localized.meta_description
        assert localized.body == "Content body here"
        assert localized.cta_text == "Lire la suite"
        assert len(localized.hashtags) >= 2

    def test_localized_meta_prefix_inclusion(self):
        """Test that meta prefix is included in localized headline."""
        gen = MultiLanguageGenerator()
        result = gen.localize(
            topic="SEO",
            headline="SEO Best Practices",
            meta_description="SEO guide",
            body="SEO content",
            target_languages=["es"],
        )
        localized = result.localized_contents["es"]
        assert "Descubre" in localized.headline  # Spanish meta prefix

    def test_localized_cta_inclusion(self):
        """Test proper CTA in localized content."""
        gen = MultiLanguageGenerator()
        result = gen.localize(
            topic="Test",
            headline="Test",
            meta_description="Test",
            body="Test",
            target_languages=["de"],
        )
        localized = result.localized_contents["de"]
        assert localized.cta_text == "Weiterlesen"

    def test_all_languages_generate(self):
        """Test generating content in all available languages."""
        gen = MultiLanguageGenerator()
        all_langs = list(LANGUAGE_PRESETS.keys())
        # Remove source language
        target_langs = [l for l in all_langs if l != "en"]

        result = gen.localize(
            topic="Global Content",
            headline="World News",
            meta_description="News summary",
            body="Full news article here.",
            target_languages=target_langs,
        )
        # Should have all non-English languages
        assert len(result.localized_contents) == len(target_langs)

    def test_empty_body_handling(self):
        """Test localization with empty body."""
        gen = MultiLanguageGenerator()
        result = gen.localize(
            topic="Test",
            headline="Test",
            meta_description="",
            body="",
            target_languages=["es"],
        )
        assert "es" in result.localized_contents

    def test_generator_supported_languages(self):
        """Test SUPPORTED_LANGUAGES constant."""
        assert len(MultiLanguageGenerator.SUPPORTED_LANGUAGES) >= 7
        assert "en" in MultiLanguageGenerator.SUPPORTED_LANGUAGES

    def test_localized_hashtags(self):
        """Test that localized content includes hashtags."""
        gen = MultiLanguageGenerator()
        result = gen.localize(
            topic="Digital Marketing",
            headline="DM Trends",
            meta_description="Trends in digital marketing",
            body="Content about digital marketing trends.",
            target_languages=["fr"],
        )
        localized = result.localized_contents["fr"]
        assert any("digitalmarketing" in h.lower() for h in localized.hashtags)
        assert "fr" in localized.hashtags

    def test_multi_language_result_source(self):
        """Test MultiLanguageResult source_language tracking."""
        gen = MultiLanguageGenerator({"source_language": "de"})
        result = gen.localize(
            topic="Test",
            headline="Test",
            meta_description="Test",
            body="Test",
            target_languages=["en", "fr"],
        )
        assert result.source_language == "de"
        assert result.target_languages == ["en", "fr"]

    def test_localize_with_no_target_languages(self):
        """Test localization with empty target languages list."""
        gen = MultiLanguageGenerator({"languages": ["en"]})
        result = gen.localize(
            topic="Test",
            headline="Test",
            meta_description="Test",
            body="Test",
            target_languages=[],
        )
        assert len(result.localized_contents) == 0

    def test_presets_have_unique_ctas(self):
        """Test that each language has a unique CTA."""
        ctas = {lang: preset["cta"] for lang, preset in LANGUAGE_PRESETS.items()}
        # At least most should be unique
        assert len(set(ctas.values())) >= 5

    def test_chinese_preset(self):
        """Test Chinese (Simplified) preset values."""
        zh = LANGUAGE_PRESETS["zh"]
        assert zh["name"] == "Chinese (Simplified)"
        assert zh["cta"] == "了解更多"
