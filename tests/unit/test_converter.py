"""Unit tests for the content converter module."""

from mcp_kanka.converter import ContentConverter


class TestContentConverter:
    """Test the ContentConverter class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.converter = ContentConverter()

    def test_markdown_to_html_basic(self):
        """Test basic markdown to HTML conversion."""
        md = "# Hello World\n\nThis is a **bold** text."
        html = self.converter.markdown_to_html(md)
        assert "<h1>Hello World</h1>" in html
        assert "<strong>bold</strong>" in html

    def test_markdown_to_html_preserves_mentions(self):
        """Test that entity mentions are preserved during conversion."""
        md = "This references [entity:123] and [entity:456|Custom Name]."
        html = self.converter.markdown_to_html(md)
        assert "[entity:123]" in html
        assert "[entity:456|Custom Name]" in html

    def test_markdown_to_html_with_code_block(self):
        """Test markdown with code blocks."""
        md = "```python\nprint('hello')\n```"
        html = self.converter.markdown_to_html(md)
        assert "<code>" in html or "<pre>" in html

    def test_markdown_to_html_with_lists(self):
        """Test markdown list conversion."""
        md = "- Item 1\n- Item 2\n  - Nested item"
        html = self.converter.markdown_to_html(md)
        assert "<ul>" in html
        assert "<li>" in html

    def test_html_to_markdown_basic(self):
        """Test basic HTML to markdown conversion."""
        html = "<h1>Hello World</h1><p>This is <strong>bold</strong> text.</p>"
        md = self.converter.html_to_markdown(html)
        assert "# Hello World" in md
        assert "**bold**" in md

    def test_html_to_markdown_preserves_mentions(self):
        """Test that entity mentions are preserved during conversion."""
        html = "<p>This references [entity:123] and [entity:456|Custom Name].</p>"
        md = self.converter.html_to_markdown(html)
        assert "[entity:123]" in md
        assert "[entity:456|Custom Name]" in md

    def test_html_to_markdown_with_links(self):
        """Test HTML link conversion."""
        html = '<p>Visit <a href="https://example.com">Example</a></p>'
        md = self.converter.html_to_markdown(html)
        assert "[Example](https://example.com)" in md

    def test_html_to_markdown_with_images(self):
        """Test HTML image conversion."""
        html = '<img src="image.jpg" alt="Test Image">'
        md = self.converter.html_to_markdown(html)
        assert "![Test Image](image.jpg)" in md

    def test_round_trip_conversion(self):
        """Test that content survives round-trip conversion."""
        original_md = "# Title\n\nThis has [entity:123] and **bold** text."
        html = self.converter.markdown_to_html(original_md)
        back_to_md = self.converter.html_to_markdown(html)

        # Check key elements are preserved
        assert "Title" in back_to_md
        assert "[entity:123]" in back_to_md
        assert "bold" in back_to_md

    def test_empty_content(self):
        """Test handling of empty content."""
        assert self.converter.markdown_to_html("") == ""
        assert self.converter.html_to_markdown("") == ""

    def test_none_content(self):
        """Test handling of None content."""
        assert self.converter.markdown_to_html(None) == ""
        assert self.converter.html_to_markdown(None) == ""

    def test_complex_mentions(self):
        """Test various mention formats."""
        test_cases = [
            "[entity:123]",
            "[entity:456|Custom Name]",
            "[entity:789|Name with spaces]",
            "[entity:999|Name|with|pipes]",
        ]

        for mention in test_cases:
            md = f"Text with {mention} mention"
            html = self.converter.markdown_to_html(md)
            assert mention in html

            back_to_md = self.converter.html_to_markdown(html)
            assert mention in back_to_md

    def test_multiple_mentions_in_text(self):
        """Test multiple mentions in the same text."""
        md = "Meet [entity:1|Alice] and [entity:2|Bob] at [entity:3|Town Square]."
        html = self.converter.markdown_to_html(md)

        assert "[entity:1|Alice]" in html
        assert "[entity:2|Bob]" in html
        assert "[entity:3|Town Square]" in html

    def test_nested_formatting_with_mentions(self):
        """Test mentions within formatted text."""
        md = "**Important: See [entity:123|The Guide] for details**"
        html = self.converter.markdown_to_html(md)

        # Should preserve both formatting and mention
        assert "[entity:123|The Guide]" in html
        assert "<strong>" in html or "<b>" in html
