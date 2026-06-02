"""Content scoring weights configuration module.

Allows customizing how quality scores are calculated by adjusting
the relative importance of each quality dimension.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class ScoringWeights:
    """Configurable weights for quality scoring dimensions.

    Each weight represents the relative importance of a dimension.
    Weights are normalized automatically to sum to 1.0.
    """

    readability: float = 0.20
    seo: float = 0.25
    completeness: float = 0.20
    consistency: float = 0.15
    engagement: float = 0.20

    def __post_init__(self):
        """Normalize weights to ensure they sum to 1.0."""
        total = sum([self.readability, self.seo, self.completeness, self.consistency, self.engagement])
        if total != 1.0 and total > 0:
            scale = 1.0 / total
            self.readability *= scale
            self.seo *= scale
            self.completeness *= scale
            self.consistency *= scale
            self.engagement *= scale

    def to_dict(self) -> Dict[str, float]:
        """Return weights as a dictionary."""
        return {
            "readability": self.readability,
            "seo": self.seo,
            "completeness": self.completeness,
            "consistency": self.consistency,
            "engagement": self.engagement,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, float]) -> "ScoringWeights":
        """Create weights from a dictionary."""
        return cls(
            readability=data.get("readability", 0.20),
            seo=data.get("seo", 0.25),
            completeness=data.get("completeness", 0.20),
            consistency=data.get("consistency", 0.15),
            engagement=data.get("engagement", 0.20),
        )


# Predefined weight presets
WEIGHT_PRESETS: Dict[str, ScoringWeights] = {
    "balanced": ScoringWeights(),
    "seo_focused": ScoringWeights(readability=0.10, seo=0.40, completeness=0.20, consistency=0.10, engagement=0.20),
    "readability_focused": ScoringWeights(readability=0.40, seo=0.15, completeness=0.15, consistency=0.15, engagement=0.15),
    "engagement_focused": ScoringWeights(readability=0.15, seo=0.15, completeness=0.15, consistency=0.15, engagement=0.40),
}
