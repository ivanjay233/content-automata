"""Content pipeline orchestrator with state machine."""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from content_automata.models import (
    ContentBrief,
    ContentPackage,
    FinalContent,
    PipelineState,
    ResearchResult,
)
from content_automata.stages.research import TopicResearch
from content_automata.stages.copywriter import CopyWriter
from content_automata.stages.image_gen import ImageGenerator
from content_automata.stages.scheduler import ContentScheduler

logger = logging.getLogger(__name__)


class ContentPipeline:
    """Orchestrates the full content creation pipeline.

    State machine: idle → research → draft → review → visuals → schedule → complete
    """

    def __init__(
        self,
        config: Optional[str | Dict[str, Any]] = None,
        api_key: Optional[str] = None,
        **kwargs,
    ):
        self._config: Dict[str, Any] = {}
        self._package: Optional[ContentPackage] = None
        self._api_key = api_key or kwargs.get("api_key")

        if config:
            if isinstance(config, str):
                path = Path(config)
                if path.exists():
                    with open(path) as f:
                        self._config = yaml.safe_load(f) or {}
            elif isinstance(config, dict):
                self._config = config

        # Merge kwargs into config
        self._config.update(kwargs)

        # Initialize stages
        self.research_stage = TopicResearch(self._config)
        self.copywriter_stage = CopyWriter(self._config)
        self.image_gen_stage = ImageGenerator(self._config)
        self.scheduler_stage = ContentScheduler(self._config)

        logger.info("ContentPipeline initialized")

    @property
    def state(self) -> PipelineState:
        return self._package.state if self._package else PipelineState.IDLE

    @property
    def package(self) -> Optional[ContentPackage]:
        return self._package

    def from_topic(self, topic: str, **kwargs) -> ContentPackage:
        """Run pipeline starting from a topic.

        Args:
            topic: The content topic to research and write about.
            **kwargs: Additional parameters for the content brief.

        Returns:
            A ContentPackage with all pipeline stages executed.
        """
        brief = ContentBrief(topic=topic, **kwargs)
        return self._run(brief)

    def from_url(self, url: str, **kwargs) -> ContentPackage:
        """Run pipeline starting from a URL for research.

        Args:
            url: A URL to extract content and ideas from.
            **kwargs: Additional parameters for the content brief.

        Returns:
            A ContentPackage with all pipeline stages executed.
        """
        brief = ContentBrief(topic=f"Content from {url}", **kwargs)
        brief.custom_instructions = f"Research and expand upon content at: {url}"
        return self._run(brief)

    def from_brief(self, brief: Dict[str, Any] | ContentBrief) -> ContentPackage:
        """Run pipeline from a structured content brief.

        Args:
            brief: A dictionary or ContentBrief with full specifications.

        Returns:
            A ContentPackage with all pipeline stages executed.
        """
        if isinstance(brief, dict):
            brief = ContentBrief(**brief)
        return self._run(brief)

    def _run(self, brief: ContentBrief) -> ContentPackage:
        """Execute the full pipeline: research → draft → review → visuals → schedule."""
        self._package = ContentPackage(brief=brief, state=PipelineState.RESEARCH)
        final = self._package.final

        try:
            # Stage 1: Research
            logger.info(f"Stage 1/4: Research — topic='{brief.topic}'")
            self._package.state = PipelineState.RESEARCH
            research: ResearchResult = self.research_stage.research(brief)
            final.research = research

            # Stage 2: Draft / Copywriting
            logger.info("Stage 2/4: Copywriting")
            self._package.state = PipelineState.DRAFT
            draft = self.copywriter_stage.generate(research, brief)
            final.draft = draft

            # Stage 3: Review (quality checks)
            logger.info("Stage 3/4: Review & Visuals")
            self._package.state = PipelineState.REVIEW

            # Stage 4: Image Generation
            self._package.state = PipelineState.VISUALS
            visuals = self.image_gen_stage.generate(final.draft, brief)
            final.visuals = visuals

            # Stage 5: Schedule & Export
            logger.info("Stage 4/4: Scheduling & Export")
            self._package.state = PipelineState.SCHEDULE
            schedule = self.scheduler_stage.schedule(final, brief)
            final.schedule = schedule

            # Mark complete
            self._package.state = PipelineState.COMPLETE
            self._package.completed_at = datetime.now()
            logger.info("Pipeline complete!")

        except Exception as e:
            self._package.state = PipelineState.ERROR
            self._package.metadata["error"] = str(e)
            logger.error(f"Pipeline failed: {e}")
            raise

        return self._package
