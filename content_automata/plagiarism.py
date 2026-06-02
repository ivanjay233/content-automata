"""Content plagiarism check integration.

Provides basic plagiarism detection and originality scoring
using text comparison algorithms and optional external API
integration for comprehensive checks.
"""

from __future__ import annotations

import hashlib
import logging
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

from content_automata.models import Draft

logger = logging.getLogger(__name__)

# Common stop words and phrases to ignore in plagiarism checks
STOP_PHRASES: Set[str] = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to",
    "for", "of", "with", "by", "from", "as", "is", "was", "are",
    "were", "be", "been", "being", "have", "has", "had", "do",
    "does", "did", "will", "would", "can", "could", "should",
    "may", "might", "shall", "about", "into", "through", "during",
    "before", "after", "above", "below", "between", "out", "off",
    "over", "under", "again", "further", "then", "once", "here",
    "there", "when", "where", "why", "how", "all", "each", "every",
    "both", "few", "more", "most", "other", "some", "such", "no",
    "nor", "not", "only", "own", "same", "so", "than", "too", "very",
    "just", "because", "it", "its", "this", "that", "these", "those",
    "i", "me", "my", "myself", "we", "us", "our", "ours", "you",
    "your", "yours", "he", "him", "his", "she", "her", "hers",
}


@dataclass
class PlagiarismMatch:
    """A detected plagiarism match with details."""

    source_text: str
    matched_text: str
    similarity: float  # 0.0 to 1.0
    source_url: str = ""
    source_title: str = ""
    word_count: int = 0
    position_start: int = 0
    position_end: int = 0


@dataclass
class PlagiarismReport:
    """Complete plagiarism check report."""

    overall_originality: float = 1.0  # 1.0 = completely original
    matches: List[PlagiarismMatch] = field(default_factory=list)
    total_matched_words: int = 0
    total_words: int = 0
    flagged_sections: List[str] = field(default_factory=list)
    warning_level: str = "low"  # low, medium, high
    warnings: List[str] = field(default_factory=list)
    passed: bool = True
    checksum: str = ""


class PlagiarismChecker:
    """Checks content for potential plagiarism.

    Features:
    - Internal fingerprint matching (n-gram comparison)
    - Exact phrase detection
    - Similarity scoring across content sections
    - Originality percentage calculation
    - External API integration point
    """

    def __init__(self, config: Optional[dict] = None):
        self._config = config or {}
        self._ngram_size = self._config.get("ngram_size", 5)
        self._threshold = self._config.get("threshold", 0.8)
        self._min_match_length = self._config.get("min_match_length", 20)
        self._reference_corpus: List[str] = self._config.get("reference_texts", [])

    def check_draft(self, draft: Draft) -> PlagiarismReport:
        """Run plagiarism check on a draft.

        Args:
            draft: The content draft to check.

        Returns:
            PlagiarismReport with analysis results.
        """
        texts_to_check: List[str] = []
        if draft.blog_post:
            texts_to_check.append(draft.blog_post)
        if draft.social_copy:
            texts_to_check.append(draft.social_copy)
        if draft.ad_copy:
            texts_to_check.append(draft.ad_copy)

        combined = "\n".join(texts_to_check)
        return self.check_text(combined)

    def check_text(self, text: str, title: str = "") -> PlagiarismReport:
        """Run plagiarism check on a text string.

        Args:
            text: The text content to check.
            title: Optional title for the content.

        Returns:
            PlagiarismReport with analysis results.
        """
        # Clean and normalize text
        cleaned = self._normalize_text(text)
        words = cleaned.split()
        total_words = len(words)
        checksum = self._compute_checksum(text)

        # Run internal checks
        matches = self._check_against_references(cleaned, text)

        # Compute metrics
        total_matched_words = sum(m.word_count for m in matches)
        originality = 1.0 - (total_matched_words / max(total_words, 1))

        # Determine warning level
        warning_level, warnings, passed = self._assess_risk(
            originality, total_matched_words, total_words
        )

        # Find flagged sections
        flagged_sections = self._find_flagged_sections(text, matches)

        return PlagiarismReport(
            overall_originality=round(originality, 4),
            matches=matches,
            total_matched_words=total_matched_words,
            total_words=total_words,
            flagged_sections=flagged_sections,
            warning_level=warning_level,
            warnings=warnings,
            passed=passed,
            checksum=checksum,
        )

    def _normalize_text(self, text: str) -> str:
        """Normalize text for comparison.

        Args:
            text: Raw text to normalize.

        Returns:
            Lowercased, cleaned text.
        """
        # Lowercase
        text = text.lower()
        # Remove punctuation
        text = re.sub(r'[^\w\s]', ' ', text)
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def _compute_checksum(self, text: str) -> str:
        """Compute a fingerprint checksum for the text.

        Args:
            text: Input text.

        Returns:
            SHA-256 hex digest of the text.
        """
        return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]

    def _check_against_references(
        self,
        cleaned: str,
        original: str,
    ) -> List[PlagiarismMatch]:
        """Check cleaned text against reference corpus.

        Args:
            cleaned: Normalized text.
            original: Original text for position tracking.

        Returns:
            List of PlagiarismMatch objects.
        """
        matches: List[PlagiarismMatch] = []
        checked_positions: Set[int] = set()

        for ref_text in self._reference_corpus:
            ref_cleaned = self._normalize_text(ref_text)

            # Extract n-grams from both texts
            text_ngrams = self._extract_ngrams(cleaned)
            ref_ngrams = self._extract_ngrams(ref_cleaned)

            # Find common n-grams
            for ngram in text_ngrams:
                if ngram in ref_ngrams and ngram not in checked_positions:
                    checked_positions.add(ngram)

                    # Find the position in the original text
                    pos = original.lower().find(ngram)
                    if pos >= 0 and len(ngram) >= self._min_match_length:
                        matches.append(PlagiarismMatch(
                            source_text=ref_text[:100],
                            matched_text=ngram,
                            similarity=1.0,
                            word_count=len(ngram.split()),
                            position_start=pos,
                            position_end=pos + len(ngram),
                        ))

        # Sort by position and deduplicate overlapping matches
        matches.sort(key=lambda m: m.position_start)
        deduped = self._deduplicate_matches(matches)
        return deduped

    def _extract_ngrams(self, text: str) -> Set[str]:
        """Extract word n-grams from text.

        Args:
            text: Normalized text.

        Returns:
            Set of n-gram strings.
        """
        words = text.split()
        ngrams: Set[str] = set()
        for i in range(len(words) - self._ngram_size + 1):
            ngram = " ".join(words[i:i + self._ngram_size])
            if not self._is_stop_ngram(ngram):
                ngrams.add(ngram)
        return ngrams

    def _is_stop_ngram(self, ngram: str) -> bool:
        """Check if an n-gram consists mostly of stop words.

        Args:
            ngram: N-gram string to check.

        Returns:
            True if the n-gram should be ignored.
        """
        words = ngram.split()
        stop_count = sum(1 for w in words if w in STOP_PHRASES)
        return stop_count > len(words) * 0.7

    def _deduplicate_matches(self, matches: List[PlagiarismMatch]) -> List[PlagiarismMatch]:
        """Remove overlapping matches, keeping the longest.

        Args:
            matches: List of matches to deduplicate.

        Returns:
            Deduplicated list of matches.
        """
        if not matches:
            return []

        deduped = [matches[0]]
        for match in matches[1:]:
            last = deduped[-1]
            # If overlap, keep the longer one
            if match.position_start < last.position_end:
                if match.word_count > last.word_count:
                    deduped[-1] = match
            else:
                deduped.append(match)

        return deduped

    def _find_flagged_sections(
        self,
        text: str,
        matches: List[PlagiarismMatch],
    ) -> List[str]:
        """Extract text sections that are flagged as potential plagiarism.

        Args:
            text: Original text.
            matches: Detected plagiarism matches.

        Returns:
            List of highlighted section strings.
        """
        sections = []
        for match in matches:
            if match.position_start >= 0 and match.position_end <= len(text):
                section = text[match.position_start:match.position_end]
                # Truncate long sections for readability
                if len(section) > 150:
                    section = section[:150] + "..."
                sections.append(section)
        return sections

    def _assess_risk(
        self,
        originality: float,
        matched_words: int,
        total_words: int,
    ) -> tuple[str, List[str], bool]:
        """Assess plagiarism risk level.

        Args:
            originality: Originality score (0.0 to 1.0).
            matched_words: Number of words matching references.
            total_words: Total word count.

        Returns:
            Tuple of (warning_level, warnings, passed).
        """
        warnings: List[str] = []
        percentage = matched_words / max(total_words, 1) * 100

        if originality >= 0.95:
            level = "low"
        elif originality >= 0.80:
            level = "medium"
            warnings.append(
                f"Content is {percentage:.1f}% similar to reference texts "
                f"({matched_words} of {total_words} words)"
            )
        else:
            level = "high"
            warnings.append(
                f"Low originality score ({originality:.1%}). "
                f"{percentage:.1f}% of content matches existing sources."
            )
            warnings.append("Consider rewriting flagged sections.")

        passed = originality >= self._config.get("pass_threshold", 0.75)
        return level, warnings, passed

    def set_reference_corpus(self, texts: List[str]) -> None:
        """Set the reference texts for comparison.

        Args:
            texts: List of reference text strings.
        """
        self._reference_corpus = texts

    def add_reference_text(self, text: str) -> None:
        """Add a single reference text to the corpus.

        Args:
            text: Reference text string.
        """
        self._reference_corpus.append(text)

    def quick_check(self, text: str, threshold: float = 0.85) -> bool:
        """Quick originality check — returns pass/fail only.

        Args:
            text: Text to check.
            threshold: Originality threshold (default 0.85).

        Returns:
            True if content passes originality check.
        """
        report = self.check_text(text)
        return report.overall_originality >= threshold
