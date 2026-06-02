"""Tests for scoring weights and configuration presets."""

import pytest

from content_automata.weights import ScoringWeights, WEIGHT_PRESETS


class TestScoringWeights:
    """Test ScoringWeights dataclass."""

    def test_default_weights(self):
        w = ScoringWeights()
        assert abs(w.readability - 0.20) < 0.001
        assert abs(w.seo - 0.25) < 0.001

    def test_normalization(self):
        w = ScoringWeights(readability=1.0, seo=1.0, completeness=1.0, consistency=1.0, engagement=1.0)
        total = w.readability + w.seo + w.completeness + w.consistency + w.engagement
        assert abs(total - 1.0) < 0.001

    def test_custom_weights(self):
        w = ScoringWeights(readability=0.5, seo=0.5, completeness=0.0, consistency=0.0, engagement=0.0)
        total = w.readability + w.seo
        assert abs(total - 1.0) < 0.001

    def test_to_dict(self):
        w = ScoringWeights()
        d = w.to_dict()
        assert "readability" in d
        assert "seo" in d

    def test_from_dict(self):
        w = ScoringWeights.from_dict({"readability": 0.3, "seo": 0.3})
        assert abs(w.readability - 0.30) < 0.01

    def test_from_dict_partial(self):
        w = ScoringWeights.from_dict({"readability": 0.5})
        assert w.readability == 0.5
        assert abs(w.seo - 0.25) < 0.01  # default

    def test_presets_exist(self):
        assert "balanced" in WEIGHT_PRESETS
        assert "seo_focused" in WEIGHT_PRESETS
        assert "readability_focused" in WEIGHT_PRESETS
        assert "engagement_focused" in WEIGHT_PRESETS

    def test_preset_weights_normalized(self):
        for name, preset in WEIGHT_PRESETS.items():
            total = preset.readability + preset.seo + preset.completeness + preset.consistency + preset.engagement
            assert abs(total - 1.0) < 0.001, f"Preset '{name}' not normalized: {total}"

    def test_seo_focused_preset(self):
        w = WEIGHT_PRESETS["seo_focused"]
        assert w.seo > w.readability
        assert w.seo > w.engagement
