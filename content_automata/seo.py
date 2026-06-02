"""SEO analysis for generated content."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from content_automata.models import Draft

logger = logging.getLogger(__name__)


@dataclass
class KeywordAnalysis:
    """Analysis for a single keyword."""

    keyword: str
    count: int
    density: float  # percentage
    in_title: bool = False
    in_meta: bool = False
    in_headings: bool = False
    in_first_paragraph: bool = False


@dataclass
class SEOScore:
    """Overall SEO analysis result."""

    title_score: float = 0.0
    meta_score: float = 0.0
    keyword_score: float = 0.0
    structure_score: float = 0.0
    readability_score: float = 0.0
    overall: float = 0.0
    keywords: List[KeywordAnalysis] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)


class SEOAnalyzer:
    """Analyzes content for SEO optimization.

    Checks title quality, meta description, keyword usage,
    content structure, and provides actionable suggestions.
    """

    def __init__(self, config: Optional[Dict] = None):
        self._config = config or {}
        self._target_keywords = self._config.get("target_keywords", [])

    def analyze(self, draft: Draft, target_keywords: Optional[List[str]] = None) -> SEOScore:
        """Run full SEO analysis on a content draft.

        Args:
            draft: The content draft to analyze.
            target_keywords: Optional list of target keywords.

        Returns:
            SEOScore with dimension scores and keyword analysis.
        """
        keywords = target_keywords or self._target_keywords
        result = SEOScore()

        # Title analysis
        result.title_score = self._analyze_title(draft, keywords, result)

        # Meta description analysis
        result.meta_score = self._analyze_meta(draft, keywords, result)

        # Keyword analysis
        result.keyword_score = self._analyze_keywords(draft, keywords, result)

        # Structure analysis
        result.structure_score = self._analyze_structure(draft, result)

        # Readability analysis
        result.readability_score = self._analyze_readability(draft, result)

        # Overall score (weighted average)
        weights = {"title": 0.25, "meta": 0.15, "keyword": 0.30, "structure": 0.15, "readability": 0.15}
        result.overall = (
            result.title_score * weights["title"]
            + result.meta_score * weights["meta"]
            + result.keyword_score * weights["keyword"]
            + result.structure_score * weights["structure"]
            + result.readability_score * weights["readability"]
        )

        # Final suggestions
        if result.overall < 0.7:
            result.suggestions.append("Improve overall SEO score — review keyword usage and content structure")
        if result.title_score < 0.6:
            result.suggestions.append("Optimize title: keep 50-60 characters, include primary keyword")
        if result.meta_score < 0.6:
            result.suggestions.append("Write a compelling meta description (120-158 chars) with target keyword")
        if result.keyword_score < 0.5:
            result.suggestions.append("Increase keyword density to 1-2% of total word count")
        if result.structure_score < 0.6:
            result.suggestions.append("Add H2/H3 headings with keyword variants")

        return result

    def _analyze_title(self, draft: Draft, keywords: List[str], result: SEOScore) -> float:
        score = 0.0
        title = draft.headline or ""
        if not title:
            result.suggestions.append("Missing title — every page needs an H1 title")
            return 0.0

        # Length check (50-60 chars ideal)
        title_len = len(title)
        if 50 <= title_len <= 60:
            score += 0.4
        elif 30 <= title_len <= 70:
            score += 0.2
        else:
            result.suggestions.append(f"Title length ({title_len}) outside ideal range (50-60 chars)")

        # Primary keyword in title
        if keywords:
            kw_in_title = any(kw.lower() in title.lower() for kw in keywords)
            if kw_in_title:
                score += 0.4
            else:
                result.suggestions.append("Add primary keyword to title")

        # Title starts with strong word
        if title and title[0].isupper():
            score += 0.2

        return min(1.0, score)

    def _analyze_meta(self, draft: Draft, keywords: List[str], result: SEOScore) -> float:
        score = 0.0
        meta = draft.meta_description or ""
        if not meta:
            result.suggestions.append("Missing meta description — add one for better CTR")
            return 0.0

        # Length check (120-158 chars)
        meta_len = len(meta)
        if 120 <= meta_len <= 158:
            score += 0.5
        elif meta_len >= 50:
            score += 0.3
        else:
            result.suggestions.append(f"Meta description too short ({meta_len} chars)")

        # Keyword in meta
        if keywords:
            if any(kw.lower() in meta.lower() for kw in keywords):
                score += 0.5
            else:
                result.suggestions.append("Include target keyword in meta description")

        return min(1.0, score)

    def _analyze_keywords(self, draft: Draft, keywords: List[str], result: SEOScore) -> float:
        if not keywords:
            return 0.5  # neutral if no keywords specified

        body = (draft.blog_post or "") + " " + (draft.social_copy or "")
        if not body:
            return 0.0

        words = body.split()
        total_words = len(words)
        scores = []

        for kw in keywords:
            count = len(re.findall(re.escape(kw), body, re.IGNORECASE))
            density = (count * 100.0) / total_words if total_words > 0 else 0

            analysis = KeywordAnalysis(
                keyword=kw,
                count=count,
                density=round(density, 2),
                in_title=draft.headline and kw.lower() in draft.headline.lower() if draft.headline else False,
                in_meta=draft.meta_description and kw.lower() in draft.meta_description.lower() if draft.meta_description else False,
                in_headings=bool(re.search(r'^#{1,3}.*' + re.escape(kw), body, re.MULTILINE | re.IGNORECASE)),
                in_first_paragraph=kw.lower() in body[:500].lower() if body else False,
            )
            result.keywords.append(analysis)

            # Score: 1-2% density is ideal
            if 1.0 <= density <= 2.0:
                scores.append(1.0)
            elif 0.5 <= density <= 3.0:
                scores.append(0.7)
            elif density > 0:
                scores.append(0.4)
            else:
                scores.append(0.0)

        return sum(scores) / len(scores) if scores else 0.0

    def _analyze_structure(self, draft: Draft, result: SEOScore) -> float:
        score = 0.0
        body = draft.blog_post or ""
        if not body:
            return 0.0

        # Heading structure
        h2_count = len(re.findall(r'^##\s', body, re.MULTILINE))
        h3_count = len(re.findall(r'^###\s', body, re.MULTILINE))
        total_headings = h2_count + h3_count

        if h2_count >= 3:
            score += 0.3
        elif h2_count >= 1:
            score += 0.15

        if total_headings >= 5:
            score += 0.2

        # Paragraph length
        paragraphs = [p.strip() for p in body.split('\n\n') if p.strip()]
        if paragraphs:
            long_paras = sum(1 for p in paragraphs if len(p.split()) > 100)
            if long_paras <= len(paragraphs) * 0.3:
                score += 0.2

        # List usage
        if re.search(r'^\s*[-*\d+.]\s', body, re.MULTILINE):
            score += 0.3

        return min(1.0, score)

    def _analyze_readability(self, draft: Draft, result: SEOScore) -> float:
        body = draft.blog_post or ""
        if not body:
            return 0.0

        sentences = re.split(r'[.!?]+', body)
        sentences = [s.strip() for s in sentences if s.strip()]
        if not sentences:
            return 0.0

        words = body.split()
        avg_words_per_sentence = len(words) / len(sentences)

        if avg_words_per_sentence <= 15:
            return 1.0
        elif avg_words_per_sentence <= 20:
            return 0.8
        elif avg_words_per_sentence <= 25:
            return 0.5
        else:
            result.suggestions.append(f"Average sentence length ({avg_words_per_sentence:.0f}) is too high — aim for 15-20 words")
            return 0.3
