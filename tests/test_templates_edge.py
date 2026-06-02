"""Tests for template rendering functionality."""

import pytest

from content_automata.templates import (
    BUILTIN_TEMPLATES,
    ContentTemplate,
    TemplateField,
    TemplateManager,
)


class TestTemplateRendering:
    """Tests for template rendering and management."""

    def test_all_builtin_templates_exist(self):
        """Test that all expected builtin templates are available."""
        expected = {"blog", "social", "newsletter", "ad"}
        for name in expected:
            assert name in BUILTIN_TEMPLATES, f"Missing builtin template: {name}"

    def test_builtin_templates_have_required_fields(self):
        """Test that all builtin templates have required properties."""
        for name, tpl in BUILTIN_TEMPLATES.items():
            assert tpl.name, f"Template {name} missing name"
            assert tpl.label, f"Template {name} missing label"
            assert tpl.description, f"Template {name} missing description"
            assert len(tpl.sections) > 0, f"Template {name} has no sections"
            assert tpl.suggested_length > 0, f"Template {name} has no suggested length"

    def test_blog_template_structure(self):
        """Test blog template structure."""
        blog = BUILTIN_TEMPLATES["blog"]
        assert blog.seo_priority == "high"
        assert "seo" in blog.tags
        assert "title" in blog.sections
        assert "body" in blog.sections
        assert "introduction" in blog.sections

    def test_social_template_structure(self):
        """Test social template structure."""
        social = BUILTIN_TEMPLATES["social"]
        assert social.seo_priority == "low"
        assert "social" in social.tags
        assert "hashtags" in social.sections

    def test_newsletter_template_structure(self):
        """Test newsletter template structure."""
        nsl = BUILTIN_TEMPLATES["newsletter"]
        assert "newsletter" in nsl.tags
        assert "subject_line" in nsl.sections

    def test_ad_template_structure(self):
        """Test ad template structure."""
        ad = BUILTIN_TEMPLATES["ad"]
        assert "ad" in ad.tags
        assert "cta" in ad.sections
        assert "headline" in ad.sections

    def test_template_manager_list_templates(self):
        """Test listing templates from TemplateManager."""
        mgr = TemplateManager()
        templates = mgr.list_templates()
        assert len(templates) >= 4
        assert "blog" in templates
        assert "social" in templates

    def test_template_manager_get_template(self):
        """Test getting a specific template."""
        mgr = TemplateManager()
        blog = mgr.get_template("blog")
        assert blog is not None
        assert blog.label == "Blog Post"

    def test_template_manager_get_nonexistent(self):
        """Test getting a nonexistent template returns None."""
        mgr = TemplateManager()
        assert mgr.get_template("nonexistent") is None

    def test_register_custom_template(self):
        """Test registering a custom template."""
        mgr = TemplateManager()
        custom = ContentTemplate(
            name="custom_test",
            label="Custom Test",
            description="A test template",
            sections=["intro", "body", "outro"],
            suggested_length=500,
            seo_priority="medium",
            tags=["test"],
            fields=[
                TemplateField(name="custom_field", label="Custom Field", field_type="text"),
            ],
        )
        mgr.register_template(custom)
        retrieved = mgr.get_template("custom_test")
        assert retrieved is not None
        assert retrieved.name == "custom_test"
        assert len(retrieved.fields) == 1

    def test_remove_template(self):
        """Test removing a template."""
        mgr = TemplateManager()
        # Register a temporary template
        tmp = ContentTemplate(name="temp", label="Temp", description="Temporary")
        mgr.register_template(tmp)
        assert mgr.get_template("temp") is not None
        assert mgr.remove_template("temp") is True
        assert mgr.get_template("temp") is None

    def test_remove_nonexistent_template(self):
        """Test removing a nonexistent template returns False."""
        mgr = TemplateManager()
        assert mgr.remove_template("nonexistent") is False

    def test_get_sections(self):
        """Test getting template sections."""
        mgr = TemplateManager()
        sections = mgr.get_sections("blog")
        assert isinstance(sections, list)
        assert len(sections) > 0
        assert "title" in sections

    def test_get_sections_nonexistent(self):
        """Test getting sections for nonexistent template."""
        mgr = TemplateManager()
        assert mgr.get_sections("nonexistent") == []

    def test_template_field_defaults(self):
        """Test TemplateField default values."""
        field = TemplateField(name="test", label="Test Field")
        assert field.field_type == "text"
        assert field.required is False
        assert field.default is None
        assert field.options is None
        assert field.description == ""

    def test_template_field_all_fields(self):
        """Test TemplateField with all fields specified."""
        field = TemplateField(
            name="choice",
            label="Choice",
            field_type="select",
            required=True,
            default="option1",
            options=["option1", "option2"],
            description="Choose an option",
        )
        assert field.name == "choice"
        assert field.required is True
        assert field.default == "option1"
        assert len(field.options) == 2

    def test_template_suggested_length_variation(self):
        """Test that templates have different suggested lengths."""
        blog = BUILTIN_TEMPLATES["blog"]
        social = BUILTIN_TEMPLATES["social"]
        assert blog.suggested_length != social.suggested_length

    def test_template_sections_are_ordered(self):
        """Test that template sections maintain order."""
        blog = BUILTIN_TEMPLATES["blog"]
        sections = blog.sections
        # Sections should be in logical order
        assert sections.index("title") < sections.index("body")

    def test_template_tag_categorization(self):
        """Test that templates have appropriate tags."""
        for name, tpl in BUILTIN_TEMPLATES.items():
            assert len(tpl.tags) > 0, f"Template {name} has no tags"

    def test_default_templates_immutable(self):
        """Test that modifying a retrieved template doesn't affect the original."""
        mgr = TemplateManager()
        blog = mgr.get_template("blog")
        blog.suggested_length = 9999
        # Re-retrieve and verify original is unchanged
        blog_again = mgr.get_template("blog")
        assert blog_again.suggested_length != 9999

    def test_custom_template_overrides_builtin(self):
        """Test that registering a template with builtin name overrides it."""
        mgr = TemplateManager()
        custom_blog = ContentTemplate(
            name="blog",
            label="Custom Blog",
            description="Overridden blog template",
            sections=["custom"],
            suggested_length=100,
        )
        mgr.register_template(custom_blog)
        retrieved = mgr.get_template("blog")
        assert retrieved.label == "Custom Blog"
        # Restore
        mgr.remove_template("blog")

    def test_blog_template_fields(self):
        """Test blog template has expected fields."""
        blog = BUILTIN_TEMPLATES["blog"]
        field_names = {f.name for f in blog.fields}
        assert "target_keyword" in field_names
        assert "read_time" in field_names

    def test_template_field_required_in_blog(self):
        """Test that target_keyword is required in blog template."""
        blog = BUILTIN_TEMPLATES["blog"]
        kw_field = next((f for f in blog.fields if f.name == "target_keyword"), None)
        assert kw_field is not None
        assert kw_field.required is True

    def test_newsletter_has_subject_line(self):
        """Test newsletter template has subject_line section."""
        nsl = BUILTIN_TEMPLATES["newsletter"]
        assert "subject_line" in nsl.sections
