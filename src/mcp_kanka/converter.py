"""Content conversion between Markdown and HTML with Kanka mention preservation."""

import re

import markdown
from markdownify import markdownify as md


class ContentConverter:
    """Handles conversion between Markdown and HTML while preserving Kanka mentions."""

    # Pattern for Kanka mentions: [entity:ID] or [entity:ID|text]
    MENTION_PATTERN = re.compile(r"\[entity:(\d+)(?:\|([^\]]+))?\]")

    # Placeholder format for protecting mentions during conversion
    PLACEHOLDER_TEMPLATE = "KANKAMENTIONPLACEHOLDER{}"
    PLACEHOLDER_PATTERN = re.compile(r"KANKAMENTIONPLACEHOLDER(\d+)")

    def __init__(self) -> None:
        """Initialize the converter with markdown extensions."""
        self.md = markdown.Markdown(
            extensions=[
                "markdown.extensions.nl2br",  # Convert newlines to <br>
                "markdown.extensions.fenced_code",  # Support for code blocks
                "markdown.extensions.tables",  # Support for tables
                "markdown.extensions.sane_lists",  # Better list handling
            ]
        )

    def markdown_to_html(self, content: str) -> str:
        """
        Convert Markdown to HTML while preserving Kanka mentions.

        Args:
            content: Markdown content

        Returns:
            HTML content with mentions preserved
        """
        if not content:
            return ""

        # Extract and protect mentions
        protected_content, mentions = self._protect_mentions(content)

        # Convert to HTML
        html = self.md.convert(protected_content)

        # Restore mentions
        html = self._restore_mentions(html, mentions)

        # Reset markdown instance for next use
        self.md.reset()

        return html

    def html_to_markdown(self, html: str) -> str:
        """
        Convert HTML to Markdown while preserving Kanka mentions.

        Args:
            html: HTML content

        Returns:
            Markdown content with mentions preserved
        """
        if not html:
            return ""

        # Extract and protect mentions
        protected_html, mentions = self._protect_mentions(html)

        # Use markdownify to convert HTML to Markdown
        markdown_text: str = md(
            protected_html,
            heading_style="ATX",  # Use # for headings
            bullets="-",  # Use - for unordered lists
            code_language="",  # Don't add language to code blocks
        )

        # Restore mentions
        markdown_text = self._restore_mentions(markdown_text, mentions)

        # Clean up extra whitespace
        markdown_text = re.sub(r"\n{3,}", "\n\n", markdown_text.strip())

        return markdown_text

    def _protect_mentions(self, content: str) -> tuple[str, list[tuple[str, str, str]]]:
        """
        Replace mentions with placeholders to protect them during conversion.

        Args:
            content: Original content with mentions

        Returns:
            Tuple of (protected content, list of (placeholder, entity_id, text))
        """
        mentions = []
        placeholder_counter = 0

        def replace_mention(match: re.Match[str]) -> str:
            nonlocal placeholder_counter
            entity_id = match.group(1)
            text = match.group(2)
            placeholder = self.PLACEHOLDER_TEMPLATE.format(placeholder_counter)
            placeholder_counter += 1

            mentions.append((placeholder, entity_id, text))
            return placeholder

        protected_content = self.MENTION_PATTERN.sub(replace_mention, content)
        return protected_content, mentions

    def _restore_mentions(
        self, content: str, mentions: list[tuple[str, str, str]]
    ) -> str:
        """
        Restore mentions from placeholders.

        Args:
            content: Content with placeholders
            mentions: List of (placeholder, entity_id, text)

        Returns:
            Content with mentions restored
        """
        # Sort mentions by placeholder length (descending) to avoid partial replacements
        # This ensures KANKAMENTIONPLACEHOLDER10 is replaced before KANKAMENTIONPLACEHOLDER1
        sorted_mentions = sorted(mentions, key=lambda x: len(x[0]), reverse=True)

        for placeholder, entity_id, text in sorted_mentions:
            if text:
                mention = f"[entity:{entity_id}|{text}]"
            else:
                mention = f"[entity:{entity_id}]"
            content = content.replace(placeholder, mention)

        return content
