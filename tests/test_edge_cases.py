"""Tests for edge cases and empty input handling."""

import pytest

from content_automata.models import ContentBrief, Draft, ResearchResult
from content_automata.stages.research import TopicResearch
from content_automata.stages.copywriter import CopyWriter
from content_automata.stages.image_gen import ImageGenerator
from content_automata.stages.scheduler import ContentScheduler


class TestEmptyResearchHandling:
    """Test that pipeline handles empty or minimal research gracefully."""

    def test_empty_research_result(self):
        """Copywriter should handle completely empty research."""
        writer = CopyWriter()
        research = ResearchResult()  # All defaults
        brief = ContentBrief(topic="Default Topic")
        draft = writer.generate(research, brief)
        assert draft.blog_post is not None
        assert draft.word_count >= 0

    def test_research_without_key_points(self):
        """Research with empty key_points should not crash."""
        writer = CopyWriter()
        research = ResearchResult(topic="Test", key_points=[])
        brief = ContentBrief(topic="Test")
        draft = writer.generate(research, brief)
        assert draft.blog_post is not None

    def test_research_without_outline(self):
        """Research without outline should generate anyway."""
        writer = CopyWriter()
        research = ResearchResult(topic="Test", key_points=["Point"])
        brief = ContentBrief(topic="Test")
        draft = writer.generate(research, brief)
        assert draft.blog_post is not None

    def test_empty_draft_in_image_gen(self):
        """Image generation should handle empty draft."""
        gen = ImageGenerator()
        draft = Draft()  # Empty draft
        brief = ContentBrief(topic="Test Topic")
        result = gen.generate(draft, brief)
        assert len(result.images) > 0

    def test_empty_research_in_scheduler(self):
        """Scheduler should handle empty research result."""
        scheduler = ContentScheduler()
        from content_automata.models import FinalContent
        final = FinalContent(
            research=ResearchResult(),
            draft=Draft(blog_post="Some content"),
        )
        brief = ContentBrief(topic="Test")
        result = scheduler.schedule(final, brief)
        assert len(result.exports) > 0


class TestEmptyInputPipeline:
    """Test full pipeline with edge case inputs."""

    def test_topic_with_special_chars(self):
        """Pipeline handles special characters in topic."""
        from content_automata import Pipeline
        pipeline = Pipeline()
        result = pipeline.from_topic("C++ & Python: What's New? (2026 Edition!)")
        assert result.state.value == "complete"

    def test_very_short_topic(self):
        """Pipeline handles very short topic."""
        from content_automata import Pipeline
        pipeline = Pipeline()
        result = pipeline.from_topic("AI")
        assert result.state.value == "complete"

    def test_topic_with_numbers(self):
        """Pipeline handles numeric topics."""
        from content_automata import Pipeline
        pipeline = Pipeline()
        result = pipeline.from_topic("Top 10 Ways to Improve SEO in 2026")
        assert result.state.value == "complete"


class TestEdgeCaseQuality:
    """Test quality scorer with edge cases."""

    def test_quality_with_minimal_content(self):
        from content_automata.quality import QualityScorer
        scorer = QualityScorer()
        draft = Draft(blog_post="Short content.")
        research = ResearchResult(topic="Test")
        report = scorer.score(draft, research)
        assert report.overall_score >= 0
        assert report.overall_score <= 1.0

    def test_quality_with_very_long_content(self):
        from content_automata.quality import QualityScorer
        scorer = QualityScorer()
        draft = Draft(
            blog_post="Long " * 1000 + ". ",
            headline="Test Headline",
            meta_description="Meta " * 10,
            word_count=5000,
        )
        research = ResearchResult(
            topic="Test",
            key_points=["P1", "P2", "P3", "P4", "P5"],
        )
        report = scorer.score(draft, research)
        assert report.overall_score > 0


class TestEdgeCaseSEO:
    """Test SEO analyzer with edge cases."""

    def test_seo_with_no_keywords(self):
        from content_automata.seo import SEOAnalyzer
        analyzer = SEOAnalyzer()
        draft = Draft(blog_post="Just some content", headline="A Title")
        result = analyzer.analyze(draft)
        assert result.overall >= 0

    def test_seo_with_many_keywords(self):
        from content_automata.seo import SEOAnalyzer
        analyzer = SEOAnalyzer()
        draft = Draft(
            blog_post="AI is great. AI helps. AI changes everything. AI is the future. AI everywhere.",
            headline="AI Revolution",
            meta_description="AI changes everything about AI",
        )
        result = analyzer.analyze(draft, target_keywords=["AI"])
        assert len(result.keywords) > 0
        assert result.keywords[0].count > 0
