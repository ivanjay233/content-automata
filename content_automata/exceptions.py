"""Custom exceptions for content-automata pipeline."""


class ContentAutomataError(Exception):
    """Base exception for all content-automata errors."""

    def __init__(self, message: str, stage: str | None = None, details: dict | None = None):
        self.stage = stage
        self.details = details or {}
        super().__init__(message)


class ConfigurationError(ContentAutomataError):
    """Raised when configuration is invalid or missing."""

    def __init__(self, message: str, field: str | None = None):
        self.field = field
        super().__init__(message, stage="config")


class ResearchError(ContentAutomataError):
    """Raised when the research stage fails."""

    def __init__(self, message: str, topic: str | None = None, provider: str | None = None):
        self.topic = topic
        self.provider = provider
        super().__init__(message, stage="research", details={"topic": topic, "provider": provider})


class CopywritingError(ContentAutomataError):
    """Raised when the copywriting stage fails."""

    def __init__(self, message: str, tone: str | None = None):
        self.tone = tone
        super().__init__(message, stage="copywriting", details={"tone": tone})


class ImageGenerationError(ContentAutomataError):
    """Raised when image generation fails."""

    def __init__(self, message: str, provider: str | None = None, aspect_ratio: str | None = None):
        self.provider = provider
        self.aspect_ratio = aspect_ratio
        super().__init__(message, stage="image_gen", details={"provider": provider, "aspect_ratio": aspect_ratio})


class SchedulingError(ContentAutomataError):
    """Raised when scheduling or export fails."""

    def __init__(self, message: str, export_format: str | None = None):
        self.export_format = export_format
        super().__init__(message, stage="scheduling", details={"export_format": export_format})


class APIError(ContentAutomataError):
    """Raised when an external API call fails."""

    def __init__(self, message: str, provider: str, status_code: int | None = None, response: str | None = None):
        self.provider = provider
        self.status_code = status_code
        self.response = response
        super().__init__(
            message,
            stage="api",
            details={"provider": provider, "status_code": status_code, "response": response},
        )


class ValidationError(ContentAutomataError):
    """Raised when input validation fails."""

    def __init__(self, message: str, field: str | None = None, value: object = None):
        self.field = field
        self.value = value
        super().__init__(message, stage="validation", details={"field": field, "value": str(value)})


class EmptyResearchError(ResearchError):
    """Raised when research returns no results."""

    def __init__(self, topic: str):
        super().__init__(f"Research returned no results for topic: '{topic}'", topic=topic)
