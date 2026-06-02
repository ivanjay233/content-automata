"""Hashtag and keyword suggestion module."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

logger = logging.getLogger(__name__)


@dataclass
class HashtagSuggestion:
    """A suggested hashtag with metadata."""

    tag: str
    relevance: float  # 0.0 to 1.0
    category: str = "general"  # general, trending, niche, branded
    usage_tip: str = ""


@dataclass
class KeywordSuggestion:
    """A suggested keyword with metadata."""

    keyword: str
    search_volume: str = "medium"  # low, medium, high
    competition: str = "medium"  # low, medium, high
    relevance: float = 0.5
    suggested_as: str = "primary"  # primary, secondary, long_tail


class SuggestionEngine:
    """Generates hashtag and keyword suggestions from content.

    Extracts key concepts from topic and draft content,
    then generates relevant tags and keywords.
    """

    # Common content categories with related hashtags
    CATEGORY_HASHTAGS: Dict[str, List[str]] = {
        "technology": ["#Tech", "#Innovation", "#DigitalTransformation", "#AI", "#FutureOfWork"],
        "business": ["#Business", "#Entrepreneurship", "#Growth", "#Strategy", "#Leadership"],
        "marketing": ["#Marketing", "#ContentMarketing", "#SEO", "#DigitalMarketing", "#Branding"],
        "health": ["#Health", "#Wellness", "#Healthcare", "#MentalHealth", "#Fitness"],
        "finance": ["#Finance", "#Investing", "#WealthManagement", "#FinTech", "#Economy"],
        "education": ["#Education", "#Learning", "#EdTech", "#OnlineLearning", "#Skills"],
        "lifestyle": ["#Lifestyle", "#Productivity", "#WorkLifeBalance", "#SelfCare", "#Motivation"],
    }

    STOP_WORDS: Set[str] = {
        "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
        "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
        "being", "have", "has", "had", "do", "does", "did", "will", "would",
        "could", "should", "may", "might", "shall", "can", "need", "dare",
        "this", "that", "these", "those", "it", "its", "they", "them", "their",
        "what", "which", "who", "whom", "how", "when", "where", "why",
    }

    def __init__(self, config: Optional[Dict] = None):
        self._config = config or {}
        self._max_hashtags = self._config.get("max_hashtags", 10)
        self._max_keywords = self._config.get("max_keywords", 5)

    def suggest_hashtags(self, topic: str, content: str | None = None) -> List[HashtagSuggestion]:
        """Generate hashtag suggestions from topic and content.

        Args:
            topic: The content topic.
            content: Optional content body for deeper analysis.

        Returns:
            List of hashtag suggestions sorted by relevance.
        """
        suggestions: List[HashtagSuggestion] = []
        seen: Set[str] = set()

        # Category-based suggestions
        topic_lower = topic.lower()
        for category, tags in self.CATEGORY_HASHTAGS.items():
            if category in topic_lower:
                for tag in tags:
                    if tag not in seen:
                        suggestions.append(HashtagSuggestion(
                            tag=tag,
                            relevance=0.8,
                            category=category,
                            usage_tip=f"Use with {category} content",
                        ))
                        seen.add(tag)

        # Topic-based hashtag
        topic_hashtag = "#" + "".join(w.capitalize() for w in topic.split()[:3])
        if topic_hashtag not in seen:
            suggestions.append(HashtagSuggestion(
                tag=topic_hashtag,
                relevance=1.0,
                category="niche",
                usage_tip="Primary topic hashtag",
            ))
            seen.add(topic_hashtag)

        # Content-based suggestions
        if content:
            words = re.findall(r'\b[a-zA-Z]{4,}\b', content.lower())
            word_freq: Dict[str, int] = {}
            for w in words:
                if w not in self.STOP_WORDS:
                    word_freq[w] = word_freq.get(w, 0) + 1

            # Top frequent content words as hashtags
            sorted_words = sorted(word_freq.items(), key=lambda x: -x[1])
            for word, freq in sorted_words[:5]:
                tag = "#" + word.capitalize()
                if tag not in seen and len(tag) <= 30:
                    suggestions.append(HashtagSuggestion(
                        tag=tag,
                        relevance=min(0.9, 0.3 + freq * 0.01),
                        category="general",
                        usage_tip=f"Used {freq} times in content",
                    ))
                    seen.add(tag)

        # Limit
        return suggestions[:self._max_hashtags]

    def suggest_keywords(self, topic: str, content: str | None = None) -> List[KeywordSuggestion]:
        """Generate keyword suggestions from topic and content.

        Args:
            topic: The content topic.
            content: Optional content body for deeper analysis.

        Returns:
            List of keyword suggestions sorted by relevance.
        """
        suggestions: List[KeywordSuggestion] = []

        # Primary keyword is the topic itself
        suggestions.append(KeywordSuggestion(
            keyword=topic,
            search_volume="medium",
            competition="medium",
            relevance=1.0,
            suggested_as="primary",
        ))

        # Topic bigrams as secondary keywords
        words = topic.split()
        if len(words) >= 2:
            for i in range(len(words) - 1):
                bigram = f"{words[i]} {words[i + 1]}"
                if len(bigram) > 3:
                    suggestions.append(KeywordSuggestion(
                        keyword=bigram,
                        search_volume="low",
                        competition="low",
                        relevance=0.7,
                        suggested_as="long_tail",
                    ))

        # Content-based keywords
        if content:
            content_words = re.findall(r'\b[a-zA-Z]{4,}\b', content.lower())
            word_freq: Dict[str, int] = {}
            for w in content_words:
                if w not in self.STOP_WORDS and w not in topic.lower():
                    word_freq[w] = word_freq.get(w, 0) + 1

            # Find meaningful 2-3 word phrases
            sentences = re.split(r'[.!?]+', content)
            phrases: Dict[str, int] = {}
            for sentence in sentences:
                sentence_words = sentence.strip().split()
                for i in range(len(sentence_words) - 1):
                    phrase = f"{sentence_words[i]} {sentence_words[i + 1]}"
                    phrase_lower = phrase.lower()
                    if all(w not in self.STOP_WORDS for w in phrase_lower.split()):
                        phrases[phrase] = phrases.get(phrase, 0) + 1

            sorted_phrases = sorted(phrases.items(), key=lambda x: -x[1])
            for phrase, count in sorted_phrases[:3]:
                if len(phrase) > 5 and not any(kw.keyword.lower() == phrase.lower() for kw in suggestions):
                    suggestions.append(KeywordSuggestion(
                        keyword=phrase,
                        search_volume="low",
                        competition="low",
                        relevance=min(0.8, 0.3 + count * 0.05),
                        suggested_as="long_tail",
                    ))

        return suggestions[:self._max_keywords]
