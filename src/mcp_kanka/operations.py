"""High-level operations layer for Kanka functionality.

This module provides a reusable operations layer that can be used by both
MCP tools and external scripts, ensuring consistent behavior and type safety.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from .service import KankaService, get_service
from .types import (
    CheckEntityUpdatesResult,
    CreateEntityResult,
    CreatePostResult,
    DeleteEntityResult,
    DeletePostResult,
    GetEntityResult,
    UpdateEntityResult,
    UpdatePostResult,
)
from .utils import (
    filter_entities_by_name,
    filter_entities_by_tags,
    filter_entities_by_type,
    filter_journals_by_date_range,
    paginate_results,
    search_in_content,
)

logger = logging.getLogger(__name__)


# Result classes with to_dict() methods for MCP compatibility
@dataclass
class FindEntitiesResult:
    """Structured result for find_entities operation."""

    entities: list[dict[str, Any]]
    sync_info: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Convert to MCP response format."""
        return {"entities": self.entities, "sync_info": self.sync_info}


@dataclass
class OperationResult:
    """Generic result for operations that return lists."""

    results: list[dict[str, Any]]

    def to_list(self) -> list[dict[str, Any]]:
        """Convert to MCP response format."""
        return self.results


class KankaOperationsError(Exception):
    """Base exception for operations layer."""

    pass


class PartialSuccessError(KankaOperationsError):
    """Some operations succeeded, some failed."""

    def __init__(self, successes: list[Any], failures: list[Any]):
        self.successes = successes
        self.failures = failures
        super().__init__(
            f"Partial success: {len(successes)} succeeded, {len(failures)} failed"
        )


class KankaOperations:
    """High-level operations for Kanka, used by both MCP tools and external scripts."""

    def __init__(self, service: KankaService | None = None):
        """Initialize operations with optional service instance.

        Args:
            service: Optional KankaService instance. If not provided, creates a new one.
        """
        self.service = service or KankaService()

    async def find_entities(
        self,
        query: str | None = None,
        entity_type: str | None = None,
        name: str | None = None,
        name_exact: bool = False,
        name_fuzzy: bool = False,
        type: str | None = None,
        tags: list[str] | None = None,
        date_range: dict[str, str] | None = None,
        include_full: bool = True,
        page: int = 1,
        limit: int = 25,
        last_synced: str | None = None,
    ) -> dict[str, Any]:
        """Find entities with search and filtering capabilities.

        Args:
            query: Search term for full-text search across names and content
            entity_type: Type of entity to search for
            name: Filter by entity name
            name_exact: Use exact name matching (case-insensitive)
            name_fuzzy: Use fuzzy name matching (typo-tolerant)
            type: Filter by custom type field
            tags: Filter by tags (must have all specified tags)
            date_range: Date range filter for journals
            include_full: Whether to include full entity details
            page: Page number for pagination
            limit: Number of results per page (0 for all)
            last_synced: ISO timestamp to get only entities modified after this time

        Returns:
            Dictionary with entities and sync_info
        """
        # Validate entity type if provided
        valid_types = [
            "character",
            "creature",
            "location",
            "organization",
            "race",
            "note",
            "journal",
            "quest",
        ]
        if entity_type and entity_type not in valid_types:
            logger.error(
                f"Invalid entity_type: {entity_type}. Must be one of: {', '.join(valid_types)}"
            )
            return {"entities": [], "sync_info": {}}

        try:
            # Step 1: Get entities
            if query:
                # For content search, we need full entities
                entities = []

                if entity_type:
                    # Search specific entity type
                    # Cast to EntityType since we validated it above
                    from typing import cast

                    from .types import EntityType

                    entity_objects = self.service.list_entities(
                        cast(EntityType, entity_type),
                        page=1,
                        limit=0,
                        last_sync=last_synced,
                        related=include_full,
                    )
                    for obj in entity_objects:
                        entity_dict = self.service._entity_to_dict(obj, entity_type)
                        entities.append(entity_dict)
                else:
                    # Search across all entity types
                    from .types import EntityType

                    entity_types: list[EntityType] = [
                        "character",
                        "creature",
                        "location",
                        "organization",
                        "race",
                        "note",
                        "journal",
                        "quest",
                    ]
                    for et in entity_types:
                        try:
                            entity_objects = self.service.list_entities(
                                et,
                                page=1,
                                limit=0,
                                last_sync=last_synced,
                                related=include_full,
                            )
                            for obj in entity_objects:
                                entity_dict = self.service._entity_to_dict(obj, et)
                                entities.append(entity_dict)
                        except Exception as e:
                            logger.debug(f"Could not search {et}: {e}")
                            continue

                # Apply content search
                entities = search_in_content(entities, query)

                # If not including full details, strip to minimal data
                if not include_full:
                    minimal_entities = []
                    for entity in entities:
                        minimal_entities.append(
                            {
                                "entity_id": entity["entity_id"],
                                "name": entity["name"],
                                "entity_type": entity["entity_type"],
                            }
                        )
                    entities = minimal_entities
            else:
                # List entities of specific type (no search)
                if not entity_type:
                    # No entity type specified, can't list all
                    return {"entities": [], "sync_info": {}}

                # Get all entities of this type
                # Cast to EntityType since we validated it above
                from typing import cast

                from .types import EntityType

                entity_objects = self.service.list_entities(
                    cast(EntityType, entity_type),
                    page=1,
                    limit=0,
                    last_sync=last_synced,
                    related=include_full,
                )

                # Convert to dictionaries
                entities = []
                for obj in entity_objects:
                    entity_dict = self.service._entity_to_dict(obj, entity_type)
                    entities.append(entity_dict)

            # Step 2: Apply client-side filters
            if name:
                entities = filter_entities_by_name(
                    entities, name, exact=name_exact, fuzzy=name_fuzzy
                )

            if type:
                entities = filter_entities_by_type(entities, type)

            if tags:
                entities = filter_entities_by_tags(entities, tags)

            if date_range and entity_type == "journal":
                start = date_range.get("start")
                end = date_range.get("end")
                if start and end:
                    entities = filter_journals_by_date_range(entities, start, end)

            # Don't apply content search if we already used the search API
            # The search API already searched content

            # Step 3: Paginate results
            paginated, total_pages, total_items = paginate_results(
                entities, page, limit
            )

            # Step 4: Calculate sync metadata
            # Find newest updated_at timestamp
            newest_updated_at = None
            for entity in paginated:
                if entity.get("updated_at") and (
                    newest_updated_at is None
                    or entity["updated_at"] > newest_updated_at
                ):
                    newest_updated_at = entity["updated_at"]

            # Build sync info
            sync_info = {
                "request_timestamp": datetime.now(timezone.utc).isoformat(),
                "newest_updated_at": newest_updated_at,
                "total_count": total_items,
                "returned_count": len(paginated),
            }

            # Step 5: Format results based on include_full
            if not include_full:
                # Return minimal data
                formatted_entities = [
                    {
                        "entity_id": e["entity_id"],
                        "name": e["name"],
                        "entity_type": e["entity_type"],
                    }
                    for e in paginated
                ]
            else:
                # Return full data
                formatted_entities = paginated

            # Return the new response structure
            return {
                "entities": formatted_entities,
                "sync_info": sync_info,
            }

        except Exception as e:
            logger.error(f"find_entities failed: {e}")
            raise

    async def create_entities(
        self, entities: list[dict[str, Any]]
    ) -> list[CreateEntityResult]:
        """Create one or more entities.

        Args:
            entities: List of entity data to create

        Returns:
            List of results, one per entity (success or failure)
        """
        results = []
        valid_types = [
            "character",
            "creature",
            "location",
            "organization",
            "race",
            "note",
            "journal",
            "quest",
        ]

        for entity_input in entities:
            entity_type = entity_input.get("entity_type")
            entity_name = entity_input.get("name", "")

            # Validate entity type
            if not entity_type or entity_type not in valid_types:
                logger.error(
                    f"Invalid entity_type '{entity_type}' for entity '{entity_name}'"
                )
                error_result: CreateEntityResult = {
                    "id": None,
                    "entity_id": None,
                    "name": entity_name,
                    "mention": None,
                    "success": False,
                    "error": f"Invalid entity_type '{entity_type}'. Must be one of: {', '.join(valid_types)}",
                }
                results.append(error_result)
                continue

            # Validate required fields
            if not entity_name:
                name_error: CreateEntityResult = {
                    "id": None,
                    "entity_id": None,
                    "name": "",
                    "mention": None,
                    "success": False,
                    "error": "Name is required",
                }
                results.append(name_error)
                continue

            try:
                # Create entity
                created = self.service.create_entity(
                    entity_type=entity_type,
                    name=entity_name,
                    type=entity_input.get("type"),
                    entry=entity_input.get("entry"),
                    tags=entity_input.get("tags"),
                    is_hidden=entity_input.get("is_hidden"),
                    is_completed=entity_input.get("is_completed"),
                    image_uuid=entity_input.get("image_uuid"),
                    header_uuid=entity_input.get("header_uuid"),
                )

                result: CreateEntityResult = {
                    "id": created["id"],
                    "entity_id": created["entity_id"],
                    "name": created["name"],
                    "mention": created["mention"],
                    "success": True,
                    "error": None,
                }
                results.append(result)

            except Exception as e:
                logger.error(
                    f"Failed to create entity '{entity_input.get('name')}': {e}"
                )
                create_error: CreateEntityResult = {
                    "id": None,
                    "entity_id": None,
                    "name": entity_input.get("name", ""),
                    "mention": None,
                    "success": False,
                    "error": str(e),
                }
                results.append(create_error)

        return results

    async def update_entities(
        self, updates: list[dict[str, Any]]
    ) -> list[UpdateEntityResult]:
        """Update one or more entities.

        Args:
            updates: List of entity updates to apply

        Returns:
            List of results, one per entity (success or failure)
        """
        results = []
        for update in updates:
            entity_id = update.get("entity_id")
            name = update.get("name")

            # Validate required fields
            if not entity_id:
                id_error: UpdateEntityResult = {
                    "entity_id": 0,
                    "success": False,
                    "error": "entity_id is required",
                }
                results.append(id_error)
                continue

            if not name:
                name_error: UpdateEntityResult = {
                    "entity_id": entity_id,
                    "success": False,
                    "error": "name is required for updates (Kanka API requirement)",
                }
                results.append(name_error)
                continue

            try:
                # Update entity
                success = self.service.update_entity(
                    entity_id=entity_id,
                    name=name,
                    type=update.get("type"),
                    entry=update.get("entry"),
                    tags=update.get("tags"),
                    is_hidden=update.get("is_hidden"),
                    is_completed=update.get("is_completed"),
                    image_uuid=update.get("image_uuid"),
                    header_uuid=update.get("header_uuid"),
                )

                result: UpdateEntityResult = {
                    "entity_id": update["entity_id"],
                    "success": success,
                    "error": None,
                }
                results.append(result)

            except Exception as e:
                logger.error(f"Failed to update entity {update['entity_id']}: {e}")
                update_error: UpdateEntityResult = {
                    "entity_id": update["entity_id"],
                    "success": False,
                    "error": str(e),
                }
                results.append(update_error)

        return results

    async def get_entities(
        self, entity_ids: list[int], include_posts: bool = False
    ) -> list[GetEntityResult]:
        """Get specific entities by ID.

        Args:
            entity_ids: List of entity IDs to retrieve
            include_posts: Whether to include posts for each entity

        Returns:
            List of results, one per entity
        """
        results = []
        for entity_id in entity_ids:
            try:
                # Get entity
                entity = self.service.get_entity_by_id(entity_id, include_posts)

                if entity:
                    result: GetEntityResult = {
                        "id": entity["id"],
                        "entity_id": entity["entity_id"],
                        "name": entity["name"],
                        "entity_type": entity["entity_type"],
                        "type": entity.get("type"),
                        "entry": entity.get("entry"),
                        "tags": entity.get("tags", []),
                        "is_hidden": entity.get("is_hidden", False),
                        "created_at": entity.get("created_at"),
                        "updated_at": entity.get("updated_at"),
                        "success": True,
                        "error": None,
                    }

                    # Add quest-specific fields
                    if entity.get("entity_type") == "quest":
                        result["is_completed"] = entity.get("is_completed")

                    # Add all image fields (they should always be present from service layer)
                    result["image"] = entity.get("image")
                    result["image_full"] = entity.get("image_full")
                    result["image_thumb"] = entity.get("image_thumb")
                    result["image_uuid"] = entity.get("image_uuid")
                    result["header_uuid"] = entity.get("header_uuid")

                    if include_posts:
                        result["posts"] = entity.get("posts", [])

                    results.append(result)
                else:
                    not_found_result: GetEntityResult = {
                        "entity_id": entity_id,
                        "success": False,
                        "error": f"Entity {entity_id} not found",
                    }
                    results.append(not_found_result)

            except Exception as e:
                logger.error(f"Failed to get entity {entity_id}: {e}")
                error_result: GetEntityResult = {
                    "entity_id": entity_id,
                    "success": False,
                    "error": str(e),
                }
                results.append(error_result)

        return results

    async def delete_entities(self, entity_ids: list[int]) -> list[DeleteEntityResult]:
        """Delete one or more entities.

        Args:
            entity_ids: List of entity IDs to delete

        Returns:
            List of results, one per entity
        """
        results = []
        for entity_id in entity_ids:
            try:
                # Delete entity
                success = self.service.delete_entity(entity_id)

                result: DeleteEntityResult = {
                    "entity_id": entity_id,
                    "success": success,
                    "error": None,
                }
                results.append(result)

            except Exception as e:
                logger.error(f"Failed to delete entity {entity_id}: {e}")
                error_result: DeleteEntityResult = {
                    "entity_id": entity_id,
                    "success": False,
                    "error": str(e),
                }
                results.append(error_result)

        return results

    async def create_posts(self, posts: list[dict[str, Any]]) -> list[CreatePostResult]:
        """Create posts on entities.

        Args:
            posts: List of post data to create

        Returns:
            List of results, one per post
        """
        results = []
        for post_input in posts:
            try:
                # Create post
                created = self.service.create_post(
                    entity_id=post_input["entity_id"],
                    name=post_input["name"],
                    entry=post_input.get("entry"),
                    is_hidden=post_input.get("is_hidden", False),
                )

                result: CreatePostResult = {
                    "post_id": created["post_id"],
                    "entity_id": created["entity_id"],
                    "success": True,
                    "error": None,
                }
                results.append(result)

            except Exception as e:
                logger.error(
                    f"Failed to create post on entity {post_input['entity_id']}: {e}"
                )
                error_result: CreatePostResult = {
                    "post_id": None,
                    "entity_id": post_input["entity_id"],
                    "success": False,
                    "error": str(e),
                }
                results.append(error_result)

        return results

    async def update_posts(
        self, updates: list[dict[str, Any]]
    ) -> list[UpdatePostResult]:
        """Update existing posts.

        Args:
            updates: List of post updates to apply

        Returns:
            List of results, one per post
        """
        results = []
        for update in updates:
            try:
                # Update post
                success = self.service.update_post(
                    entity_id=update["entity_id"],
                    post_id=update["post_id"],
                    name=update["name"],
                    entry=update.get("entry"),
                    is_hidden=update.get("is_hidden"),
                )

                result: UpdatePostResult = {
                    "entity_id": update["entity_id"],
                    "post_id": update["post_id"],
                    "success": success,
                    "error": None,
                }
                results.append(result)

            except Exception as e:
                logger.error(
                    f"Failed to update post {update['post_id']} on entity {update['entity_id']}: {e}"
                )
                error_result: UpdatePostResult = {
                    "entity_id": update["entity_id"],
                    "post_id": update["post_id"],
                    "success": False,
                    "error": str(e),
                }
                results.append(error_result)

        return results

    async def delete_posts(
        self, deletions: list[dict[str, Any]]
    ) -> list[DeletePostResult]:
        """Delete posts from entities.

        Args:
            deletions: List of post deletions to perform

        Returns:
            List of results, one per post
        """
        results = []
        for deletion in deletions:
            try:
                # Delete post
                success = self.service.delete_post(
                    entity_id=deletion["entity_id"],
                    post_id=deletion["post_id"],
                )

                result: DeletePostResult = {
                    "entity_id": deletion["entity_id"],
                    "post_id": deletion["post_id"],
                    "success": success,
                    "error": None,
                }
                results.append(result)

            except Exception as e:
                logger.error(
                    f"Failed to delete post {deletion['post_id']} from entity {deletion['entity_id']}: {e}"
                )
                error_result: DeletePostResult = {
                    "entity_id": deletion["entity_id"],
                    "post_id": deletion["post_id"],
                    "success": False,
                    "error": str(e),
                }
                results.append(error_result)

        return results

    async def check_entity_updates(
        self, entity_ids: list[int], last_synced: str
    ) -> CheckEntityUpdatesResult:
        """Check which entities have been modified since last sync.

        Args:
            entity_ids: List of entity IDs to check
            last_synced: ISO timestamp of last sync

        Returns:
            Result containing modified and deleted entity IDs
        """
        if not last_synced:
            raise ValueError("last_synced parameter is required")

        modified_entity_ids = []
        deleted_entity_ids = []

        try:
            # Get all entities using the entities endpoint
            # This is more efficient than checking each entity individually
            page = 1
            all_entities = {}

            while page <= 20:  # Reasonable limit to avoid infinite loops
                batch = self.service.client.entities(page=page, limit=100)
                if not batch:
                    break

                for entity_data in batch:
                    entity_id = entity_data.get("id")
                    if entity_id:
                        all_entities[entity_id] = entity_data

                if len(batch) < 100:
                    break
                page += 1

            # Check each requested entity
            for entity_id in entity_ids:
                if entity_id in all_entities:
                    entity_data = all_entities[entity_id]
                    updated_at = entity_data.get("updated_at")

                    if updated_at and updated_at > last_synced:
                        modified_entity_ids.append(entity_id)
                else:
                    # Entity not found - might be deleted
                    deleted_entity_ids.append(entity_id)

            # Get current timestamp
            check_timestamp = datetime.now(timezone.utc).isoformat()

            return {
                "modified_entity_ids": modified_entity_ids,
                "deleted_entity_ids": deleted_entity_ids,
                "check_timestamp": check_timestamp,
            }

        except Exception as e:
            logger.error(f"Check entity updates failed: {e}")
            raise


# Global instance management
_operations: KankaOperations | None = None


def get_operations() -> KankaOperations:
    """Get or create the singleton operations instance.

    Returns:
        The global KankaOperations instance
    """
    global _operations
    if _operations is None:
        _operations = KankaOperations(service=get_service())
    return _operations


def create_operations(service: KankaService | None = None) -> KankaOperations:
    """Create a new operations instance for external use.

    This is useful for scripts that want to manage their own instances
    or provide a custom service configuration.

    Args:
        service: Optional KankaService instance

    Returns:
        A new KankaOperations instance
    """
    return KankaOperations(service)
