"""Unit tests for the sync and timestamp features."""

from datetime import datetime, timezone
from unittest.mock import Mock, patch

import pytest

from mcp_kanka.tools import handle_check_entity_updates, handle_find_entities


class TestTimestampSupport:
    """Test timestamp support in entity responses."""

    @patch("mcp_kanka.operations.get_service")
    async def test_find_entities_includes_timestamps(self, mock_get_service):
        """Test that find_entities includes created_at and updated_at timestamps."""
        # Mock service
        mock_service = Mock()
        mock_get_service.return_value = mock_service

        # Mock entities with timestamps
        mock_entities = [
            Mock(
                id=1,
                entity_id=101,
                name="Alice",
                type="NPC",
                created_at=datetime(2023, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
                updated_at=datetime(2023, 6, 15, 14, 30, 0, tzinfo=timezone.utc),
            ),
            Mock(
                id=2,
                entity_id=102,
                name="Bob",
                type="Player",
                created_at=datetime(2023, 2, 1, 12, 0, 0, tzinfo=timezone.utc),
                updated_at=datetime(2023, 8, 20, 16, 45, 0, tzinfo=timezone.utc),
            ),
        ]
        mock_service.list_entities.return_value = mock_entities

        # Mock _entity_to_dict to include timestamps
        mock_service._entity_to_dict.side_effect = [
            {
                "id": 1,
                "entity_id": 101,
                "name": "Alice",
                "entity_type": "character",
                "type": "NPC",
                "entry": "Test character",
                "tags": [],
                "is_hidden": False,
                "created_at": "2023-01-01T10:00:00+00:00",
                "updated_at": "2023-06-15T14:30:00+00:00",
            },
            {
                "id": 2,
                "entity_id": 102,
                "name": "Bob",
                "entity_type": "character",
                "type": "Player",
                "entry": "Another character",
                "tags": [],
                "is_hidden": False,
                "created_at": "2023-02-01T12:00:00+00:00",
                "updated_at": "2023-08-20T16:45:00+00:00",
            },
        ]

        # Test with full details
        result = await handle_find_entities(
            entity_type="character",
            include_full=True,
        )

        # Check response structure
        assert "entities" in result
        assert "sync_info" in result

        entities = result["entities"]
        assert len(entities) == 2

        # Check timestamps are included
        assert entities[0]["created_at"] == "2023-01-01T10:00:00+00:00"
        assert entities[0]["updated_at"] == "2023-06-15T14:30:00+00:00"
        assert entities[1]["created_at"] == "2023-02-01T12:00:00+00:00"
        assert entities[1]["updated_at"] == "2023-08-20T16:45:00+00:00"

    @patch("mcp_kanka.operations.get_service")
    async def test_sync_info_metadata(self, mock_get_service):
        """Test that sync_info metadata is correctly calculated."""
        # Mock service
        mock_service = Mock()
        mock_get_service.return_value = mock_service

        # Mock entities with timestamps
        mock_entities = [
            Mock(id=1, entity_id=101, name="Alice"),
            Mock(id=2, entity_id=102, name="Bob"),
            Mock(id=3, entity_id=103, name="Charlie"),
        ]
        mock_service.list_entities.return_value = mock_entities

        # Mock _entity_to_dict
        mock_service._entity_to_dict.side_effect = [
            {
                "id": 1,
                "entity_id": 101,
                "name": "Alice",
                "entity_type": "character",
                "updated_at": "2023-06-15T14:30:00+00:00",
            },
            {
                "id": 2,
                "entity_id": 102,
                "name": "Bob",
                "entity_type": "character",
                "updated_at": "2023-08-20T16:45:00+00:00",  # Newest
            },
            {
                "id": 3,
                "entity_id": 103,
                "name": "Charlie",
                "entity_type": "character",
                "updated_at": "2023-07-10T10:00:00+00:00",
            },
        ]

        # Test
        result = await handle_find_entities(
            entity_type="character",
            limit=2,  # Paginate to return only 2
        )

        sync_info = result["sync_info"]

        # Check sync_info fields
        assert "request_timestamp" in sync_info
        assert (
            sync_info["newest_updated_at"] == "2023-08-20T16:45:00+00:00"
        )  # Bob's timestamp
        assert sync_info["total_count"] == 3
        assert sync_info["returned_count"] == 2

    @patch("mcp_kanka.operations.get_service")
    async def test_last_synced_parameter(self, mock_get_service):
        """Test that last_synced parameter is passed to the service."""
        # Mock service
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        mock_service.list_entities.return_value = []

        # Test with last_synced
        last_sync_time = "2023-06-01T00:00:00Z"
        await handle_find_entities(
            entity_type="character",
            last_synced=last_sync_time,
        )

        # Verify service was called with last_sync
        mock_service.list_entities.assert_called_with(
            "character", page=1, limit=0, last_sync=last_sync_time, related=True
        )


class TestCheckEntityUpdates:
    """Test the check_entity_updates functionality."""

    @patch("mcp_kanka.operations.get_service")
    async def test_check_entity_updates_basic(self, mock_get_service):
        """Test basic check_entity_updates functionality."""
        # Mock service
        mock_service = Mock()
        mock_client = Mock()
        mock_service.client = mock_client
        mock_get_service.return_value = mock_service

        # Mock entities response
        mock_client.entities.return_value = [
            {"id": 101, "updated_at": "2023-06-15T14:30:00Z"},
            {"id": 102, "updated_at": "2023-08-20T16:45:00Z"},
            {"id": 103, "updated_at": "2023-05-01T10:00:00Z"},
            # 104 is not in response (deleted)
        ]

        # Test
        result = await handle_check_entity_updates(
            entity_ids=[101, 102, 103, 104], last_synced="2023-06-01T00:00:00Z"
        )

        # Check results
        assert set(result["modified_entity_ids"]) == {101, 102}  # Updated after June 1
        assert result["deleted_entity_ids"] == [104]  # Not found
        assert "check_timestamp" in result

    @patch("mcp_kanka.operations.get_service")
    async def test_check_entity_updates_no_modifications(self, mock_get_service):
        """Test check_entity_updates when no entities are modified."""
        # Mock service
        mock_service = Mock()
        mock_client = Mock()
        mock_service.client = mock_client
        mock_get_service.return_value = mock_service

        # Mock entities response - all updated before last_synced
        mock_client.entities.return_value = [
            {"id": 101, "updated_at": "2023-01-15T14:30:00Z"},
            {"id": 102, "updated_at": "2023-02-20T16:45:00Z"},
        ]

        # Test
        result = await handle_check_entity_updates(
            entity_ids=[101, 102], last_synced="2023-06-01T00:00:00Z"
        )

        # Check results
        assert result["modified_entity_ids"] == []
        assert result["deleted_entity_ids"] == []
        assert "check_timestamp" in result

    @patch("mcp_kanka.operations.get_service")
    async def test_check_entity_updates_pagination(self, mock_get_service):
        """Test that check_entity_updates handles pagination correctly."""
        # Mock service
        mock_service = Mock()
        mock_client = Mock()
        mock_service.client = mock_client
        mock_get_service.return_value = mock_service

        # Mock paginated responses
        def mock_entities(page=1, limit=100):
            if page == 1:
                return [
                    {"id": i, "updated_at": "2023-07-01T00:00:00Z"}
                    for i in range(1, 101)
                ]
            elif page == 2:
                return [
                    {"id": i, "updated_at": "2023-07-01T00:00:00Z"}
                    for i in range(101, 151)
                ]
            else:
                return []

        mock_client.entities.side_effect = mock_entities

        # Test with entity ID from second page
        result = await handle_check_entity_updates(
            entity_ids=[50, 125, 200],  # 200 doesn't exist
            last_synced="2023-06-01T00:00:00Z",
        )

        # Check results
        assert set(result["modified_entity_ids"]) == {50, 125}
        assert result["deleted_entity_ids"] == [200]

    @patch("mcp_kanka.operations.get_service")
    async def test_check_entity_updates_missing_last_synced(self, mock_get_service):
        """Test that check_entity_updates requires last_synced parameter."""
        # Mock service (not actually used in this test)
        mock_service = Mock()
        mock_get_service.return_value = mock_service

        with pytest.raises(ValueError, match="last_synced parameter is required"):
            await handle_check_entity_updates(
                entity_ids=[101, 102],
                # last_synced missing
            )

    @patch("mcp_kanka.operations.get_service")
    async def test_check_entity_updates_empty_list(self, mock_get_service):
        """Test check_entity_updates with empty entity list."""
        # Mock service
        mock_service = Mock()
        mock_client = Mock()
        mock_service.client = mock_client
        mock_get_service.return_value = mock_service

        mock_client.entities.return_value = []

        # Test
        result = await handle_check_entity_updates(
            entity_ids=[], last_synced="2023-06-01T00:00:00Z"
        )

        # Check results
        assert result["modified_entity_ids"] == []
        assert result["deleted_entity_ids"] == []
        assert "check_timestamp" in result
