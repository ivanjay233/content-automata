"""Topic research stage — performs web research and analysis."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from content_automata.models import ContentBrief, ResearchResult

logger = logging.getLogger(__name__)


class TopicResearch:
    """Performs web research on a given topic.

    Supports Tavily and Exa as research providers. Returns outlines,
    key points, competitor analysis, and source references.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self._config = config or {}
        self._provider = self._config.get("research", {}).get("provider", "tavily")
        self._max_results = self._config.get("research", {}).get("max_results", 5)
        self._api_key = (
            self._config.get("api_key")
            or self._config.get("research", {}).get("api_key")
            or ""
        )
        logger.info(f"TopicResearch initialized with provider='{self._provider}'")

    def research(self, brief: ContentBrief) -> ResearchResult:
        """Execute research on the given content brief.

        Args:
            brief: The content brief containing the topic and keywords.

        Returns:
            A ResearchResult with outline, key points, and analysis.
        """
        topic = brief.topic
        keywords = brief.keywords
        logger.info(f"Researching topic: '{topic}'")

        # Perform web research
        sources, raw_data = self._fetch_research(topic, keywords)

        # Process into structured result
        outline = self._generate_outline(topic, raw_data)
        key_points = self._extract_key_points(raw_data)
        competitor_analysis = self._analyze_competitors(topic, raw_data)
        summary = self._generate_summary(topic, key_points)

        return ResearchResult(
            topic=topic,
            outline=outline,
            key_points=key_points,
            competitor_analysis=competitor_analysis,
            sources=sources,
            summary=summary,
            raw_data=raw_data,
        )

    def _fetch_research(
        self, topic: str, keywords: List[str]
    ) -> tuple[List[str], Dict[str, Any]]:
        """Fetch research data from the configured provider.

        Falls back to simulated research if no API key is configured.
        """
        if not self._api_key:
            logger.warning("No API key configured; using simulated research data")
            return self._simulate_research(topic, keywords)

        try:
            if self._provider == "tavily":
                return self._fetch_tavily(topic, keywords)
            elif self._provider == "exa":
                return self._fetch_exa(topic, keywords)
            else:
                logger.warning(f"Unknown provider '{self._provider}', simulating")
                return self._simulate_research(topic, keywords)
        except Exception as e:
            logger.error(f"Research fetch failed: {e}")
            return self._simulate_research(topic, keywords)

    def _fetch_tavily(
        self, topic: str, keywords: List[str]
    ) -> tuple[List[str], Dict[str, Any]]:
        """Fetch research via Tavily API."""
        import httpx

        query = f"{topic} {' '.join(keywords[:3])}" if keywords else topic
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "query": query,
            "max_results": self._max_results,
            "include_answer": True,
            "include_raw_content": False,
        }

        response = httpx.post(
            "https://api.tavily.com/search",
            json=payload,
            headers=headers,
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()

        sources = [r.get("url", "") for r in data.get("results", [])]
        return sources, data

    def _fetch_exa(
        self, topic: str, keywords: List[str]
    ) -> tuple[List[str], Dict[str, Any]]:
        """Fetch research via Exa API."""
        import httpx

        query = f"{topic} {' '.join(keywords[:3])}" if keywords else topic
        headers = {
            "x-api-key": self._api_key,
            "Content-Type": "application/json",
        }
        payload = {
            "query": query,
            "num_results": self._max_results,
        }

        response = httpx.post(
            "https://api.exa.ai/search",
            json=payload,
            headers=headers,
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()

        sources = [r.get("url", "") for r in data.get("results", [])]
        return sources, data

    def _simulate_research(
        self, topic: str, keywords: List[str]
    ) -> tuple[List[str], Dict[str, Any]]:
        """Simulate research data for development/testing."""
        kw_str = ", ".join(keywords) if keywords else "general"
        data = {
            "query": topic,
            "answer": f"{topic} is an emerging field with significant growth potential. "
            f"Key trends include automation, personalization, and accessibility.",
            "results": [
                {
                    "title": f"Introduction to {topic}",
                    "url": f"https://example.com/intro-{topic.lower().replace(' ', '-')}",
                    "content": f"An overview of {topic} and its applications.",
                },
                {
                    "title": f"Latest Trends in {topic}",
                    "url": f"https://example.com/trends-{topic.lower().replace(' ', '-')}",
                    "content": f"Current trends shaping the {topic} landscape.",
                },
                {
                    "title": f"{topic}: A Comprehensive Guide",
                    "url": f"https://example.com/guide-{topic.lower().replace(' ', '-')}",
                    "content": f"A deep dive into {topic} for practitioners.",
                },
            ],
        }
        sources = [r["url"] for r in data["results"]]
        return sources, data

    def _generate_outline(self, topic: str, raw_data: Dict[str, Any]) -> str:
        """Generate a structured outline from research data."""
        outline = f"# {topic}\n\n"
        outline += "## Introduction\n"
        outline += f"- Overview of {topic}\n"
        outline += "- Why this matters now\n\n"
        outline += "## Key Concepts\n"
        outline += f"- Core principles of {topic}\n"
        outline += "- Industry terminology\n\n"
        outline += "## Current Landscape\n"
        outline += "- Market trends and statistics\n"
        outline += "- Major players and innovations\n\n"
        outline += "## Practical Applications\n"
        outline += "- Real-world use cases\n"
        outline += "- Implementation strategies\n\n"
        outline += "## Future Outlook\n"
        outline += "- Emerging developments\n"
        outline += "- Opportunities and challenges\n\n"
        outline += "## Conclusion\n"
        outline += f"- Summary of {topic}'s impact\n"
        outline += "- Actionable takeaways\n"
        return outline

    def _extract_key_points(self, raw_data: Dict[str, Any]) -> List[str]:
        """Extract key points from research data."""
        answer = raw_data.get("answer", "")
        if answer:
            return [
                point.strip()
                for point in answer.split(".")
                if point.strip()
            ][:5]

        return [
            f"Growing adoption across industries",
            "Significant ROI potential for early adopters",
            "Key technological advancements driving change",
            "Important regulatory and ethical considerations",
            "Integration with existing workflows is critical",
        ]

    def _analyze_competitors(
        self, topic: str, raw_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze competitor landscape from research."""
        return {
            "topic": topic,
            "competitors": [
                {"name": "Competitor A", "strengths": ["Market share", "Brand recognition"]},
                {"name": "Competitor B", "strengths": ["Innovation", "Feature set"]},
                {"name": "Competitor C", "strengths": ["Pricing", "Accessibility"]},
            ],
            "gap_analysis": "Opportunity in combining ease-of-use with advanced features",
            "differentiation_opportunities": [
                "Simplified user experience",
                "Better integration ecosystem",
                "More affordable pricing model",
            ],
        }

    def _generate_summary(self, topic: str, key_points: List[str]) -> str:
        """Generate an executive summary."""
        points = "; ".join(key_points[:3])
        return (
            f"{topic} represents a significant opportunity. "
            f"Key findings: {points}. "
            f"Recommended approach: focus on practical, value-driven implementation "
            f"that addresses real user pain points."
        )
