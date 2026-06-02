"""Basic pipeline example — blog post from topic."""

import sys
from pathlib import Path

# Add parent directory to path for direct script execution
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from content_automata import Pipeline


def main():
    """Run a basic content pipeline from a topic."""
    print("=" * 60)
    print("  content-automata — Basic Pipeline Example")
    print("  Topic: AI for Small Businesses")
    print("=" * 60)

    # Initialize the pipeline
    pipeline = Pipeline()

    print("\n[1/4] Running research stage...")
    print("[2/4] Generating copy...")
    print("[3/4] Creating visuals...")
    print("[4/4] Exporting content...\n")

    # Run the pipeline
    result = pipeline.from_topic(
        topic="AI for Small Businesses",
        keywords=["automation", "customer service", "marketing", "efficiency"],
        target_audience="small business owners and entrepreneurs",
        tone="professional",
    )

    # Display results
    print("\n" + "=" * 60)
    print("  RESULTS")
    print("=" * 60)

    print(f"\n📝 Topic: {result.final.research.topic}")
    print(f"📊 State: {result.state.value}")
    print(f"📅 Completed: {result.completed_at}")

    print(f"\n── Research Summary ──")
    print(result.final.research.summary)

    print(f"\n── Key Points ──")
    for i, point in enumerate(result.final.research.key_points, 1):
        print(f"  {i}. {point}")

    print(f"\n── Draft Info ──")
    print(f"  Headline: {result.final.draft.headline}")
    print(f"  Tone: {result.final.draft.tone}")
    print(f"  Word Count: {result.final.draft.word_count}")

    print(f"\n── Visual Assets ──")
    for img in result.final.visuals.images:
        print(f"  🖼  {img.url}")
        print(f"     Aspect: {img.aspect_ratio}, Alt: {img.alt_text[:60]}...")

    print(f"\n── Exports ──")
    for exp in result.final.schedule.exports:
        print(f"  📄 {exp.format.upper()}: {exp.file_path or 'in-memory'}")

    print(f"\n── Blog Post Preview (first 500 chars) ──")
    if result.final.draft.blog_post:
        preview = result.final.draft.blog_post[:500]
        print(preview + "...")

    print("\n" + "=" * 60)
    print("  Pipeline complete! ✨")
    print("=" * 60)


if __name__ == "__main__":
    main()
