"""Unit tests for the tools module with mocked service."""

from unittest.mock import Mock, patch

from mcp_kanka.tools import (
    handle_create_entities,
    handle_create_posts,
    handle_delete_entities,
    handle_delete_posts,
    handle_find_entities,
    handle_get_entities,
    handle_update_entities,
    handle_update_posts,
)


class TestFindEntities:
    """Test the handle_find_entities function."""

    @patch("mcp_kanka.operations.get_service")
    async def test_find_with_search_query(self, mock_get_service):
        """Test finding entities with a search query."""
        # Mock service
        mock_service = Mock()
        mock_get_service.return_value = mock_service

        # Mock list results for content search
        mock_entities = [
            Mock(id=1, entity_id=1, name="Alice", type="NPC"),
            Mock(id=2, entity_id=2, name="Bob", type="Player"),
            Mock(id=3, entity_id=3, name="Charlie", type="NPC"),
        ]
        mock_service.list_entities.return_value = mock_entities

        # Mock _entity_to_dict conversions
        mock_service._entity_to_dict.side_effect = [
            {
                "id": 1,
                "entity_id": 1,
                "name": "Alice",
                "entity_type": "character",
                "type": "NPC",
                "entry": "A brave warrior test",
                "tags": ["hero"],
                "is_hidden": False,
                "created_at": "2023-01-01T10:00:00Z",
                "updated_at": "2023-01-01T10:00:00Z",
            },
            {
                "id": 2,
                "entity_id": 2,
                "name": "Bob",
                "entity_type": "character",
                "type": "Player",
                "entry": "A cunning rogue",
                "tags": ["rogue"],
                "is_hidden": False,
                "created_at": "2023-01-01T10:00:00Z",
                "updated_at": "2023-01-01T10:00:00Z",
            },
            {
                "id": 3,
                "entity_id": 3,
                "name": "Test Charlie",
                "entity_type": "character",
                "type": "NPC",
                "entry": "Another character",
                "tags": [],
                "is_hidden": False,
                "created_at": "2023-01-01T10:00:00Z",
                "updated_at": "2023-01-01T10:00:00Z",
            },
        ]

        # Test search with full details
        result = await handle_find_entities(
            query="test",
            entity_type="character",
            include_full=True,
            limit=25,
        )

        # Check response structure
        assert "entities" in result
        assert "sync_info" in result

        entities = result["entities"]
        # Alice has "test" in entry, Charlie has "Test" in name
        assert len(entities) == 2
        assert entities[0]["name"] == "Alice"
        assert entities[1]["name"] == "Test Charlie"

        mock_service.list_entities.assert_called_once_with(
            "character", page=1, limit=0, last_sync=None, related=True
        )

    @patch("mcp_kanka.operations.get_service")
    async def test_find_without_search_query(self, mock_get_service):
        """Test finding entities by listing when no search query."""
        # Mock service
        mock_service = Mock()
        mock_get_service.return_value = mock_service

        # Mock list results
        mock_entities = [
            Mock(id=1, entity_id=1, name="Alice", type="NPC"),
            Mock(id=2, entity_id=2, name="Bob", type="Player"),
        ]
        mock_service.list_entities.return_value = mock_entities

        # Mock _entity_to_dict
        mock_service._entity_to_dict.side_effect = [
            {
                "id": 1,
                "entity_id": 1,
                "name": "Alice",
                "entity_type": "character",
                "type": "NPC",
                "tags": [],
                "is_hidden": False,
                "entry": None,
                "created_at": "2023-01-01T10:00:00Z",
                "updated_at": "2023-01-01T10:00:00Z",
            },
            {
                "id": 2,
                "entity_id": 2,
                "name": "Bob",
                "entity_type": "character",
                "type": "Player",
                "tags": [],
                "is_hidden": False,
                "entry": None,
                "created_at": "2023-01-01T10:00:00Z",
                "updated_at": "2023-01-01T10:00:00Z",
            },
        ]

        # Test list without search
        result = await handle_find_entities(
            entity_type="character",
            include_full=True,
        )

        entities = result["entities"]
        assert len(entities) == 2
        assert entities[0]["name"] == "Alice"
        assert entities[1]["name"] == "Bob"

        mock_service.list_entities.assert_called_once_with(
            "character", page=1, limit=0, last_sync=None, related=True
        )

    @patch("mcp_kanka.operations.filter_entities_by_name")
    @patch("mcp_kanka.operations.get_service")
    async def test_find_with_filters(self, mock_get_service, mock_filter_by_name):
        """Test finding entities with various filters."""
        # Mock service
        mock_service = Mock()
        mock_get_service.return_value = mock_service

        # Mock entities with various attributes
        mock_service.list_entities.return_value = []
        mock_service._entity_to_dict.side_effect = lambda e, t: {
            "id": e.id,
            "entity_id": e.entity_id,
            "name": e.name,
            "entity_type": t,
            "type": e.type,
            "tags": e.tags,
            "is_hidden": False,
            "entry": e.entry,
        }

        entities = [
            Mock(
                id=1,
                entity_id=1,
                name="Alice",
                type="NPC",
                tags=["hero", "warrior"],
                entry="Brave",
            ),
            Mock(
                id=2,
                entity_id=2,
                name="Bob",
                type="Player",
                tags=["rogue"],
                entry="Cunning",
            ),
            Mock(
                id=3,
                entity_id=3,
                name="Charlie",
                type="NPC",
                tags=["hero", "wizard"],
                entry="Wise",
            ),
        ]
        mock_service.list_entities.return_value = entities

        # Mock the filter function to return Alice
        mock_filter_by_name.return_value = [
            {
                "id": 1,
                "entity_id": 1,
                "name": "Alice",
                "entity_type": "character",
                "type": "NPC",
                "tags": ["hero", "warrior"],
                "is_hidden": False,
                "entry": "Brave",
            }
        ]

        # Test with name filter
        result = await handle_find_entities(
            entity_type="character",
            name="Alice",
            include_full=True,
        )

        # Should return results with proper structure
        assert "entities" in result
        assert "sync_info" in result
        assert len(result["entities"]) == 1
        assert result["entities"][0]["name"] == "Alice"

    @patch("mcp_kanka.operations.get_service")
    async def test_find_minimal_results(self, mock_get_service):
        """Test finding entities with minimal results (include_full=False)."""
        # Mock service
        mock_service = Mock()
        mock_get_service.return_value = mock_service

        # Mock list results for all entity types
        # Since no entity_type is specified, it will search all types
        mock_service.list_entities.side_effect = [
            # Characters
            [Mock(id=1, entity_id=1, name="Alice Test", type="NPC")],
            # Creatures - empty
            [],
            # Locations
            [Mock(id=2, entity_id=2, name="Test Location", type="City")],
            # Others empty
            [],
            [],
            [],
            [],
            [],
        ]

        # Mock _entity_to_dict for the entities that will be found
        mock_service._entity_to_dict.side_effect = [
            {
                "id": 1,
                "entity_id": 1,
                "name": "Alice Test",
                "entity_type": "character",
                "type": "NPC",
                "entry": "A character",
            },
            {
                "id": 2,
                "entity_id": 2,
                "name": "Test Location",
                "entity_type": "location",
                "type": "City",
                "entry": "A place",
            },
        ]

        # Test search with minimal details
        result = await handle_find_entities(
            query="test",
            include_full=False,
        )

        entities = result["entities"]
        assert len(entities) == 2
        assert entities[0] == {
            "entity_id": 1,
            "name": "Alice Test",
            "entity_type": "character",
        }
        assert entities[1] == {
            "entity_id": 2,
            "name": "Test Location",
            "entity_type": "location",
        }


class TestCreateEntities:
    """Test the handle_create_entities function."""

    @patch("mcp_kanka.operations.get_service")
    async def test_create_single_entity(self, mock_get_service):
        """Test creating a single entity."""
        # Mock service
        mock_service = Mock()
        mock_get_service.return_value = mock_service

        # Mock creation result
        mock_service.create_entity.return_value = {
            "id": 1,
            "entity_id": 101,
            "name": "Test Character",
            "mention": "[entity:101]",
        }

        # Test create
        result = await handle_create_entities(
            entities=[
                {
                    "entity_type": "character",
                    "name": "Test Character",
                    "type": "NPC",
                    "entry": "A test character",
                    "tags": ["test"],
                    "is_hidden": False,
                }
            ]
        )

        assert len(result) == 1
        assert result[0]["success"] is True
        assert result[0]["entity_id"] == 101
        assert result[0]["name"] == "Test Character"
        assert result[0]["mention"] == "[entity:101]"
        assert result[0]["error"] is None

    @patch("mcp_kanka.operations.get_service")
    async def test_create_multiple_entities(self, mock_get_service):
        """Test creating multiple entities with partial failures."""
        # Mock service
        mock_service = Mock()
        mock_get_service.return_value = mock_service

        # Mock mixed results
        mock_service.create_entity.side_effect = [
            {
                "id": 1,
                "entity_id": 101,
                "name": "Success Entity",
                "mention": "[entity:101]",
            },
            Exception("API Error: Name already exists"),
            {
                "id": 3,
                "entity_id": 103,
                "name": "Another Success",
                "mention": "[entity:103]",
            },
        ]

        # Test create multiple
        result = await handle_create_entities(
            entities=[
                {"entity_type": "character", "name": "Success Entity"},
                {"entity_type": "character", "name": "Duplicate Name"},
                {"entity_type": "location", "name": "Another Success"},
            ]
        )

        assert len(result) == 3

        # First entity succeeded
        assert result[0]["success"] is True
        assert result[0]["entity_id"] == 101

        # Second entity failed
        assert result[1]["success"] is False
        assert result[1]["entity_id"] is None
        assert result[1]["name"] == "Duplicate Name"
        assert "Name already exists" in result[1]["error"]

        # Third entity succeeded
        assert result[2]["success"] is True
        assert result[2]["entity_id"] == 103


class TestUpdateEntities:
    """Test the handle_update_entities function."""

    @patch("mcp_kanka.operations.get_service")
    async def test_update_entities(self, mock_get_service):
        """Test updating multiple entities."""
        # Mock service
        mock_service = Mock()
        mock_get_service.return_value = mock_service

        # Mock update results
        mock_service.update_entity.side_effect = [
            True,  # Success
            Exception("Entity not found"),  # Failure
            True,  # Success
        ]

        # Test update
        result = await handle_update_entities(
            updates=[
                {"entity_id": 101, "name": "Updated Name 1"},
                {"entity_id": 999, "name": "This will fail"},
                {"entity_id": 103, "name": "Updated Name 3", "type": "Boss NPC"},
            ]
        )

        assert len(result) == 3

        # Check results
        assert result[0]["entity_id"] == 101
        assert result[0]["success"] is True
        assert result[0]["error"] is None

        assert result[1]["entity_id"] == 999
        assert result[1]["success"] is False
        assert "not found" in result[1]["error"]

        assert result[2]["entity_id"] == 103
        assert result[2]["success"] is True


class TestGetEntities:
    """Test the handle_get_entities function."""

    @patch("mcp_kanka.operations.get_service")
    async def test_get_entities_without_posts(self, mock_get_service):
        """Test getting entities without posts."""
        # Mock service
        mock_service = Mock()
        mock_get_service.return_value = mock_service

        # Mock get results
        mock_service.get_entity_by_id.side_effect = [
            {
                "id": 1,
                "entity_id": 101,
                "name": "Alice",
                "entity_type": "character",
                "type": "NPC",
                "entry": "Description",
                "tags": ["hero"],
                "is_hidden": False,
            },
            None,  # Not found
            {
                "id": 3,
                "entity_id": 103,
                "name": "Cave",
                "entity_type": "location",
                "type": "Dungeon",
                "entry": None,
                "tags": [],
                "is_hidden": True,
            },
        ]

        # Test get
        result = await handle_get_entities(
            entity_ids=[101, 102, 103],
            include_posts=False,
        )

        assert len(result) == 3

        # First entity found
        assert result[0]["success"] is True
        assert result[0]["entity_id"] == 101
        assert result[0]["name"] == "Alice"
        assert "posts" not in result[0]

        # Second entity not found
        assert result[1]["success"] is False
        assert result[1]["entity_id"] == 102
        assert "not found" in result[1]["error"]

        # Third entity found
        assert result[2]["success"] is True
        assert result[2]["entity_id"] == 103

    @patch("mcp_kanka.operations.get_service")
    async def test_get_entities_with_posts(self, mock_get_service):
        """Test getting entities with posts."""
        # Mock service
        mock_service = Mock()
        mock_get_service.return_value = mock_service

        # Mock get results with posts
        mock_service.get_entity_by_id.return_value = {
            "id": 1,
            "entity_id": 101,
            "name": "Alice",
            "entity_type": "character",
            "posts": [
                {"id": 1, "name": "Background", "entry": "Long ago..."},
                {"id": 2, "name": "Recent Events", "entry": "Recently..."},
            ],
        }

        # Test get with posts
        result = await handle_get_entities(
            entity_ids=[101],
            include_posts=True,
        )

        assert len(result) == 1
        assert result[0]["success"] is True
        assert "posts" in result[0]
        assert len(result[0]["posts"]) == 2
        assert result[0]["posts"][0]["name"] == "Background"


class TestDeleteEntities:
    """Test the handle_delete_entities function."""

    @patch("mcp_kanka.operations.get_service")
    async def test_delete_entities(self, mock_get_service):
        """Test deleting multiple entities."""
        # Mock service
        mock_service = Mock()
        mock_get_service.return_value = mock_service

        # Mock delete results
        mock_service.delete_entity.side_effect = [
            True,  # Success
            Exception("Entity not found"),  # Failure
            True,  # Success
        ]

        # Test delete
        result = await handle_delete_entities(entity_ids=[101, 102, 103])

        assert len(result) == 3

        assert result[0]["entity_id"] == 101
        assert result[0]["success"] is True
        assert result[0]["error"] is None

        assert result[1]["entity_id"] == 102
        assert result[1]["success"] is False
        assert "not found" in result[1]["error"]

        assert result[2]["entity_id"] == 103
        assert result[2]["success"] is True


class TestInvalidParameters:
    """Test handling of invalid parameters."""

    @patch("mcp_kanka.operations.get_service")
    async def test_find_entities_invalid_entity_type(self, mock_get_service):
        """Test find_entities with invalid entity type."""
        # Mock service
        mock_service = Mock()
        mock_get_service.return_value = mock_service

        # Should handle invalid entity type gracefully
        # The service will raise an AttributeError when trying to access invalid manager
        mock_service.list_entities.side_effect = AttributeError(
            "'KankaClient' object has no attribute 'dragons'"
        )

        result = await handle_find_entities(
            entity_type="dragon",  # Invalid - should be "creature"
            include_full=True,
        )
        # Should return empty entities with empty sync_info
        assert result == {"entities": [], "sync_info": {}}

    @patch("mcp_kanka.operations.get_service")
    async def test_create_entities_invalid_entity_type(self, mock_get_service):
        """Test create_entities with invalid entity type."""
        # Mock service
        mock_service = Mock()
        mock_get_service.return_value = mock_service

        # Should handle invalid entity type
        result = await handle_create_entities(
            entities=[
                {
                    "entity_type": "invalid_type",
                    "name": "Test Entity",
                }
            ]
        )

        # Should return error for invalid entity
        assert len(result) == 1
        assert result[0]["success"] is False
        assert "error" in result[0]

    @patch("mcp_kanka.operations.get_service")
    async def test_find_entities_invalid_date_format(self, mock_get_service):
        """Test find_entities with invalid date format."""
        # Mock service
        mock_service = Mock()
        mock_get_service.return_value = mock_service

        # Mock list results
        mock_entities = [Mock(id=1, entity_id=1, name="Test Journal", type="Session")]
        mock_service.list_entities.return_value = mock_entities

        # Mock _entity_to_dict
        mock_service._entity_to_dict.return_value = {
            "id": 1,
            "entity_id": 1,
            "name": "Test Journal",
            "entity_type": "journal",
            "entry": "Date: 2025-05-30",
        }

        # Test with invalid date format
        result = await handle_find_entities(
            entity_type="journal",
            date_range={
                "start": "invalid-date",
                "end": "2025-12-31",
            },
            include_full=True,
        )

        # Should handle gracefully - return dict with entities
        assert isinstance(result, dict)
        assert "entities" in result
        assert isinstance(result["entities"], list)

    @patch("mcp_kanka.operations.get_service")
    async def test_update_entities_missing_required_fields(self, mock_get_service):
        """Test update_entities with missing required fields."""
        # Mock service
        mock_service = Mock()
        mock_get_service.return_value = mock_service

        # Test missing name (required by Kanka API)
        result = await handle_update_entities(
            updates=[
                {
                    "entity_id": 123,
                    # Missing "name" field
                    "entry": "Updated content",
                }
            ]
        )

        # Should return error for missing required field
        assert len(result) == 1
        assert result[0]["success"] is False
        assert (
            "name" in result[0]["error"].lower()
            or "required" in result[0]["error"].lower()
        )


class TestPostOperations:
    """Test post-related operations."""

    @patch("mcp_kanka.operations.get_service")
    async def test_create_posts(self, mock_get_service):
        """Test creating posts."""
        # Mock service
        mock_service = Mock()
        mock_get_service.return_value = mock_service

        # Mock create results
        mock_service.create_post.side_effect = [
            {"post_id": 50, "entity_id": 101},
            Exception("Entity not found"),
        ]

        # Test create posts
        result = await handle_create_posts(
            posts=[
                {
                    "entity_id": 101,
                    "name": "Test Post",
                    "entry": "Post content",
                    "is_hidden": False,
                },
                {
                    "entity_id": 999,
                    "name": "This will fail",
                },
            ]
        )

        assert len(result) == 2

        assert result[0]["success"] is True
        assert result[0]["post_id"] == 50
        assert result[0]["entity_id"] == 101

        assert result[1]["success"] is False
        assert result[1]["post_id"] is None
        assert result[1]["entity_id"] == 999

    @patch("mcp_kanka.operations.get_service")
    async def test_update_posts(self, mock_get_service):
        """Test updating posts."""
        # Mock service
        mock_service = Mock()
        mock_get_service.return_value = mock_service

        # Mock update results
        mock_service.update_post.side_effect = [True, Exception("Post not found")]

        # Test update posts
        result = await handle_update_posts(
            updates=[
                {
                    "entity_id": 101,
                    "post_id": 50,
                    "name": "Updated Post",
                    "entry": "Updated content",
                },
                {
                    "entity_id": 101,
                    "post_id": 999,
                    "name": "This will fail",
                },
            ]
        )

        assert len(result) == 2

        assert result[0]["success"] is True
        assert result[0]["entity_id"] == 101
        assert result[0]["post_id"] == 50

        assert result[1]["success"] is False
        assert result[1]["post_id"] == 999

    @patch("mcp_kanka.operations.get_service")
    async def test_delete_posts(self, mock_get_service):
        """Test deleting posts."""
        # Mock service
        mock_service = Mock()
        mock_get_service.return_value = mock_service

        # Mock delete results
        mock_service.delete_post.side_effect = [True, Exception("Post not found")]

        # Test delete posts
        result = await handle_delete_posts(
            deletions=[
                {"entity_id": 101, "post_id": 50},
                {"entity_id": 101, "post_id": 999},
            ]
        )

        assert len(result) == 2

        assert result[0]["success"] is True
        assert result[0]["entity_id"] == 101
        assert result[0]["post_id"] == 50

        assert result[1]["success"] is False
        assert result[1]["post_id"] == 999
