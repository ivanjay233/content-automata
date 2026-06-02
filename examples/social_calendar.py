"""Social media content calendar example."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from content_automata.calendar import CalendarPlanner


def main():
    """Generate a monthly social media content calendar."""
    print("=" * 60)
    print("  content-automata — Social Media Content Calendar")
    print("=" * 60)

    # Topics for the month
    topics = [
        "AI in Business",
        "Remote Work Best Practices",
        "Digital Marketing Trends",
        "Customer Experience Optimization",
        "Data-Driven Decision Making",
        "Cybersecurity Essentials",
        "Innovation in the Workplace",
        "Employee Wellbeing Programs",
        "Sustainable Business Growth",
        "Leadership in the Digital Age",
    ]

    # Generate calendar
    planner = CalendarPlanner()
    calendar = planner.plan_month(topics)

    print(f"\n📅 Content Calendar for {calendar.month}")
    print(f"📊 Total items: {calendar.total_items}")
    print()

    # Print weekly overview
    current_week = 1
    for i, entry in enumerate(calendar.entries):
        if i > 0 and i % 7 == 0:
            print(f"\n{'─' * 50}")
            current_week += 1

        icon = {"blog": "📝", "social": "💬", "newsletter": "📧", "ad": "📢"}
        print(f"  {icon.get(entry.content_type, '📄')} {entry.date} | "
              f"[{entry.content_type.upper():10}] {entry.topic[:45]}")

    # Show content mix
    print(f"\n📊 Content Mix:")
    from collections import Counter
    mix = Counter(e.content_type for e in calendar.entries)
    for content_type, count in mix.most_common():
        print(f"  {content_type.title():15}: {count} items")

    # Export as markdown
    print(f"\n📄 Calendar exported as markdown ({len(calendar.to_markdown())} chars)")
    print(f"📄 Calendar exported as JSON ({len(calendar.to_json())} chars)")

    print("\n" + "=" * 60)
    print("  Calendar generation complete! ✨")
    print("=" * 60)


if __name__ == "__main__":
    main()
