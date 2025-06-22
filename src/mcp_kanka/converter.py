"""Content conversion between Markdown and HTML with Kanka mention preservation."""

import re

import mistune
from markdownify import markdownify as md


class ContentConverter:
    """Handles conversion between Markdown and HTML while preserving Kanka mentions and HTML embeds."""

    # Pattern for Kanka mentions: [entity:ID] or [entity:ID|text]
    MENTION_PATTERN = re.compile(r"\[entity:(\d+)(?:\|([^\]]+))?\]")

    # Placeholder format for protecting mentions during conversion
    PLACEHOLDER_TEMPLATE = "KANKAMENTIONPLACEHOLDER{}"
    PLACEHOLDER_PATTERN = re.compile(r"KANKAMENTIONPLACEHOLDER(\d+)")

    # Pattern for HTML embeds to preserve (iframe, embed, video, audio, object)
    # Note: While we preserve all these tags, Kanka's API currently only allows iframe elements
    # Other embed types (audio, video, etc.) will be stripped by Kanka when saving
    # Matches both self-closing and regular tags with content
    EMBED_PATTERN = re.compile(
        r"<(iframe|embed|video|audio|object)(?:\s[^>]*)?>.*?</\1>|<(iframe|embed|video|audio|object)(?:\s[^>]*)?/>",
        re.IGNORECASE | re.DOTALL,
    )

    # Placeholder format for protecting embeds during conversion
    EMBED_PLACEHOLDER_TEMPLATE = "KANKAEMBEDPLACEHOLDER{}"
    EMBED_PLACEHOLDER_PATTERN = re.compile(r"KANKAEMBEDPLACEHOLDER(\d+)")

    def __init__(self) -> None:
        """Initialize the converter with mistune renderer."""
        # Use mistune for more tolerant markdown parsing
        # It handles 2-space indented nested lists correctly
        self.md = mistune.create_markdown(renderer="html")

    def markdown_to_html(self, content: str) -> str:
        """
        Convert Markdown to HTML while preserving Kanka mentions and HTML embeds.

        Args:
            content: Markdown content

        Returns:
            HTML content with mentions and embeds preserved
        """
        if not content:
            return ""

        # Extract and protect mentions
        protected_content, mentions = self._protect_mentions(content)

        # Extract and protect embeds (they pass through unchanged)
        protected_content, embeds = self._protect_embeds(protected_content)

        # Convert to HTML
        html = self.md(protected_content)

        # Ensure html is a string
        if not isinstance(html, str):
            # If mistune returns something else, convert it
            html = str(html)

        # Restore mentions
        html = self._restore_mentions(html, mentions)

        # Restore embeds
        html = self._restore_embeds(html, embeds)

        return html

    def html_to_markdown(self, html: str) -> str:
        """
        Convert HTML to Markdown while preserving Kanka mentions and HTML embeds.

        Args:
            html: HTML content

        Returns:
            Markdown content with mentions and embeds preserved
        """
        if not html:
            return ""

        # Extract and protect mentions
        protected_html, mentions = self._protect_mentions(html)

        # Extract and protect embeds
        protected_html, embeds = self._protect_embeds(protected_html)

        # Use markdownify to convert HTML to Markdown
        markdown_text: str = md(
            protected_html,
            heading_style="ATX",  # Use # for headings
            bullets="-",  # Use - for unordered lists
            code_language="",  # Don't add language to code blocks
        )

        # Restore mentions
        markdown_text = self._restore_mentions(markdown_text, mentions)

        # Restore embeds
        markdown_text = self._restore_embeds(markdown_text, embeds)

        # Clean up unwanted HTML tags that markdownify leaves behind
        markdown_text = self._clean_leftover_html(markdown_text)

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

    def _clean_leftover_html(self, content: str) -> str:
        """
        Clean up unwanted HTML tags that markdownify doesn't handle properly.

        Args:
            content: Markdown content that may contain leftover HTML tags

        Returns:
            Cleaned content with unwanted HTML tags removed
        """
        # Remove empty <ins></ins> tags that accumulate during conversion
        content = re.sub(r"<ins></ins>", "", content)

        # Remove any other empty HTML tags that might cause issues
        content = re.sub(r"<(\w+)></\1>", "", content)

        return content

    def _protect_embeds(self, content: str) -> tuple[str, list[tuple[str, str]]]:
        """
        Replace HTML embeds with placeholders to protect them during conversion.

        Args:
            content: Original content with HTML embeds

        Returns:
            Tuple of (protected content, list of (placeholder, embed_html))
        """
        embeds = []
        placeholder_counter = 0

        def replace_embed(match: re.Match[str]) -> str:
            nonlocal placeholder_counter
            embed_html = match.group(0)
            placeholder = self.EMBED_PLACEHOLDER_TEMPLATE.format(placeholder_counter)
            placeholder_counter += 1

            embeds.append((placeholder, embed_html))
            return placeholder

        protected_content = self.EMBED_PATTERN.sub(replace_embed, content)
        return protected_content, embeds

    def _restore_embeds(self, content: str, embeds: list[tuple[str, str]]) -> str:
        """
        Restore HTML embeds from placeholders.

        Args:
            content: Content with placeholders
            embeds: List of (placeholder, embed_html)

        Returns:
            Content with embeds restored
        """
        # Sort embeds by placeholder length (descending) to avoid partial replacements
        sorted_embeds = sorted(embeds, key=lambda x: len(x[0]), reverse=True)

        for placeholder, embed_html in sorted_embeds:
            content = content.replace(placeholder, embed_html)

        return content
