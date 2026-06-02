"""Content variation generation for A/B testing."""

from __future__ import annotations

import logging
import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from content_automata.models import Draft

logger = logging.getLogger(__name__)


@dataclass
class ContentVariant:
    """A single content variant for A/B testing."""

    variant_id: str
    label: str
    headline: str
    body: str
    cta: str
    tone: str
    adjustments: Dict[str, str] = field(default_factory=dict)


@dataclass
class VariationSet:
    """Set of content variations for A/B testing."""

    control: ContentVariant
    variants: List[ContentVariant] = field(default_factory=list)
    test_type: str = "headline"  # headline, body, cta, full


class VariationGenerator:
    """Generates content variations for A/B testing.

    Creates multiple versions of content by varying headline,
    tone, structure, and calls-to-action.
    """

    HEADLINE_PATTERNS = [
        "question",      # "Are You Ready for {topic}?"
        "how_to",        # "How to Master {topic} in 2026"
        "list",          # "10 {topic} Strategies That Work"
        "benefit",       # "Transform Your {industry} with {topic}"
        "urgent",        # "Why {topic} Matters Now More Than Ever"
        "controversial", # "The Truth About {topic} Nobody Tells You"
        "ultimate",      # "The Ultimate {topic} Guide for Beginners"
        "statistic",     # "{number}% of Businesses Are Adopting {topic}"
    ]

    CTA_VARIATIONS = [
        "Get Started Today",
        "Learn More Now",
        "Join the Movement",
        "Start Your Journey",
        "Unlock Your Potential",
        "Claim Your Free Guide",
        "Schedule a Demo",
        "Subscribe for Updates",
    ]

    def __init__(self, config: Optional[Dict] = None):
        self._config = config or {}
        self._num_variants = self._config.get("num_variants", 3)

    def generate(
        self,
        draft: Draft,
        topic: str,
        test_type: str = "headline",
        num_variants: int | None = None,
    ) -> VariationSet:
        """Generate content variations for A/B testing.

        Args:
            draft: The original content draft (control).
            topic: The content topic.
            test_type: Type of variation ('headline', 'body', 'cta', 'full').
            num_variants: Number of variants to generate.

        Returns:
            VariationSet with control and variant content.
        """
        n = num_variants or self._num_variants
        variations: List[ContentVariant] = []

        control = ContentVariant(
            variant_id="control",
            label="Control (Original)",
            headline=draft.headline or topic,
            body=draft.blog_post or "",
            cta="Learn More",
            tone=draft.tone,
        )

        for i in range(n):
            vid = f"variant-{i + 1}"

            if test_type == "headline":
                variant = self._vary_headline(control, topic, i)
            elif test_type == "cta":
                variant = self._vary_cta(control, topic, i)
            elif test_type == "body":
                variant = self._vary_body(control, topic, i)
            else:
                variant = self._vary_full(control, topic, i)

            variant.variant_id = vid
            variations.append(variant)

        return VariationSet(
            control=control,
            variants=variations,
            test_type=test_type,
        )

    def _vary_headline(self, control: ContentVariant, topic: str, index: int) -> ContentVariant:
        pattern = self.HEADLINE_PATTERNS[index % len(self.HEADLINE_PATTERNS)]
        headline = self._apply_headline_pattern(pattern, topic)
        return ContentVariant(
            variant_id=f"headline-{pattern}",
            label=f"Headline: {pattern.replace('_', ' ').title()}",
            headline=headline,
            body=control.body,
            cta=control.cta,
            tone=control.tone,
            adjustments={"pattern": pattern},
        )

    def _vary_cta(self, control: ContentVariant, topic: str, index: int) -> ContentVariant:
        cta = self.CTA_VARIATIONS[index % len(self.CTA_VARIATIONS)]
        return ContentVariant(
            variant_id=f"cta-{index}",
            label=f"CTA: {cta}",
            headline=control.headline,
            body=control.body,
            cta=cta,
            tone=control.tone,
            adjustments={"cta": cta},
        )

    def _vary_body(self, control: ContentVariant, topic: str, index: int) -> ContentVariant:
        """Create a body variation by restructuring paragraphs."""
        body = control.body
        paragraphs = [p.strip() for p in body.split("\n\n") if p.strip()]

        if index % 2 == 0 and len(paragraphs) > 2:
            # Reorder paragraphs
            reordered = [paragraphs[0]]  # Keep intro
            middle = paragraphs[1:-1]
            random.shuffle(middle)
            reordered.extend(middle)
            reordered.append(paragraphs[-1])  # Keep conclusion
            body = "\n\n".join(reordered)

        return ContentVariant(
            variant_id=f"body-{index}",
            label=f"Body: Restructured v{index + 1}",
            headline=control.headline,
            body=body,
            cta=control.cta,
            tone=control.tone,
            adjustments={"restructured": "true"},
        )

    def _vary_full(self, control: ContentVariant, topic: str, index: int) -> ContentVariant:
        """Create a full variation with different headline and CTA."""
        pattern = self.HEADLINE_PATTERNS[(index + 2) % len(self.HEADLINE_PATTERNS)]
        headline = self._apply_headline_pattern(pattern, topic)
        cta = self.CTA_VARIATIONS[(index + 3) % len(self.CTA_VARIATIONS)]
        return ContentVariant(
            variant_id=f"full-{index}",
            label=f"Full: {pattern.replace('_', ' ').title()}",
            headline=headline,
            body=control.body,
            cta=cta,
            tone=control.tone,
            adjustments={"pattern": pattern, "cta": cta},
        )

    def _apply_headline_pattern(self, pattern: str, topic: str) -> str:
        """Generate a headline following a specific pattern."""
        templates = {
            "question": f"Are You Ready for {topic}?",
            "how_to": f"How to Master {topic} in 2026",
            "list": f"10 {topic} Strategies That Actually Work",
            "benefit": f"Transform Your Results with {topic}",
            "urgent": f"Why {topic} Matters Now More Than Ever",
            "controversial": f"The Truth About {topic} Nobody Tells You",
            "ultimate": f"The Ultimate {topic} Guide for Beginners",
            "statistic": f"73% of Businesses Are Adopting {topic} — Here's Why",
        }
        return templates.get(pattern, f"Everything About {topic}")
