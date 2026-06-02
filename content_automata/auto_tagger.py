"""Content auto-tagging based on NLP techniques.

Automatically generates relevant tags, categories, and topics
from content using keyword extraction, TF-IDF-like scoring,
and configurable tag taxonomies.
"""

from __future__ import annotations

import logging
import math
import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

from content_automata.models import Draft, ResearchResult

logger = logging.getLogger(__name__)

# Common English stop words for keyword extraction
STOP_WORDS: Set[str] = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an",
    "and", "any", "are", "arent", "as", "at", "be", "because", "been",
    "before", "being", "below", "between", "both", "but", "by", "cant",
    "cannot", "could", "couldnt", "did", "didnt", "do", "does", "doesnt",
    "doing", "dont", "down", "during", "each", "few", "for", "from",
    "further", "had", "hadnt", "has", "hasnt", "have", "havent", "having",
    "he", "hed", "hell", "hes", "her", "here", "heres", "hers", "herself",
    "him", "himself", "his", "how", "hows", "i", "id", "ill", "im", "ive",
    "if", "in", "into", "is", "isnt", "it", "its", "itself", "lets", "me",
    "more", "most", "mustnt", "my", "myself", "no", "nor", "not", "of",
    "off", "on", "once", "only", "or", "other", "ought", "our", "ours",
    "ourselves", "out", "over", "own", "same", "shant", "she", "shed",
    "shell", "shes", "should", "shouldnt", "so", "some", "such", "than",
    "that", "thats", "the", "their", "theirs", "them", "themselves",
    "then", "there", "theres", "these", "they", "theyd", "theyll",
    "theyre", "theyve", "this", "those", "through", "to", "too", "under",
    "until", "up", "very", "was", "wasnt", "we", "wed", "well", "were",
    "werent", "weve", "what", "whats", "when", "whens", "where", "wheres",
    "which", "while", "who", "whos", "whom", "why", "whys", "with", "wont",
    "would", "wouldnt", "you", "youd", "youll", "youre", "youve", "your",
    "yours", "yourself", "yourselves",
}

# Predefined content categories and their associated keywords
CATEGORY_KEYWORDS: Dict[str, Set[str]] = {
    "technology": {
        "software", "hardware", "app", "application", "digital", "tech",
        "ai", "artificial intelligence", "machine learning", "data", "cloud",
        "cybersecurity", "programming", "code", "developer", "api",
        "blockchain", "iot", "saas", "platform", "algorithm",
    },
    "marketing": {
        "marketing", "seo", "content", "social media", "brand", "branding",
        "advertising", "campaign", "audience", "conversion", "leads",
        "analytics", "growth", "strategy", "engagement", "reach",
        "influencer", "ppc", "email marketing", "funnel",
    },
    "business": {
        "business", "startup", "entrepreneur", "enterprise", "smb",
        "revenue", "profit", "investment", "funding", "venture",
        "management", "leadership", "strategy", "operations", "scale",
        "b2b", "b2c", "market", "industry", "stakeholder",
    },
    "finance": {
        "finance", "financial", "money", "banking", "investment", "stock",
        "crypto", "cryptocurrency", "budget", "saving", "retirement",
        "tax", "insurance", "loan", "mortgage", "credit", "debt",
        "wealth", "portfolio", "dividend",
    },
    "health": {
        "health", "wellness", "fitness", "nutrition", "diet", "exercise",
        "mental health", "meditation", "yoga", "sleep", "recovery",
        "medical", "healthcare", "disease", "treatment", "therapy",
        "vitamin", "supplement", "doctor", "patient",
    },
    "education": {
        "education", "learning", "teaching", "student", "teacher",
        "school", "university", "course", "training", "skill",
        "online learning", "elearning", "tutorial", "lesson", "curriculum",
        "degree", "certification", "study", "knowledge", "academic",
    },
    "lifestyle": {
        "lifestyle", "travel", "food", "recipe", "fashion", "beauty",
        "home", "decor", "garden", "pet", "parenting", "relationship",
        "hobby", "entertainment", "music", "movie", "book", "art",
        "culture", "sport",
    },
    "productivity": {
        "productivity", "efficiency", "time management", "workflow",
        "automation", "organization", "planning", "goal", "habit",
        "focus", "priority", "deadline", "task", "tool", "system",
        "optimization", "streamline", "agile", "scrum", "kanban",
    },
}

# Default tag synonyms
TAG_SYNONYMS: Dict[str, str] = {
    "ai": "artificial-intelligence",
    "ml": "machine-learning",
    "ecommerce": "e-commerce",
    "saas": "software-as-a-service",
    "seo": "search-engine-optimization",
    "ui": "user-interface",
    "ux": "user-experience",
    "api": "api-integration",
    "smb": "small-business",
    "b2b": "business-to-business",
    "b2c": "business-to-consumer",
    "cta": "call-to-action",
    "roi": "return-on-investment",
    "kpi": "key-performance-indicator",
    "devops": "development-operations",
}


@dataclass
class Tag:
    """A tagged keyword with relevance score."""

    name: str
    relevance: float  # 0.0 to 1.0
    category: str = "uncategorized"
    source: str = "extracted"  # extracted, category, synonym


@dataclass
class TaggingResult:
    """Complete auto-tagging result with metadata."""

    tags: List[Tag] = field(default_factory=list)
    primary_category: str = "uncategorized"
    categories: List[str] = field(default_factory=list)
    key_phrases: List[str] = field(default_factory=list)
    suggested_tags: List[str] = field(default_factory=list)
    top_tags: List[str] = field(default_factory=list)
    confidence: float = 0.0


class AutoTagger:
    """Automatically generates tags and categories from content.

    Uses TF-IDF-like keyword extraction, category matching via
    keyword sets, synonym resolution, and phrase detection.
    """

    def __init__(self, config: Optional[dict] = None):
        self._config = config or {}
        self._max_tags = self._config.get("max_tags", 10)
        self._min_relevance = self._config.get("min_relevance", 0.1)
        self._ngram_max = self._config.get("ngram_max", 3)

        # Allow custom category keywords
        custom_categories = self._config.get("custom_categories", {})
        self._categories: Dict[str, Set[str]] = {**CATEGORY_KEYWORDS}
        for cat, keywords in custom_categories.items():
            if cat in self._categories:
                self._categories[cat].update(keywords)
            else:
                self._categories[cat] = set(keywords)

    def tag_draft(self, draft: Draft, research: Optional[ResearchResult] = None) -> TaggingResult:
        """Generate tags from a content draft.

        Args:
            draft: Content draft with blog/social/ad copy.
            research: Optional research result for additional context.

        Returns:
            TaggingResult with extracted tags and categories.
        """
        # Combine all text sources
        texts: List[str] = []
        if draft.blog_post:
            texts.append(draft.blog_post)
        if draft.social_copy:
            texts.append(draft.social_copy)
        if draft.ad_copy:
            texts.append(draft.ad_copy)
        if draft.headline:
            texts.append(draft.headline)
        if draft.meta_description:
            texts.append(draft.meta_description)

        combined = "\n".join(texts)

        if not combined:
            return TaggingResult()

        # Add research context
        context = ""
        if research:
            context = research.summary + " " + " ".join(research.key_points)

        return self.tag_text(combined, context)

    def tag_text(self, text: str, context: str = "") -> TaggingResult:
        """Generate tags from raw text content.

        Args:
            text: The text content to analyze.
            context: Optional additional context text.

        Returns:
            TaggingResult with extracted tags and categories.
        """
        # Combine text and context
        full_text = f"{text} {context}" if context else text

        # Clean and tokenize
        cleaned = self._clean_text(full_text)
        words = cleaned.split()
        if not words:
            return TaggingResult()

        # Extract keywords
        keywords = self._extract_keywords(words, full_text)

        # Detect n-gram phrases
        phrases = self._extract_phrases(full_text)

        # Classify categories
        categories = self._classify_categories(full_text, keywords)

        # Build tags with relevance
        tags: List[Tag] = []
        seen_words: Set[str] = set()

        # Add extracted keywords as tags
        for word, score in keywords:
            tag_name = self._normalize_tag(word)
            if tag_name and tag_name not in seen_words and score >= self._min_relevance:
                seen_words.add(tag_name)
                cat = self._find_best_category(word)
                tags.append(Tag(
                    name=tag_name,
                    relevance=round(score, 3),
                    category=cat,
                    source="extracted",
                ))

        # Add phrase-based tags
        for phrase, score in phrases:
            tag_name = self._normalize_tag(phrase)
            if tag_name and tag_name not in seen_words and score >= self._min_relevance:
                seen_words.add(tag_name)
                cat = self._find_best_category(phrase)
                tags.append(Tag(
                    name=tag_name,
                    relevance=round(score, 3),
                    category=cat,
                    source="extracted",
                ))

        # Add category-based tags
        for cat in categories:
            cat_tag = self._normalize_tag(cat)
            if cat_tag and cat_tag not in seen_words:
                seen_words.add(cat_tag)
                tags.append(Tag(
                    name=cat_tag,
                    relevance=self._compute_category_relevance(full_text, cat),
                    category=cat,
                    source="category",
                ))

        # Sort by relevance
        tags.sort(key=lambda t: t.relevance, reverse=True)

        # Trim to max tags
        tags = tags[:self._max_tags]

        # Build results
        result = TaggingResult(
            tags=tags,
            primary_category=categories[0] if categories else "uncategorized",
            categories=categories,
            key_phrases=[p for p, _ in phrases[:5]],
            suggested_tags=[t.name for t in tags if t.relevance > 0.2],
            top_tags=[t.name for t in tags[:5]],
            confidence=self._compute_confidence(tags, categories, len(words)),
        )

        return result

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text for analysis.

        Args:
            text: Raw text.

        Returns:
            Lowercased, cleaned text.
        """
        text = text.lower()
        text = re.sub(r'[^\w\s\'-]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def _extract_keywords(
        self,
        words: List[str],
        full_text: str,
    ) -> List[tuple[str, float]]:
        """Extract keywords using TF-IDF-like scoring.

        Args:
            words: Tokenized word list.
            full_text: Original text for frequency counting.

        Returns:
            List of (keyword, score) tuples sorted by score.
        """
        # Filter stop words and short words
        filtered = [w for w in words if w not in STOP_WORDS and len(w) > 2]

        # Count frequencies
        word_freq = Counter(filtered)
        total_words = len(filtered)

        if total_words == 0:
            return []

        # Score using normalized frequency with length bonus
        scored: List[tuple[str, float]] = []
        for word, count in word_freq.most_common(50):
            # Normalized frequency
            freq_score = count / max(total_words, 1) * 100

            # Length bonus (longer words are more specific)
            length_bonus = min(len(word) / 10, 0.3)

            # Position bonus (words in first 20% get a boost)
            first_tenth = full_text.lower()[:len(full_text) // 5]
            position_bonus = 0.2 if word in first_tenth else 0.0

            score = freq_score + length_bonus + position_bonus
            scored.append((word, score))

        # Sort by score descending
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:20]

    def _extract_phrases(self, text: str) -> List[tuple[str, float]]:
        """Extract meaningful multi-word phrases.

        Args:
            text: Cleaned text.

        Returns:
            List of (phrase, score) tuples.
        """
        words = self._clean_text(text).split()
        scored: Dict[str, float] = {}

        for n in range(2, self._ngram_max + 1):
            for i in range(len(words) - n + 1):
                phrase = " ".join(words[i:i + n])

                # Skip if all stop words
                phr_words = phrase.split()
                if all(w in STOP_WORDS for w in phr_words):
                    continue

                # Skip if starts/ends with stop word
                if phr_words[0] in STOP_WORDS or phr_words[-1] in STOP_WORDS:
                    continue

                # Score: prefer medium-length, content-rich phrases
                if phrase in scored:
                    scored[phrase] += 1.0
                else:
                    scored[phrase] = 1.0

        # Convert to sorted list
        result = [(phrase, count) for phrase, count in scored.items()]
        result.sort(key=lambda x: x[1] * len(x[0]) / max(len(x[0].split()), 1), reverse=True)
        return result[:10]

    def _classify_categories(self, text: str, keywords: List[tuple[str, float]]) -> List[str]:
        """Classify content into predefined categories.

        Args:
            text: Full text content.
            keywords: Extracted keywords.

        Returns:
            List of category names sorted by relevance.
        """
        text_lower = text.lower()
        cat_scores: Dict[str, float] = {}

        for category, cat_keywords in self._categories.items():
            score = 0.0
            for kw in cat_keywords:
                if kw in text_lower:
                    score += text_lower.count(kw) * 2.0

            # Add keyword-based matches
            for word, _ in keywords:
                if word in cat_keywords:
                    score += 3.0

            if score > 0:
                cat_scores[category] = score

        return sorted(cat_scores.keys(), key=lambda c: cat_scores[c], reverse=True)

    def _find_best_category(self, word: str) -> str:
        """Find the best category for a word.

        Args:
            word: The word to categorize.

        Returns:
            Category name, or 'uncategorized'.
        """
        word_lower = word.lower()
        for category, keywords in self._categories.items():
            if word_lower in keywords:
                return category
        return "uncategorized"

    def _compute_category_relevance(self, text: str, category: str) -> float:
        """Compute relevance score for a category assignment.

        Args:
            text: Content text.
            category: Category name.

        Returns:
            Relevance score (0.1 to 1.0).
        """
        if category not in self._categories:
            return 0.1

        keywords = self._categories[category]
        text_lower = text.lower()
        matches = sum(1 for kw in keywords if kw in text_lower)
        return min(1.0, matches / 5 + 0.1)

    def _compute_confidence(
        self,
        tags: List[Tag],
        categories: List[str],
        word_count: int,
    ) -> float:
        """Compute overall confidence in the tagging result.

        Args:
            tags: Extracted tags.
            categories: Detected categories.
            word_count: Total word count.

        Returns:
            Confidence score (0.0 to 1.0).
        """
        if word_count < 10:
            return 0.1

        # More tags = more confident (up to a point)
        tag_conf = min(len(tags) / 10, 1.0) * 0.4

        # Category detection adds confidence
        cat_conf = min(len(categories) / 3, 1.0) * 0.3

        # Word count adds confidence (more words = better analysis)
        size_conf = min(word_count / 500, 1.0) * 0.3

        return round(tag_conf + cat_conf + size_conf, 2)

    def _normalize_tag(self, tag: str) -> str:
        """Normalize a tag for consistent formatting.

        Converts to lowercase, replaces spaces with hyphens,
        resolves synonyms, and removes non-alphanumeric chars.

        Args:
            tag: Raw tag string.

        Returns:
            Normalized tag string, or empty string if invalid.
        """
        # Clean and lowercase
        tag = tag.lower().strip()
        tag = re.sub(r'[^\w\s-]', '', tag)
        tag = re.sub(r'\s+', '-', tag).strip('-')

        if not tag or len(tag) < 2:
            return ""

        # Resolve synonyms
        return TAG_SYNONYMS.get(tag, tag)

    def list_categories(self) -> Dict[str, List[str]]:
        """List all available categories and their keywords.

        Returns:
            Dict mapping category names to keyword lists.
        """
        return {
            cat: sorted(kws)
            for cat, kws in self._categories.items()
        }
