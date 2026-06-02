"""WordPress/HTML export for publishing."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from content_automata.models import Draft, FinalContent

logger = logging.getLogger(__name__)


@dataclass
class WordPressPost:
    """A WordPress-compatible post object."""

    title: str
    content: str
    excerpt: str = ""
    slug: str = ""
    status: str = "draft"  # draft, publish, pending
    categories: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    featured_media_url: Optional[str] = None
    meta: Dict[str, str] = field(default_factory=dict)


class WordPressExporter:
    """Exports content in WordPress-compatible formats.

    Supports WordPress REST API XML-RPC payload format and
    generates import-ready HTML with Gutenberg-compatible blocks.
    """

    def __init__(self, config: Optional[Dict] = None):
        self._config = config or {}
        self._site_url = self._config.get("wordpress_url", "")
        self._default_status = self._config.get("default_post_status", "draft")

    def export(
        self, final: FinalContent, brief: Dict[str, Any] | None = None
    ) -> WordPressPost:
        """Create a WordPress post from pipeline output.

        Args:
            final: The complete pipeline output.
            brief: Optional brief with additional metadata.

        Returns:
            A WordPressPost ready for REST API submission.
        """
        title = final.draft.headline or final.research.topic
        slug = title.lower().replace(" ", "-").replace("--", "-")[:50]

        # Build Gutenberg-compatible HTML content
        content_parts: List[str] = []

        # Featured image banner note
        if final.visuals.primary_image:
            content_parts.append(
                f'<!-- wp:image {{"id":0,"sizeSlug":"large"}} -->\n'
                f'<figure class="wp-block-image size-large">\n'
                f'    <img src="{final.visuals.primary_image.url}" '
                f'alt="{final.visuals.primary_image.alt_text}" />\n'
                f'</figure>\n'
                f'<!-- /wp:image -->\n'
            )

        # Research summary as intro
        if final.research.summary:
            content_parts.append(
                f'<!-- wp:paragraph -->\n'
                f'<p>{final.research.summary}</p>\n'
                f'<!-- /wp:paragraph -->\n'
            )

        # Main blog content
        if final.draft.blog_post:
            # Convert markdown headings to HTML
            html_body = self._markdown_to_html(final.draft.blog_post)
            content_parts.append(
                f'<!-- wp:html -->\n{html_body}\n<!-- /wp:html -->\n'
            )

        # Key points as list
        if final.research.key_points:
            points_html = "\n".join(
                f'<li>{point}</li>' for point in final.research.key_points
            )
            content_parts.append(
                f'<!-- wp:list -->\n'
                f'<ul>\n{points_html}\n</ul>\n'
                f'<!-- /wp:list -->\n'
            )

        # Image gallery
        if len(final.visuals.images) > 1:
            gallery_images = "\n".join(
                f'    <li class="blocks-gallery-item">\n'
                f'        <figure>\n'
                f'            <img src="{img.url}" alt="{img.alt_text}" />\n'
                f'        </figure>\n'
                f'    </li>'
                for img in final.visuals.images[1:]
            )
            content_parts.append(
                f'<!-- wp:gallery {{"columns":2}} -->\n'
                f'<figure class="wp-block-gallery has-nested-images columns-default is-cropped">\n'
                f'    <ul class="blocks-gallery-grid">\n{gallery_images}\n    </ul>\n'
                f'</figure>\n'
                f'<!-- /wp:gallery -->\n'
            )

        # Excerpt / meta description
        excerpt = final.draft.meta_description or final.research.summary[:160]

        # Tags from research
        tags = final.research.key_points[:3] if final.research.key_points else []
        tags = [t[:30] for t in tags]  # WordPress tag limit

        return WordPressPost(
            title=title,
            content="\n".join(content_parts),
            excerpt=excerpt,
            slug=slug,
            status=brief.get("post_status", self._default_status) if brief else self._default_status,
            categories=brief.get("categories", []) if brief else [],
            tags=tags,
            featured_media_url=final.visuals.primary_image.url if final.visuals.primary_image else None,
            meta={
                "seo_title": title,
                "meta_description": excerpt,
                "focus_keyword": final.research.topic,
            },
        )

    def to_rest_api_payload(self, post: WordPressPost) -> Dict[str, Any]:
        """Convert a WordPressPost to WordPress REST API payload.

        Args:
            post: The WordPress post object.

        Returns:
            Dict ready for WP REST API POST /wp-json/wp/v2/posts.
        """
        payload: Dict[str, Any] = {
            "title": post.title,
            "content": post.content,
            "excerpt": post.excerpt,
            "slug": post.slug,
            "status": post.status,
            "meta": post.meta,
        }

        if post.featured_media_url:
            payload["featured_media_url"] = post.featured_media_url

        return payload

    def to_xmlrpc_payload(self, post: WordPressPost) -> Dict[str, Any]:
        """Convert a WordPressPost to XML-RPC (wp.newPost) payload.

        Args:
            post: The WordPress post object.

        Returns:
            Dict ready for WordPress XML-RPC API.
        """
        return {
            "post_title": post.title,
            "post_content": post.content,
            "post_excerpt": post.excerpt,
            "post_status": post.status,
            "post_name": post.slug,
            "terms": {
                "category": post.categories,
                "post_tag": post.tags,
            },
            "custom_fields": [
                {"key": k, "value": v} for k, v in post.meta.items()
            ],
        }

    def to_html_file(self, post: WordPressPost) -> str:
        """Export as standalone HTML file.

        Args:
            post: The WordPress post object.

        Returns:
            Complete HTML document string.
        """
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="{post.excerpt}">
    <title>{post.title}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 800px; margin: 0 auto; padding: 2rem; line-height: 1.6; }}
        img {{ max-width: 100%; height: auto; }}
        h1, h2, h3 {{ color: #1a1a1a; }}
        figure {{ margin: 2rem 0; text-align: center; }}
        figcaption {{ font-style: italic; color: #666; }}
        .wp-block-gallery {{ display: flex; flex-wrap: wrap; gap: 1rem; }}
        .wp-block-gallery figure {{ flex: 1 1 45%; }}
    </style>
</head>
<body>
    <article>
        <h1>{post.title}</h1>
        {post.content}
    </article>
</body>
</html>"""

    def _markdown_to_html(self, markdown: str) -> str:
        """Convert basic markdown to HTML.

        Args:
            markdown: Markdown content.

        Returns:
            HTML string.
        """
        lines = markdown.split("\n")
        html_lines = []
        in_list = False

        for line in lines:
            # Headings
            if line.startswith("# "):
                if in_list:
                    html_lines.append("</ul>")
                    in_list = False
                html_lines.append(f"<h1>{line[2:]}</h1>")
            elif line.startswith("## "):
                if in_list:
                    html_lines.append("</ul>")
                    in_list = False
                html_lines.append(f"<h2>{line[3:]}</h2>")
            elif line.startswith("### "):
                if in_list:
                    html_lines.append("</ul>")
                    in_list = False
                html_lines.append(f"<h3>{line[4:]}</h3>")
            # Bold/italic
            elif line.strip().startswith("**") and line.strip().endswith("**"):
                if in_list:
                    html_lines.append("</ul>")
                    in_list = False
                html_lines.append(f"<p><strong>{line.strip('* ')}</strong></p>")
            # List items
            elif line.strip().startswith("- ") or line.strip().startswith("* "):
                if not in_list:
                    html_lines.append("<ul>")
                    in_list = True
                html_lines.append(f"<li>{line.strip()[2:]}</li>")
            elif line.strip().startswith("1. ") or line.strip().startswith("2. "):
                if not in_list:
                    html_lines.append("<ol>")
                    in_list = True
                html_lines.append(f"<li>{line.strip()[3:]}</li>")
            # Empty line
            elif not line.strip():
                if in_list:
                    html_lines.append("</ul>")
                    in_list = False
                html_lines.append("")
            # Paragraph
            else:
                if in_list:
                    html_lines.append("</ul>")
                    in_list = False
                html_lines.append(f"<p>{line}</p>")

        if in_list:
            html_lines.append("</ul>")

        return "\n".join(html_lines)
