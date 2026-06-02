"""Social media post character limit validation.

Validates content against platform-specific character limits
with truncation strategies, warnings, and multi-post splitting
for cross-platform publishing compliance.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class PlatformLimits:
    """Character limits for a social media platform."""

    name: str
    max_chars: int
    recommended_chars: int
    headline_max: int = 0
    threadable: bool = False
    max_hashtags: int = 0
    link_allowed: bool = True
    media_limit: int = 1
    warning_at: float = 0.9  # warn at 90% of limit


# Platform-specific character limits
PLATFORM_LIMITS: Dict[str, PlatformLimits] = {
    "twitter": PlatformLimits(
        name="Twitter / X",
        max_chars=280,
        recommended_chars=240,
        headline_max=0,
        threadable=True,
        max_hashtags=2,
        link_allowed=True,
        media_limit=4,
    ),
    "linkedin": PlatformLimits(
        name="LinkedIn",
        max_chars=3000,
        recommended_chars=1500,
        headline_max=220,
        threadable=False,
        max_hashtags=5,
        link_allowed=True,
        media_limit=9,
    ),
    "facebook": PlatformLimits(
        name="Facebook",
        max_chars=63206,
        recommended_chars=250,
        headline_max=0,
        threadable=False,
        max_hashtags=5,
        link_allowed=True,
        media_limit=10,
    ),
    "instagram": PlatformLimits(
        name="Instagram",
        max_chars=2200,
        recommended_chars=150,
        headline_max=0,
        threadable=False,
        max_hashtags=30,
        link_allowed=False,
        media_limit=10,
    ),
    "threads": PlatformLimits(
        name="Threads",
        max_chars=500,
        recommended_chars=150,
        headline_max=0,
        threadable=False,
        max_hashtags=10,
        link_allowed=True,
        media_limit=10,
    ),
    "mastodon": PlatformLimits(
        name="Mastodon",
        max_chars=500,
        recommended_chars=400,
        headline_max=0,
        threadable=True,
        max_hashtags=8,
        link_allowed=True,
        media_limit=4,
    ),
    "bluesky": PlatformLimits(
        name="Bluesky",
        max_chars=300,
        recommended_chars=250,
        headline_max=0,
        threadable=True,
        max_hashtags=5,
        link_allowed=True,
        media_limit=4,
    ),
    "tiktok": PlatformLimits(
        name="TikTok",
        max_chars=2200,
        recommended_chars=150,
        headline_max=0,
        threadable=False,
        max_hashtags=5,
        link_allowed=True,
        media_limit=1,
    ),
    "youtube": PlatformLimits(
        name="YouTube",
        max_chars=5000,
        recommended_chars=200,
        headline_max=100,
        threadable=False,
        max_hashtags=15,
        link_allowed=True,
        media_limit=1,
    ),
}


@dataclass
class ValidationResult:
    """Result of validating content against platform limits."""

    platform: str
    total_chars: int
    max_chars: int
    recommended_chars: int
    within_limit: bool
    within_recommended: bool
    excess_chars: int = 0
    truncation_needed: bool = False
    warnings: List[str] = field(default_factory=list)
    thread_count: int = 1
    truncated_text: str = ""
    hashtag_count: int = 0
    link_present: bool = False


class SocialValidator:
    """Validates content against social media platform character limits.

    Supports:
    - Per-platform character limit checking
    - Warning generation for approaching limits
    - Content truncation strategies
    - Thread splitting for threadable platforms
    - Hashtag and link validation
    """

    def __init__(self, config: Optional[dict] = None):
        self._config = config or {}
        self._limits = {
            **PLATFORM_LIMITS,
            **self._config.get("custom_platforms", {}),
        }

    def validate(
        self,
        text: str,
        platform: str = "twitter",
        headline: str = "",
        hashtags: Optional[List[str]] = None,
    ) -> ValidationResult:
        """Validate content for a specific platform.

        Args:
            text: The content text to validate.
            platform: Target platform name.
            headline: Optional headline (counts toward limits on some platforms).
            hashtags: Optional list of hashtags to include.

        Returns:
            ValidationResult with limit check results.
        """
        limits = self._limits.get(platform.lower())
        if not limits:
            raise ValueError(
                f"Unknown platform '{platform}'. "
                f"Supported: {list(self._limits.keys())}"
            )

        hashtag_list = hashtags or []
        hashtag_text = " ".join(f"#{h.strip('#')}" for h in hashtag_list) if hashtag_list else ""

        # Build full post text
        if platform.lower() == "youtube" and headline:
            full_text = f"{headline}\n\n{text} {hashtag_text}".strip()
        else:
            full_text = f"{text} {hashtag_text}".strip()

        total_chars = len(full_text)
        excess_chars = max(0, total_chars - limits.max_chars)
        within_limit = total_chars <= limits.max_chars
        within_recommended = total_chars <= limits.recommended_chars
        hashtag_count = len(hashtag_list)
        link_present = "http://" in text or "https://" in text

        warnings: List[str] = []

        # Check recommended limit
        if total_chars > limits.recommended_chars and limits.recommended_chars > 0:
            pct = (total_chars / limits.max_chars) * 100
            if pct >= limits.warning_at * 100:
                warnings.append(
                    f"Content is at {total_chars}/{limits.max_chars} chars "
                    f"({pct:.0f}% of limit)"
                )

        # Check max limit
        if not within_limit:
            warnings.append(
                f"Content exceeds {limits.name}'s {limits.max_chars} char limit "
                f"by {excess_chars} characters"
            )

        # Check hashtag count
        if limits.max_hashtags > 0 and hashtag_count > limits.max_hashtags:
            warnings.append(
                f"Hashtag count ({hashtag_count}) exceeds "
                f"{limits.name}'s limit of {limits.max_hashtags}"
            )

        # Check link
        if link_present and not limits.link_allowed:
            warnings.append(f"{limits.name} does not support clickable links in posts")

        # Check headline
        if headline and limits.headline_max > 0 and len(headline) > limits.headline_max:
            warnings.append(
                f"Headline ({len(headline)} chars) exceeds "
                f"{limits.name}'s {limits.headline_max} char limit"
            )

        # Determine truncation and threading needs
        truncation_needed = not within_limit
        truncated_text = ""
        thread_count = 1

        if truncation_needed:
            truncated_text = self.truncate(full_text, limits.max_chars)

        if limits.threadable and truncation_needed:
            thread_count = math_ceil(total_chars / limits.max_chars)
            if thread_count > 1:
                warnings.append(
                    f"Content requires {thread_count} threads/posts "
                    f"({total_chars} chars across {limits.max_chars} per post)"
                )

        return ValidationResult(
            platform=limits.name,
            total_chars=total_chars,
            max_chars=limits.max_chars,
            recommended_chars=limits.recommended_chars,
            within_limit=within_limit,
            within_recommended=within_recommended,
            excess_chars=excess_chars,
            truncation_needed=truncation_needed,
            warnings=warnings,
            thread_count=thread_count,
            truncated_text=truncated_text,
            hashtag_count=hashtag_count,
            link_present=link_present,
        )

    def validate_multi_platform(
        self,
        text: str,
        platforms: Optional[List[str]] = None,
        headline: str = "",
        hashtags: Optional[List[str]] = None,
    ) -> Dict[str, ValidationResult]:
        """Validate content across multiple platforms.

        Args:
            text: Content text to validate.
            platforms: List of platform names (defaults to all known).
            headline: Optional headline.
            hashtags: Optional list of hashtags.

        Returns:
            Dict mapping platform names to ValidationResult.
        """
        targets = platforms or list(self._limits.keys())
        results: Dict[str, ValidationResult] = {}

        for platform in targets:
            try:
                results[platform] = self.validate(text, platform, headline, hashtags)
            except ValueError as e:
                logger.warning("Skipping platform '%s': %s", platform, e)

        return results

    def truncate(self, text: str, max_chars: int, ellipsis: str = "...") -> str:
        """Truncate text to fit within character limits.

        Tries to break at sentence or word boundaries.

        Args:
            text: Text to truncate.
            max_chars: Maximum character count.
            ellipsis: Suffix to indicate truncation.

        Returns:
            Truncated text within the character limit.
        """
        if len(text) <= max_chars:
            return text

        # Try to truncate at sentence boundary
        truncated = text[:max_chars - len(ellipsis)]
        last_sentence = max(
            truncated.rfind(". "),
            truncated.rfind("! "),
            truncated.rfind("? "),
        )
        if last_sentence > max_chars // 2:
            return text[:last_sentence + 1] + ellipsis

        # Try word boundary
        last_space = truncated.rfind(" ")
        if last_space > max_chars // 2:
            return text[:last_space] + ellipsis

        # Hard truncation
        return truncated + ellipsis

    def split_thread(
        self,
        text: str,
        platform: str = "twitter",
        separator: str = "\n\n🧵 ({n}/{total})",
    ) -> List[str]:
        """Split long content into a thread for threadable platforms.

        Args:
            text: Content to split into a thread.
            platform: Target platform name.
            separator: Post separator template.

        Returns:
            List of post strings for the thread.
        """
        limits = self._limits.get(platform.lower())
        if not limits or not limits.threadable:
            return [text]

        max_chars = limits.max_chars
        paras = text.split("\n\n")
        thread: List[str] = []
        current_post = ""

        for para in paras:
            sep = separator.format(n=len(thread) + 1, total="?")
            if current_post and len(current_post) + len(sep) + len(para) + 2 > max_chars:
                thread.append(current_post.strip())
                current_post = para
            elif current_post:
                current_post += "\n\n" + para
            else:
                current_post = para

        if current_post:
            thread.append(current_post.strip())

        # Add thread numbering
        total = len(thread)
        result = []
        for i, post in enumerate(thread, 1):
            sep = separator.format(n=i, total=total)
            if len(post) + len(sep) <= max_chars:
                result.append(post + sep)
            else:
                # Post is too long even alone — truncate it
                result.append(self.truncate(post, max_chars - len(sep)) + sep)

        return result

    def list_platforms(self) -> Dict[str, Dict]:
        """List all supported platforms with their limits.

        Returns:
            Dict of platform info dictionaries.
        """
        return {
            name: {
                "name": limits.name,
                "max_chars": limits.max_chars,
                "recommended_chars": limits.recommended_chars,
                "threadable": limits.threadable,
                "max_hashtags": limits.max_hashtags,
                "link_allowed": limits.link_allowed,
            }
            for name, limits in self._limits.items()
        }

    def get_best_fit_platforms(
        self,
        text: str,
        max_results: int = 3,
    ) -> List[str]:
        """Find the best-matching platforms for a given text length.

        Ranks platforms by how well the content fits their
        recommended and maximum character limits.

        Args:
            text: Content text to evaluate.
            max_results: Number of top platforms to return.

        Returns:
            List of platform names ranked by fit.
        """
        length = len(text)
        scored: List[tuple[float, str]] = []

        for name, limits in self._limits.items():
            if length <= limits.max_chars:
                # Score based on how close to recommended (closer = better)
                if length <= limits.recommended_chars:
                    score = 100.0 - (length / max(limits.recommended_chars, 1)) * 30
                else:
                    score = 70.0 - ((length - limits.recommended_chars) / max(limits.max_chars - limits.recommended_chars, 1)) * 40
                scored.append((max(0, score), name))

        scored.sort(reverse=True)
        return [name for _, name in scored[:max_results]]


def math_ceil(x: float) -> int:
    """Integer ceiling (math.ceil polyfill).

    Args:
        x: Number to round up.

    Returns:
        Smallest integer >= x.
    """
    return int(x) + (1 if x > int(x) else 0)
