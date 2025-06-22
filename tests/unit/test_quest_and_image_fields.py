"""Tests for quest-specific and image-related fields."""

from datetime import datetime
from unittest.mock import MagicMock, Mock, patch

import pytest

from mcp_kanka.operations import KankaOperations
from mcp_kanka.service import KankaService


class TestQuestFields:
    """Test quest-specific field handling."""

    @patch("mcp_kanka.service.KankaClient")
    @patch.dict("os.environ", {"KANKA_TOKEN": "test-token", "KANKA_CAMPAIGN_ID": "123"})
    def setup_method(self, method, mock_client_class):
        """Set up test fixtures with mocked client."""
        self.mock_client = MagicMock()
        mock_client_class.return_value = self.mock_client
        self.service = KankaService()

        # Set up mock managers
        self.mock_client.quests = MagicMock()
        self.mock_client.entities = MagicMock()
        self.mock_client.characters = MagicMock()

    def test_create_quest_with_is_completed(self):
        """Test creating a quest with is_completed field."""
        # Mock the create response
        mock_quest = Mock()
        mock_quest.id = 1
        mock_quest.entity_id = 123
        mock_quest.name = "Test Quest"
        mock_quest.type = None
        mock_quest.is_private = False
        mock_quest.is_completed = True
        mock_quest.created_at = datetime.now()
        mock_quest.updated_at = datetime.now()
        mock_quest.tags = []
        mock_quest.entry = None
        mock_quest.posts = None  # No posts by default

        self.mock_client.quests.create.return_value = mock_quest

        # Create quest with is_completed=True
        result = self.service.create_entity(
            entity_type="quest", name="Test Quest", is_completed=True
        )

        # Verify the API was called with is_completed
        self.mock_client.quests.create.assert_called_once()
        call_args = self.mock_client.quests.create.call_args[1]
        assert call_args["is_completed"] is True

        # Verify the result includes is_completed
        assert result["is_completed"] is True

    def test_update_quest_is_completed(self):
        """Test updating a quest's is_completed status."""
        # Mock getting entity to find its type
        self.service.get_entity_by_id = Mock(
            return_value={
                "id": 1,
                "entity_id": 123,
                "entity_type": "quest",
                "name": "Test Quest",
            }
        )

        # Mock the update response
        self.mock_client.quests.update.return_value = None

        # Update quest with is_completed=True
        result = self.service.update_entity(
            entity_id=123, name="Test Quest", is_completed=True
        )

        # Verify the API was called with is_completed
        self.mock_client.quests.update.assert_called_once()
        call_args = self.mock_client.quests.update.call_args[1]
        assert call_args["is_completed"] is True

        assert result is True

    def test_entity_to_dict_quest_with_is_completed(self):
        """Test _entity_to_dict extracts is_completed for quests."""
        # Mock a quest entity
        mock_quest = Mock()
        mock_quest.id = 1
        mock_quest.entity_id = 123
        mock_quest.name = "Test Quest"
        mock_quest.type = None
        mock_quest.is_private = False
        mock_quest.is_completed = True
        mock_quest.created_at = datetime.now()
        mock_quest.updated_at = datetime.now()
        mock_quest.tags = []
        mock_quest.entry = None
        mock_quest.posts = None  # No posts by default

        # Convert to dict
        result = self.service._entity_to_dict(mock_quest, "quest")

        # Verify is_completed is included
        assert result["is_completed"] is True


class TestImageFields:
    """Test image-related field handling."""

    @patch("mcp_kanka.service.KankaClient")
    @patch.dict("os.environ", {"KANKA_TOKEN": "test-token", "KANKA_CAMPAIGN_ID": "123"})
    def setup_method(self, method, mock_client_class):
        """Set up test fixtures with mocked client."""
        self.mock_client = MagicMock()
        mock_client_class.return_value = self.mock_client
        self.service = KankaService()

        # Set up mock managers
        self.mock_client.characters = MagicMock()
        self.mock_client.entities = MagicMock()

    def test_create_entity_with_image_fields(self):
        """Test creating an entity with image_uuid and header_uuid."""
        # Mock the create response
        mock_character = Mock()
        mock_character.id = 1
        mock_character.entity_id = 123
        mock_character.name = "Test Character"
        mock_character.type = None
        mock_character.is_private = False
        mock_character.created_at = datetime.now()
        mock_character.updated_at = datetime.now()
        mock_character.tags = []
        mock_character.entry = None
        mock_character.posts = None  # No posts by default
        mock_character.image_uuid = "image-123"
        mock_character.header_uuid = "header-456"

        self.mock_client.characters.create.return_value = mock_character

        # Create character with image fields
        self.service.create_entity(
            entity_type="character",
            name="Test Character",
            image_uuid="image-123",
            header_uuid="header-456",
        )

        # Verify the API was called with image fields
        self.mock_client.characters.create.assert_called_once()
        call_args = self.mock_client.characters.create.call_args[1]
        assert call_args["image_uuid"] == "image-123"
        assert call_args["header_uuid"] == "header-456"

    def test_update_entity_image_fields(self):
        """Test updating an entity's image fields."""
        # Mock getting entity to find its type
        self.service.get_entity_by_id = Mock(
            return_value={
                "id": 1,
                "entity_id": 123,
                "entity_type": "character",
                "name": "Test Character",
            }
        )

        # Mock the update response
        self.mock_client.characters.update.return_value = None

        # Update character with image fields
        result = self.service.update_entity(
            entity_id=123,
            name="Test Character",
            image_uuid="new-image-789",
            header_uuid="new-header-101",
        )

        # Verify the API was called with image fields
        self.mock_client.characters.update.assert_called_once()
        call_args = self.mock_client.characters.update.call_args[1]
        assert call_args["image_uuid"] == "new-image-789"
        assert call_args["header_uuid"] == "new-header-101"

        assert result is True

    def test_entity_to_dict_includes_all_image_fields(self):
        """Test _entity_to_dict includes all 5 image fields."""
        # Mock an entity with all image fields
        mock_entity = Mock()
        mock_entity.id = 1
        mock_entity.entity_id = 123
        mock_entity.name = "Test Entity"
        mock_entity.type = None
        mock_entity.is_private = False
        mock_entity.created_at = datetime.now()
        mock_entity.updated_at = datetime.now()
        mock_entity.tags = []
        mock_entity.entry = None
        mock_entity.posts = None  # No posts by default

        # Set all image fields
        mock_entity.image = "/path/to/image.jpg"
        mock_entity.image_full = "https://example.com/image-full.jpg"
        mock_entity.image_thumb = "https://example.com/image-thumb.jpg"
        mock_entity.image_uuid = "image-uuid-123"
        mock_entity.header_uuid = "header-uuid-456"

        # Convert to dict
        result = self.service._entity_to_dict(mock_entity, "character")

        # Verify all image fields are included
        assert result["image"] == "/path/to/image.jpg"
        assert result["image_full"] == "https://example.com/image-full.jpg"
        assert result["image_thumb"] == "https://example.com/image-thumb.jpg"
        assert result["image_uuid"] == "image-uuid-123"
        assert result["header_uuid"] == "header-uuid-456"

    def test_entity_to_dict_image_fields_none_when_missing(self):
        """Test _entity_to_dict sets image fields to None when missing."""
        # Mock an entity without image fields using spec to limit attributes
        mock_entity = Mock(
            spec=[
                "id",
                "entity_id",
                "name",
                "type",
                "is_private",
                "created_at",
                "updated_at",
                "tags",
                "entry",
                "posts",
            ]
        )
        mock_entity.id = 1
        mock_entity.entity_id = 123
        mock_entity.name = "Test Entity"
        mock_entity.type = None
        mock_entity.is_private = False
        mock_entity.created_at = datetime.now()
        mock_entity.updated_at = datetime.now()
        mock_entity.tags = []
        mock_entity.entry = None
        mock_entity.posts = None  # No posts by default

        # Convert to dict
        result = self.service._entity_to_dict(mock_entity, "character")

        # Verify all image fields are None
        assert result["image"] is None
        assert result["image_full"] is None
        assert result["image_thumb"] is None
        assert result["image_uuid"] is None
        assert result["header_uuid"] is None


class TestOperationsImageFields:
    """Test image fields in operations layer."""

    @pytest.mark.asyncio
    async def test_find_entities_full_includes_image_fields(self):
        """Test find_entities with include_full=True includes image fields."""
        # Mock service
        mock_service = Mock()
        mock_service.list_entities.return_value = []

        # Mock entity with image fields
        mock_entity = {
            "id": 1,
            "entity_id": 123,
            "name": "Test Entity",
            "entity_type": "character",
            "type": None,
            "entry": None,
            "tags": [],
            "is_hidden": False,
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
            "image": "/path/to/image.jpg",
            "image_full": "https://example.com/image-full.jpg",
            "image_thumb": "https://example.com/image-thumb.jpg",
            "image_uuid": "image-uuid-123",
            "header_uuid": "header-uuid-456",
        }

        mock_service._entity_to_dict.return_value = mock_entity

        # Create operations with mocked service
        ops = KankaOperations(service=mock_service)
        ops.service = mock_service

        # Mock the list_entities to return one entity
        mock_entity_obj = Mock()
        mock_service.list_entities.return_value = [mock_entity_obj]

        # Find entities with full details
        result = await ops.find_entities(entity_type="character", include_full=True)

        # Check that the image fields are present in full results
        assert len(result["entities"]) == 1
        entity = result["entities"][0]
        assert entity["image"] == "/path/to/image.jpg"
        assert entity["image_full"] == "https://example.com/image-full.jpg"
        assert entity["image_thumb"] == "https://example.com/image-thumb.jpg"
        assert entity["image_uuid"] == "image-uuid-123"
        assert entity["header_uuid"] == "header-uuid-456"

    @pytest.mark.asyncio
    async def test_find_entities_minimal_excludes_image_fields(self):
        """Test find_entities with include_full=False excludes complex fields but includes basic ones."""
        # Mock service
        mock_service = Mock()

        # Mock entity with all fields
        mock_entity = {
            "id": 1,
            "entity_id": 123,
            "name": "Test Entity",
            "entity_type": "character",
            "type": "NPC",
            "entry": "Some long description",
            "tags": ["tag1", "tag2"],
            "is_hidden": False,
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
            "image": "/path/to/image.jpg",
            "image_full": "https://example.com/image-full.jpg",
            "image_thumb": "https://example.com/image-thumb.jpg",
            "image_uuid": "image-uuid-123",
            "header_uuid": "header-uuid-456",
        }

        mock_service._entity_to_dict.return_value = mock_entity

        # Create operations with mocked service
        ops = KankaOperations(service=mock_service)
        ops.service = mock_service

        # Mock the list_entities to return one entity
        mock_entity_obj = Mock()
        mock_service.list_entities.return_value = [mock_entity_obj]

        # Find entities without full details
        result = await ops.find_entities(entity_type="character", include_full=False)

        # Check that only minimal fields are present
        assert len(result["entities"]) == 1
        entity = result["entities"][0]
        assert entity["entity_id"] == 123
        assert entity["name"] == "Test Entity"
        assert entity["entity_type"] == "character"

        # Complex fields should not be present
        assert "type" not in entity
        assert "entry" not in entity
        assert "tags" not in entity
        assert "is_hidden" not in entity
        assert "created_at" not in entity
        assert "updated_at" not in entity
        assert "image" not in entity
        assert "image_full" not in entity
        assert "image_thumb" not in entity
        assert "image_uuid" not in entity
        assert "header_uuid" not in entity

    @pytest.mark.asyncio
    async def test_get_entities_includes_image_fields(self):
        """Test get_entities includes all image fields."""
        # Mock service
        mock_service = Mock()

        # Mock entity with image fields
        mock_entity = {
            "id": 1,
            "entity_id": 123,
            "name": "Test Entity",
            "entity_type": "character",
            "type": None,
            "entry": None,
            "tags": [],
            "is_hidden": False,
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
            "image": "/path/to/image.jpg",
            "image_full": "https://example.com/image-full.jpg",
            "image_thumb": "https://example.com/image-thumb.jpg",
            "image_uuid": "image-uuid-123",
            "header_uuid": "header-uuid-456",
        }

        mock_service.get_entity_by_id.return_value = mock_entity

        # Create operations with mocked service
        ops = KankaOperations(service=mock_service)

        # Get entity
        results = await ops.get_entities([123])

        # Check that image fields are included
        assert len(results) == 1
        result = results[0]
        assert result["image"] == "/path/to/image.jpg"
        assert result["image_full"] == "https://example.com/image-full.jpg"
        assert result["image_thumb"] == "https://example.com/image-thumb.jpg"
        assert result["image_uuid"] == "image-uuid-123"
        assert result["header_uuid"] == "header-uuid-456"
