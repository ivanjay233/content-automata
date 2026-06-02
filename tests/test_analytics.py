"""Tests for content analytics module."""

import pytest
import tempfile
from pathlib import Path

from content_automata.analytics import ContentAnalytics, ContentStats
from content_automata.history import RevisionHistory


class TestContentAnalytics:
    """Test ContentAnalytics."""

    def test_compute_stats_empty(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config = {"history_dir": str(Path(tmpdir) / "hist")}
            analytics = ContentAnalytics(config)
            stats = analytics.compute_stats(days=30)
            assert stats.total_runs == 0
            assert stats.total_words == 0

    def test_compute_stats_with_data(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            hist_dir = str(Path(tmpdir) / "hist")
            hist = RevisionHistory({"history_dir": hist_dir})
            hist.record(topic="Topic A", word_count=500, tone="professional", num_images=2)
            hist.record(topic="Topic B", word_count=300, tone="casual", num_images=1)
            hist.record(topic="Topic C", word_count=700, tone="professional", num_images=3)

            analytics = ContentAnalytics({"history_dir": hist_dir})
            stats = analytics.compute_stats(days=30)
            assert stats.total_runs == 3
            assert stats.total_words == 1500
            assert stats.total_images == 6
            assert abs(stats.avg_word_count - 500.0) < 0.1

    def test_top_topics(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            hist_dir = str(Path(tmpdir) / "hist")
            hist = RevisionHistory({"history_dir": hist_dir})
            hist.record(topic="AI", word_count=100)
            hist.record(topic="AI", word_count=200)
            hist.record(topic="ML", word_count=150)

            analytics = ContentAnalytics({"history_dir": hist_dir})
            stats = analytics.compute_stats()
            assert "AI" in stats.top_topics

    def test_word_count_trend(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            hist_dir = str(Path(tmpdir) / "hist")
            hist = RevisionHistory({"history_dir": hist_dir})
            hist.record(topic="T1", word_count=100)
            hist.record(topic="T2", word_count=200)

            analytics = ContentAnalytics({"history_dir": hist_dir})
            trend = analytics.word_count_trend()
            assert len(trend) > 0
            assert "date" in trend[0]
            assert "words" in trend[0]
            assert "runs" in trend[0]

    def test_content_stats_dataclass(self):
        stats = ContentStats(
            total_runs=10,
            total_words=5000,
            avg_word_count=500.0,
        )
        assert stats.total_runs == 10
        assert stats.avg_word_count == 500.0
