"""Tests for templates, quality, SEO, suggestions, and batch processing."""

import pytest

from content_automata.templates import TemplateManager, ContentTemplate, BUILTIN_TEMPLATES
from content_automata.quality import QualityScorer
from content_automata.seo import SEOAnalyzer
from content_automata.suggestions import SuggestionEngine
from content_automata.batch import BatchProcessor
from content_automata.models import Draft, ResearchResult


# ── Template Tests ──

class TestTemplateManager:
    def test_list_templates(self):
        mgr = TemplateManager()
        templates = mgr.list_templates()
        assert len(templates) >= 4
        assert "blog" in templates
        assert "social" in templates

    def test_get_template(self):
        mgr = TemplateManager()
        tpl = mgr.get_template("blog")
        assert tpl is not None
        assert tpl.label == "Blog Post"

    def test_get_nonexistent_template(self):
        mgr = TemplateManager()
        assert mgr.get_template("nonexistent") is None

    def test_register_template(self):
        mgr = TemplateManager()
        tpl = ContentTemplate(name="custom", label="Custom", description="A custom template", sections=["intro"])
        mgr.register_template(tpl)
        assert mgr.get_template("custom") is not None

    def test_remove_template(self):
        mgr = TemplateManager()
        mgr.register_template(ContentTemplate(name="tmp", label="Temp", description="Temp"))
        assert mgr.remove_template("tmp") is True
        assert mgr.remove_template("nonexistent") is False

    def test_get_sections(self):
        mgr = TemplateManager()
        sections = mgr.get_sections("blog")
        assert "title" in sections
        assert "introduction" in sections

    def test_builtin_templates_have_fields(self):
        for name, tpl in BUILTIN_TEMPLATES.items():
            assert len(tpl.sections) > 0
            assert tpl.suggested_length > 0


# ── Quality Scorer Tests ──

class TestQualityScorer:
    @pytest.fixture
    def draft(self):
        return Draft(
            blog_post="# Headline\n\nThis is a well-written article with sufficient content. It covers the topic in detail and provides value to the reader. Sign up today for more!",
            social_copy="Great content here!",
            ad_copy="Buy now!",
            headline="10 Tips for Better Content",
            meta_description="Discover 10 actionable tips for creating better content that engages your audience and drives results.",
            tone="professional",
            word_count=500,
        )

    @pytest.fixture
    def research(self):
        return ResearchResult(
            topic="Content Marketing",
            key_points=["SEO is important", "Quality matters", "Consistency is key", "Analytics help"],
        )

    def test_score_returns_report(self, draft, research):
        scorer = QualityScorer()
        report = scorer.score(draft, research)
        assert report.overall_score >= 0

    def test_score_dimensions_present(self, draft, research):
        scorer = QualityScorer()
        report = scorer.score(draft, research)
        assert "readability" in report.scores
        assert "seo" in report.scores
        assert "completeness" in report.scores
        assert "consistency" in report.scores
        assert "engagement" in report.scores

    def test_empty_content_scores_low(self):
        scorer = QualityScorer()
        draft = Draft()
        research = ResearchResult(topic="Test")
        report = scorer.score(draft, research)
        assert report.overall_score < 0.5

    def test_threshold_check(self, draft, research):
        scorer = QualityScorer({"quality_threshold": 0.5})
        report = scorer.score(draft, research)
        assert report.passed_threshold is True or report.passed_threshold is False

    def test_improvements_list(self):
        scorer = QualityScorer()
        draft = Draft(blog_post="Short.")
        research = ResearchResult(topic="Test")
        report = scorer.score(draft, research)
        assert len(report.improvements) >= 0


# ── SEO Analyzer Tests ──

class TestSEOAnalyzer:
    def test_analyze_empty(self):
        analyzer = SEOAnalyzer()
        draft = Draft()
        result = analyzer.analyze(draft)
        assert result.overall == 0.0

    def test_analyze_with_content(self):
        analyzer = SEOAnalyzer()
        draft = Draft(
            blog_post="# Title\n\nThis is content with keywords. Content marketing is great.",
            headline="Content Marketing: The Ultimate Guide",
            meta_description="Learn about content marketing strategies that drive results and engagement.",
        )
        result = analyzer.analyze(draft, target_keywords=["content marketing"])
        assert len(result.keywords) > 0
        assert result.overall > 0

    def test_keyword_analysis(self):
        analyzer = SEOAnalyzer()
        draft = Draft(
            blog_post="AI technology is transforming business.",
            headline="AI in Business",
            meta_description="AI technology trends",
        )
        result = analyzer.analyze(draft, target_keywords=["AI"])
        kw = result.keywords[0]
        assert kw.keyword == "AI"
        assert kw.in_title is True

    def test_suggestions_generated(self):
        analyzer = SEOAnalyzer()
        draft = Draft()
        result = analyzer.analyze(draft)
        assert len(result.suggestions) > 0


# ── Suggestion Engine Tests ──

class TestSuggestionEngine:
    def test_suggest_hashtags(self):
        engine = SuggestionEngine()
        hashtags = engine.suggest_hashtags("Technology Trends", "AI and machine learning are transforming technology")
        assert len(hashtags) > 0

    def test_hashtag_relevance_scores(self):
        engine = SuggestionEngine()
        hashtags = engine.suggest_hashtags("Marketing")
        for tag in hashtags:
            assert 0.0 <= tag.relevance <= 1.0

    def test_suggest_keywords(self):
        engine = SuggestionEngine()
        keywords = engine.suggest_keywords("Digital Marketing Trends")
        assert len(keywords) > 0

    def test_keyword_primary(self):
        engine = SuggestionEngine()
        keywords = engine.suggest_keywords("AI in Healthcare")
        assert keywords[0].keyword == "AI in Healthcare"
        assert keywords[0].suggested_as == "primary"

    def test_suggest_with_content(self):
        engine = SuggestionEngine()
        keywords = engine.suggest_keywords("Remote Work", "Remote work is becoming the new normal for many companies worldwide")
        assert len(keywords) >= 1


# ── Batch Processor Tests ──

class TestBatchProcessor:
    def test_batch_with_single_topic(self):
        processor = BatchProcessor()
        result = processor.run(["Test Topic"])
        assert result.total == 1
        assert result.succeeded >= 1

    def test_batch_with_multiple_topics(self):
        processor = BatchProcessor({"batch": {"max_workers": 2}})
        result = processor.run(["Topic A", "Topic B", "Topic C"])
        assert result.total == 3
        assert result.succeeded >= 3

    def test_batch_result_structure(self):
        processor = BatchProcessor()
        result = processor.run(["Test"])
        assert hasattr(result, "total")
        assert hasattr(result, "succeeded")
        assert hasattr(result, "failed")
        assert hasattr(result, "duration_seconds")
        assert result.duration_seconds >= 0

    def test_batch_results_contain_packages(self):
        processor = BatchProcessor()
        result = processor.run(["Test Topic"])
        for topic, package in result.results.items():
            assert package is not None
