"""Comprehensive unit tests for the content converter module.

These tests focus on edge cases and scenarios that commonly break
in markdown/HTML conversion.
"""

from mcp_kanka.converter import ContentConverter


class TestMarkdownToHtmlEdgeCases:
    """Test edge cases for Markdown to HTML conversion."""

    def setup_method(self):
        """Set up test fixtures."""
        self.converter = ContentConverter()

    def test_mentions_with_special_characters(self):
        """Test mentions containing special markdown characters."""
        test_cases = [
            # Mention with asterisks (could be interpreted as emphasis)
            "[entity:123|The **Bold** Knight]",
            # Mention with underscores (could be interpreted as emphasis)
            "[entity:456|The_Underground_City]",
            # Mention with backticks (could be interpreted as code)
            "[entity:789|The `Code` Master]",
            # Mention with brackets
            "[entity:101|The [Secret] Society]",
            # Mention with HTML-like content
            "[entity:102|<script>alert('test')</script>]",
        ]

        for mention in test_cases:
            md = f"Visit {mention} today"
            html = self.converter.markdown_to_html(md)
            assert mention in html, f"Lost mention: {mention}"

    def test_mentions_in_different_contexts(self):
        """Test mentions in various markdown contexts."""
        # In headers
        md = "# Meet [entity:123|The King]\n## And [entity:456|The Queen]"
        html = self.converter.markdown_to_html(md)
        assert "[entity:123|The King]" in html
        assert "[entity:456|The Queen]" in html

        # In lists
        md = """
- Visit [entity:1|Town Hall]
- Meet [entity:2|Mayor]
  - At [entity:3|Office]
"""
        html = self.converter.markdown_to_html(md)
        assert "[entity:1|Town Hall]" in html
        assert "[entity:2|Mayor]" in html
        assert "[entity:3|Office]" in html

        # In blockquotes
        md = "> According to [entity:123|The Prophet], all will be well"
        html = self.converter.markdown_to_html(md)
        assert "[entity:123|The Prophet]" in html

        # In code blocks (should be preserved as-is)
        md = "```\n[entity:123] is preserved in code\n```"
        html = self.converter.markdown_to_html(md)
        assert "[entity:123]" in html

    def test_adjacent_mentions(self):
        """Test mentions that are adjacent or very close."""
        md = "[entity:1|Alice][entity:2|Bob] are friends"
        html = self.converter.markdown_to_html(md)
        assert "[entity:1|Alice]" in html
        assert "[entity:2|Bob]" in html

        # With punctuation between
        md = "[entity:1|Alice], [entity:2|Bob], and [entity:3|Charlie]"
        html = self.converter.markdown_to_html(md)
        assert "[entity:1|Alice]" in html
        assert "[entity:2|Bob]" in html
        assert "[entity:3|Charlie]" in html

    def test_mentions_with_markdown_inside(self):
        """Test mentions where the custom text contains markdown."""
        # This is tricky - the mention text might have markdown
        md = "Visit [entity:123|The **Bold** Castle]"
        html = self.converter.markdown_to_html(md)
        # The mention should be preserved exactly
        assert "[entity:123|The **Bold** Castle]" in html

    def test_table_with_mentions(self):
        """Test mentions inside markdown tables."""
        md = """
| Location | Owner |
|----------|-------|
| [entity:1|Castle] | [entity:2|King] |
| [entity:3|Tower] | [entity:4|Wizard] |
"""
        html = self.converter.markdown_to_html(md)
        assert "[entity:1|Castle]" in html
        assert "[entity:2|King]" in html
        assert "[entity:3|Tower]" in html
        assert "[entity:4|Wizard]" in html

    def test_complex_nested_formatting(self):
        """Test deeply nested formatting with mentions."""
        md = "***Visit [entity:123|The Place] for ~~more~~ info***"
        html = self.converter.markdown_to_html(md)
        assert "[entity:123|The Place]" in html

    def test_mentions_with_newlines(self):
        """Test mentions split across lines (should not happen but test anyway)."""
        # Single mention should not have newlines, but test robustness
        md = "Visit [entity:123|The\nPlace] today"
        # This might break the mention - that's expected
        # But it shouldn't crash
        html = self.converter.markdown_to_html(md)  # noqa: F841


class TestHtmlToMarkdownEdgeCases:
    """Test edge cases for HTML to Markdown conversion."""

    def setup_method(self):
        """Set up test fixtures."""
        self.converter = ContentConverter()

    def test_nested_html_elements(self):
        """Test deeply nested HTML structures."""
        html = """
        <div>
            <p>Visit <strong><em>[entity:123|The Place]</em></strong></p>
            <blockquote>
                <p>As said by <a href="#"><strong>[entity:456|The Sage]</strong></a></p>
            </blockquote>
        </div>
        """
        md = self.converter.html_to_markdown(html)
        assert "[entity:123|The Place]" in md
        assert "[entity:456|The Sage]" in md

    def test_html_entities_and_mentions(self):
        """Test HTML entities don't break mentions."""
        html = "<p>Visit [entity:123|Caf&eacute;] &amp; [entity:456|Bar]</p>"
        md = self.converter.html_to_markdown(html)
        assert "[entity:123|Café]" in md or "[entity:123|Caf&eacute;]" in md
        assert "[entity:456|Bar]" in md

    def test_malformed_html(self):
        """Test conversion handles malformed HTML gracefully."""
        html = "<p>Visit [entity:123|Place] <strong>bold text</p>"  # Missing closing </strong>
        md = self.converter.html_to_markdown(html)
        assert "[entity:123|Place]" in md

    def test_html_with_attributes(self):
        """Test HTML elements with various attributes."""
        html = """
        <p class="important" id="main">
            Visit <span style="color: red">[entity:123|The Place]</span>
        </p>
        """
        md = self.converter.html_to_markdown(html)
        assert "[entity:123|The Place]" in md

    def test_html_tables(self):
        """Test HTML table conversion with mentions."""
        html = """
        <table>
            <tr>
                <th>Location</th>
                <th>Owner</th>
            </tr>
            <tr>
                <td>[entity:1|Castle]</td>
                <td>[entity:2|King]</td>
            </tr>
        </table>
        """
        md = self.converter.html_to_markdown(html)
        assert "[entity:1|Castle]" in md
        assert "[entity:2|King]" in md

    def test_pre_formatted_text(self):
        """Test pre-formatted text blocks."""
        html = """
        <pre>
        [entity:123] should be preserved
        exactly as is
        </pre>
        """
        md = self.converter.html_to_markdown(html)
        assert "[entity:123]" in md

    def test_html_comments(self):
        """Test HTML comments don't interfere."""
        html = """
        <p>Visit <!-- comment --> [entity:123|Place] <!-- another comment --></p>
        """
        md = self.converter.html_to_markdown(html)
        assert "[entity:123|Place]" in md


class TestRoundTripConversions:
    """Test that content survives multiple round-trip conversions."""

    def setup_method(self):
        """Set up test fixtures."""
        self.converter = ContentConverter()

    def test_multiple_round_trips(self):
        """Test content survives multiple conversions."""
        original_md = """
# Adventure Log

Visit [entity:123|The Castle] to meet [entity:456|King Arthur].

## Quest Items
- [entity:789|Holy Grail]
- [entity:101|Excalibur]

> "The quest begins at [entity:102|Round Table]" - [entity:103|Merlin]

**Important:** See [entity:104|Quest Board] for details.
"""

        # Do multiple round trips
        content = original_md
        for _ in range(5):
            html = self.converter.markdown_to_html(content)
            content = self.converter.html_to_markdown(html)

        # All mentions should still be present
        assert "[entity:123|The Castle]" in content
        assert "[entity:456|King Arthur]" in content
        assert "[entity:789|Holy Grail]" in content
        assert "[entity:101|Excalibur]" in content
        assert "[entity:102|Round Table]" in content
        assert "[entity:103|Merlin]" in content
        assert "[entity:104|Quest Board]" in content

    def test_complex_document_round_trip(self):
        """Test a complex document with various elements."""
        original_md = """
# Campaign Setting: [entity:1|Realm of Shadows]

## Overview
The [entity:2|Dark Lord] has returned to [entity:3|Shadow Keep].

### Key Locations
1. **[entity:4|The Capital]** - Main city
2. **[entity:5|The Wastes]** - Dangerous area
   - Contains [entity:6|Ancient Ruins]
   - Home to [entity:7|Shadow Beasts]

### Important NPCs
| Name | Location | Role |
|------|----------|------|
| [entity:8|Queen Elara] | [entity:4|The Capital] | Ruler |
| [entity:9|Sage Aldric] | [entity:10|Tower of Wisdom] | Advisor |

### Code of Laws
```
The [entity:11|Ancient Code] states:
- Rule 1: Respect [entity:12|The Crown]
- Rule 2: Fear [entity:13|The Darkness]
```

> According to [entity:14|The Prophecy], only [entity:15|The Chosen One] can defeat the [entity:2|Dark Lord].

---

*Last updated by [entity:16|The Chronicler]*
"""

        # Convert to HTML and back
        html = self.converter.markdown_to_html(original_md)
        back_to_md = self.converter.html_to_markdown(html)

        # Check all 16 entities are preserved
        for i in range(1, 17):
            assert f"[entity:{i}|" in back_to_md, f"Lost entity {i}"

    def test_whitespace_preservation(self):
        """Test that whitespace around mentions is handled correctly."""
        test_cases = [
            "Word[entity:1|Place]Word",  # No spaces
            "Word [entity:2|Place] Word",  # Normal spaces
            "Word  [entity:3|Place]  Word",  # Multiple spaces
            "Word\t[entity:4|Place]\tWord",  # Tabs
            "Word\n[entity:5|Place]\nWord",  # Newlines
        ]

        for md in test_cases:
            html = self.converter.markdown_to_html(md)
            back = self.converter.html_to_markdown(html)
            # Extract the entity number to verify
            import re

            match = re.search(r"\[entity:(\d+)\|Place\]", md)
            if match:
                entity_num = match.group(1)
                assert f"[entity:{entity_num}|Place]" in back


class TestErrorHandling:
    """Test error handling and edge cases."""

    def setup_method(self):
        """Set up test fixtures."""
        self.converter = ContentConverter()

    def test_invalid_mention_formats(self):
        """Test that invalid mention formats don't break conversion."""
        invalid_mentions = [
            "[entity:]",  # Missing ID
            "[entity:abc]",  # Non-numeric ID
            "[entity:123|]",  # Empty custom text
            "[entity:|Name]",  # Missing ID with name
            "[entity123]",  # Missing colon
            "[entity:123 Name]",  # Missing pipe
        ]

        for mention in invalid_mentions:
            md = f"Text with {mention} here"
            # Should not raise exception
            html = self.converter.markdown_to_html(md)
            back = self.converter.html_to_markdown(html)  # noqa: F841

    def test_extremely_long_content(self):
        """Test handling of very long content."""
        # Create content with many mentions
        mentions = [f"[entity:{i}|Location {i}]" for i in range(100)]
        md = "Visit these places: " + ", ".join(mentions)

        html = self.converter.markdown_to_html(md)
        back = self.converter.html_to_markdown(html)

        # Check a sample of mentions
        assert "[entity:1|Location 1]" in back
        assert "[entity:50|Location 50]" in back
        assert "[entity:99|Location 99]" in back

    def test_unicode_in_mentions(self):
        """Test Unicode characters in mention text."""
        unicode_mentions = [
            "[entity:1|Café ☕]",
            "[entity:2|Москва]",
            "[entity:3|東京]",
            "[entity:4|🏰 Castle]",
            "[entity:5|Ñoño's Place]",
        ]

        for mention in unicode_mentions:
            md = f"Visit {mention}"
            html = self.converter.markdown_to_html(md)
            back = self.converter.html_to_markdown(html)
            assert mention in back, f"Lost Unicode mention: {mention}"


class TestKankaSpecificScenarios:
    """Test scenarios specific to Kanka's use cases."""

    def setup_method(self):
        """Set up test fixtures."""
        self.converter = ContentConverter()

    def test_typical_kanka_entry(self):
        """Test a typical Kanka entity entry."""
        kanka_entry = """
# [entity:100|Waterdeep]

**Type:** City
**Population:** 1,000,000

## Description
[entity:100|Waterdeep] is the greatest city in [entity:200|Faerûn]. It is ruled by [entity:300|Lord Piergeiron].

## Districts
- **[entity:101|Castle Ward]** - Where the nobles live
- **[entity:102|Dock Ward]** - The harbor district
- **[entity:103|Trade Ward]** - Commercial center

## Notable Locations
1. [entity:104|The Yawning Portal] - Famous tavern
2. [entity:105|Blackstaff Tower] - Home of [entity:301|The Blackstaff]
3. [entity:106|City Guard Barracks] - Headquarters of [entity:302|The Watch]

> "Welcome to [entity:100|Waterdeep], friend!" - [entity:303|Random Guard]

---
*See also: [entity:201|Neverwinter], [entity:202|Baldur's Gate]*
"""

        html = self.converter.markdown_to_html(kanka_entry)
        back = self.converter.html_to_markdown(html)

        # Verify all mentions are preserved
        import re

        original_mentions = re.findall(r"\[entity:\d+\|[^\]]+\]", kanka_entry)
        for mention in original_mentions:
            assert mention in back, f"Lost mention: {mention}"

    def test_nested_entity_references(self):
        """Test entries that reference other entities multiple times."""
        md = """
The [entity:1|Ancient Sword] was forged by [entity:2|The Smith] in [entity:3|The Forge].

Later, [entity:2|The Smith] gave [entity:1|Ancient Sword] to [entity:4|The Hero],
who used it to defeat [entity:5|The Dragon] at [entity:6|Dragon's Lair].

[entity:1|Ancient Sword] was then lost in [entity:7|The Depths] until [entity:8|The Explorer]
found it and returned it to [entity:3|The Forge].
"""

        html = self.converter.markdown_to_html(md)
        back = self.converter.html_to_markdown(html)

        # Count occurrences of each entity
        assert back.count("[entity:1|Ancient Sword]") == 3
        assert back.count("[entity:2|The Smith]") == 2
        assert back.count("[entity:3|The Forge]") == 2
