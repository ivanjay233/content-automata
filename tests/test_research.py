"""Tests for the research stage."""

import pytest

from content_automata.models import ContentBrief, ResearchResult
from content_automata.stages.research import TopicResearch


class TestTopicResearchInit:
    """Test TopicResearch initialization."""

    def test_default_init(self):
        researcher = TopicResearch()
        assert researcher._provider == "tavily"
        assert researcher._max_results == 5

    def test_custom_config(self):
        config = {"research": {"provider": "exa", "max_results": 10}}
        researcher = TopicResearch(config)
        assert researcher._provider == "exa"
        assert researcher._max_results == 10


class TestTopicResearchExecution:
    """Test research execution."""

    def test_research_returns_correct_type(self):
        researcher = TopicResearch()
        brief = ContentBrief(topic="Python Programming")
        result = researcher.research(brief)
        assert isinstance(result, ResearchResult)

    def test_research_populates_topic(self):
        researcher = TopicResearch()
        brief = ContentBrief(topic="Data Science")
        result = researcher.research(brief)
        assert result.topic == "Data Science"

    def test_research_with_keywords(self):
        researcher = TopicResearch()
        brief = ContentBrief(topic="Cloud Computing", keywords=["AWS", "Azure"])
        result = researcher.research(brief)
        assert len(result.sources) > 0

    def test_research_generates_outline(self):
        researcher = TopicResearch()
        brief = ContentBrief(topic="Machine Learning")
        result = researcher.research(brief)
        assert "# Machine Learning" in result.outline
        assert "## Introduction" in result.outline
        assert "## Conclusion" in result.outline

    def test_research_key_points_not_empty(self):
        researcher = TopicResearch()
        brief = ContentBrief(topic="Blockchain")
        result = researcher.research(brief)
        assert len(result.key_points) > 0

    def test_research_summary_not_empty(self):
        researcher = TopicResearch()
        brief = ContentBrief(topic="Quantum Computing")
        result = researcher.research(brief)
        assert result.summary != ""

    def test_research_sources_are_urls(self):
        researcher = TopicResearch()
        brief = ContentBrief(topic="Web Development")
        result = researcher.research(brief)
        for source in result.sources:
            assert source.startswith("http")

    def test_research_competitor_analysis(self):
        researcher = TopicResearch()
        brief = ContentBrief(topic="Digital Marketing")
        result = researcher.research(brief)
        assert "competitors" in result.competitor_analysis
        assert "gap_analysis" in result.competitor_analysis
        assert "differentiation_opportunities" in result.competitor_analysis


class TestTopicResearchInternal:
    """Test internal methods."""

    def test_generate_outline_structure(self):
        researcher = TopicResearch()
        outline = researcher._generate_outline("Test", {"query": "test"})
        assert outline.startswith("# Test")
        assert "## Key Concepts" in outline
        assert "## Practical Applications" in outline
        assert "## Future Outlook" in outline

    def test_extract_key_points_from_answer(self):
        researcher = TopicResearch()
        raw_data = {"answer": "Point one. Point two. Point three."}
        points = researcher._extract_key_points(raw_data)
        assert len(points) == 3

    def test_extract_key_points_empty(self):
        researcher = TopicResearch()
        points = researcher._extract_key_points({})
        assert len(points) == 5  # defaults

    def test_generate_summary(self):
        researcher = TopicResearch()
        summary = researcher._generate_summary("Test", ["Point A", "Point B"])
        assert "Test" in summary
        assert "Point A" in summary or "Point B" in summary

    def test_simulate_research_structure(self):
        researcher = TopicResearch()
        sources, data = researcher._simulate_research("Test Topic", ["kw1"])
        assert len(sources) == 3
        assert "answer" in data
        assert "results" in data

    def test_fetch_research_simulated_without_key(self):
        researcher = TopicResearch()
        sources, data = researcher._fetch_research("Test", [])
        assert len(sources) > 0


class TestTopicResearchEdgeCases:
    """Test edge cases."""

    def test_empty_topic(self):
        researcher = TopicResearch()
        brief = ContentBrief(topic="")
        result = researcher.research(brief)
        assert result.outline != ""

    def test_very_long_topic(self):
        researcher = TopicResearch()
        long_topic = "A" * 500
        brief = ContentBrief(topic=long_topic)
        result = researcher.research(brief)
        assert result.topic == long_topic

    def test_special_characters_in_topic(self):
        researcher = TopicResearch()
        brief = ContentBrief(topic="C++ vs Python: Which is Better? (2026)")
        result = researcher.research(brief)
        assert result.outline != ""
