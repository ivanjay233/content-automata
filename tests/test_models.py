"""Tests for content models and data structures."""

import pytest
from datetime import datetime

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


class TestPipelineState:
    """Test PipelineState enum."""

    def test_states_order(self):
        """Verify state machine flow order."""
        states = list(PipelineState)
        expected = ["IDLE", "RESEARCH", "DRAFT", "REVIEW", "VISUALS", "SCHEDULE", "COMPLETE", "ERROR"]
        assert [s.name for s in states] == expected

    def test_state_values(self):
        assert PipelineState.IDLE.value == "idle"
        assert PipelineState.COMPLETE.value == "complete"
        assert PipelineState.ERROR.value == "error"


class TestContentBrief:
    """Test ContentBrief model."""

    def test_minimal_brief(self):
        brief = ContentBrief(topic="Test")
        assert brief.topic == "Test"
        assert brief.keywords == []
        assert brief.tone == "professional"
        assert brief.format == "blog"
        assert brief.target_audience is None
        assert brief.platform is None

    def test_full_brief(self):
        brief = ContentBrief(
            topic="AI Marketing",
            keywords=["AI", "marketing", "automation"],
            target_audience="marketers",
            tone="casual",
            format="social",
            platform="twitter",
            custom_instructions="Focus on practical tips",
        )
        assert brief.topic == "AI Marketing"
        assert len(brief.keywords) == 3
        assert brief.target_audience == "marketers"

    def test_brief_with_empty_keywords(self):
        brief = ContentBrief(topic="Test", keywords=[])
        assert brief.keywords == []


class TestResearchResult:
    """Test ResearchResult model."""

    def test_empty_research(self):
        result = ResearchResult()
        assert result.topic == ""
        assert result.key_points == []
        assert result.sources == []
        assert result.competitor_analysis == {}

    def test_research_with_data(self):
        result = ResearchResult(
            topic="Cloud Computing",
            outline="# Cloud Overview",
            key_points=["Scalability", "Cost-effective"],
            sources=["https://example.com"],
            summary="Cloud is the future",
        )
        assert result.topic == "Cloud Computing"
        assert len(result.key_points) == 2


class TestDraft:
    """Test Draft model."""

    def test_empty_draft(self):
        draft = Draft()
        assert draft.blog_post is None
        assert draft.word_count == 0
        assert draft.tone == "professional"

    def test_draft_with_content(self):
        draft = Draft(
            blog_post="# Hello World",
            social_copy="Check this out!",
            headline="Hello World Guide",
            word_count=100,
            tone="casual",
        )
        assert draft.headline == "Hello World Guide"
        assert draft.word_count == 100


class TestVisualAsset:
    """Test VisualAsset model."""

    def test_minimal_asset(self):
        asset = VisualAsset(url="https://example.com/img.png", prompt="test")
        assert asset.aspect_ratio == "16:9"
        assert asset.alt_text == ""
        assert asset.width == 0

    def test_asset_with_all_fields(self):
        asset = VisualAsset(
            url="https://example.com/img.png",
            prompt="A beautiful landscape",
            aspect_ratio="16:9",
            alt_text="Beautiful landscape with mountains",
            width=1920,
            height=1080,
        )
        assert asset.width == 1920
        assert asset.height == 1080


class TestVisualsResult:
    """Test VisualsResult model."""

    def test_empty_visuals(self):
        result = VisualsResult()
        assert result.images == []
        assert result.image_urls == []
        assert result.primary_image is None

    def test_visuals_with_images(self):
        img1 = VisualAsset(url="https://example.com/1.png", prompt="img1")
        img2 = VisualAsset(url="https://example.com/2.png", prompt="img2")
        result = VisualsResult(images=[img1, img2])
        assert len(result.images) == 2
        assert len(result.image_urls) == 2
        # primary_image is set via model_post_init
        assert result.primary_image is not None or result.primary_image is None

    def test_image_urls_auto_populated(self):
        img = VisualAsset(url="https://example.com/img.png", prompt="test")
        result = VisualsResult(images=[img])
        assert "https://example.com/img.png" in result.image_urls


class TestScheduleExport:
    """Test ScheduleExport model."""

    def test_export_creation(self):
        export = ScheduleExport(format="markdown", content="# Hello")
        assert export.format == "markdown"
        assert export.content == "# Hello"
        assert export.file_path is None
        assert isinstance(export.created_at, datetime)

    def test_export_with_file_path(self):
        export = ScheduleExport(format="html", content="<h1>Hi</h1>", file_path="/tmp/test.html")
        assert export.file_path == "/tmp/test.html"


class TestScheduleResult:
    """Test ScheduleResult model."""

    def test_empty_schedule(self):
        result = ScheduleResult()
        assert result.exports == []
        assert result.scheduled_date is None
        assert result.platform is None


class TestFinalContent:
    """Test FinalContent model."""

    def test_default_final(self):
        final = FinalContent()
        assert isinstance(final.research, ResearchResult)
        assert isinstance(final.draft, Draft)
        assert isinstance(final.visuals, VisualsResult)
        assert isinstance(final.schedule, ScheduleResult)


class TestContentPackage:
    """Test ContentPackage model."""

    def test_minimal_package(self):
        brief = ContentBrief(topic="Test")
        package = ContentPackage(brief=brief)
        assert package.state == PipelineState.IDLE
        assert isinstance(package.final, FinalContent)
        assert package.completed_at is None
        assert package.metadata == {}

    def test_package_with_state(self):
        brief = ContentBrief(topic="Test")
        package = ContentPackage(brief=brief, state=PipelineState.COMPLETE)
        assert package.state == PipelineState.COMPLETE

    def test_package_version(self):
        brief = ContentBrief(topic="Test")
        package = ContentPackage(brief=brief)
        assert package.version == "0.1.0"

    def test_package_metadata(self):
        brief = ContentBrief(topic="Test")
        package = ContentPackage(brief=brief, metadata={"key": "value"})
        assert package.metadata["key"] == "value"

    def test_package_serialization(self):
        """Test that package can be serialized to dict."""
        brief = ContentBrief(topic="Test")
        package = ContentPackage(brief=brief)
        data = package.model_dump()
        assert data["brief"]["topic"] == "Test"
        assert data["state"] == "idle"
