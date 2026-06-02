"""Batch processing — run the pipeline for multiple topics in parallel."""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from content_automata import ContentPipeline
from content_automata.models import ContentPackage

logger = logging.getLogger(__name__)


@dataclass
class BatchResult:
    """Result of a batch processing run."""

    total: int
    succeeded: int
    failed: int
    results: Dict[str, ContentPackage] = field(default_factory=dict)
    errors: Dict[str, str] = field(default_factory=dict)
    duration_seconds: float = 0.0


class BatchProcessor:
    """Process multiple content topics in batches.

    Supports parallel execution with configurable concurrency and
    per-item configuration overrides.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self._config = config or {}
        self._max_workers = self._config.get("batch", {}).get("max_workers", 4)

    def run(
        self,
        topics: List[str],
        pipeline_config: Optional[Dict[str, Any]] = None,
        progress_callback: Optional[Callable[[str, str], None]] = None,
    ) -> BatchResult:
        """Run the pipeline for a list of topics.

        Args:
            topics: List of content topics to process.
            pipeline_config: Optional config overrides for all pipelines.
            progress_callback: Optional callback(topic, status) for progress tracking.

        Returns:
            BatchResult with per-topic results and error info.
        """
        import time

        start = time.time()
        result = BatchResult(total=len(topics))

        def process_topic(topic: str) -> tuple[str, ContentPackage | None, str | None]:
            try:
                pipe = ContentPipeline(config=pipeline_config or self._config)
                if progress_callback:
                    progress_callback(topic, "researching")
                package = pipe.from_topic(topic)
                if progress_callback:
                    progress_callback(topic, "complete")
                return topic, package, None
            except Exception as e:
                logger.error(f"Batch topic '{topic}' failed: {e}")
                if progress_callback:
                    progress_callback(topic, "failed")
                return topic, None, str(e)

        with ThreadPoolExecutor(max_workers=self._max_workers) as executor:
            futures = {executor.submit(process_topic, topic): topic for topic in topics}

            for future in as_completed(futures):
                topic, package, error = future.result()
                if error:
                    result.errors[topic] = error
                    result.failed += 1
                else:
                    result.results[topic] = package  # type: ignore
                    result.succeeded += 1

        result.duration_seconds = time.time() - start
        logger.info(
            f"Batch complete: {result.succeeded}/{result.total} succeeded "
            f"in {result.duration_seconds:.1f}s"
        )
        return result
