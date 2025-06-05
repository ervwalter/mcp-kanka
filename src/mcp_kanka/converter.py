"""Content conversion between Markdown and HTML with Kanka mention preservation."""

import re
from typing import Any

import markdown
from bs4 import BeautifulSoup


class ContentConverter:
    """Handles conversion between Markdown and HTML while preserving Kanka mentions."""

    # Pattern for Kanka mentions: [entity:ID] or [entity:ID|text]
    MENTION_PATTERN = re.compile(r"\[entity:(\d+)(?:\|([^\]]+))?\]")

    # Placeholder format for protecting mentions during conversion
    PLACEHOLDER_TEMPLATE = "__KANKA_MENTION_{}__{}"
    PLACEHOLDER_PATTERN = re.compile(r"__KANKA_MENTION_(\d+)__")

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

        # Parse HTML
        soup = BeautifulSoup(html, "html.parser")

        # Convert to text while preserving structure
        markdown_text = self._html_to_markdown_recursive(soup)

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
        for placeholder, entity_id, text in mentions:
            if text:
                mention = f"[entity:{entity_id}|{text}]"
            else:
                mention = f"[entity:{entity_id}]"
            content = content.replace(placeholder, mention)

        return content

    def _html_to_markdown_recursive(self, element: Any) -> str:
        """
        Recursively convert HTML elements to Markdown.

        Args:
            element: BeautifulSoup element

        Returns:
            Markdown representation
        """
        if element.name is None:
            # Text node
            text = str(element).strip()
            # Preserve mentions as-is
            return text

        # Handle different tags
        if element.name == "p":
            content = self._process_children(element)
            return f"{content}\n\n"

        elif element.name == "br":
            return "\n"

        elif element.name in ["h1", "h2", "h3", "h4", "h5", "h6"]:
            level = int(element.name[1])
            content = self._process_children(element)
            return f"{'#' * level} {content}\n\n"

        elif element.name == "strong" or element.name == "b":
            content = self._process_children(element)
            return f"**{content}**"

        elif element.name == "em" or element.name == "i":
            content = self._process_children(element)
            return f"*{content}*"

        elif element.name == "code":
            content = element.get_text()
            return f"`{content}`"

        elif element.name == "pre":
            # Handle code blocks
            code_elem = element.find("code")
            content = code_elem.get_text() if code_elem else element.get_text()
            return f"```\n{content}\n```\n\n"

        elif element.name == "a":
            text = self._process_children(element)
            href = element.get("href", "")
            # Check if this is a mention link
            if "[entity:" in text:
                return text
            return f"[{text}]({href})"

        elif element.name == "ul":
            items = []
            for li in element.find_all("li", recursive=False):
                content = self._process_children(li)
                items.append(f"- {content}")
            return "\n".join(items) + "\n\n"

        elif element.name == "ol":
            items = []
            for i, li in enumerate(element.find_all("li", recursive=False), 1):
                content = self._process_children(li)
                items.append(f"{i}. {content}")
            return "\n".join(items) + "\n\n"

        elif element.name == "blockquote":
            content = self._process_children(element)
            lines = content.strip().split("\n")
            quoted_lines = ["> " + line for line in lines]
            return "\n".join(quoted_lines) + "\n\n"

        elif element.name == "hr":
            return "---\n\n"

        elif element.name == "table":
            # Simple table conversion
            rows = []
            for tr in element.find_all("tr"):
                cells = []
                for td in tr.find_all(["td", "th"]):
                    cells.append(self._process_children(td).strip())
                rows.append("| " + " | ".join(cells) + " |")

            if rows:
                # Add header separator after first row
                if len(rows) > 1:
                    header_cells = len(rows[0].split("|")) - 2
                    separator = "| " + " | ".join(["---"] * header_cells) + " |"
                    rows.insert(1, separator)

                return "\n".join(rows) + "\n\n"
            return ""

        elif element.name in ["div", "span"]:
            # Pass through containers
            return self._process_children(element)

        else:
            # Default: just get the text content
            return self._process_children(element)

    def _process_children(self, element: Any) -> str:
        """
        Process all children of an element.

        Args:
            element: Parent element

        Returns:
            Combined markdown text
        """
        parts = []
        for child in element.children:
            parts.append(self._html_to_markdown_recursive(child))

        return "".join(parts).strip()
