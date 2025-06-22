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

    def test_html_to_markdown_removes_ins_tags(self):
        """Test that empty <ins></ins> tags are removed during HTML to markdown conversion."""
        html = "<p>[entity:123|Character<ins></ins><ins></ins>] does something with [entity:456|Location<ins></ins>].</p>"
        markdown = self.converter.html_to_markdown(html)

        # Should remove all <ins></ins> tags
        assert "<ins></ins>" not in markdown
        assert "[entity:123|Character]" in markdown
        assert "[entity:456|Location]" in markdown

    def test_html_to_markdown_removes_other_empty_tags(self):
        """Test that other empty HTML tags are also removed."""
        html = "<p>Text with <span></span> empty <div></div> tags <em></em>.</p>"
        markdown = self.converter.html_to_markdown(html)

        # Should remove empty tags
        assert "<span></span>" not in markdown
        assert "<div></div>" not in markdown
        assert "<em></em>" not in markdown
        assert "Text with" in markdown and "emptytags" in markdown

    def test_html_to_markdown_preserves_youtube_embed(self):
        """Test that YouTube iframe embeds are preserved during HTML to Markdown conversion."""
        html = """<p>Check out this video:</p>
<iframe width="560" height="315" src="https://www.youtube.com/embed/dQw4w9WgXcQ"
        frameborder="0" allowfullscreen></iframe>
<p>Pretty cool, right?</p>"""

        md = self.converter.html_to_markdown(html)

        # The iframe should be preserved in the markdown
        assert (
            '<iframe width="560" height="315" src="https://www.youtube.com/embed/dQw4w9WgXcQ"'
            in md
        )
        assert 'frameborder="0" allowfullscreen></iframe>' in md
        assert "Check out this video:" in md
        assert "Pretty cool, right?" in md

    def test_html_to_markdown_preserves_multiple_embeds(self):
        """Test that multiple embeds are preserved."""
        html = """<p>Multiple embeds:</p>
<iframe src="https://player.vimeo.com/video/123456"></iframe>
<p>And another:</p>
<embed src="game.swf" type="application/x-shockwave-flash" />
<video controls><source src="movie.mp4" type="video/mp4"></video>"""

        md = self.converter.html_to_markdown(html)

        # All embeds should be preserved
        assert '<iframe src="https://player.vimeo.com/video/123456"></iframe>' in md
        assert '<embed src="game.swf" type="application/x-shockwave-flash" />' in md
        assert '<video controls><source src="movie.mp4" type="video/mp4"></video>' in md

    def test_markdown_to_html_preserves_embeds(self):
        """Test that embeds in markdown pass through to HTML unchanged."""
        md = """# My Content

Here's a video:

<iframe width="560" height="315" src="https://www.youtube.com/embed/test123"></iframe>

And some more text."""

        html = self.converter.markdown_to_html(md)

        # The iframe should pass through unchanged
        assert (
            '<iframe width="560" height="315" src="https://www.youtube.com/embed/test123"></iframe>'
            in html
        )
        assert "<h1>My Content</h1>" in html

    def test_embeds_and_mentions_together(self):
        """Test that embeds and mentions work together."""
        html = """<p>Check out [entity:123|this character] in the video:</p>
<iframe src="https://youtube.com/embed/abc"></iframe>
<p>Also see [entity:456]</p>"""

        md = self.converter.html_to_markdown(html)

        # Both mentions and embeds should be preserved
        assert "[entity:123|this character]" in md
        assert "[entity:456]" in md
        assert '<iframe src="https://youtube.com/embed/abc"></iframe>' in md

    def test_malformed_embeds_handled_gracefully(self):
        """Test that malformed embeds don't break conversion."""
        html = """<p>Normal text</p>
<iframe>Missing src</iframe>
<p>More text</p>"""

        md = self.converter.html_to_markdown(html)

        # Should handle the malformed iframe
        assert "Normal text" in md
        assert "More text" in md
        # The malformed iframe should still be preserved
        assert "<iframe>Missing src</iframe>" in md

    def test_audio_embed_preservation(self):
        """Test that audio elements are preserved."""
        html = """<p>Listen to this:</p>
<audio controls>
  <source src="audio.mp3" type="audio/mpeg">
  Your browser does not support audio.
</audio>"""

        md = self.converter.html_to_markdown(html)

        # Audio element should be preserved
        assert "<audio controls>" in md
        assert '<source src="audio.mp3" type="audio/mpeg">' in md
        assert "</audio>" in md
