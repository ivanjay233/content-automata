"""SEO-optimized blog post pipeline example."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from content_automata import Pipeline
from content_automata.seo import SEOAnalyzer
from content_automata.quality import QualityScorer
from content_automata.suggestions import SuggestionEngine


def main():
    """Run an SEO-optimized blog post pipeline with quality check."""
    print("=" * 60)
    print("  content-automata — SEO-Optimized Blog Pipeline")
    print("=" * 60)

    # Pipeline config with SEO focus
    config = {
        "research": {
            "provider": "tavily",
            "max_results": 10,
        },
        "copywriting": {
            "default_tone": "professional",
            "variants": ["blog", "social"],
        },
        "image_generation": {
            "default_aspect": "16:9",
        },
    }

    pipeline = Pipeline(config=config)

    # Define target keywords
    target_keywords = [
        "content marketing strategy",
        "digital content creation",
        "SEO optimization",
        "content automation",
    ]

    print(f"\n🎯 Target Keywords: {', '.join(target_keywords)}")

    # Generate content
    print("\n[1/3] Generating SEO-optimized content...")
    result = pipeline.from_topic(
        topic="Content Marketing Strategy for 2026",
        keywords=target_keywords,
        tone="professional",
    )

    print(f"  ✓ Content generated: {result.final.draft.word_count} words")
    print(f"  ✓ Headline: {result.final.draft.headline}")

    # Run SEO analysis
    print("\n[2/3] Running SEO analysis...")
    seo = SEOAnalyzer({"target_keywords": target_keywords})
    seo_result = seo.analyze(result.final.draft, target_keywords)

    print(f"  📊 SEO Score: {seo_result.overall:.1%}")
    print(f"  📊 Title Score: {seo_result.title_score:.1%}")
    print(f"  📊 Meta Score: {seo_result.meta_score:.1%}")
    print(f"  📊 Keyword Score: {seo_result.keyword_score:.1%}")
    print(f"  📊 Structure Score: {seo_result.structure_score:.1%}")

    if seo_result.keywords:
        print(f"\n  🔑 Keyword Analysis:")
        for kw in seo_result.keywords[:3]:
            print(f"     '{kw.keyword}': count={kw.count}, "
                  f"density={kw.density:.2f}%, "
                  f"title={'✓' if kw.in_title else '✗'}, "
                  f"meta={'✓' if kw.in_meta else '✗'}")

    if seo_result.suggestions:
        print(f"\n  💡 SEO Suggestions:")
        for s in seo_result.suggestions[:3]:
            print(f"     • {s}")

    # Quality scoring
    print("\n[3/3] Running quality assessment...")
    quality = QualityScorer()
    quality_report = quality.score(result.final.draft, result.final.research)

    print(f"  ⭐ Overall Quality: {quality_report.overall_score:.1%}")
    for name, score in quality_report.scores.items():
        icon = "✅" if score.score >= 0.7 else "⚠️" if score.score >= 0.5 else "❌"
        print(f"     {icon} {name.title()}: {score.score:.1%}")

    if quality_report.strengths:
        print(f"\n  💪 Strengths:")
        for s in quality_report.strengths:
            print(f"     ✓ {s}")

    if quality_report.improvements:
        print(f"\n  📈 Areas to Improve:")
        for imp in quality_report.improvements[:3]:
            print(f"     • {imp}")

    # Hashtag suggestions
    engine = SuggestionEngine()
    hashtags = engine.suggest_hashtags(result.final.research.topic, result.final.draft.blog_post)
    keywords = engine.suggest_keywords(result.final.research.topic, result.final.draft.blog_post)

    print(f"\n  🏷️  Suggested Hashtags: {' '.join(h.tag for h in hashtags[:5])}")
    print(f"  🔑 Suggested Keywords: {', '.join(k.keyword for k in keywords[:3])}")

    print("\n" + "=" * 60)
    print("  SEO-optimized pipeline complete! ✨")
    print("=" * 60)


if __name__ == "__main__":
    main()
