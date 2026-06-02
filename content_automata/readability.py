"""Reading time and content complexity scoring.

Estimates reading time based on average reading speeds and
computes complexity scores using lexical diversity, sentence
structure, and readability metrics.
"""

from __future__ import annotations

import logging
import math
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from content_automata.models import Draft

logger = logging.getLogger(__name__)

# Average reading speeds (words per minute) by content type
READING_SPEEDS: Dict[str, int] = {
    "blog": 238,      # Average adult reading speed
    "social": 300,    # Faster scan reading for social media
    "ad": 250,        # Moderate for ad copy
    "newsletter": 220, # Slightly slower for detailed reading
    "technical": 200,  # Technical content requires slower reading
    "default": 238,
}

# Complexity thresholds
COMPLEXITY_RANGES = {
    "very_easy": (0.0, 30.0),
    "easy": (30.0, 50.0),
    "moderate": (50.0, 60.0),
    "fairly_difficult": (60.0, 70.0),
    "difficult": (70.0, 80.0),
    "very_difficult": (80.0, 100.0),
}


@dataclass
class ReadingTime:
    """Estimated reading time information."""

    minutes: int
    seconds: int
    word_count: int
    reading_speed_wpm: int
    formatted: str = ""
    content_type: str = "default"

    def __post_init__(self) -> None:
        if not self.formatted:
            if self.minutes == 0:
                self.formatted = f"{self.seconds}s"
            elif self.minutes == 1:
                self.formatted = f"{self.minutes} min {self.seconds}s"
            else:
                self.formatted = f"{self.minutes} min {self.seconds}s"


@dataclass
class ComplexityScore:
    """Content complexity and readability metrics."""

    flesch_score: float = 0.0
    flesch_level: str = "standard"
    avg_sentence_length: float = 0.0
    avg_word_length: float = 0.0
    lexical_diversity: float = 0.0
    complex_word_ratio: float = 0.0
    passive_voice_count: int = 0
    long_sentence_count: int = 0
    compound_score: float = 0.0
    level: str = "moderate"
    details: Dict[str, str] = field(default_factory=dict)


class ReadingTimeEstimator:
    """Estimates reading time for content.

    Uses configurable reading speeds per content type
    and accounts for images, lists, and code blocks.
    """

    def __init__(self, config: Optional[dict] = None):
        self._config = config or {}
        self._speeds = {**READING_SPEEDS, **self._config.get("speeds", {})}

    def estimate(
        self,
        text: str,
        content_type: str = "blog",
        image_count: int = 0,
    ) -> ReadingTime:
        """Estimate reading time for the given text.

        Args:
            text: The content text to analyze.
            content_type: Type of content (blog, social, ad, etc.).
            image_count: Number of images (adds ~12s each).

        Returns:
            ReadingTime with estimated duration.
        """
        word_count = len(text.split())
        speed = self._speeds.get(content_type, self._speeds["default"])

        # Base reading time
        minutes_raw = word_count / speed * 1.0

        # Add time for images (~12 seconds each)
        image_time = image_count * 12 / 60.0

        # Add time for code blocks and lists (~10% extra)
        code_blocks = len(re.findall(r'```.*?```', text, re.DOTALL))
        lists = len(re.findall(r'^\s*[-*+]\s', text, re.MULTILINE))
        format_bonus = (code_blocks * 15 + lists * 5) / 60.0

        total_minutes = minutes_raw + image_time + format_bonus
        total_seconds = int(total_minutes * 60)
        minutes = total_seconds // 60
        seconds = total_seconds % 60

        return ReadingTime(
            minutes=minutes,
            seconds=seconds,
            word_count=word_count,
            reading_speed_wpm=speed,
            content_type=content_type,
        )

    def estimate_from_draft(
        self,
        draft: Draft,
        content_type: str = "blog",
    ) -> Dict[str, ReadingTime]:
        """Estimate reading time for all draft variants.

        Args:
            draft: Content draft with multiple variants.
            content_type: Content type for speed selection.

        Returns:
            Dict mapping variant names to ReadingTime estimates.
        """
        estimates: Dict[str, ReadingTime] = {}

        if draft.blog_post:
            img_count = 0
            estimates["blog_post"] = self.estimate(
                draft.blog_post, content_type, img_count
            )

        if draft.social_copy:
            estimates["social_copy"] = self.estimate(
                draft.social_copy, "social", 0
            )

        if draft.ad_copy:
            estimates["ad_copy"] = self.estimate(
                draft.ad_copy, "ad", 0
            )

        return estimates


class ComplexityAnalyzer:
    """Analyzes content complexity and readability.

    Computes:
    - Flesch Reading Ease score
    - Average sentence and word length
    - Lexical diversity (unique word ratio)
    - Complex word ratio (3+ syllables)
    - Passive voice detection
    - Overall compound complexity score
    """

    def __init__(self, config: Optional[dict] = None):
        self._config = config or {}

    def analyze(self, text: str, title: str = "") -> ComplexityScore:
        """Analyze content complexity.

        Args:
            text: The content text to analyze.
            title: Optional title (excluded from analysis).

        Returns:
            ComplexityScore with all metrics.
        """
        if not text:
            return ComplexityScore()

        # Remove title from analysis if present
        if title and text.startswith(title):
            text = text[len(title):]

        # Basic metrics
        sentences = self._split_sentences(text)
        words = text.split()
        total_sentences = len(sentences)
        total_words = len(words)

        if total_words == 0 or total_sentences == 0:
            return ComplexityScore()

        # Average sentence length
        avg_sentence_length = total_words / max(total_sentences, 1)

        # Average word length (in syllables)
        total_syllables = sum(self._count_syllables(w) for w in words)
        avg_word_length = total_syllables / max(total_words, 1)

        # Lexical diversity
        unique_words = set(w.lower().strip(".,!?;:\"'()[]{}") for w in words)
        lexical_diversity = len(unique_words) / max(total_words, 1)

        # Complex word ratio (3+ syllables)
        complex_words = sum(1 for w in words if self._count_syllables(w) >= 3)
        complex_word_ratio = complex_words / max(total_words, 1)

        # Flesch Reading Ease score
        flesch_score = self._compute_flesch(total_syllables, total_words, total_sentences)

        # Passive voice detection
        passive_count = self._count_passive_voice(text)

        # Long sentences (>30 words)
        long_sentences = sum(1 for s in sentences if len(s.split()) > 30)

        # Compound score (normalized 0-100)
        compound_score = self._compute_compound_score(
            flesch_score=flesch_score,
            lexical_diversity=lexical_diversity,
            complex_word_ratio=complex_word_ratio,
            avg_sentence_length=avg_sentence_length,
        )

        # Determine level
        level = self._classify_level(compound_score)

        return ComplexityScore(
            flesch_score=round(flesch_score, 2),
            flesch_level=self._classify_flesch(flesch_score),
            avg_sentence_length=round(avg_sentence_length, 1),
            avg_word_length=round(avg_word_length, 2),
            lexical_diversity=round(lexical_diversity, 3),
            complex_word_ratio=round(complex_word_ratio, 3),
            passive_voice_count=passive_count,
            long_sentence_count=long_sentences,
            compound_score=round(compound_score, 1),
            level=level,
            details={
                "total_sentences": str(total_sentences),
                "total_words": str(total_words),
                "unique_words": str(len(unique_words)),
                "complex_words": str(complex_words),
                "syllable_count": str(total_syllables),
            },
        )

    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences.

        Args:
            text: Input text.

        Returns:
            List of sentence strings.
        """
        # Basic sentence splitting
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]

    def _count_syllables(self, word: str) -> int:
        """Estimate syllable count for a word.

        Uses a simple heuristic based on vowel groups.

        Args:
            word: Input word.

        Returns:
            Estimated syllable count.
        """
        word = word.lower().strip(".,!?;:\"'()[]{}")
        if not word:
            return 0

        # Common exceptions (silent e, etc.)
        if word.endswith("e") and len(word) > 2:
            word = word[:-1]

        # Count vowel groups
        vowels = "aeiouy"
        count = 0
        prev_vowel = False
        for char in word:
            is_vowel = char in vowels
            if is_vowel and not prev_vowel:
                count += 1
            prev_vowel = is_vowel

        return max(1, count)

    def _compute_flesch(
        self,
        total_syllables: int,
        total_words: int,
        total_sentences: int,
    ) -> float:
        """Compute Flesch Reading Ease score.

        Score range: 0-100 (higher = easier to read).

        Args:
            total_syllables: Total syllable count.
            total_words: Total word count.
            total_sentences: Total sentence count.

        Returns:
            Flesch Reading Ease score.
        """
        if total_words == 0 or total_sentences == 0:
            return 0.0

        return max(
            0.0,
            206.835
            - 1.015 * (total_words / total_sentences)
            - 84.6 * (total_syllables / total_words),
        )

    def _classify_flesch(self, score: float) -> str:
        """Classify Flesch score into readability level.

        Args:
            score: Flesch Reading Ease score.

        Returns:
            Readability level description.
        """
        if score >= 90:
            return "very_easy"
        elif score >= 80:
            return "easy"
        elif score >= 70:
            return "fairly_easy"
        elif score >= 60:
            return "standard"
        elif score >= 50:
            return "fairly_difficult"
        elif score >= 30:
            return "difficult"
        else:
            return "very_confusing"

    def _count_passive_voice(self, text: str) -> int:
        """Count instances of passive voice.

        Simple heuristic: searches for forms of 'to be' + past participle.

        Args:
            text: Input text.

        Returns:
            Approximate count of passive voice constructions.
        """
        # Common passive patterns
        patterns = [
            r'\b(is|are|was|were|be|been|being)\s+(\w+ed)\b',
            r'\b(is|are|was|were|be|been|being)\s+(\w+en)\b',
            r'\b(is|are|was|were|be|been|being)\s+(\w+t)\b',
        ]
        count = 0
        for pattern in patterns:
            count += len(re.findall(pattern, text, re.IGNORECASE))
        return count

    def _compute_compound_score(
        self,
        flesch_score: float,
        lexical_diversity: float,
        complex_word_ratio: float,
        avg_sentence_length: float,
    ) -> float:
        """Compute a normalized compound complexity score (0-100).

        Higher score = more complex.

        Args:
            flesch_score: Flesch Reading Ease score.
            lexical_diversity: Unique word ratio.
            complex_word_ratio: Complex word ratio.
            avg_sentence_length: Average sentence length.

        Returns:
            Compound complexity score (0-100).
        """
        # Normalize Flesch (invert: higher flesch = lower complexity)
        flesch_component = max(0, (100 - flesch_score) / 100) * 40

        # Lexical diversity component
        diversity_component = min(lexical_diversity, 1.0) * 20

        # Complex word component
        complex_component = min(complex_word_ratio * 2, 1.0) * 20

        # Sentence length component (normalize: >25 words is complex)
        length_component = min(avg_sentence_length / 25, 1.0) * 20

        return flesch_component + diversity_component + complex_component + length_component

    def _classify_level(self, score: float) -> str:
        """Classify compound score into a complexity level.

        Args:
            score: Compound complexity score (0-100).

        Returns:
            Complexity level string.
        """
        for level, (low, high) in COMPLEXITY_RANGES.items():
            if low <= score < high:
                return level
        return "very_difficult"

    def analyze_draft(self, draft: Draft) -> Dict[str, ComplexityScore]:
        """Analyze complexity of all draft variants.

        Args:
            draft: Content draft with multiple variants.

        Returns:
            Dict mapping variant names to ComplexityScore.
        """
        results: Dict[str, ComplexityScore] = {}

        if draft.blog_post:
            results["blog_post"] = self.analyze(
                draft.blog_post,
                title=draft.headline or "",
            )

        if draft.social_copy:
            results["social_copy"] = self.analyze(draft.social_copy)

        if draft.ad_copy:
            results["ad_copy"] = self.analyze(draft.ad_copy)

        return results
