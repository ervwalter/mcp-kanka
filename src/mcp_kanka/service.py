"""Service layer for Kanka API operations."""

# mypy: warn_return_any=False

import logging
import os
from typing import Any

from kanka import KankaClient
from kanka.exceptions import KankaException
from kanka.models import (
    Character,
    Creature,
    Entity,
    Journal,
    Location,
    Note,
    Organisation,
    Quest,
    Race,
    Tag,
)

from .converter import ContentConverter
from .types import EntityType

logger = logging.getLogger(__name__)


class KankaService:
    """Service layer wrapping the python-kanka client."""

    # Map entity types to their model classes
    ENTITY_TYPE_MAP = {
        "character": Character,
        "creature": Creature,
        "location": Location,
        "organization": Organisation,  # Note: Kanka uses "organisation"
        "race": Race,
        "note": Note,
        "journal": Journal,
        "quest": Quest,
    }

    # Map entity types to their Kanka API endpoints
    API_ENDPOINT_MAP = {
        "character": "characters",
        "creature": "creatures",
        "location": "locations",
        "organization": "organisations",  # API uses British spelling
        "race": "races",
        "note": "notes",
        "journal": "journals",
        "quest": "quests",
    }

    def __init__(self) -> None:
        """Initialize the service with Kanka client."""
        token = os.getenv("KANKA_TOKEN")
        campaign_id = os.getenv("KANKA_CAMPAIGN_ID")

        if not token or not campaign_id:
            raise ValueError(
                "KANKA_TOKEN and KANKA_CAMPAIGN_ID environment variables are required"
            )

        self.client = KankaClient(token=token, campaign_id=int(campaign_id))
        self.converter = ContentConverter()
        self._tag_cache: dict[str, Tag] = {}

    def search_entities(
        self,
        query: str,
        entity_type: EntityType | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """
        Search for entities by name using list endpoints with filtering.

        This uses the list endpoints with name filtering instead of the search API,
        as they provide the same partial matching capability but with more control.

        Args:
            query: Search query (matches partial names)
            entity_type: Optional entity type filter
            limit: Maximum results

        Returns:
            List of minimal entity data
        """
        try:
            entities = []

            if entity_type:
                # Search specific entity type
                manager = getattr(self.client, self.API_ENDPOINT_MAP[entity_type])

                # Use name filter to search - it does partial matching!
                results = manager.list(name=query, limit=limit)

                for entity in results:
                    entities.append(
                        {
                            "entity_id": entity.entity_id,
                            "name": entity.name,
                            "entity_type": entity_type,
                        }
                    )
            else:
                # Search across all entity types
                # We'll need to query each type separately
                remaining_limit = limit

                for our_type, manager_name in self.API_ENDPOINT_MAP.items():
                    if remaining_limit <= 0:
                        break

                    manager = getattr(self.client, manager_name)

                    # Get up to remaining_limit results from this type
                    type_limit = min(remaining_limit, 100)  # API max is 100

                    try:
                        results = manager.list(name=query, limit=type_limit)

                        for entity in results:
                            entities.append(
                                {
                                    "entity_id": entity.entity_id,
                                    "name": entity.name,
                                    "entity_type": our_type,
                                }
                            )

                        remaining_limit -= len(results)

                    except Exception as e:
                        # Some entity types might not be available in the campaign
                        logger.debug(f"Could not search {our_type}: {e}")
                        continue

            return entities

        except KankaException as e:
            logger.error(f"Search failed: {e}")
            raise

    def list_entities(
        self,
        entity_type: EntityType,
        page: int = 1,
        limit: int = 100,
        last_sync: str | None = None,
    ) -> list[Entity]:
        """
        List entities of a specific type.

        Args:
            entity_type: Entity type to list
            page: Page number
            limit: Results per page (0 for all)
            last_sync: ISO 8601 timestamp to get only entities modified after this time

        Returns:
            List of entity objects
        """
        try:
            manager = getattr(self.client, self.API_ENDPOINT_MAP[entity_type])

            # Build filters
            filters = {}
            if last_sync:
                filters["lastSync"] = last_sync

            if limit == 0:
                # Get all results by using a high limit
                # The API supports up to 100 per page, so we'll need to paginate
                all_entities = []
                current_page = 1
                while True:
                    batch = manager.list(page=current_page, limit=100, **filters)
                    if not batch:
                        break
                    all_entities.extend(batch)
                    if len(batch) < 100:
                        break
                    current_page += 1
                entities = all_entities
            else:
                # Get paginated results
                entities = manager.list(page=page, limit=limit, **filters)

            return list(entities)

        except KankaException as e:
            logger.error(f"List entities failed: {e}")
            raise

    def get_entity_by_id(
        self, entity_id: int, include_posts: bool = False
    ) -> dict[str, Any] | None:
        """
        Get a specific entity by its entity_id.

        Args:
            entity_id: Entity ID
            include_posts: Whether to include posts

        Returns:
            Entity data with converted content
        """
        try:
            # Get all recent entities since we can't filter by ID directly
            page = 1
            found_entity = None

            # Search through recent entities
            while page <= 10 and not found_entity:  # Check up to 10 pages
                batch = self.client.entities(page=page, limit=100)
                if not batch:
                    break

                for e in batch:
                    # The 'id' field in entities response is the entity_id
                    if e.get("id") == entity_id:
                        found_entity = e
                        break

                if len(batch) < 100:
                    break
                page += 1

            if not found_entity:
                # Entity not found
                return None

            # Get entity type - it's in the 'type' field
            entity_type = found_entity.get("type")

            # Map to our internal type
            our_type = None
            if entity_type == "character":
                our_type = "character"
            elif entity_type == "creature":
                our_type = "creature"
            elif entity_type == "location":
                our_type = "location"
            elif entity_type == "organisation":
                our_type = "organization"
            elif entity_type == "race":
                our_type = "race"
            elif entity_type == "note":
                our_type = "note"
            elif entity_type == "journal":
                our_type = "journal"
            elif entity_type == "quest":
                our_type = "quest"
            else:
                return None

            # Get the type-specific ID from child_id
            type_id = found_entity.get("child_id")
            if not type_id:
                return None

            # Now get the full entity using the type-specific manager
            manager = getattr(self.client, self.API_ENDPOINT_MAP[our_type])
            entity = manager.get(type_id)

            # Convert to our format
            result = self._entity_to_dict(entity, our_type)

            # Get posts if requested
            if include_posts:
                try:
                    # Use entity_id, not the type-specific id
                    posts = manager.list_posts(entity_id, limit=100)
                    result["posts"] = [self._post_to_dict(post) for post in posts]
                except Exception as e:
                    logger.warning(f"Failed to get posts for entity {entity_id}: {e}")
                    result["posts"] = []

            return result

        except Exception as e:
            logger.error(f"Get entity failed for {entity_id}: {e}")
            return None

    def create_entity(
        self,
        entity_type: EntityType,
        name: str,
        type: str | None = None,
        entry: str | None = None,
        tags: list[str] | None = None,
        is_private: bool | None = None,
    ) -> dict[str, Any]:
        """
        Create a new entity.

        Args:
            entity_type: Type of entity
            name: Entity name
            type: Entity subtype
            entry: Description in Markdown
            tags: List of tag names
            is_private: Privacy setting

        Returns:
            Created entity data
        """
        try:
            manager = getattr(self.client, self.API_ENDPOINT_MAP[entity_type])

            # Prepare data
            data: dict[str, Any] = {"name": name}

            if type is not None:
                data["type"] = type

            if entry is not None:
                # Convert markdown to HTML
                data["entry"] = self.converter.markdown_to_html(entry)

            if is_private is not None:
                data["is_private"] = is_private
            elif entity_type == "note":
                # Notes default to private
                data["is_private"] = True

            # Handle tags
            if tags:
                tag_ids = self._get_or_create_tag_ids(tags)
                data["tags"] = tag_ids

            # Create entity
            entity = manager.create(**data)

            # Convert to our format
            result = self._entity_to_dict(entity, entity_type)
            result["mention"] = f"[entity:{entity.entity_id}]"

            return result

        except KankaException as e:
            logger.error(f"Create entity failed: {e}")
            raise

    def update_entity(
        self,
        entity_id: int,
        name: str,
        type: str | None = None,
        entry: str | None = None,
        tags: list[str] | None = None,
        is_private: bool | None = None,
    ) -> bool:
        """
        Update an existing entity.

        Args:
            entity_id: Entity ID
            name: Entity name (required by API)
            type: Entity subtype
            entry: Description in Markdown
            tags: List of tag names
            is_private: Privacy setting

        Returns:
            True if successful
        """
        try:
            # First get the entity to find its type
            entity_data = self.get_entity_by_id(entity_id)
            if not entity_data:
                raise ValueError(f"Entity {entity_id} not found")

            entity_type = entity_data["entity_type"]
            manager = getattr(self.client, self.API_ENDPOINT_MAP[entity_type])

            # Prepare update data
            data: dict[str, Any] = {"name": name}

            if type is not None:
                data["type"] = type

            if entry is not None:
                # Convert markdown to HTML
                data["entry"] = self.converter.markdown_to_html(entry)

            if is_private is not None:
                data["is_private"] = is_private

            # Handle tags
            if tags is not None:
                tag_ids = self._get_or_create_tag_ids(tags)
                data["tags"] = tag_ids

            # Update entity
            manager.update(entity_data["id"], **data)
            return True

        except Exception as e:
            logger.error(f"Update entity failed for {entity_id}: {e}")
            raise

    def delete_entity(self, entity_id: int) -> bool:
        """
        Delete an entity.

        Args:
            entity_id: Entity ID

        Returns:
            True if successful
        """
        try:
            # First get the entity to find its type
            entity_data = self.get_entity_by_id(entity_id)
            if not entity_data:
                raise ValueError(f"Entity {entity_id} not found")

            entity_type = entity_data["entity_type"]
            manager = getattr(self.client, self.API_ENDPOINT_MAP[entity_type])

            # Delete entity
            manager.delete(entity_data["id"])
            return True

        except Exception as e:
            logger.error(f"Delete entity failed for {entity_id}: {e}")
            raise

    def create_post(
        self,
        entity_id: int,
        name: str,
        entry: str | None = None,
        is_private: bool = False,
    ) -> dict[str, Any]:
        """
        Create a post on an entity.

        Args:
            entity_id: Entity ID
            name: Post title
            entry: Post content in Markdown
            is_private: Privacy setting

        Returns:
            Created post data
        """
        try:
            # Get entity to find its type
            entity_data = self.get_entity_by_id(entity_id)
            if not entity_data:
                raise ValueError(f"Entity {entity_id} not found")

            entity_type = entity_data["entity_type"]
            manager = getattr(self.client, self.API_ENDPOINT_MAP[entity_type])

            # Prepare post data
            data: dict[str, Any] = {"name": name, "is_private": is_private}

            if entry:
                data["entry"] = self.converter.markdown_to_html(entry)

            # Create post - use entity_id, not the type-specific id
            post = manager.create_post(entity_id, **data)

            return {
                "post_id": post.id,
                "entity_id": entity_id,
            }

        except Exception as e:
            logger.error(f"Create post failed: {e}")
            raise

    def update_post(
        self,
        entity_id: int,
        post_id: int,
        name: str,
        entry: str | None = None,
        is_private: bool | None = None,
    ) -> bool:
        """
        Update a post.

        Args:
            entity_id: Entity ID
            post_id: Post ID
            name: Post title (required by API)
            entry: Post content in Markdown
            is_private: Privacy setting

        Returns:
            True if successful
        """
        try:
            # Get entity to find its type
            entity_data = self.get_entity_by_id(entity_id)
            if not entity_data:
                raise ValueError(f"Entity {entity_id} not found")

            entity_type = entity_data["entity_type"]
            manager = getattr(self.client, self.API_ENDPOINT_MAP[entity_type])

            # Prepare update data
            data: dict[str, Any] = {"name": name}

            if entry is not None:
                data["entry"] = self.converter.markdown_to_html(entry)

            if is_private is not None:
                data["is_private"] = int(is_private)

            # Update post - use entity_id, not the type-specific id
            manager.update_post(entity_id, post_id, **data)
            return True

        except Exception as e:
            logger.error(f"Update post failed: {e}")
            raise

    def delete_post(self, entity_id: int, post_id: int) -> bool:
        """
        Delete a post.

        Args:
            entity_id: Entity ID
            post_id: Post ID

        Returns:
            True if successful
        """
        try:
            # Get entity to find its type
            entity_data = self.get_entity_by_id(entity_id)
            if not entity_data:
                raise ValueError(f"Entity {entity_id} not found")

            entity_type = entity_data["entity_type"]
            manager = getattr(self.client, self.API_ENDPOINT_MAP[entity_type])

            # Delete post - use entity_id, not the type-specific id
            manager.delete_post(entity_id, post_id)
            return True

        except Exception as e:
            logger.error(f"Delete post failed: {e}")
            raise

    def _get_or_create_tag_ids(self, tag_names: list[str]) -> list[int]:
        """
        Get or create tags by name.

        Args:
            tag_names: List of tag names

        Returns:
            List of tag IDs
        """
        # Load tag cache if needed
        if not self._tag_cache:
            self._load_tag_cache()

        tag_ids = []
        for name in tag_names:
            name_lower = name.lower()

            # Check cache
            if name_lower in self._tag_cache:
                tag_ids.append(self._tag_cache[name_lower].id)
            else:
                # Create new tag
                try:
                    tag = self.client.tags.create(name=name)
                    self._tag_cache[name_lower] = tag
                    tag_ids.append(tag.id)
                except Exception as e:
                    logger.warning(f"Failed to create tag '{name}': {e}")

        return tag_ids

    def _load_tag_cache(self) -> None:
        """Load all tags into cache."""
        self._tag_cache = {}
        try:
            # Get all tags by paginating through them
            current_page = 1
            while True:
                batch = self.client.tags.list(page=current_page, limit=100)
                if not batch:
                    break
                for tag in batch:
                    self._tag_cache[tag.name.lower()] = tag
                if len(batch) < 100:
                    break
                current_page += 1
        except Exception as e:
            logger.warning(f"Failed to load tag cache: {e}")

    def _entity_to_dict(self, entity: Entity, entity_type: str) -> dict[str, Any]:
        """
        Convert entity object to dictionary.

        Args:
            entity: Entity object
            entity_type: Our entity type string

        Returns:
            Dictionary representation
        """
        result = {
            "id": entity.id,
            "entity_id": entity.entity_id,
            "name": entity.name,
            "entity_type": entity_type,
            "type": getattr(entity, "type", None),
            "tags": [],
            "is_private": getattr(entity, "is_private", False),
            "created_at": (
                entity.created_at.isoformat()
                if hasattr(entity, "created_at") and entity.created_at
                else None
            ),
            "updated_at": (
                entity.updated_at.isoformat()
                if hasattr(entity, "updated_at") and entity.updated_at
                else None
            ),
        }

        # Convert HTML entry to Markdown
        if hasattr(entity, "entry") and entity.entry:
            result["entry"] = self.converter.html_to_markdown(entity.entry)
        else:
            result["entry"] = None

        # Extract tag names
        if hasattr(entity, "tags") and entity.tags and isinstance(entity.tags, list):
            # Tags are returned as IDs, we need to resolve them to names
            tag_names = []
            for tag_item in entity.tags:
                if isinstance(tag_item, int | str):
                    # It's a tag ID, need to look it up
                    tag_id = int(tag_item) if isinstance(tag_item, str) else tag_item
                    # Check cache first
                    tag_name = None
                    for _, cached_tag in self._tag_cache.items():
                        if cached_tag.id == tag_id:
                            tag_name = cached_tag.name
                            break
                    if tag_name:
                        tag_names.append(tag_name)
                    else:
                        # Not in cache, need to fetch
                        try:
                            tag = self.client.tags.get(tag_id)
                            tag_names.append(tag.name)
                            self._tag_cache[tag.name.lower()] = tag
                        except Exception:
                            # If we can't resolve it, keep the ID as string
                            tag_names.append(str(tag_item))
                elif hasattr(tag_item, "name"):
                    # It's a tag object
                    tag_names.append(tag_item.name)
                else:
                    # Unknown format
                    tag_names.append(str(tag_item))
            result["tags"] = tag_names

        return result

    def _post_to_dict(self, post: Any) -> dict[str, Any]:
        """
        Convert post object to dictionary.

        Args:
            post: Post object

        Returns:
            Dictionary representation
        """
        result = {
            "id": post.id,
            "name": post.name,
            "is_private": getattr(post, "is_private", False),
        }

        # Convert HTML entry to Markdown
        if hasattr(post, "entry") and post.entry:
            result["entry"] = self.converter.html_to_markdown(post.entry)
        else:
            result["entry"] = None

        return result
