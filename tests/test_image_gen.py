"""Tests for the image generation stage."""

import pytest

from content_automata.models import ContentBrief, Draft, VisualAsset, VisualsResult
from content_automata.stages.image_gen import ImageGenerator


class TestImageGeneratorInit:
    """Test ImageGenerator initialization."""

    def test_default_init(self):
        gen = ImageGenerator()
        assert gen._provider == "openai"
        assert gen._default_aspect == "16:9"

    def test_custom_config(self):
        config = {"image_generation": {"provider": "stability", "default_aspect": "1:1"}}
        gen = ImageGenerator(config)
        assert gen._provider == "stability"
        assert gen._default_aspect == "1:1"


class TestImageGeneratorGeneration:
    """Test image generation."""

    def test_generate_without_api_key(self):
        gen = ImageGenerator()
        draft = Draft(blog_post="Content about AI", headline="AI Overview")
        brief = ContentBrief(topic="Artificial Intelligence")
        result = gen.generate(draft, brief)
        assert isinstance(result, VisualsResult)
        assert len(result.images) > 0

    def test_generated_images_have_urls(self):
        gen = ImageGenerator()
        draft = Draft(blog_post="Tech trends", headline="Tech 2026")
        brief = ContentBrief(topic="Technology")
        result = gen.generate(draft, brief)
        for img in result.images:
            assert img.url != ""

    def test_generated_images_have_prompts(self):
        gen = ImageGenerator()
        draft = Draft(blog_post="Health tips", headline="Healthy Living")
        brief = ContentBrief(topic="Health")
        result = gen.generate(draft, brief)
        for img in result.images:
            assert img.prompt != ""

    def test_primary_image_set(self):
        gen = ImageGenerator()
        draft = Draft(blog_post="Science", headline="Science Breakthroughs")
        brief = ContentBrief(topic="Science")
        result = gen.generate(draft, brief)
        assert result.primary_image is not None
        assert result.primary_image == result.images[0]


class TestPromptGeneration:
    """Test prompt generation."""

    def test_prompts_for_blog_post(self):
        gen = ImageGenerator()
        prompts = gen._generate_prompts("AI", "AI in Business", "Blog content here")
        assert len(prompts) >= 2
        # With blog post, should have 3 prompts
        assert len(prompts) == 3

    def test_prompts_without_blog_post(self):
        gen = ImageGenerator()
        prompts = gen._generate_prompts("AI", "AI Title", None)
        assert len(prompts) == 2

    def test_prompt_contains_topic(self):
        gen = ImageGenerator()
        topic = "Quantum Computing"
        prompts = gen._generate_prompts(topic, "QC Title", None)
        # First prompt should contain the full topic
        assert topic in prompts[0] or topic.lower() in prompts[0].lower()


class TestSimulation:
    """Test simulated image generation."""

    def test_simulate_image_creates_asset(self):
        gen = ImageGenerator()
        asset = gen._simulate_image("Test prompt", "16:9")
        assert isinstance(asset, VisualAsset)
        assert "placeholder.com" in asset.url

    def test_simulate_aspect_ratio_16_9(self):
        gen = ImageGenerator()
        asset = gen._simulate_image("Test", "16:9")
        assert asset.width == 1920
        assert asset.height == 1080

    def test_simulate_aspect_ratio_1_1(self):
        gen = ImageGenerator()
        asset = gen._simulate_image("Test", "1:1")
        assert asset.width == 1024
        assert asset.height == 1024

    def test_simulate_aspect_ratio_9_16(self):
        gen = ImageGenerator()
        asset = gen._simulate_image("Test", "9:16")
        assert asset.width == 1080
        assert asset.height == 1920

    def test_simulate_unknown_aspect_defaults(self):
        gen = ImageGenerator()
        asset = gen._simulate_image("Test", "3:2")
        assert asset.width == 1024
        assert asset.height == 1024  # defaults


class TestAspectRatio:
    """Test aspect ratio handling."""

    def test_default_aspect_from_config(self):
        gen = ImageGenerator()
        brief = ContentBrief(topic="Test")
        aspect = gen._get_aspect_ratio(brief)
        assert aspect == "16:9"

    def test_aspect_from_custom_instructions(self):
        gen = ImageGenerator()
        brief = ContentBrief(topic="Test", custom_instructions="1:1")
        aspect = gen._get_aspect_ratio(brief)
        assert aspect == "1:1"

    def test_aspect_invalid_in_instructions(self):
        gen = ImageGenerator()
        brief = ContentBrief(topic="Test", custom_instructions="Some text without aspect")
        aspect = gen._get_aspect_ratio(brief)
        assert aspect == "16:9"  # falls back to default
