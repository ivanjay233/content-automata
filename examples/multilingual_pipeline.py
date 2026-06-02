"""Multilingual content pipeline example."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from content_automata import Pipeline
from content_automata.i18n import MultiLanguageGenerator


def main():
    """Run a multilingual content generation pipeline."""
    print("=" * 60)
    print("  content-automata — Multilingual Content Pipeline")
    print("=" * 60)

    # Generate content in English first
    pipeline = Pipeline()
    print("\n[1/2] Generating source content (English)...")
    result = pipeline.from_topic(
        topic="Sustainable Business Practices",
        keywords=["sustainability", "ESG", "green business", "carbon footprint"],
        tone="professional",
    )

    print(f"\n  ✓ Source content generated: {result.final.draft.word_count} words")
    print(f"  ✓ Headline: {result.final.draft.headline}")

    # Localize to multiple languages
    print("\n[2/2] Localizing content to multiple languages...")
    i18n = MultiLanguageGenerator({"languages": ["en", "es", "fr", "de", "pt"]})

    localization_result = i18n.localize(
        topic=result.final.research.topic,
        headline=result.final.draft.headline or result.final.research.topic,
        meta_description=result.final.draft.meta_description or "",
        body=result.final.draft.blog_post or "",
        target_languages=["es", "fr", "de", "pt"],
    )

    print(f"\n  ✓ Localized to {len(localization_result.localized_contents)} languages:")
    for lang_code, content in localization_result.localized_contents.items():
        print(f"     - {content.language} ({lang_code}): {content.headline[:60]}...")
        print(f"       CTA: {content.cta_text}")

    print("\n" + "=" * 60)
    print("  Multilingual pipeline complete! ✨")
    print("=" * 60)


if __name__ == "__main__":
    main()
