"""Tests for the scheduling stage."""

import pytest
import tempfile
from pathlib import Path

from content_automata.models import (
    ContentBrief,
    Draft,
    FinalContent,
    ResearchResult,
    ScheduleExport,
    ScheduleResult,
    VisualAsset,
    VisualsResult,
)
from content_automata.stages.scheduler import ContentScheduler


@pytest.fixture
def sample_final():
    """Create a sample FinalContent for testing."""
    return FinalContent(
        research=ResearchResult(
            topic="Test Topic",
            key_points=["Point 1", "Point 2", "Point 3"],
            summary="This is a test summary.",
        ),
        draft=Draft(
            blog_post="# Blog Post\n\nContent here.",
            social_copy="Social post here!",
            ad_copy="Ad copy here.",
            headline="Test Headline",
            meta_description="Test meta description for SEO.",
            tone="professional",
            word_count=50,
        ),
        visuals=VisualsResult(
            images=[
                VisualAsset(
                    url="https://example.com/img1.png",
                    prompt="Test image 1",
                    alt_text="Test image 1 description",
                    width=1024,
                    height=1024,
                ),
                VisualAsset(
                    url="https://example.com/img2.png",
                    prompt="Test image 2",
                    alt_text="Test image 2 description",
                    width=1920,
                    height=1080,
                ),
            ],
        ),
    )


class TestContentSchedulerInit:
    """Test ContentScheduler initialization."""

    def test_default_init(self):
        scheduler = ContentScheduler()
        assert "markdown" in scheduler._export_formats

    def test_custom_config(self):
        config = {"scheduling": {"export_formats": ["html", "csv"], "output_dir": "/tmp/test_out"}}
        scheduler = ContentScheduler(config)
        assert "html" in scheduler._export_formats
        assert "csv" in scheduler._export_formats


class TestScheduling:
    """Test scheduling operations."""

    def test_schedule_returns_result(self, sample_final):
        scheduler = ContentScheduler()
        brief = ContentBrief(topic="Test Topic")
        result = scheduler.schedule(sample_final, brief)
        assert isinstance(result, ScheduleResult)

    def test_default_schedule_has_one_export(self, sample_final):
        scheduler = ContentScheduler()
        brief = ContentBrief(topic="Test Topic")
        result = scheduler.schedule(sample_final, brief)
        assert len(result.exports) > 0

    def test_schedule_with_custom_formats(self, sample_final):
        scheduler = ContentScheduler(config={"scheduling": {"export_formats": ["markdown", "csv", "html"]}})
        brief = ContentBrief(topic="Test Topic")
        result = scheduler.schedule(sample_final, brief)
        formats = [e.format for e in result.exports]
        assert "markdown" in formats
        assert "csv" in formats
        assert "html" in formats

    def test_schedule_sets_date(self, sample_final):
        scheduler = ContentScheduler()
        brief = ContentBrief(topic="Test Topic")
        result = scheduler.schedule(sample_final, brief)
        assert result.scheduled_date is not None

    def test_schedule_sets_platform(self, sample_final):
        scheduler = ContentScheduler()
        brief = ContentBrief(topic="Test Topic")
        result = scheduler.schedule(sample_final, brief)
        assert result.platform is not None


class TestExportFormats:
    """Test export format generation."""

    def test_export_markdown_content(self, sample_final):
        scheduler = ContentScheduler()
        brief = ContentBrief(topic="Test Topic")
        content = scheduler._export_markdown(sample_final, brief)
        assert "Test Topic" in content
        assert "Research Summary" in content
        assert "Point 1" in content
        assert "Key Points" in content
        assert "Visual Assets" in content

    def test_export_html_content(self, sample_final):
        scheduler = ContentScheduler()
        brief = ContentBrief(topic="Test Topic")
        content = scheduler._export_html(sample_final, brief)
        assert "<h1>Test Topic</h1>" in content
        assert "<html" in content
        assert "<meta" in content
        assert "<img" in content
        assert "</html>" in content

    def test_export_csv_content(self, sample_final):
        scheduler = ContentScheduler()
        brief = ContentBrief(topic="Test Topic")
        content = scheduler._export_csv(sample_final, brief)
        assert "Test Topic" in content
        assert "Field,Value" in content
        assert "Blog Post" in content

    def test_export_markdown_includes_images(self, sample_final):
        scheduler = ContentScheduler()
        brief = ContentBrief(topic="Test Topic")
        content = scheduler._export_markdown(sample_final, brief)
        assert "img1.png" in content
        assert "img2.png" in content

    def test_export_html_includes_styles(self, sample_final):
        scheduler = ContentScheduler()
        brief = ContentBrief(topic="Test Topic")
        content = scheduler._export_html(sample_final, brief)
        assert "font-family" in content
        assert "max-width" in content


class TestSaveExports:
    """Test file saving."""

    def test_save_markdown(self, sample_final):
        with tempfile.TemporaryDirectory() as tmpdir:
            scheduler = ContentScheduler(config={"scheduling": {"output_dir": tmpdir}})
            brief = ContentBrief(topic="Test Topic")
            result = scheduler.schedule(sample_final, brief)
            for export in result.exports:
                if export.file_path:
                    path = Path(export.file_path)
                    assert path.exists()
                    assert path.suffix in [".md", ".html", ".csv"]

    def test_save_creates_output_dir(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "nested" / "output"
            scheduler = ContentScheduler(config={"scheduling": {"output_dir": str(output_dir)}})
            brief = ContentBrief(topic="Test")
            final = FinalContent(
                research=ResearchResult(topic="Test", key_points=["P1"]),
                draft=Draft(blog_post="Content"),
            )
            result = scheduler.schedule(final, brief)
            assert output_dir.exists()


class TestSchedulerEdgeCases:
    """Test edge cases."""

    def test_empty_research(self):
        scheduler = ContentScheduler()
        final = FinalContent(
            research=ResearchResult(),
            draft=Draft(blog_post="Content"),
        )
        brief = ContentBrief(topic="Test")
        result = scheduler.schedule(final, brief)
        assert len(result.exports) > 0

    def test_empty_draft(self):
        scheduler = ContentScheduler()
        final = FinalContent(
            research=ResearchResult(topic="Test", key_points=["P1"]),
            draft=Draft(),
        )
        brief = ContentBrief(topic="Test")
        result = scheduler.schedule(final, brief)
        assert len(result.exports) > 0

    def test_unsupported_format_skipped(self, sample_final):
        scheduler = ContentScheduler(config={"scheduling": {"export_formats": ["markdown", "pdf", "docx"]}})
        brief = ContentBrief(topic="Test Topic")
        result = scheduler.schedule(sample_final, brief)
        formats = [e.format for e in result.exports]
        assert "markdown" in formats
        assert "pdf" not in formats
        assert "docx" not in formats
