"""Tests for WordPress exporter, calendar planner, and progress tracking."""

import pytest
import tempfile
from pathlib import Path

from content_automata.wordpress import WordPressExporter, WordPressPost
from content_automata.calendar import CalendarPlanner, ContentCalendar, CalendarEntry
from content_automata.progress import PipelineProgress
from content_automata.models import FinalContent, ResearchResult, Draft, VisualAsset, VisualsResult


class TestWordPressExporter:
    """Test WordPress exporter."""

    def test_creates_post(self):
        exporter = WordPressExporter()
        final = FinalContent(
            research=ResearchResult(topic="Test", key_points=["P1"], summary="Summary"),
            draft=Draft(blog_post="Blog content", headline="Test Headline", meta_description="Meta desc"),
        )
        post = exporter.export(final)
        assert isinstance(post, WordPressPost)
        assert post.title == "Test Headline"

    def test_post_includes_content(self):
        exporter = WordPressExporter()
        final = FinalContent(
            research=ResearchResult(topic="Test", key_points=["P1"]),
            draft=Draft(blog_post="# Hello World", headline="Hello", meta_description="Desc"),
        )
        post = exporter.export(final)
        assert "Hello World" in post.content

    def test_rest_api_payload(self):
        exporter = WordPressExporter()
        post = WordPressPost(title="Test", content="Content", status="draft")
        payload = exporter.to_rest_api_payload(post)
        assert payload["title"] == "Test"
        assert payload["status"] == "draft"

    def test_xmlrpc_payload(self):
        exporter = WordPressExporter()
        post = WordPressPost(title="Test", content="Content", slug="test-post")
        payload = exporter.to_xmlrpc_payload(post)
        assert payload["post_title"] == "Test"
        assert payload["post_name"] == "test-post"

    def test_to_html_file(self):
        exporter = WordPressExporter()
        post = WordPressPost(title="Test Page", content="<p>Hello</p>")
        html = exporter.to_html_file(post)
        assert "<!DOCTYPE html>" in html
        assert "Test Page" in html
        assert "<p>Hello</p>" in html


class TestCalendarPlanner:
    """Test calendar planner."""

    def test_plan_month(self):
        planner = CalendarPlanner()
        calendar = planner.plan_month(["Topic A", "Topic B"])
        assert isinstance(calendar, ContentCalendar)
        assert len(calendar.entries) > 0

    def test_plan_month_with_year_month(self):
        planner = CalendarPlanner()
        calendar = planner.plan_month(["Test"], year=2026, month=6)
        assert calendar.year == 2026
        assert "2026-06" in calendar.month

    def test_calendar_entries_have_types(self):
        planner = CalendarPlanner()
        calendar = planner.plan_month(["Test Topic"])
        for entry in calendar.entries:
            assert entry.content_type in ["blog", "social", "newsletter", "ad"]

    def test_calendar_to_markdown(self):
        planner = CalendarPlanner()
        calendar = planner.plan_month(["Topic"])
        md = calendar.to_markdown()
        assert "Content Calendar" in md
        assert "| Date |" in md

    def test_calendar_to_json(self):
        planner = CalendarPlanner()
        calendar = planner.plan_month(["Topic"])
        json_str = calendar.to_json()
        assert '"month"' in json_str
        assert '"entries"' in json_str

    def test_calendar_entry_defaults(self):
        entry = CalendarEntry(date="2026-06-01", topic="Test", content_type="blog")
        assert entry.status == "draft"
        assert entry.platform == "web"


class TestPipelineProgress:
    """Test progress tracking."""

    def test_stage_labels(self):
        assert PipelineProgress.stage_label("research") == "Research"
        assert PipelineProgress.stage_label("copywriting") == "Copywriting"
        assert PipelineProgress.stage_label("unknown") == "unknown"

    def test_initialization(self):
        progress = PipelineProgress()
        assert progress._current_stage == ""
