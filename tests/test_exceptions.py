"""Tests for exceptions and error handling."""

import pytest

from content_automata.exceptions import (
    ContentAutomataError,
    ConfigurationError,
    ResearchError,
    CopywritingError,
    ImageGenerationError,
    SchedulingError,
    APIError,
    ValidationError,
    EmptyResearchError,
)


class TestBaseException:
    """Test base ContentAutomataError."""

    def test_base_error(self):
        error = ContentAutomataError("Something went wrong")
        assert str(error) == "Something went wrong"
        assert error.stage is None
        assert error.details == {}

    def test_error_with_stage(self):
        error = ContentAutomataError("Failed", stage="research")
        assert error.stage == "research"

    def test_error_with_details(self):
        error = ContentAutomataError("Failed", details={"key": "value"})
        assert error.details == {"key": "value"}


class TestSpecificExceptions:
    """Test specific exception types."""

    def test_configuration_error(self):
        error = ConfigurationError("Missing API key", field="api_key")
        assert "Missing API key" in str(error)
        assert error.field == "api_key"
        assert error.stage == "config"

    def test_research_error(self):
        error = ResearchError("Search failed", topic="AI", provider="tavily")
        assert error.topic == "AI"
        assert error.provider == "tavily"
        assert error.stage == "research"

    def test_copywriting_error(self):
        error = CopywritingError("Generation failed", tone="professional")
        assert error.tone == "professional"
        assert error.stage == "copywriting"

    def test_image_generation_error(self):
        error = ImageGenerationError("API error", provider="openai", aspect_ratio="16:9")
        assert error.provider == "openai"
        assert error.aspect_ratio == "16:9"
        assert error.stage == "image_gen"

    def test_scheduling_error(self):
        error = SchedulingError("Export failed", export_format="pdf")
        assert error.export_format == "pdf"
        assert error.stage == "scheduling"

    def test_api_error(self):
        error = APIError("Rate limited", provider="openai", status_code=429, response="Too many requests")
        assert error.provider == "openai"
        assert error.status_code == 429
        assert error.response == "Too many requests"
        assert error.stage == "api"

    def test_validation_error(self):
        error = ValidationError("Invalid input", field="topic", value="")
        assert error.field == "topic"
        assert error.value == ""
        assert error.stage == "validation"

    def test_empty_research_error(self):
        error = EmptyResearchError(topic="Quantum Physics")
        assert "Quantum Physics" in str(error)
        assert error.topic == "Quantum Physics"
        assert isinstance(error, ResearchError)


class TestExceptionHierarchy:
    """Test that exceptions form a proper hierarchy."""

    def test_all_are_content_automata_errors(self):
        errors = [
            ConfigurationError("test"),
            ResearchError("test"),
            CopywritingError("test"),
            ImageGenerationError("test"),
            SchedulingError("test"),
            APIError("test", provider="test"),
            ValidationError("test"),
            EmptyResearchError("test"),
        ]
        for error in errors:
            assert isinstance(error, ContentAutomataError)

    def test_empty_research_is_research(self):
        error = EmptyResearchError("test")
        assert isinstance(error, ResearchError)
        assert isinstance(error, ContentAutomataError)
