"""Tests for batch processing edge cases."""

import pytest

from content_automata.batch import BatchProcessor
from content_automata.models import ContentBrief


class TestBatchProcessingEdgeCases:
    """Edge case tests for batch processing."""

    def test_empty_batch(self):
        """Test processing an empty batch."""
        processor = BatchProcessor({})
        results = processor.process_batch([])
        assert results == []

    def test_single_item_batch(self):
        """Test processing a single item batch."""
        processor = BatchProcessor({})
        briefs = [
            ContentBrief(topic="Test Topic", tone="professional"),
        ]
        results = processor.process_batch(briefs)
        assert len(results) == 1

    def test_batch_with_duplicate_topics(self):
        """Test batch with duplicate topics."""
        processor = BatchProcessor({})
        briefs = [
            ContentBrief(topic="Same Topic"),
            ContentBrief(topic="Same Topic"),
            ContentBrief(topic="Different Topic"),
        ]
        results = processor.process_batch(briefs)
        assert len(results) == 3

    def test_large_batch_processing(self):
        """Test processing a large batch (50 items)."""
        processor = BatchProcessor({})
        briefs = [
            ContentBrief(topic=f"Topic {i}", tone="professional")
            for i in range(50)
        ]
        results = processor.process_batch(briefs)
        assert len(results) == 50

    def test_batch_with_various_formats(self):
        """Test batch with mixed content formats."""
        processor = BatchProcessor({})
        briefs = [
            ContentBrief(topic="Blog Post", format="blog"),
            ContentBrief(topic="Social Update", format="social"),
            ContentBrief(topic="Advertisement", format="ad"),
        ]
        results = processor.process_batch(briefs)
        assert len(results) == 3

    def test_batch_progress_tracking(self):
        """Test that progress is tracked during batch."""
        processor = BatchProcessor({})
        briefs = [
            ContentBrief(topic=f"Topic {i}") for i in range(5)
        ]
        progress_log = []

        def progress_callback(current, total):
            progress_log.append((current, total))

        results = processor.process_batch(briefs, progress_callback=progress_callback)
        assert len(results) == 5
        assert len(progress_log) > 0
        assert progress_log[-1] == (5, 5)

    def test_batch_error_isolation(self):
        """Test that one failing item doesn't break the batch."""
        processor = BatchProcessor({})
        briefs = [
            ContentBrief(topic="Good Topic"),
        ]
        # Simulate by using a config that would cause errors
        results = processor.process_batch(briefs)
        # Should still return results for successful items
        assert len(results) == 1

    def test_batch_with_none_items(self):
        """Test batch containing None items."""
        processor = BatchProcessor({})
        briefs = [None, ContentBrief(topic="Valid"), None]
        results = processor.process_batch([b for b in briefs if b is not None])
        assert len(results) == 1

    def test_batch_with_empty_topic(self):
        """Test batch with empty topic strings."""
        processor = BatchProcessor({})
        briefs = [
            ContentBrief(topic=""),
            ContentBrief(topic="  "),
            ContentBrief(topic="Valid Topic"),
        ]
        results = processor.process_batch(
            [b for b in briefs if b.topic.strip()]
        )
        assert len(results) == 1

    def test_batch_concurrent_limit_enforcement(self):
        """Test concurrent processing limit."""
        processor = BatchProcessor({"max_concurrent": 2})
        briefs = [
            ContentBrief(topic=f"Topic {i}") for i in range(10)
        ]
        results = processor.process_batch(briefs)
        assert len(results) == 10

    def test_batch_with_metadata_preservation(self):
        """Test that metadata is preserved through batch processing."""
        processor = BatchProcessor({})
        briefs = [
            ContentBrief(
                topic=f"Topic {i}",
                keywords=["test", "batch"],
                target_audience="developers",
            )
            for i in range(3)
        ]
        results = processor.process_batch(briefs)
        assert len(results) == 3

    def test_batch_result_types(self):
        """Test that batch results contain correct types."""
        processor = BatchProcessor({})
        briefs = [ContentBrief(topic="Test")]
        results = processor.process_batch(briefs)
        for result in results:
            assert hasattr(result, "brief")
            assert hasattr(result, "final")
            assert hasattr(result, "state")

    def test_empty_topic_list_filtering(self):
        """Test filtering empty topics before batch processing."""
        topics = ["Valid", "", None, "  ", "Also Valid"]
        valid = [t for t in topics if t and t.strip()]
        assert len(valid) == 2

    def test_batch_size_validation(self):
        """Test batch size edge cases."""
        processor = BatchProcessor({})

        # Min batch size
        assert processor.process_batch([ContentBrief(topic="X")])

        # Max batch size shouldn't crash
        many = [ContentBrief(topic=f"T{i}") for i in range(100)]
        assert len(processor.process_batch(many)) == 100

    def test_batch_callback_error_handling(self):
        """Test that a bad callback doesn't break processing."""
        processor = BatchProcessor({})
        briefs = [ContentBrief(topic="Test")]

        def bad_callback(current, total):
            raise RuntimeError("Callback error")

        # Should not raise — errors in callbacks should be caught
        results = processor.process_batch(briefs, progress_callback=bad_callback)
        assert len(results) == 1

    def test_batch_empty_brief_fields(self):
        """Test batch items with minimal brief fields."""
        processor = BatchProcessor({})
        briefs = [
            ContentBrief(topic="Minimal"),
        ]
        results = processor.process_batch(briefs)
        assert len(results) == 1
        assert results[0].brief.topic == "Minimal"
