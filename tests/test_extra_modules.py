"""Tests for caching, alt-text, variations, dryrun, history, wordpress modules."""

import pytest
import tempfile
from pathlib import Path

from content_automata.cache import ContentCache
from content_automata.alt_text import AltTextGenerator
from content_automata.variations import VariationGenerator
from content_automata.dryrun import DryRunMode
from content_automata.history import RevisionHistory
from content_automata.models import Draft, ResearchResult


# ── Cache Tests ──

class TestContentCache:
    def test_cache_get_set(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = ContentCache({"cache": {"directory": tmpdir, "enabled": True}})
            cache.set("test_key", {"data": "value"}, ttl=3600)
            result = cache.get("test_key")
            assert result is not None
            assert result["data"] == "value"

    def test_cache_miss(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = ContentCache({"cache": {"directory": tmpdir, "enabled": True}})
            result = cache.get("nonexistent_key")
            assert result is None

    def test_cache_disabled(self):
        cache = ContentCache({"cache": {"enabled": False}})
        cache.set("key", "value")
        assert cache.get("key") is None

    def test_cache_clear(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = ContentCache({"cache": {"directory": tmpdir, "enabled": True}})
            cache.set("key1", "value1")
            cache.set("key2", "value2")
            cache.clear()
            assert cache.get("key1") is None
            assert cache.get("key2") is None

    def test_cache_invalidate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = ContentCache({"cache": {"directory": tmpdir, "enabled": True}})
            cache.set("key", "value")
            cache.invalidate("key")
            assert cache.get("key") is None

    def test_cache_stats(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = ContentCache({"cache": {"directory": tmpdir, "enabled": True}})
            stats = cache.stats()
            assert "enabled" in stats
            assert stats["enabled"] is True


# ── Alt Text Tests ──

class TestAltTextGenerator:
    def test_generate_with_topic(self):
        gen = AltTextGenerator()
        alt = gen.generate("AI Technology", "The Future of AI")
        assert "AI" in alt or "future" in alt.lower()

    def test_generate_with_prompt(self):
        gen = AltTextGenerator()
        alt = gen.generate("Tech", "Tech Trends", image_prompt="Modern office with digital elements")
        assert len(alt) > 0

    def test_generate_with_content(self):
        gen = AltTextGenerator()
        alt = gen.generate("Test", "Headline", content_snippet="This is a meaningful sentence about the topic.")
        assert len(alt) > 0

    def test_generate_bulk(self):
        gen = AltTextGenerator()
        alts = gen.generate_bulk("Tech", "Tech Trends", ["Prompt 1", "Prompt 2"])
        assert len(alts) == 2

    def test_generate_max_length(self):
        gen = AltTextGenerator({"alt_text_max_length": 50})
        alt = gen.generate("Very Long Topic Name Here", "Very Long Headline That Goes On And On And On")
        assert len(alt) <= 50


# ── Variation Tests ──

class TestVariationGenerator:
    def test_generate_headline_variants(self):
        gen = VariationGenerator()
        draft = Draft(blog_post="Content", headline="Original Headline")
        result = gen.generate(draft, "Test Topic", test_type="headline", num_variants=2)
        assert len(result.variants) == 2
        assert result.control.headline == "Original Headline"

    def test_generate_cta_variants(self):
        gen = VariationGenerator()
        draft = Draft(blog_post="Content", headline="Headline")
        result = gen.generate(draft, "Test", test_type="cta", num_variants=3)
        assert len(result.variants) == 3

    def test_generate_full_variants(self):
        gen = VariationGenerator()
        draft = Draft(blog_post="Content", headline="Headline")
        result = gen.generate(draft, "Test", test_type="full", num_variants=2)
        assert len(result.variants) == 2

    def test_variants_have_unique_ids(self):
        gen = VariationGenerator()
        draft = Draft(blog_post="Content", headline="Headline")
        result = gen.generate(draft, "Test", num_variants=3)
        ids = [v.variant_id for v in result.variants]
        assert len(ids) == len(set(ids))


# ── Dry Run Tests ──

class TestDryRunMode:
    def test_preview_from_string(self):
        dryrun = DryRunMode()
        report = dryrun.preview({"topic": "Test Topic"})
        assert report.topic == "Test Topic"
        assert len(report.actions) > 0

    def test_preview_includes_all_stages(self):
        dryrun = DryRunMode()
        report = dryrun.preview({"topic": "Test"})
        stages = [a.stage for a in report.actions]
        assert "research" in stages
        assert "copywriting" in stages
        assert "image_gen" in stages
        assert "scheduling" in stages

    def test_preview_cost_estimate(self):
        dryrun = DryRunMode()
        report = dryrun.preview({"topic": "Test"})
        assert "$" in report.total_estimated_cost

    def test_preview_api_calls(self):
        dryrun = DryRunMode()
        report = dryrun.preview({"topic": "Test"})
        assert report.api_calls > 0

    def test_to_markdown(self):
        dryrun = DryRunMode()
        report = dryrun.preview({"topic": "Test"})
        md = dryrun.to_markdown(report)
        assert "Dry Run Report" in md
        assert "Actions" in md


# ── Revision History Tests ──

class TestRevisionHistory:
    def test_record_revision(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            hist = RevisionHistory({"history_dir": str(Path(tmpdir) / "history")})
            entry = hist.record(topic="Test Topic", word_count=500, tone="professional")
            assert entry.version.startswith("v1")

    def test_list_revisions(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            hist = RevisionHistory({"history_dir": str(Path(tmpdir) / "history")})
            hist.record(topic="Topic 1")
            hist.record(topic="Topic 2")
            revisions = hist.list_revisions()
            assert len(revisions) == 2

    def test_get_revision(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            hist = RevisionHistory({"history_dir": str(Path(tmpdir) / "history")})
            entry = hist.record(topic="Test")
            retrieved = hist.get_revision(entry.version)
            assert retrieved is not None
            assert retrieved.topic == "Test"

    def test_get_latest(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            hist = RevisionHistory({"history_dir": str(Path(tmpdir) / "history")})
            hist.record(topic="First")
            hist.record(topic="Latest")
            latest = hist.get_latest()
            assert latest is not None
            assert latest.topic == "Latest"

    def test_count(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            hist = RevisionHistory({"history_dir": str(Path(tmpdir) / "history")})
            assert hist.count() == 0
            hist.record(topic="T1")
            hist.record(topic="T2")
            hist.record(topic="T3")
            assert hist.count() == 3

    def test_clear(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            hist = RevisionHistory({"history_dir": str(Path(tmpdir) / "history")})
            hist.record(topic="Test")
            hist.clear()
            assert hist.count() == 0

    def test_export_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            hist = RevisionHistory({"history_dir": str(Path(tmpdir) / "history")})
            hist.record(topic="Test")
            json_str = hist.export_json()
            assert "version" in json_str
            assert "Test" in json_str
