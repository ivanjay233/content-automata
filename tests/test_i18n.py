"""Tests for multi-language (i18n) support."""

import pytest

from content_automata.i18n import (
    MultiLanguageGenerator,
    MultiLanguageResult,
    LocalizedContent,
    LANGUAGE_PRESETS,
)


class TestLanguagePresets:
    """Test language configuration presets."""

    def test_english_preset(self):
        assert "en" in LANGUAGE_PRESETS
        assert LANGUAGE_PRESETS["en"]["name"] == "English"

    def test_multiple_languages(self):
        assert len(LANGUAGE_PRESETS) >= 7
        for lang in ["en", "es", "fr", "de", "pt", "zh", "ja"]:
            assert lang in LANGUAGE_PRESETS

    def test_all_presets_have_required_keys(self):
        required = ["name", "meta_prefix", "cta", "date_format"]
        for lang, preset in LANGUAGE_PRESETS.items():
            for key in required:
                assert key in preset, f"Missing {key} in {lang}"


class TestMultiLanguageGenerator:
    """Test MultiLanguageGenerator."""

    def test_default_init(self):
        gen = MultiLanguageGenerator()
        assert gen._target_languages == ["en"]
        assert gen._source_language == "en"

    def test_init_with_config(self):
        gen = MultiLanguageGenerator({"languages": ["en", "es", "fr"]})
        assert "es" in gen._target_languages
        assert "fr" in gen._target_languages

    def test_localize_returns_result(self):
        gen = MultiLanguageGenerator({"languages": ["en", "es"]})
        result = gen.localize(
            topic="AI Technology",
            headline="The Future of AI",
            meta_description="Discover AI trends",
            body="Content body here",
        )
        assert isinstance(result, MultiLanguageResult)

    def test_localize_skips_source_language(self):
        gen = MultiLanguageGenerator({"languages": ["en", "es", "fr"]})
        result = gen.localize(
            topic="Test",
            headline="Test Headline",
            meta_description="Test description",
            body="Test body",
        )
        assert "en" not in result.localized_contents

    def test_localize_creates_correct_languages(self):
        gen = MultiLanguageGenerator({"languages": ["en"]})
        result = gen.localize(
            topic="Test",
            headline="Test",
            meta_description="Test",
            body="Test",
            target_languages=["es", "fr"],
        )
        assert "es" in result.localized_contents
        assert "fr" in result.localized_contents

    def test_localized_content_has_cta(self):
        gen = MultiLanguageGenerator({"languages": ["en"]})
        result = gen.localize(
            topic="Test",
            headline="Test",
            meta_description="Test",
            body="Test",
            target_languages=["es"],
        )
        es_content = result.localized_contents["es"]
        assert es_content.cta_text == "Leer más"
        assert es_content.locale == "es"

    def test_localized_content_has_hashtags(self):
        gen = MultiLanguageGenerator({"languages": ["en"]})
        result = gen.localize(
            topic="Artificial Intelligence",
            headline="AI Future",
            meta_description="AI trends",
            body="Content",
            target_languages=["fr"],
        )
        fr_content = result.localized_contents["fr"]
        assert len(fr_content.hashtags) >= 2
        assert any("Intelligence" in tag or "artificial" in tag.lower() for tag in fr_content.hashtags)


class TestLocalizedContent:
    """Test LocalizedContent dataclass."""

    def test_create_localized_content(self):
        content = LocalizedContent(
            language="Spanish",
            locale="es",
            headline="Descubre: AI Future",
            meta_description="Descubre AI",
            body="Contenido",
            cta_text="Leer más",
            hashtags=["#AI", "#es"],
        )
        assert content.language == "Spanish"
        assert len(content.hashtags) == 2
