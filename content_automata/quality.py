"""Content quality scoring module."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from content_automata.models import Draft, ResearchResult

logger = logging.getLogger(__name__)


@dataclass
class QualityScore:
    """Score for a single quality dimension."""

    name: str
    score: float  # 0.0 to 1.0
    weight: float = 1.0
    details: List[str] = field(default_factory=list)
    passed: bool = True


@dataclass
class QualityReport:
    """Complete quality report for generated content."""

    overall_score: float = 0.0
    scores: Dict[str, QualityScore] = field(default_factory=dict)
    strengths: List[str] = field(default_factory=list)
    improvements: List[str] = field(default_factory=list)
    passed_threshold: bool = True


class QualityScorer:
    """Scores content quality across multiple dimensions.

    Dimensions:
    - Readability: Flesch-like reading ease estimation
    - SEO Score: Keyword usage, meta presence, structure
    - Completeness: Sections filled, word count adequacy
    - Consistency: Tone alignment, formatting uniformity
    - Engagement: Headline quality, CTA presence, hooks
    """

    MIN_WORDS_BLOG = 300
    MIN_WORDS_SOCIAL = 50

    def __init__(self, config: Optional[Dict] = None):
        self._config = config or {}
        self._threshold = self._config.get("quality_threshold", 0.6)
        self._weights = self._config.get("quality_weights", {
            "readability": 0.2,
            "seo": 0.25,
            "completeness": 0.2,
            "consistency": 0.15,
            "engagement": 0.2,
        })

    def score(self, draft: Draft, research: ResearchResult) -> QualityReport:
        """Score the quality of generated content.

        Args:
            draft: The generated content draft.
            research: The research data used for generation.

        Returns:
            A QualityReport with dimension scores and recommendations.
        """
        report = QualityReport()

        readability = self._score_readability(draft)
        seo = self._score_seo(draft, research)
        completeness = self._score_completeness(draft, research)
        consistency = self._score_consistency(draft)
        engagement = self._score_engagement(draft)

        report.scores = {
            "readability": readability,
            "seo": seo,
            "completeness": completeness,
            "consistency": consistency,
            "engagement": engagement,
        }

        # Weighted overall score
        total_weight = sum(self._weights.get(k, 0.2) for k in report.scores)
        weighted_sum = sum(
            s.score * self._weights.get(k, 0.2)
            for k, s in report.scores.items()
        )
        report.overall_score = weighted_sum / total_weight if total_weight > 0 else 0.0

        # Collect strengths and improvements
        for name, score in report.scores.items():
            if score.score >= 0.7:
                report.strengths.append(f"Strong {name}: {score.score:.0%}")
            elif score.score < 0.5:
                report.improvements.extend(score.details)

        report.passed_threshold = report.overall_score >= self._threshold
        return report

    def _score_readability(self, draft: Draft) -> QualityScore:
        """Score readability based on sentence/word complexity."""
        details = []
        text = draft.blog_post or ""
        if not text:
            return QualityScore(name="readability", score=0.0, details=["No content to evaluate"], passed=False)

        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        if not sentences:
            return QualityScore(name="readability", score=0.0, details=["No sentences found"], passed=False)

        words = text.split()
        avg_sentence_len = len(words) / len(sentences) if sentences else 0
        long_words = sum(1 for w in words if len(w) > 6)
        long_word_ratio = long_words / len(words) if words else 0

        # Score: shorter sentences and fewer long words = more readable
        len_score = max(0, 1.0 - (avg_sentence_len - 10) / 30) if avg_sentence_len > 10 else 1.0
        complex_score = max(0, 1.0 - long_word_ratio * 3)

        score = (len_score * 0.6 + complex_score * 0.4)

        if avg_sentence_len > 25:
            details.append("Sentences are too long (avg > 25 words)")
        if long_word_ratio > 0.3:
            details.append("High ratio of complex words (>6 letters)")

        return QualityScore(name="readability", score=score, details=details)

    def _score_seo(self, draft: Draft, research: ResearchResult) -> QualityScore:
        """Score SEO optimization."""
        details = []
        score = 0.0
        checks = 0

        # Meta description
        if draft.meta_description and len(draft.meta_description) >= 50:
            score += 0.25
            checks += 1
        elif draft.meta_description:
            details.append("Meta description is too short (< 50 chars)")

        # Headline
        if draft.headline:
            hl_len = len(draft.headline.split())
            if 5 <= hl_len <= 15:
                score += 0.25
            else:
                details.append(f"Headline length ({hl_len} words) outside optimal range (5-15)")
            checks += 1
        else:
            details.append("No headline provided")

        # Keyword in content
        if research.key_points and draft.blog_post:
            topic_words = research.topic.lower().split()
            body_lower = draft.blog_post.lower()
            found = sum(1 for w in topic_words if w in body_lower)
            if found >= len(topic_words) * 0.5:
                score += 0.25
            else:
                details.append("Topic keywords not sufficiently used in content")
            checks += 1
        else:
            checks += 1  # neutral

        # Content structure (headings)
        if draft.blog_post:
            has_headings = bool(re.search(r'^#{1,3}\s', draft.blog_post, re.MULTILINE))
            if has_headings:
                score += 0.25
            else:
                details.append("No headings found in content")
            checks += 1
        else:
            checks += 1

        final_score = score / checks if checks > 0 else 0.0
        return QualityScore(name="seo", score=final_score, details=details)

    def _score_completeness(self, draft: Draft, research: ResearchResult) -> QualityScore:
        """Score content completeness."""
        details = []
        score = 0.0
        checks = 0

        # Word count adequacy
        if draft.blog_post:
            min_words = self.MIN_WORDS_BLOG
            if draft.word_count >= min_words:
                score += 0.3
            elif draft.word_count >= min_words * 0.5:
                score += 0.15
                details.append(f"Blog post below minimum word count ({draft.word_count} < {min_words})")
            else:
                details.append(f"Blog post far below minimum ({draft.word_count} < {min_words})")
            checks += 1

        # Social copy
        if draft.social_copy:
            score += 0.15
        else:
            details.append("No social media copy generated")
        checks += 1

        # Ad copy
        if draft.ad_copy:
            score += 0.15
        else:
            details.append("No ad copy generated")
        checks += 1

        # Research usage
        if research.key_points and len(research.key_points) >= 3:
            score += 0.2
        else:
            details.append("Insufficient research key points")
        checks += 1

        # Meta description
        if draft.meta_description:
            score += 0.2
        else:
            details.append("No meta description")
        checks += 1

        final_score = score / checks if checks > 0 else 0.0
        return QualityScore(name="completeness", score=final_score, details=details)

    def _score_consistency(self, draft: Draft) -> QualityScore:
        """Score content consistency."""
        details = []
        score = 0.5  # start neutral

        # Check tone consistency
        if draft.blog_post and draft.social_copy:
            # Simple heuristic: if both exist, they should have similar reading level
            blog_words = draft.blog_post.split()
            social_words = draft.social_copy.split()
            if blog_words and social_words:
                ratio = len(blog_words) / max(len(social_words), 1)
                if 5 <= ratio <= 50:
                    score += 0.25
                else:
                    details.append("Large length discrepancy between blog and social copy")

        # Check formatting consistency (if multiple variants exist)
        if draft.blog_post and draft.ad_copy:
            score += 0.25

        return QualityScore(name="consistency", score=min(1.0, score), details=details)

    def _score_engagement(self, draft: Draft) -> QualityScore:
        """Score content engagement potential."""
        details = []
        score = 0.0
        checks = 0

        text = (draft.blog_post or "") + " " + (draft.social_copy or "")

        # CTA presence
        cta_indicators = ["sign up", "subscribe", "learn more", "get started", "download", "contact", "read more"]
        if any(cta in text.lower() for cta in cta_indicators):
            score += 0.25
        else:
            details.append("No call-to-action detected")
        checks += 1

        # Question hooks
        if "?" in text:
            score += 0.2
        else:
            details.append("No questions used as engagement hooks")
        checks += 1

        # Emotional language
        emotional_words = ["amazing", "incredible", "essential", "critical", "transform", "revolutionary", "game-changing", "breakthrough"]
        found_emotional = sum(1 for w in emotional_words if w in text.lower())
        if found_emotional >= 2:
            score += 0.3
        elif found_emotional >= 1:
            score += 0.15
        else:
            details.append("No emotional or compelling language detected")
        checks += 1

        # Headline quality
        if draft.headline:
            hl_words = len(draft.headline.split())
            if 6 <= hl_words <= 12:
                score += 0.25
            elif hl_words > 0:
                score += 0.1
        checks += 1

        final_score = score / checks if checks > 0 else 0.0
        return QualityScore(name="engagement", score=final_score, details=details)
