"""Tests for __init__ exports and package structure."""

from content_automata import Pipeline, ContentPipeline, __version__, __all__


class TestPackageExports:
    """Test package __init__ exports."""

    def test_pipeline_exported(self):
        assert Pipeline is ContentPipeline

    def test_version_exported(self):
        assert __version__ == "0.1.0"

    def test_all_imports(self):
        assert "Pipeline" in __all__
        assert "ContentPipeline" in __all__


class TestImportAllModules:
    """Test all modules can be imported."""

    def test_import_alt_text(self):
        from content_automata.alt_text import AltTextGenerator
        assert AltTextGenerator is not None

    def test_import_batch(self):
        from content_automata.batch import BatchProcessor
        assert BatchProcessor is not None

    def test_import_cache(self):
        from content_automata.cache import ContentCache
        assert ContentCache is not None

    def test_import_calendar(self):
        from content_automata.calendar import CalendarPlanner
        assert CalendarPlanner is not None

    def test_import_config(self):
        from content_automata.config import PipelineConfig
        assert PipelineConfig is not None

    def test_import_dryrun(self):
        from content_automata.dryrun import DryRunMode
        assert DryRunMode is not None

    def test_import_exceptions(self):
        from content_automata.exceptions import ContentAutomataError
        assert ContentAutomataError is not None

    def test_import_history(self):
        from content_automata.history import RevisionHistory
        assert RevisionHistory is not None

    def test_import_i18n(self):
        from content_automata.i18n import MultiLanguageGenerator
        assert MultiLanguageGenerator is not None

    def test_import_providers(self):
        from content_automata.providers import ProviderFactory
        assert ProviderFactory is not None

    def test_import_quality(self):
        from content_automata.quality import QualityScorer
        assert QualityScorer is not None

    def test_import_seo(self):
        from content_automata.seo import SEOAnalyzer
        assert SEOAnalyzer is not None

    def test_import_suggestions(self):
        from content_automata.suggestions import SuggestionEngine
        assert SuggestionEngine is not None

    def test_import_templates(self):
        from content_automata.templates import TemplateManager
        assert TemplateManager is not None

    def test_import_variations(self):
        from content_automata.variations import VariationGenerator
        assert VariationGenerator is not None

    def test_import_weights(self):
        from content_automata.weights import ScoringWeights
        assert ScoringWeights is not None

    def test_import_wordpress(self):
        from content_automata.wordpress import WordPressExporter
        assert WordPressExporter is not None

    def test_import_progress(self):
        from content_automata.progress import PipelineProgress
        assert PipelineProgress is not None

    def test_import_all_stages(self):
        from content_automata.stages.base import StageContract
        from content_automata.stages.research import TopicResearch
        from content_automata.stages.copywriter import CopyWriter
        from content_automata.stages.image_gen import ImageGenerator
        from content_automata.stages.scheduler import ContentScheduler
        assert StageContract is not None
        assert TopicResearch is not None
        assert CopyWriter is not None
        assert ImageGenerator is not None
        assert ContentScheduler is not None
