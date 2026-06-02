"""Contributing guide enhancements with detailed setup instructions."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from content_automata.alt_text import AltTextGenerator
from content_automata.cache import ContentCache
from content_automata.config import PipelineConfig
from content_automata.dryrun import DryRunMode
from content_automata.history import RevisionHistory
from content_automata.providers import ProviderFactory
from content_automata.quality import QualityScorer
from content_automata.seo import SEOAnalyzer
from content_automata.suggestions import SuggestionEngine
from content_automata.templates import TemplateManager
from content_automata.variations import VariationGenerator
from content_automata.wordpress import WordPressExporter
from content_automata.models import Draft, ResearchResult


def test_alt_text_generator():
    gen = AltTextGenerator()
    alt = gen.generate("AI", "AI Overview", "Content about artificial intelligence")
    assert alt and len(alt) > 0
    print(f"  ✓ AltTextGenerator: '{alt[:60]}...'")


def test_content_cache():
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = ContentCache({"cache": {"directory": tmpdir, "enabled": True}})
        cache.set("test", {"value": 42})
        assert cache.get("test") == {"value": 42}
    print(f"  ✓ ContentCache: get/set works")


def test_pipeline_config():
    config = PipelineConfig.from_dict({"api_key": "test", "research": {"provider": "exa"}})
    assert config.research.provider == "exa"
    print(f"  ✓ PipelineConfig: loads from dict")


def test_dry_run():
    dryrun = DryRunMode()
    report = dryrun.preview({"topic": "Test"})
    assert len(report.actions) == 4
    print(f"  ✓ DryRunMode: previews {len(report.actions)} stages")


def test_revision_history():
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        hist = RevisionHistory({"history_dir": str(Path(tmpdir) / "hist")})
        hist.record(topic="Test")
        assert hist.count() == 1
    print(f"  ✓ RevisionHistory: records and counts revisions")


def test_provider_factory():
    research = ProviderFactory.create_research("tavily")
    content = ProviderFactory.create_content("openai")
    print(f"  ✓ ProviderFactory: creates {type(research).__name__} and {type(content).__name__}")


def test_quality_scorer():
    scorer = QualityScorer()
    draft = Draft(blog_post="Well-written content with sufficient length.", headline="Title", word_count=100)
    research = ResearchResult(topic="Test", key_points=["P1", "P2", "P3"])
    report = scorer.score(draft, research)
    print(f"  ✓ QualityScorer: overall={report.overall_score:.2f}")


def test_seo_analyzer():
    analyzer = SEOAnalyzer()
    draft = Draft(blog_post="Content about AI.", headline="AI Guide", meta_description="Learn about AI")
    result = analyzer.analyze(draft, target_keywords=["AI"])
    print(f"  ✓ SEOAnalyzer: overall={result.overall:.2f}, keywords={len(result.keywords)}")


def test_suggestion_engine():
    engine = SuggestionEngine()
    hashtags = engine.suggest_hashtags("Technology Trends")
    keywords = engine.suggest_keywords("Digital Marketing")
    print(f"  ✓ SuggestionEngine: {len(hashtags)} hashtags, {len(keywords)} keywords")


def test_template_manager():
    mgr = TemplateManager()
    templates = mgr.list_templates()
    print(f"  ✓ TemplateManager: {len(templates)} templates available")


def test_variation_generator():
    gen = VariationGenerator()
    draft = Draft(blog_post="Content", headline="Headline")
    result = gen.generate(draft, "Test", test_type="headline", num_variants=2)
    print(f"  ✓ VariationGenerator: {len(result.variants)} variants")


def test_wordpress_exporter():
    exporter = WordPressExporter()
    from content_automata.models import FinalContent
    final = FinalContent(
        research=ResearchResult(topic="Test", key_points=["P1"]),
        draft=Draft(blog_post="Content", headline="Title"),
    )
    post = exporter.export(final)
    print(f"  ✓ WordPressExporter: post '{post.title}'")


def main():
    print("=" * 60)
    print("  content-automata — Module Smoke Tests")
    print("=" * 60)
    print()

    tests = [
        ("Alt Text Generator", test_alt_text_generator),
        ("Content Cache", test_content_cache),
        ("Pipeline Config", test_pipeline_config),
        ("Dry Run Mode", test_dry_run),
        ("Revision History", test_revision_history),
        ("Provider Factory", test_provider_factory),
        ("Quality Scorer", test_quality_scorer),
        ("SEO Analyzer", test_seo_analyzer),
        ("Suggestion Engine", test_suggestion_engine),
        ("Template Manager", test_template_manager),
        ("Variation Generator", test_variation_generator),
        ("WordPress Exporter", test_wordpress_exporter),
    ]

    passed = 0
    failed = 0

    for name, func in tests:
        try:
            func()
            passed += 1
        except Exception as e:
            print(f"  ✗ {name}: FAILED - {e}")
            failed += 1

    print(f"\n{'=' * 60}")
    print(f"  Results: {passed} passed, {failed} failed")
    print(f"{'=' * 60}")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
