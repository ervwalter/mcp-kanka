"""Unit tests for visibility handling (is_hidden, is_private, visibility_id)."""

from unittest.mock import Mock, patch

from mcp_kanka.service import KankaService


class TestEntityVisibility:
    """Test visibility handling for entities."""

    @patch("os.getenv")
    def setup_method(self, method, mock_getenv):
        """Set up test fixtures."""
        mock_getenv.side_effect = lambda key: {
            "KANKA_TOKEN": "test_token",
            "KANKA_CAMPAIGN_ID": "123",
        }.get(key)

        with patch("mcp_kanka.service.KankaClient") as mock_client_class:
            self.mock_client = Mock()
            mock_client_class.return_value = self.mock_client
            self.service = KankaService()

    def test_create_entity_with_is_hidden_true(self):
        """Test creating entity with is_hidden=True sets is_private=True."""
        # Mock entity creation
        created_entity = Mock(
            spec=[
                "id",
                "entity_id",
                "name",
                "is_private",
                "entry",
                "tags",
                "type",
                "created_at",
                "updated_at",
            ]
        )
        created_entity.id = 1
        created_entity.entity_id = 101
        created_entity.name = "Test Character"
        created_entity.is_private = True
        created_entity.entry = None  # No entry content
        created_entity.tags = []
        created_entity.type = None
        created_entity.created_at = None
        created_entity.updated_at = None
        self.mock_client.characters.create.return_value = created_entity

        # Mock tag cache
        self.service._tag_cache = {}

        # Create entity with is_hidden=True
        result = self.service.create_entity(
            entity_type="character",
            name="Test Character",
            is_hidden=True,
        )

        # Verify is_private was sent to API
        self.mock_client.characters.create.assert_called_once()
        call_args = self.mock_client.characters.create.call_args[1]
        assert call_args["is_private"] is True
        assert "visibility_id" not in call_args

        # Verify result shows is_hidden
        assert result["is_hidden"] is True

    def test_create_entity_with_is_hidden_false(self):
        """Test creating entity with is_hidden=False sets is_private=False."""
        # Mock entity creation
        created_entity = Mock(
            spec=[
                "id",
                "entity_id",
                "name",
                "is_private",
                "entry",
                "tags",
                "type",
                "created_at",
                "updated_at",
            ]
        )
        created_entity.id = 1
        created_entity.entity_id = 101
        created_entity.name = "Test Character"
        created_entity.is_private = False
        created_entity.entry = None  # No entry content
        created_entity.tags = []
        created_entity.type = None
        created_entity.created_at = None
        created_entity.updated_at = None
        self.mock_client.characters.create.return_value = created_entity

        # Mock tag cache
        self.service._tag_cache = {}

        # Create entity with is_hidden=False
        result = self.service.create_entity(
            entity_type="character",
            name="Test Character",
            is_hidden=False,
        )

        # Verify is_private was sent to API
        self.mock_client.characters.create.assert_called_once()
        call_args = self.mock_client.characters.create.call_args[1]
        assert call_args["is_private"] is False
        assert "visibility_id" not in call_args

        # Verify result shows is_hidden
        assert result["is_hidden"] is False

    def test_update_entity_with_is_hidden(self):
        """Test updating entity visibility uses is_private."""
        # Mock get_entity_by_id
        self.service.get_entity_by_id = Mock(
            return_value={
                "id": 1,
                "entity_id": 101,
                "entity_type": "character",
                "name": "Test Character",
            }
        )

        # Mock update
        self.mock_client.characters.update.return_value = True

        # Update entity with is_hidden=True
        self.service.update_entity(
            entity_id=101,
            name="Test Character",
            is_hidden=True,
        )

        # Verify is_private was sent to API
        self.mock_client.characters.update.assert_called_once()
        call_args = self.mock_client.characters.update.call_args[1]
        assert call_args["is_private"] is True
        assert "visibility_id" not in call_args

    def test_entity_to_dict_converts_is_private_to_is_hidden(self):
        """Test _entity_to_dict converts is_private to is_hidden."""
        # Mock entity with is_private=True
        mock_entity = Mock()
        mock_entity.id = 1
        mock_entity.entity_id = 101
        mock_entity.name = "Test Entity"
        mock_entity.type = "NPC"
        mock_entity.is_private = True
        mock_entity.tags = []
        mock_entity.entry = None
        mock_entity.created_at = None
        mock_entity.updated_at = None
        mock_entity.posts = None  # No posts

        self.service._tag_cache = {}

        # Convert to dict
        result = self.service._entity_to_dict(mock_entity, "character")

        # Should show is_hidden=True
        assert result["is_hidden"] is True

    def test_entity_to_dict_no_is_private_field(self):
        """Test _entity_to_dict handles missing is_private field."""
        # Mock entity without is_private
        mock_entity = Mock(spec=["id", "entity_id", "name", "type", "tags", "entry"])
        mock_entity.id = 1
        mock_entity.entity_id = 101
        mock_entity.name = "Test Entity"
        mock_entity.type = "NPC"
        mock_entity.tags = []
        mock_entity.entry = None

        self.service._tag_cache = {}

        # Convert to dict
        result = self.service._entity_to_dict(mock_entity, "character")

        # Should default to is_hidden=False
        assert result["is_hidden"] is False


class TestPostVisibility:
    """Test visibility handling for posts."""

    @patch("os.getenv")
    def setup_method(self, method, mock_getenv):
        """Set up test fixtures."""
        mock_getenv.side_effect = lambda key: {
            "KANKA_TOKEN": "test_token",
            "KANKA_CAMPAIGN_ID": "123",
        }.get(key)

        with patch("mcp_kanka.service.KankaClient") as mock_client_class:
            self.mock_client = Mock()
            mock_client_class.return_value = self.mock_client
            self.service = KankaService()

    def test_create_post_with_is_hidden_true(self):
        """Test creating post with is_hidden=True sets visibility_id=2."""
        # Mock get_entity_by_id
        self.service.get_entity_by_id = Mock(
            return_value={
                "id": 1,
                "entity_id": 101,
                "entity_type": "character",
                "name": "Test Character",
            }
        )

        # Mock post creation
        created_post = Mock()
        created_post.id = 50
        self.mock_client.characters.create_post.return_value = created_post

        # Create post with is_hidden=True
        self.service.create_post(
            entity_id=101,
            name="Test Post",
            entry="Content",
            is_hidden=True,
        )

        # Verify visibility_id was sent to API
        self.mock_client.characters.create_post.assert_called_once()
        call_args = self.mock_client.characters.create_post.call_args[1]
        assert call_args["visibility_id"] == 2
        assert "is_private" not in call_args

    def test_create_post_with_is_hidden_false(self):
        """Test creating post with is_hidden=False sets visibility_id=1."""
        # Mock get_entity_by_id
        self.service.get_entity_by_id = Mock(
            return_value={
                "id": 1,
                "entity_id": 101,
                "entity_type": "character",
                "name": "Test Character",
            }
        )

        # Mock post creation
        created_post = Mock()
        created_post.id = 50
        self.mock_client.characters.create_post.return_value = created_post

        # Create post with is_hidden=False
        self.service.create_post(
            entity_id=101,
            name="Test Post",
            entry="Content",
            is_hidden=False,
        )

        # Verify visibility_id was sent to API
        self.mock_client.characters.create_post.assert_called_once()
        call_args = self.mock_client.characters.create_post.call_args[1]
        assert call_args["visibility_id"] == 1
        assert "is_private" not in call_args

    def test_update_post_with_is_hidden(self):
        """Test updating post visibility uses visibility_id."""
        # Mock get_entity_by_id
        self.service.get_entity_by_id = Mock(
            return_value={
                "id": 1,
                "entity_id": 101,
                "entity_type": "character",
                "name": "Test Character",
            }
        )

        # Mock update
        self.mock_client.characters.update_post.return_value = True

        # Update post with is_hidden=True
        self.service.update_post(
            entity_id=101,
            post_id=50,
            name="Test Post",
            is_hidden=True,
        )

        # Verify visibility_id was sent to API
        self.mock_client.characters.update_post.assert_called_once()
        call_args = self.mock_client.characters.update_post.call_args[1]
        assert call_args["visibility_id"] == 2
        assert "is_private" not in call_args

    def test_post_to_dict_converts_visibility_id_to_is_hidden(self):
        """Test _post_to_dict converts visibility_id to is_hidden."""
        # Mock post with visibility_id=2
        mock_post = Mock()
        mock_post.id = 50
        mock_post.name = "Test Post"
        mock_post.visibility_id = 2
        mock_post.entry = "<p>Content</p>"

        # Convert to dict
        result = self.service._post_to_dict(mock_post)

        # Should show is_hidden=True
        assert result["is_hidden"] is True

        # Test with visibility_id=1
        mock_post.visibility_id = 1
        result = self.service._post_to_dict(mock_post)
        assert result["is_hidden"] is False

    def test_post_to_dict_no_visibility_id_field(self):
        """Test _post_to_dict handles missing visibility_id field."""
        # Mock post without visibility_id
        mock_post = Mock(spec=["id", "name", "entry"])
        mock_post.id = 50
        mock_post.name = "Test Post"
        mock_post.entry = None

        # Convert to dict
        result = self.service._post_to_dict(mock_post)

        # Should default to is_hidden=False
        assert result["is_hidden"] is False
