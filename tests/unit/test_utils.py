"""Unit tests for the utils module."""

from mcp_kanka.utils import (
    filter_entities_by_name,
    filter_entities_by_tags,
    filter_entities_by_type,
    filter_journals_by_date_range,
    fuzzy_match_score,
    paginate_results,
    search_in_content,
)


class TestFuzzyMatchScore:
    """Test the fuzzy_match_score function."""

    def test_exact_match(self):
        """Test exact string matching."""
        assert fuzzy_match_score("hello", "hello") == 1.0
        assert fuzzy_match_score("Hello", "hello") == 1.0  # Case insensitive

    def test_partial_match(self):
        """Test partial string matching."""
        score1 = fuzzy_match_score("helo", "hello")
        assert 0.7 < score1 < 1.0  # High similarity

        score2 = fuzzy_match_score("hllo", "hello")
        assert 0.7 < score2 < 1.0  # High similarity

    def test_no_match(self):
        """Test strings that shouldn't match."""
        assert fuzzy_match_score("world", "hello") < 0.3
        assert fuzzy_match_score("xyz", "hello") < 0.3

    def test_empty_strings(self):
        """Test empty string handling."""
        assert fuzzy_match_score("", "") == 1.0
        assert fuzzy_match_score("", "hello") == 0.0
        assert fuzzy_match_score("hello", "") == 0.0

    def test_score_range(self):
        """Test that scores are always between 0 and 1."""
        test_pairs = [
            ("hello", "hello"),
            ("hello", "helo"),
            ("hello", "world"),
            ("", "test"),
            ("test", ""),
        ]

        for s1, s2 in test_pairs:
            score = fuzzy_match_score(s1, s2)
            assert 0.0 <= score <= 1.0


class TestFilterEntitiesByName:
    """Test the filter_entities_by_name function."""

    def setup_method(self):
        """Set up test entities."""
        self.entities = [
            {"name": "Alice"},
            {"name": "Bob"},
            {"name": "Charlie"},
            {"name": "Alice Cooper"},
        ]

    def test_exact_name_filter(self):
        """Test exact name filtering."""
        # Default is now partial matching
        result = filter_entities_by_name(self.entities, "Alice")
        assert len(result) == 2  # "Alice" and "Alice Cooper"

        # Use exact=True for exact matching
        result_exact = filter_entities_by_name(self.entities, "Alice", exact=True)
        assert len(result_exact) == 1
        assert result_exact[0]["name"] == "Alice"

    def test_fuzzy_name_filter(self):
        """Test fuzzy name filtering."""
        # Use default threshold (0.7) - only "Alice" will match perfectly
        result = filter_entities_by_name(self.entities, "Alic", fuzzy=True)
        assert len(result) == 1  # Should only match "Alice" with high score
        assert result[0]["name"] == "Alice"
        assert result[0]["match_score"] > 0.8

        # Test with a more specific query and lower threshold
        result2 = filter_entities_by_name(
            self.entities, "Alice C", fuzzy=True, threshold=0.6
        )
        assert len(result2) == 2  # Should match "Alice" and "Alice Cooper"
        names = [e["name"] for e in result2]
        assert "Alice Cooper" in names  # Should be first due to higher relevance
        assert "Alice" in names

    def test_case_insensitive(self):
        """Test case insensitive matching."""
        # Default partial matching
        result = filter_entities_by_name(self.entities, "alice")
        assert len(result) == 2  # "Alice" and "Alice Cooper"

        # Exact matching
        result_exact = filter_entities_by_name(self.entities, "alice", exact=True)
        assert len(result_exact) == 1
        assert result_exact[0]["name"] == "Alice"

    def test_no_matches(self):
        """Test when no entities match."""
        result = filter_entities_by_name(self.entities, "Dave", fuzzy=False)
        assert len(result) == 0


class TestFilterEntitiesByType:
    """Test the filter_entities_by_type function."""

    def setup_method(self):
        """Set up test entities."""
        self.entities = [
            {"name": "Alice", "type": "NPC"},
            {"name": "Bob", "type": "Player Character"},
            {"name": "Charlie", "type": "NPC"},
            {"name": "Dave", "type": None},
        ]

    def test_type_filter(self):
        """Test filtering by type."""
        result = filter_entities_by_type(self.entities, "NPC")
        assert len(result) == 2
        assert all(e["type"] == "NPC" for e in result)

    def test_case_insensitive_type(self):
        """Test case insensitive type matching."""
        result = filter_entities_by_type(self.entities, "npc")
        assert len(result) == 2

    def test_no_type_field(self):
        """Test entities without type field."""
        entities = [{"name": "Test"}]  # No type field
        result = filter_entities_by_type(entities, "NPC")
        assert len(result) == 0


class TestFilterEntitiesByTags:
    """Test the filter_entities_by_tags function."""

    def setup_method(self):
        """Set up test entities."""
        self.entities = [
            {"name": "Alice", "tags": ["hero", "warrior"]},
            {"name": "Bob", "tags": ["villain", "wizard"]},
            {"name": "Charlie", "tags": ["hero", "wizard"]},
            {"name": "Dave", "tags": []},
            {"name": "Eve"},  # No tags field
        ]

    def test_single_tag_filter(self):
        """Test filtering by single tag."""
        result = filter_entities_by_tags(self.entities, ["hero"])
        assert len(result) == 2
        names = [e["name"] for e in result]
        assert "Alice" in names
        assert "Charlie" in names

    def test_multiple_tags_filter(self):
        """Test filtering by multiple tags (ALL must match)."""
        result = filter_entities_by_tags(self.entities, ["hero", "wizard"])
        assert len(result) == 1
        assert result[0]["name"] == "Charlie"

    def test_no_matching_tags(self):
        """Test when no entities have all required tags."""
        result = filter_entities_by_tags(self.entities, ["hero", "villain"])
        assert len(result) == 0

    def test_empty_tags_list(self):
        """Test with empty required tags list."""
        result = filter_entities_by_tags(self.entities, [])
        assert len(result) == len(self.entities)  # All should match


class TestFilterJournalsByDateRange:
    """Test the filter_journals_by_date_range function."""

    def setup_method(self):
        """Set up test journals."""
        self.journals = [
            {"name": "Entry 1", "entry": "**Date: 2024-01-15**\n\nSession notes here"},
            {"name": "Entry 2", "entry": "Date: 2024-02-20\n\nMore notes"},
            {"name": "Entry 3", "entry": "2024-03-10 - Today's session"},
            {"name": "Entry 4", "entry": "No date in this entry"},
            {"name": "Entry 5"},  # No entry field
        ]

    def test_date_range_filter(self):
        """Test filtering by date range."""
        result = filter_journals_by_date_range(
            self.journals, "2024-01-01", "2024-02-28"
        )
        assert len(result) == 2
        names = [e["name"] for e in result]
        assert "Entry 1" in names
        assert "Entry 2" in names

    def test_exact_date_boundaries(self):
        """Test that boundary dates are included."""
        result = filter_journals_by_date_range(
            self.journals, "2024-01-15", "2024-01-15"
        )
        assert len(result) == 1
        assert result[0]["name"] == "Entry 1"

    def test_no_matches_in_range(self):
        """Test when no journals fall in range."""
        result = filter_journals_by_date_range(
            self.journals, "2023-01-01", "2023-12-31"
        )
        assert len(result) == 0

    def test_invalid_date_format(self):
        """Test handling of invalid date formats."""
        journals = [{"name": "Bad Date", "entry": "Date: invalid-date"}]
        result = filter_journals_by_date_range(journals, "2024-01-01", "2024-12-31")
        assert len(result) == 0


class TestSearchInContent:
    """Test the search_in_content function."""

    def setup_method(self):
        """Set up test entities."""
        self.entities = [
            {"name": "Alice", "entry": "A brave warrior from the north"},
            {"name": "Bob", "entry": "A wise wizard of great power"},
            {"name": "Charlie", "entry": None},
            {"name": "Dave"},  # No entry field
        ]

    def test_search_in_entry(self):
        """Test searching in entry content."""
        result = search_in_content(self.entities, "warrior")
        assert len(result) == 1
        assert result[0]["name"] == "Alice"

    def test_search_case_insensitive(self):
        """Test case insensitive search."""
        result = search_in_content(self.entities, "WIZARD")
        assert len(result) == 1
        assert result[0]["name"] == "Bob"

    def test_search_in_name(self):
        """Test that search also checks entity names."""
        result = search_in_content(self.entities, "Alice")
        assert len(result) == 1
        assert result[0]["name"] == "Alice"

    def test_search_multiple_matches(self):
        """Test search with multiple matches."""
        result = search_in_content(self.entities, "a")
        # Should match all entities with "a" in name or entry
        assert len(result) >= 2


class TestPaginateResults:
    """Test the paginate_results function."""

    def setup_method(self):
        """Set up test data."""
        self.items = list(range(1, 101))  # 100 items

    def test_first_page(self):
        """Test getting the first page."""
        result, total_pages, total_items = paginate_results(
            self.items, page=1, limit=10
        )
        assert len(result) == 10
        assert result == list(range(1, 11))
        assert total_pages == 10
        assert total_items == 100

    def test_middle_page(self):
        """Test getting a middle page."""
        result, total_pages, total_items = paginate_results(
            self.items, page=5, limit=10
        )
        assert len(result) == 10
        assert result == list(range(41, 51))

    def test_last_page(self):
        """Test getting the last page."""
        result, total_pages, total_items = paginate_results(
            self.items, page=10, limit=10
        )
        assert len(result) == 10
        assert result == list(range(91, 101))

    def test_partial_last_page(self):
        """Test last page with fewer items."""
        result, total_pages, total_items = paginate_results(
            self.items[:95], page=10, limit=10
        )
        assert len(result) == 5
        assert result == list(range(91, 96))

    def test_page_beyond_range(self):
        """Test requesting a page beyond available data."""
        result, total_pages, total_items = paginate_results(
            self.items, page=20, limit=10
        )
        assert len(result) == 0
        assert total_pages == 10

    def test_zero_limit(self):
        """Test limit=0 returns all items."""
        result, total_pages, total_items = paginate_results(self.items, page=1, limit=0)
        assert len(result) == 100
        assert result == self.items
        assert total_pages == 1

    def test_negative_page(self):
        """Test negative page number defaults to 1."""
        result, _, _ = paginate_results(self.items, page=-1, limit=10)
        assert result == list(range(1, 11))

    def test_empty_list(self):
        """Test pagination of empty list."""
        result, total_pages, total_items = paginate_results([], page=1, limit=10)
        assert len(result) == 0
        assert total_pages == 0
        assert total_items == 0
