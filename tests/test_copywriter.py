"""Tests for the copywriting stage."""

import pytest

from content_automata.models import ContentBrief, Draft, ResearchResult
from content_automata.stages.copywriter import CopyWriter


class TestCopyWriterInit:
    """Test CopyWriter initialization."""

    def test_default_init(self):
        writer = CopyWriter()
        assert writer._default_tone == "professional"
        assert "blog" in writer._variants
        assert "social" in writer._variants


class TestCopyWriterGeneration:
    """Test content generation."""

    @pytest.fixture
    def research(self):
        return ResearchResult(
            topic="Digital Marketing",
            key_points=["SEO is essential", "Content is king", "Social media drives traffic"],
            outline="# Outline\n## Introduction\n## Body\n## Conclusion",
            summary="Digital marketing is evolving rapidly.",
        )

    def test_generate_blog_post(self, research):
        writer = CopyWriter()
        brief = ContentBrief(topic="Digital Marketing")
        draft = writer.generate(research, brief)
        assert isinstance(draft, Draft)
        assert draft.blog_post is not None
        assert "Digital Marketing" in draft.blog_post

    def test_generate_social_copy(self, research):
        writer = CopyWriter()
        brief = ContentBrief(topic="Digital Marketing")
        draft = writer.generate(research, brief)
        assert draft.social_copy is not None

    def test_generate_ad_copy(self, research):
        writer = CopyWriter()
        brief = ContentBrief(topic="Digital Marketing")
        draft = writer.generate(research, brief)
        assert draft.ad_copy is not None

    def test_generate_headline(self, research):
        writer = CopyWriter()
        brief = ContentBrief(topic="Digital Marketing")
        draft = writer.generate(research, brief)
        assert draft.headline is not None
        assert "Digital Marketing" in draft.headline or "Ultimate Guide" in draft.headline

    def test_word_count_calculated(self, research):
        writer = CopyWriter()
        brief = ContentBrief(topic="Digital Marketing")
        draft = writer.generate(research, brief)
        assert draft.word_count > 0


class TestCopyWriterTones:
    """Test tone handling."""

    def test_professional_tone(self):
        writer = CopyWriter()
        research = ResearchResult(topic="Business Strategy", key_points=["Growth"])
        brief = ContentBrief(topic="Business Strategy", tone="professional")
        draft = writer.generate(research, brief)
        assert draft.tone == "professional"

    def test_casual_tone(self):
        writer = CopyWriter()
        research = ResearchResult(topic="Remote Work", key_points=["Flexibility"])
        brief = ContentBrief(topic="Remote Work", tone="casual")
        draft = writer.generate(research, brief)
        assert draft.tone == "casual"

    def test_unsupported_tone_fallback(self):
        writer = CopyWriter()
        research = ResearchResult(topic="Test", key_points=["Point"])
        brief = ContentBrief(topic="Test", tone="nonexistent")
        draft = writer.generate(research, brief)
        assert draft.tone == "professional"

    def test_tone_greeting_variations(self):
        writer = CopyWriter()
        assert "Welcome" in writer._tone_greeting("professional")
        assert "Hey" in writer._tone_greeting("casual")
        assert "Imagine" in writer._tone_greeting("persuasive")
        assert "Buckle" in writer._tone_greeting("humorous")
        assert "Listen" in writer._tone_greeting("authoritative")

    def test_tone_closing_variations(self):
        writer = CopyWriter()
        assert "hope" in writer._tone_closing("professional").lower()
        assert "hope this helps" in writer._tone_closing("casual").lower()
        assert "don" in writer._tone_closing("persuasive").lower()
        assert "tea" in writer._tone_closing("humorous").lower()
        assert "your move" in writer._tone_closing("authoritative").lower()


class TestCopyWriterEdgeCases:
    """Test edge cases."""

    def test_empty_key_points(self):
        writer = CopyWriter()
        research = ResearchResult(topic="Test", key_points=[])
        brief = ContentBrief(topic="Test")
        draft = writer.generate(research, brief)
        assert draft.blog_post is not None

    def test_empty_topic(self):
        writer = CopyWriter()
        research = ResearchResult(topic="", key_points=["Point"])
        brief = ContentBrief(topic="")
        draft = writer.generate(research, brief)
        assert draft.blog_post is not None

    def test_meta_description_generated(self):
        writer = CopyWriter()
        research = ResearchResult(topic="SEO Tips", key_points=["Keywords", "Links"])
        brief = ContentBrief(topic="SEO Tips")
        draft = writer.generate(research, brief)
        assert draft.meta_description is not None
        assert "SEO Tips" in draft.meta_description

    def test_multiple_variants_context(self):
        """Verify different variants have different content."""
        writer = CopyWriter()
        research = ResearchResult(topic="Content Marketing", key_points=["Strategy", "Execution"])
        brief = ContentBrief(topic="Content Marketing")
        draft = writer.generate(research, brief)
        # Blog post and social copy should be different
        assert draft.blog_post != draft.social_copy
