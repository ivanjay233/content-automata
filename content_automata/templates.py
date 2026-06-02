"""Content template system — blog, social, newsletter, and ad templates."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class TemplateField:
    """A configurable field in a content template."""

    name: str
    label: str
    field_type: str = "text"  # text, textarea, select, list
    required: bool = False
    default: Any = None
    options: List[str] | None = None
    description: str = ""


@dataclass
class ContentTemplate:
    """A content template defining structure and fields for content generation."""

    name: str
    label: str
    description: str
    fields: List[TemplateField] = field(default_factory=list)
    sections: List[str] = field(default_factory=list)
    suggested_length: int = 800
    seo_priority: str = "medium"  # low, medium, high
    tags: List[str] = field(default_factory=list)


# Built-in templates
BUILTIN_TEMPLATES: Dict[str, ContentTemplate] = {
    "blog": ContentTemplate(
        name="blog",
        label="Blog Post",
        description="Standard long-form blog post with introduction, body sections, and conclusion",
        sections=["title", "meta_description", "introduction", "body", "conclusion", "author_bio"],
        suggested_length=1200,
        seo_priority="high",
        tags=["seo", "long-form", "articles"],
        fields=[
            TemplateField(name="target_keyword", label="Target Keyword", field_type="text", required=True, description="Primary SEO keyword"),
            TemplateField(name="read_time", label="Read Time (min)", field_type="text", default="5", description="Estimated reading time"),
        ],
    ),
    "social": ContentTemplate(
        name="social",
        label="Social Media Post",
        description="Short-form content optimized for social media platforms",
        sections=["headline", "body", "hashtags", "call_to_action"],
        suggested_length=300,
        seo_priority="low",
        tags=["short-form", "social-media"],
        fields=[
            TemplateField(name="platform", label="Platform", field_type="select", required=True, options=["twitter", "linkedin", "facebook", "instagram"], default="linkedin"),
            TemplateField(name="include_emoji", label="Include Emoji", field_type="select", options=["yes", "no"], default="yes"),
        ],
    ),
    "newsletter": ContentTemplate(
        name="newsletter",
        label="Email Newsletter",
        description="Email newsletter with subject line, preview text, and body",
        sections=["subject_line", "preview_text", "greeting", "main_content", "cta", "footer"],
        suggested_length=600,
        seo_priority="medium",
        tags=["email", "marketing"],
        fields=[
            TemplateField(name="audience_segment", label="Audience Segment", field_type="text", description="Target segment for personalization"),
            TemplateField(name="cta_text", label="CTA Button Text", field_type="text", default="Learn More", description="Call-to-action button text"),
        ],
    ),
    "ad": ContentTemplate(
        name="ad",
        label="Advertisement Copy",
        description="Paid ad copy optimized for conversions",
        sections=["headline", "subheadline", "body", "cta", "disclaimer"],
        suggested_length=200,
        seo_priority="low",
        tags=["ads", "conversion"],
        fields=[
            TemplateField(name="ad_platform", label="Ad Platform", field_type="select", options=["google", "meta", "linkedin"], default="google"),
            TemplateField(name="value_proposition", label="Value Proposition", field_type="textarea", required=True),
        ],
    ),
}


class TemplateManager:
    """Manages content templates for the pipeline."""

    def __init__(self):
        self._templates = dict(BUILTIN_TEMPLATES)

    def list_templates(self) -> Dict[str, ContentTemplate]:
        """List all available templates."""
        return dict(self._templates)

    def get_template(self, name: str) -> ContentTemplate | None:
        """Get a template by name."""
        return self._templates.get(name)

    def register_template(self, template: ContentTemplate) -> None:
        """Register a custom template."""
        self._templates[template.name] = template

    def remove_template(self, name: str) -> bool:
        """Remove a template by name."""
        return self._templates.pop(name, None) is not None

    def get_sections(self, template_name: str) -> List[str]:
        """Get sections for a template."""
        template = self.get_template(template_name)
        return template.sections if template else []
