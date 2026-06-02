"""Tests for the content-automata pipeline."""

import sys
from pathlib import Path

# Ensure package is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from content_automata import Pipeline, ContentPipeline
from content_automata.models import (
    ContentBrief,
    ContentPackage,
    Draft,
    FinalContent,
    PipelineState,
    ResearchResult,
    VisualAsset,
    VisualsResult,
    ScheduleExport,
    ScheduleResult,
)
from content_automata.stages.research import TopicResearch
from content_automata.stages.copywriter import CopyWriter
from content_automata.stages.image_gen import ImageGenerator
from content_automata.stages.scheduler import ContentScheduler


class TestModels:
    """Test Pydantic model creation and validation."""

    def test_content_brief_defaults(self):
        brief = ContentBrief(topic="Test Topic")
        assert brief.topic == "Test Topic"
        assert brief.keywords == []
        assert brief.tone == "professional"
        assert brief.format == "blog"

    def test_content_brief_with_keywords(self):
        brief = ContentBrief(
            topic="AI Marketing",
            keywords=["AI", "marketing", "automation"],
            tone="casual",
        )
        assert len(brief.keywords) == 3
        assert brief.tone == "casual"

    def test_research_result(self):
        result = ResearchResult(
            topic="Test",
            outline="# Outline",
            key_points=["Point 1", "Point 2"],
            summary="Summary text",
        )
        assert result.topic == "Test"
        assert len(result.key_points) == 2

    def test_draft(self):
        draft = Draft(
            blog_post="Blog content",
            social_copy="Social content",
            headline="Test Headline",
            word_count=25,
        )
        assert draft.headline == "Test Headline"
        assert draft.word_count == 25

    def test_visual_asset(self):
        asset = VisualAsset(
            url="https://example.com/img.png",
            prompt="A test image",
            width=1024,
            height=768,
        )
        assert asset.aspect_ratio == "16:9"  # default

    def test_visuals_result(self):
        img = VisualAsset(url="https://example.com/img.png", prompt="test")
        result = VisualsResult(images=[img])
        assert len(result.images) == 1
        assert len(result.image_urls) == 1

    def test_schedule_export(self):
        export = ScheduleExport(format="markdown", content="# Hello")
        assert export.format == "markdown"
        assert export.content == "# Hello"

    def test_content_package(self):
        brief = ContentBrief(topic="Test")
        package = ContentPackage(brief=brief)
        assert package.state == PipelineState.IDLE
        assert isinstance(package.final, FinalContent)

    def test_content_package_full(self):
        brief = ContentBrief(topic="Test")
        package = ContentPackage(brief=brief, state=PipelineState.COMPLETE)
        assert package.state == PipelineState.COMPLETE
        assert package.version == "0.1.0"


class TestTopicResearch:
    """Test the research stage."""

    def test_initialization(self):
        researcher = TopicResearch()
        assert researcher is not None

    def test_research_returns_result(self):
        researcher = TopicResearch()
        brief = ContentBrief(topic="Python Programming")
        result = researcher.research(brief)
        assert isinstance(result, ResearchResult)
        assert result.topic == "Python Programming"
        assert len(result.key_points) > 0
        assert result.outline != ""
        assert result.summary != ""

    def test_research_with_keywords(self):
        researcher = TopicResearch()
        brief = ContentBrief(
            topic="Cloud Computing",
            keywords=["AWS", "Azure", "GCP"],
        )
        result = researcher.research(brief)
        assert len(result.sources) > 0

    def test_generate_outline(self):
        researcher = TopicResearch()
        outline = researcher._generate_outline("Test", {"query": "test"})
        assert "# Test" in outline
        assert "## Introduction" in outline
        assert "## Conclusion" in outline


class TestCopyWriter:
    """Test the copywriting stage."""

    def test_initialization(self):
        writer = CopyWriter()
        assert writer._default_tone == "professional"

    def test_generate_blog_post(self):
        writer = CopyWriter()
        research = ResearchResult(
            topic="Digital Marketing",
            key_points=["SEO is important", "Content is king"],
            outline="# Outline",
        )
        brief = ContentBrief(topic="Digital Marketing")
        draft = writer.generate(research, brief)
        assert isinstance(draft, Draft)
        assert draft.blog_post is not None
        assert "Digital Marketing" in draft.blog_post
        assert draft.word_count > 0

    def test_generate_social_copy(self):
        writer = CopyWriter()
        research = ResearchResult(
            topic="Remote Work",
            key_points=["Flexibility", "Productivity"],
        )
        brief = ContentBrief(topic="Remote Work", tone="casual")
        draft = writer.generate(research, brief)
        assert draft.social_copy is not None

    def test_generate_ad_copy(self):
        writer = CopyWriter()
        research = ResearchResult(
            topic="Product Launch",
            key_points=["Innovation", "Value"],
        )
        brief = ContentBrief(topic="Product Launch", tone="persuasive")
        draft = writer.generate(research, brief)
        assert draft.ad_copy is not None

    def test_generate_headline(self):
        writer = CopyWriter()
        headline = writer._generate_headline("Test Topic", "professional")
        assert "Test Topic" in headline

    def test_unsupported_tone_fallback(self):
        writer = CopyWriter()
        research = ResearchResult(topic="Test", key_points=["Point"])
        brief = ContentBrief(topic="Test", tone="nonexistent")
        draft = writer.generate(research, brief)
        assert draft.tone == "professional"


class TestImageGenerator:
    """Test the image generation stage."""

    def test_initialization(self):
        gen = ImageGenerator()
        assert gen._provider == "openai"
        assert gen._default_aspect == "16:9"

    def test_simulate_image(self):
        gen = ImageGenerator()
        asset = gen._simulate_image("Test prompt", "16:9")
        assert isinstance(asset, VisualAsset)
        assert "placeholder.com" in asset.url
        assert asset.aspect_ratio == "16:9"

    def test_generate_prompts(self):
        gen = ImageGenerator()
        prompts = gen._generate_prompts("AI", "AI Title", "Blog content here")
        assert len(prompts) == 3

    def test_generate_without_api_key(self):
        gen = ImageGenerator()
        draft = Draft(blog_post="Content", headline="Headline")
        brief = ContentBrief(topic="Test")
        result = gen.generate(draft, brief)
        assert isinstance(result, VisualsResult)
        assert len(result.images) > 0

    def test_aspect_ratio_resolution(self):
        gen = ImageGenerator()
        brief = ContentBrief(topic="Test")
        aspect = gen._get_aspect_ratio(brief)
        assert aspect == "16:9"


class TestContentScheduler:
    """Test the scheduling stage."""

    def test_initialization(self):
        scheduler = ContentScheduler()
        assert "markdown" in scheduler._export_formats

    def test_export_markdown(self):
        scheduler = ContentScheduler()
        final = FinalContent(
            research=ResearchResult(
                topic="Test", key_points=["Point 1"], summary="Summary"
            ),
            draft=Draft(blog_post="# Blog", word_count=10),
        )
        brief = ContentBrief(topic="Test")
        result = scheduler.schedule(final, brief)
        assert isinstance(result, ScheduleResult)
        assert len(result.exports) > 0
        assert result.exports[0].format == "markdown"

    def test_schedule_creates_exports(self):
        scheduler = ContentScheduler(config={
            "scheduling": {"export_formats": ["markdown", "csv"]}
        })
        final = FinalContent(
            research=ResearchResult(topic="Test", key_points=["P1"]),
            draft=Draft(blog_post="# Post"),
        )
        brief = ContentBrief(topic="Test")
        result = scheduler.schedule(final, brief)
        formats = [e.format for e in result.exports]
        assert "markdown" in formats
        assert "csv" in formats


class TestPipeline:
    """Test the main ContentPipeline orchestrator."""

    def test_initialization(self):
        pipeline = ContentPipeline()
        assert pipeline.state == PipelineState.IDLE

    def test_from_topic(self):
        pipeline = ContentPipeline()
        result = pipeline.from_topic("Test Topic")
        assert isinstance(result, ContentPackage)
        assert result.state == PipelineState.COMPLETE
        assert result.final.research.topic == "Test Topic"

    def test_from_brief_dict(self):
        pipeline = ContentPipeline()
        brief = {
            "topic": "Python Development",
            "keywords": ["Python", "programming"],
            "tone": "casual",
        }
        result = pipeline.from_brief(brief)
        assert result.state == PipelineState.COMPLETE

    def test_from_brief_object(self):
        pipeline = ContentPipeline()
        brief = ContentBrief(topic="Data Science")
        result = pipeline.from_brief(brief)
        assert result.state == PipelineState.COMPLETE

    def test_pipeline_maintains_state(self):
        pipeline = ContentPipeline()
        assert pipeline.state == PipelineState.IDLE
        result = pipeline.from_topic("Test")
        assert result.state == PipelineState.COMPLETE

    def test_from_url(self):
        pipeline = ContentPipeline()
        result = pipeline.from_url("https://example.com/article")
        assert result.state == PipelineState.COMPLETE

    def test_package_getter(self):
        pipeline = ContentPipeline()
        assert pipeline.package is None
        pipeline.from_topic("Test")
        assert pipeline.package is not None

    def test_config_from_dict(self):
        config = {"research": {"provider": "tavily"}}
        pipeline = ContentPipeline(config=config)
        assert pipeline.research_stage._provider == "tavily"


class TestPipelineExport:
    """Test Pipeline alias import."""

    def test_pipeline_alias(self):
        pipeline = Pipeline()
        assert isinstance(pipeline, ContentPipeline)

    def test_pipeline_from_topic_via_alias(self):
        pipeline = Pipeline()
        result = pipeline.from_topic("Integration Test")
        assert result.brief.topic == "Integration Test"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
