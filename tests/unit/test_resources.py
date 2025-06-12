"""Unit tests for the resources module."""

import json

from mcp_kanka.resources import get_kanka_context


class TestGetKankaContext:
    """Test the get_kanka_context function."""

    def test_returns_json_string(self):
        """Test that the function returns a valid JSON string."""
        result = get_kanka_context()
        assert isinstance(result, str)

        # Should be valid JSON
        data = json.loads(result)
        assert isinstance(data, dict)

    def test_context_structure(self):
        """Test the structure of the returned context."""
        result = get_kanka_context()
        data = json.loads(result)

        # Check top-level keys
        assert "description" in data
        assert "supported_entities" in data
        assert "core_fields" in data
        assert "terminology" in data
        assert "posts" in data
        assert "mentions" in data
        assert "limitations" in data

    def test_supported_entities(self):
        """Test the supported_entities section."""
        result = get_kanka_context()
        data = json.loads(result)

        entities = data["supported_entities"]
        assert isinstance(entities, dict)
        assert len(entities) == 8

        # Check all expected entity types
        expected_types = [
            "character",
            "creature",
            "location",
            "organization",
            "race",
            "note",
            "journal",
            "quest",
        ]
        for expected in expected_types:
            assert expected in entities
            assert isinstance(entities[expected], str)  # Should have description

    def test_core_fields(self):
        """Test the core fields documentation."""
        result = get_kanka_context()
        data = json.loads(result)

        fields = data["core_fields"]
        assert isinstance(fields, dict)

        # Check expected fields
        expected_fields = ["name", "type", "entry", "tags", "is_hidden"]
        for field in expected_fields:
            assert field in fields
            assert isinstance(fields[field], str)  # Should have description

    def test_terminology(self):
        """Test the terminology section."""
        result = get_kanka_context()
        data = json.loads(result)

        terminology = data["terminology"]
        assert isinstance(terminology, dict)
        assert "entity_type" in terminology
        assert "type" in terminology

    def test_mentions_section(self):
        """Test the mentions documentation."""
        result = get_kanka_context()
        data = json.loads(result)

        mentions = data["mentions"]
        assert isinstance(mentions, dict)
        assert "description" in mentions
        assert "examples" in mentions
        assert "note" in mentions

        # Check examples
        examples = mentions["examples"]
        assert isinstance(examples, list)
        assert len(examples) > 0

    def test_posts_field(self):
        """Test the posts field documentation."""
        result = get_kanka_context()
        data = json.loads(result)

        posts = data["posts"]
        assert isinstance(posts, str)
        assert "notes" in posts.lower() or "comments" in posts.lower()

    def test_limitations_field(self):
        """Test the limitations field."""
        result = get_kanka_context()
        data = json.loads(result)

        limitations = data["limitations"]
        assert isinstance(limitations, str)
        assert len(limitations) > 0

    def test_description_field(self):
        """Test the description field."""
        result = get_kanka_context()
        data = json.loads(result)

        description = data["description"]
        assert isinstance(description, str)
        assert "Kanka" in description
        assert "worldbuilding" in description.lower()

    def test_json_serializable(self):
        """Test that the context can be serialized and deserialized."""
        result = get_kanka_context()
        data = json.loads(result)

        # Should be able to serialize back to JSON
        json_str = json.dumps(data)
        assert isinstance(json_str, str)

        # And deserialize again
        data2 = json.loads(json_str)
        assert data2 == data
