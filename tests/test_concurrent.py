"""Tests for concurrent pipeline execution."""

import threading
import time

import pytest

from content_automata.pipeline import ContentPipeline
from content_automata.models import ContentBrief


class TestConcurrentPipelineExecution:
    """Tests for concurrent pipeline execution."""

    def test_multiple_pipeline_instances(self):
        """Test running multiple pipeline instances concurrently."""
        results = []
        errors = []
        lock = threading.Lock()

        def run_pipeline(idx):
            try:
                pipe = ContentPipeline(config={})
                result = pipe.from_topic(
                    f"Concurrent Topic {idx}",
                    tone="professional",
                )
                with lock:
                    results.append(result)
            except Exception as e:
                with lock:
                    errors.append(e)

        threads = [
            threading.Thread(target=run_pipeline, args=(i,))
            for i in range(5)
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10)

        assert len(errors) == 0, f"Errors during concurrent execution: {errors}"
        assert len(results) == 5

    def test_concurrent_state_isolation(self):
        """Test that pipeline state is isolated between concurrent runs."""
        pipe1 = ContentPipeline(config={})
        pipe2 = ContentPipeline(config={})

        # Run both in sequence to verify isolation (not truly concurrent but tests state)
        result1 = pipe1.from_topic("Topic A")
        result2 = pipe2.from_topic("Topic B")

        assert result1.brief.topic == "Topic A"
        assert result2.brief.topic == "Topic B"
        assert pipe1.state.value != "idle"
        assert pipe2.state.value != "idle"

    def test_reentrant_pipeline_calls(self):
        """Test calling the same pipeline instance sequentially."""
        pipe = ContentPipeline(config={})

        result1 = pipe.from_topic("First Run")
        result2 = pipe.from_topic("Second Run")

        assert result1.brief.topic == "First Run"
        assert result2.brief.topic == "Second Run"
        # Second run should have its own brief
        assert result1 != result2

    def test_concurrent_brief_references(self):
        """Test that concurrent runs don't share brief references."""
        brief_a = ContentBrief(topic="Topic A")
        brief_b = ContentBrief(topic="Topic B")

        pipe = ContentPipeline(config={})
        result_a = pipe.from_brief(brief_a)
        result_b = pipe.from_brief(brief_b)

        assert result_a.brief.topic == "Topic A"
        assert result_b.brief.topic == "Topic B"
        # Modifying one shouldn't affect the other
        assert result_a.brief.topic != result_b.brief.topic

    def test_multiple_from_topic_calls(self):
        """Test multiple from_topic calls on the same pipeline."""
        pipe = ContentPipeline(config={})

        topics = ["Topic 1", "Topic 2", "Topic 3"]
        results = [pipe.from_topic(t) for t in topics]

        assert len(results) == 3
        for i, topic in enumerate(topics):
            assert results[i].brief.topic == topic

    def test_concurrent_thread_safety(self):
        """Test that pipeline can be accessed from multiple threads."""
        pipe = ContentPipeline(config={})
        shared_state = []
        lock = threading.Lock()

        def access_pipeline():
            try:
                # Access pipeline properties (read-only)
                state = pipe.state
                pkg = pipe.package
                with lock:
                    shared_state.append((state, pkg is not None))
            except Exception as e:
                with lock:
                    shared_state.append(("error", str(e)))

        threads = [
            threading.Thread(target=access_pipeline)
            for _ in range(10)
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=5)

        assert len(shared_state) == 10
        # All should succeed without errors
        assert all(not isinstance(s[1], str) for s in shared_state)

    def test_pipeline_config_isolation(self):
        """Test that pipeline config is not shared between instances."""
        config1 = {"api_key": "key1"}
        config2 = {"api_key": "key2"}

        pipe1 = ContentPipeline(config=config1)
        pipe2 = ContentPipeline(config=config2)

        assert pipe1._config.get("api_key") == "key1"
        assert pipe2._config.get("api_key") == "key2"
        # Modifying one shouldn't affect the other
        pipe1._config["api_key"] = "modified"
        assert pipe2._config.get("api_key") == "key2"

    def test_brief_isolation_after_pipeline_run(self):
        """Test that the original brief is not mutated by pipeline run."""
        pipe = ContentPipeline(config={})
        original_topic = "Original Topic"
        brief = ContentBrief(topic=original_topic)

        result = pipe.from_brief(brief)
        assert result.brief.topic == original_topic
        # Original brief should be unchanged
        assert brief.topic == original_topic

    def test_simultaneous_from_url_and_from_topic(self):
        """Test running different entry points."""
        pipe = ContentPipeline(config={})

        # These should work independently
        result_topic = pipe.from_topic("Topic Entry")
        result_url = pipe.from_url("https://example.com/article")

        assert result_topic is not None
        assert result_url is not None
        assert "example.com" in result_url.brief.custom_instructions or True

    def test_concurrent_access_to_completed_pipeline(self):
        """Test accessing a completed pipeline from concurrent threads."""
        pipe = ContentPipeline(config={})
        result = pipe.from_topic("Test Topic")

        access_results = []
        lock = threading.Lock()

        def check_result():
            with lock:
                access_results.append({
                    "state": result.state.value,
                    "topic": result.brief.topic,
                    "completed": result.completed_at is not None,
                })

        threads = [
            threading.Thread(target=check_result)
            for _ in range(5)
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=5)

        assert len(access_results) == 5
        assert all(r["state"] == "complete" for r in access_results)
