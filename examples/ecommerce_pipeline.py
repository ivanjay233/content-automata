"""
E-Commerce Product Description Pipeline

Demonstrates generating SEO-optimized product descriptions
for e-commerce products using the content-automata pipeline.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from content_automata import Pipeline


# Sample product data
PRODUCTS = [
    {
        "name": "Wireless Noise-Canceling Headphones",
        "category": "Electronics",
        "features": [
            "40-hour battery life",
            "Active noise cancellation",
            "Bluetooth 5.3",
            "Comfortable over-ear design",
            "Built-in microphone",
        ],
        "target_audience": "frequent travelers and remote workers",
    },
    {
        "name": "Organic Cotton Yoga Mat",
        "category": "Fitness",
        "features": [
            "Eco-friendly organic cotton",
            "Non-slip surface",
            "6mm thickness for comfort",
            "Includes carrying strap",
            "Machine washable",
        ],
        "target_audience": "yoga practitioners and fitness enthusiasts",
    },
    {
        "name": "Smart Plant Watering System",
        "category": "Home & Garden",
        "features": [
            "WiFi-connected smart sensor",
            "Custom watering schedules",
            "Works with indoor and outdoor plants",
            "Battery-powered, lasts 6 months",
            "Companion mobile app",
        ],
        "target_audience": "plant lovers and busy homeowners",
    },
]


def format_product_features(features, max_chars=200):
    """Format product features for the pipeline."""
    text = "Features: "
    for feat in features:
        text += f"• {feat} "
        if len(text) > max_chars:
            text += "..."
            break
    return text


def generate_product_description(product):
    """Generate a product description using the pipeline.

    Args:
        product: Product dictionary with name, category, features.

    Returns:
        Generated content package.
    """
    pipeline = Pipeline()

    topic = product["name"]
    features_text = format_product_features(product["features"])
    instructions = (
        f"Write an e-commerce product description for {product['name']} "
        f"in the {product['category']} category. "
        f"Include: compelling headline, key features and benefits, "
        f"technical specifications, and a clear call-to-action. "
        f"{features_text}"
    )

    result = pipeline.from_topic(
        topic=topic,
        keywords=[product["category"].lower(), *product["name"].lower().split()[:3]],
        target_audience=product["target_audience"],
        tone="persuasive",
        custom_instructions=instructions,
    )

    return result


def main():
    """Generate product descriptions for all sample products."""
    print("=" * 60)
    print("  E-Commerce Product Description Pipeline")
    print("=" * 60)

    for i, product in enumerate(PRODUCTS, 1):
        print(f"\n{'─' * 60}")
        print(f"  Product {i}/{len(PRODUCTS)}: {product['name']}")
        print(f"  Category: {product['category']}")
        print(f"  Target: {product['target_audience']}")
        print(f"{'─' * 60}")

        result = generate_product_description(product)

        print(f"\n  📝 State: {result.state.value}")
        print(f"  📊 Word Count: {result.final.draft.word_count}")
        print(f"  🎯 Tone: {result.final.draft.tone}")
        print(f"  💡 Headline: {result.final.draft.headline}")
        print(f"  📋 Summary: {result.final.research.summary[:120]}...")

        if result.final.draft.blog_post:
            preview = result.final.draft.blog_post[:300]
            print(f"\n  Preview:\n  {preview}...")

        print()

    print("=" * 60)
    print("  All product descriptions generated! ✨")
    print("=" * 60)


if __name__ == "__main__":
    main()
