"""Unit tests for the operations module."""

from unittest.mock import Mock, patch

import pytest

from mcp_kanka.operations import KankaOperations, create_operations, get_operations


class TestOperationsSetup:
    """Test operations instance creation and management."""

    def test_create_operations_with_service(self):
        """Test creating operations with a custom service."""
        mock_service = Mock()
        ops = create_operations(service=mock_service)
        assert isinstance(ops, KankaOperations)
        assert ops.service is mock_service

    def test_create_operations_without_service(self):
        """Test creating operations creates a default service."""
        with patch("mcp_kanka.operations.KankaService") as mock_service_class:
            mock_service_instance = Mock()
            mock_service_class.return_value = mock_service_instance

            ops = create_operations()

            assert isinstance(ops, KankaOperations)
            assert ops.service is mock_service_instance
            mock_service_class.assert_called_once()

    @patch("mcp_kanka.operations.get_service")
    def test_get_operations_singleton(self, mock_get_service):
        """Test get_operations returns singleton."""
        # Reset singleton for this test
        import mcp_kanka.operations

        mcp_kanka.operations._operations = None

        mock_service = Mock()
        mock_get_service.return_value = mock_service

        # First call creates instance
        ops1 = get_operations()
        assert isinstance(ops1, KankaOperations)
        mock_get_service.assert_called_once()

        # Second call returns same instance
        ops2 = get_operations()
        assert ops1 is ops2
        mock_get_service.assert_called_once()  # Still only called once


class TestFindEntities:
    """Test find_entities operation."""

    @patch("mcp_kanka.operations.KankaService")
    async def test_find_entities_with_query(self, mock_service_class):
        """Test finding entities with search query."""
        # Setup
        mock_service = Mock()
        mock_service_class.return_value = mock_service

        # Mock entity objects
        mock_entity = Mock(id=1, entity_id=1, name="Test Entity", type="NPC")
        mock_service.list_entities.return_value = [mock_entity]
        mock_service._entity_to_dict.return_value = {
            "id": 1,
            "entity_id": 1,
            "name": "Test Entity",
            "entity_type": "character",
            "type": "NPC",
            "entry": "Test content with search term",
            "tags": [],
            "is_hidden": False,
            "created_at": "2023-01-01T00:00:00Z",
            "updated_at": "2023-01-01T00:00:00Z",
        }

        ops = KankaOperations(service=mock_service)

        # Execute
        result = await ops.find_entities(
            query="search term", entity_type="character", include_full=True
        )

        # Verify
        assert isinstance(result, dict)
        assert "entities" in result
        assert "sync_info" in result
        assert len(result["entities"]) == 1
        assert result["entities"][0]["name"] == "Test Entity"

    @patch("mcp_kanka.operations.KankaService")
    async def test_find_entities_invalid_type(self, mock_service_class):
        """Test find_entities with invalid entity type."""
        mock_service = Mock()
        mock_service_class.return_value = mock_service

        ops = KankaOperations(service=mock_service)

        # Execute with invalid type
        result = await ops.find_entities(entity_type="invalid_type")

        # Should return empty result
        assert result == {"entities": [], "sync_info": {}}


class TestCreateEntities:
    """Test create_entities operation."""

    @patch("mcp_kanka.operations.KankaService")
    async def test_create_single_entity_success(self, mock_service_class):
        """Test successfully creating a single entity."""
        mock_service = Mock()
        mock_service_class.return_value = mock_service

        # Mock successful creation
        mock_service.create_entity.return_value = {
            "id": 1,
            "entity_id": 101,
            "name": "Test Character",
            "mention": "[entity:101]",
        }

        ops = KankaOperations(service=mock_service)

        # Execute
        result = await ops.create_entities(
            [
                {
                    "entity_type": "character",
                    "name": "Test Character",
                    "type": "NPC",
                    "entry": "A test character",
                }
            ]
        )

        # Verify
        assert len(result) == 1
        assert result[0]["success"] is True
        assert result[0]["entity_id"] == 101
        assert result[0]["name"] == "Test Character"
        assert result[0]["error"] is None

    @patch("mcp_kanka.operations.KankaService")
    async def test_create_entity_invalid_type(self, mock_service_class):
        """Test creating entity with invalid type."""
        mock_service = Mock()
        mock_service_class.return_value = mock_service

        ops = KankaOperations(service=mock_service)

        # Execute with invalid type
        result = await ops.create_entities(
            [
                {
                    "entity_type": "invalid_type",
                    "name": "Test",
                }
            ]
        )

        # Verify error result
        assert len(result) == 1
        assert result[0]["success"] is False
        assert "Invalid entity_type" in result[0]["error"]
        assert result[0]["entity_id"] is None

    @patch("mcp_kanka.operations.KankaService")
    async def test_create_entity_missing_name(self, mock_service_class):
        """Test creating entity without name."""
        mock_service = Mock()
        mock_service_class.return_value = mock_service

        ops = KankaOperations(service=mock_service)

        # Execute without name
        result = await ops.create_entities(
            [
                {
                    "entity_type": "character",
                    # Missing name
                }
            ]
        )

        # Verify error result
        assert len(result) == 1
        assert result[0]["success"] is False
        assert "Name is required" in result[0]["error"]

    @patch("mcp_kanka.operations.KankaService")
    async def test_create_entities_partial_success(self, mock_service_class):
        """Test creating multiple entities with partial failure."""
        mock_service = Mock()
        mock_service_class.return_value = mock_service

        # Mock mixed results
        mock_service.create_entity.side_effect = [
            {"id": 1, "entity_id": 101, "name": "Success", "mention": "[entity:101]"},
            Exception("API Error"),
        ]

        ops = KankaOperations(service=mock_service)

        # Execute multiple
        result = await ops.create_entities(
            [
                {"entity_type": "character", "name": "Success"},
                {"entity_type": "character", "name": "Failure"},
            ]
        )

        # Verify partial success
        assert len(result) == 2
        assert result[0]["success"] is True
        assert result[1]["success"] is False
        assert "API Error" in result[1]["error"]


class TestUpdateEntities:
    """Test update_entities operation."""

    @patch("mcp_kanka.operations.KankaService")
    async def test_update_entity_success(self, mock_service_class):
        """Test successfully updating an entity."""
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.update_entity.return_value = True

        ops = KankaOperations(service=mock_service)

        # Execute
        result = await ops.update_entities([{"entity_id": 101, "name": "Updated Name"}])

        # Verify
        assert len(result) == 1
        assert result[0]["success"] is True
        assert result[0]["entity_id"] == 101
        assert result[0]["error"] is None

    @patch("mcp_kanka.operations.KankaService")
    async def test_update_entity_missing_id(self, mock_service_class):
        """Test updating entity without ID."""
        mock_service = Mock()
        mock_service_class.return_value = mock_service

        ops = KankaOperations(service=mock_service)

        # Execute without entity_id
        result = await ops.update_entities([{"name": "Updated Name"}])

        # Verify error
        assert len(result) == 1
        assert result[0]["success"] is False
        assert "entity_id is required" in result[0]["error"]

    @patch("mcp_kanka.operations.KankaService")
    async def test_update_entity_missing_name(self, mock_service_class):
        """Test updating entity without name."""
        mock_service = Mock()
        mock_service_class.return_value = mock_service

        ops = KankaOperations(service=mock_service)

        # Execute without name
        result = await ops.update_entities([{"entity_id": 101}])

        # Verify error
        assert len(result) == 1
        assert result[0]["success"] is False
        assert "name is required" in result[0]["error"]


class TestGetEntities:
    """Test get_entities operation."""

    @patch("mcp_kanka.operations.KankaService")
    async def test_get_entities_success(self, mock_service_class):
        """Test successfully getting entities."""
        mock_service = Mock()
        mock_service_class.return_value = mock_service

        # Mock entity data
        mock_service.get_entity_by_id.return_value = {
            "id": 1,
            "entity_id": 101,
            "name": "Test Entity",
            "entity_type": "character",
            "type": "NPC",
            "entry": "Description",
            "tags": ["test"],
            "is_hidden": False,
        }

        ops = KankaOperations(service=mock_service)

        # Execute
        result = await ops.get_entities([101], include_posts=False)

        # Verify
        assert len(result) == 1
        assert result[0]["success"] is True
        assert result[0]["entity_id"] == 101
        assert result[0]["name"] == "Test Entity"
        assert "posts" not in result[0]

    @patch("mcp_kanka.operations.KankaService")
    async def test_get_entities_with_posts(self, mock_service_class):
        """Test getting entities with posts."""
        mock_service = Mock()
        mock_service_class.return_value = mock_service

        # Mock entity with posts
        mock_service.get_entity_by_id.return_value = {
            "id": 1,
            "entity_id": 101,
            "name": "Test Entity",
            "entity_type": "character",
            "posts": [
                {"id": 1, "name": "Post 1", "entry": "Content 1"},
                {"id": 2, "name": "Post 2", "entry": "Content 2"},
            ],
        }

        ops = KankaOperations(service=mock_service)

        # Execute
        result = await ops.get_entities([101], include_posts=True)

        # Verify
        assert len(result) == 1
        assert result[0]["success"] is True
        assert "posts" in result[0]
        assert len(result[0]["posts"]) == 2

    @patch("mcp_kanka.operations.KankaService")
    async def test_get_entity_not_found(self, mock_service_class):
        """Test getting non-existent entity."""
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.get_entity_by_id.return_value = None

        ops = KankaOperations(service=mock_service)

        # Execute
        result = await ops.get_entities([999])

        # Verify
        assert len(result) == 1
        assert result[0]["success"] is False
        assert "not found" in result[0]["error"]


class TestDeleteEntities:
    """Test delete_entities operation."""

    @patch("mcp_kanka.operations.KankaService")
    async def test_delete_entity_success(self, mock_service_class):
        """Test successfully deleting an entity."""
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.delete_entity.return_value = True

        ops = KankaOperations(service=mock_service)

        # Execute
        result = await ops.delete_entities([101])

        # Verify
        assert len(result) == 1
        assert result[0]["success"] is True
        assert result[0]["entity_id"] == 101
        assert result[0]["error"] is None

    @patch("mcp_kanka.operations.KankaService")
    async def test_delete_entity_failure(self, mock_service_class):
        """Test failed entity deletion."""
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.delete_entity.side_effect = Exception("Not found")

        ops = KankaOperations(service=mock_service)

        # Execute
        result = await ops.delete_entities([999])

        # Verify
        assert len(result) == 1
        assert result[0]["success"] is False
        assert "Not found" in result[0]["error"]


class TestPostOperations:
    """Test post-related operations."""

    @patch("mcp_kanka.operations.KankaService")
    async def test_create_post_success(self, mock_service_class):
        """Test successfully creating a post."""
        mock_service = Mock()
        mock_service_class.return_value = mock_service

        # Mock successful creation
        mock_service.create_post.return_value = {
            "post_id": 50,
            "entity_id": 101,
        }

        ops = KankaOperations(service=mock_service)

        # Execute
        result = await ops.create_posts(
            [
                {
                    "entity_id": 101,
                    "name": "Test Post",
                    "entry": "Post content",
                }
            ]
        )

        # Verify
        assert len(result) == 1
        assert result[0]["success"] is True
        assert result[0]["post_id"] == 50
        assert result[0]["entity_id"] == 101

    @patch("mcp_kanka.operations.KankaService")
    async def test_update_post_success(self, mock_service_class):
        """Test successfully updating a post."""
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.update_post.return_value = True

        ops = KankaOperations(service=mock_service)

        # Execute
        result = await ops.update_posts(
            [
                {
                    "entity_id": 101,
                    "post_id": 50,
                    "name": "Updated Post",
                    "entry": "Updated content",
                }
            ]
        )

        # Verify
        assert len(result) == 1
        assert result[0]["success"] is True
        assert result[0]["entity_id"] == 101
        assert result[0]["post_id"] == 50

    @patch("mcp_kanka.operations.KankaService")
    async def test_delete_post_success(self, mock_service_class):
        """Test successfully deleting a post."""
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.delete_post.return_value = True

        ops = KankaOperations(service=mock_service)

        # Execute
        result = await ops.delete_posts([{"entity_id": 101, "post_id": 50}])

        # Verify
        assert len(result) == 1
        assert result[0]["success"] is True
        assert result[0]["entity_id"] == 101
        assert result[0]["post_id"] == 50


class TestCheckEntityUpdates:
    """Test check_entity_updates operation."""

    @patch("mcp_kanka.operations.KankaService")
    async def test_check_updates_basic(self, mock_service_class):
        """Test basic check_entity_updates functionality."""
        mock_service = Mock()
        mock_client = Mock()
        mock_service.client = mock_client
        mock_service_class.return_value = mock_service

        # Mock entities response
        mock_client.entities.return_value = [
            {"id": 101, "updated_at": "2023-06-15T00:00:00Z"},
            {"id": 102, "updated_at": "2023-08-20T00:00:00Z"},
            {"id": 103, "updated_at": "2023-05-01T00:00:00Z"},
        ]

        ops = KankaOperations(service=mock_service)

        # Execute
        result = await ops.check_entity_updates(
            entity_ids=[101, 102, 103, 104], last_synced="2023-06-01T00:00:00Z"
        )

        # Verify
        assert set(result["modified_entity_ids"]) == {101, 102}
        assert result["deleted_entity_ids"] == [104]
        assert "check_timestamp" in result

    @patch("mcp_kanka.operations.KankaService")
    async def test_check_updates_missing_last_synced(self, mock_service_class):
        """Test check_entity_updates requires last_synced."""
        mock_service = Mock()
        mock_service_class.return_value = mock_service

        ops = KankaOperations(service=mock_service)

        # Execute without last_synced
        with pytest.raises(ValueError, match="last_synced parameter is required"):
            await ops.check_entity_updates(entity_ids=[101, 102], last_synced="")

    @patch("mcp_kanka.operations.KankaService")
    async def test_check_updates_empty_list(self, mock_service_class):
        """Test check_entity_updates with empty entity list."""
        mock_service = Mock()
        mock_client = Mock()
        mock_service.client = mock_client
        mock_service_class.return_value = mock_service

        mock_client.entities.return_value = []

        ops = KankaOperations(service=mock_service)

        # Execute
        result = await ops.check_entity_updates(
            entity_ids=[], last_synced="2023-06-01T00:00:00Z"
        )

        # Verify
        assert result["modified_entity_ids"] == []
        assert result["deleted_entity_ids"] == []
        assert "check_timestamp" in result
