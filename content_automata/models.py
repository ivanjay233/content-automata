"""Pydantic models for the content-automata pipeline."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class PipelineState(str, Enum):
    """States of the content pipeline state machine."""

    IDLE = "idle"
    RESEARCH = "research"
    DRAFT = "draft"
    REVIEW = "review"
    VISUALS = "visuals"
    SCHEDULE = "schedule"
    COMPLETE = "complete"
    ERROR = "error"


class ContentBrief(BaseModel):
    """Input brief for content generation."""

    topic: str = Field(..., description="Main topic or subject")
    keywords: List[str] = Field(default_factory=list, description="Target keywords")
    target_audience: Optional[str] = Field(default=None, description="Intended audience")
    tone: str = Field(default="professional", description="Writing tone")
    format: str = Field(default="blog", description="Content format: blog, social, ad")
    platform: Optional[str] = Field(default=None, description="Target platform")
    custom_instructions: Optional[str] = Field(default=None, description="Additional instructions")


class ResearchResult(BaseModel):
    """Output from the research stage."""

    topic: str = Field(default="", description="The researched topic")
    outline: str = Field(default="", description="Content outline")
    key_points: List[str] = Field(default_factory=list, description="Key points found")
    competitor_analysis: Dict[str, Any] = Field(default_factory=dict, description="Competitor insights")
    sources: List[str] = Field(default_factory=list, description="Source URLs")
    summary: str = Field(default="", description="Executive summary")
    raw_data: Dict[str, Any] = Field(default_factory=dict, description="Raw research data")


class Draft(BaseModel):
    """Generated content draft."""

    blog_post: Optional[str] = Field(default=None, description="Blog post variant")
    social_copy: Optional[str] = Field(default=None, description="Social media variant")
    ad_copy: Optional[str] = Field(default=None, description="Advertisement variant")
    headline: Optional[str] = Field(default=None, description="Suggested headline")
    meta_description: Optional[str] = Field(default=None, description="SEO meta description")
    tone: str = Field(default="professional", description="Tone used")
    word_count: int = Field(default=0, description="Approximate word count")


class VisualAsset(BaseModel):
    """Generated visual asset."""

    url: str = Field(..., description="URL of the generated image")
    prompt: str = Field(default="", description="Prompt used for generation")
    aspect_ratio: str = Field(default="16:9", description="Image aspect ratio")
    alt_text: str = Field(default="", description="Alt text for accessibility")
    width: int = Field(default=0, description="Image width in pixels")
    height: int = Field(default=0, description="Image height in pixels")


class VisualsResult(BaseModel):
    """Output from the image generation stage."""

    images: List[VisualAsset] = Field(default_factory=list, description="Generated images")
    image_urls: List[str] = Field(default_factory=list, description="Shortcut to image URLs")
    primary_image: Optional[VisualAsset] = Field(default=None, description="Primary/featured image")

    def model_post_init(self, __context):
        """Auto-populate image_urls from images."""
        self.image_urls = [img.url for img in self.images]
        return super().model_post_init(__context)


class ScheduleExport(BaseModel):
    """A single export artifact."""

    format: str = Field(..., description="Export format: markdown, html, csv")
    content: str = Field(..., description="Exported content")
    file_path: Optional[str] = Field(default=None, description="Path to saved file")
    created_at: datetime = Field(default_factory=datetime.now)


class ScheduleResult(BaseModel):
    """Output from the scheduling stage."""

    exports: List[ScheduleExport] = Field(default_factory=list, description="Exported artifacts")
    scheduled_date: Optional[datetime] = Field(default=None, description="Scheduled publish date")
    platform: Optional[str] = Field(default=None, description="Target platform")


class FinalContent(BaseModel):
    """Complete generated content package."""

    research: ResearchResult = Field(default_factory=lambda: ResearchResult())
    draft: Draft = Field(default_factory=lambda: Draft())
    visuals: VisualsResult = Field(default_factory=lambda: VisualsResult())
    schedule: ScheduleResult = Field(default_factory=lambda: ScheduleResult())


class ContentPackage(BaseModel):
    """Full output of the content pipeline."""

    brief: ContentBrief = Field(..., description="Original content brief")
    final: FinalContent = Field(default_factory=FinalContent, description="Generated content")
    state: PipelineState = Field(default=PipelineState.IDLE, description="Current pipeline state")
    created_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = Field(default=None, description="Completion timestamp")
    version: str = Field(default="0.1.0", description="Package version")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
