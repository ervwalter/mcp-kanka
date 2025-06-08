"""MCP tool implementations for Kanka operations."""

import logging
from datetime import datetime, timezone
from typing import Any

from .service import KankaService
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

# Global service instance (initialized on first use)
_service: KankaService | None = None


def get_service() -> KankaService:
    """Get or create the Kanka service instance."""
    global _service
    if _service is None:
        _service = KankaService()
    return _service


async def handle_find_entities(**params: Any) -> dict[str, Any]:
    """
    Find entities by search and/or filtering.

    Args:
        **params: Parameters from FindEntitiesParams

    Returns:
        Dictionary with entities and sync_info
    """
    # Parse parameters
    query = params.get("query")
    entity_type = params.get("entity_type")
    name_filter = params.get("name")
    name_exact = params.get("name_exact", False)
    name_fuzzy = params.get("name_fuzzy", False)
    type_filter = params.get("type")
    tags = params.get("tags", [])
    date_range = params.get("date_range")
    include_full = params.get("include_full", True)
    page = params.get("page", 1)
    limit = params.get("limit", 25)
    last_synced = params.get("last_synced")

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

    service = get_service()

    try:
        # Step 1: Get entities
        if query:
            # For content search, we need full entities
            entities = []

            if entity_type:
                # Search specific entity type
                entity_objects = service.list_entities(
                    entity_type, page=1, limit=0, last_sync=last_synced
                )
                for obj in entity_objects:
                    entity_dict = service._entity_to_dict(obj, entity_type)
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
                        entity_objects = service.list_entities(
                            et, page=1, limit=0, last_sync=last_synced
                        )
                        for obj in entity_objects:
                            entity_dict = service._entity_to_dict(obj, et)
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
            entity_objects = service.list_entities(
                entity_type, page=1, limit=0, last_sync=last_synced
            )

            # Convert to dictionaries
            entities = []
            for obj in entity_objects:
                entity_dict = service._entity_to_dict(obj, entity_type)
                entities.append(entity_dict)

        # Step 2: Apply client-side filters
        if name_filter:
            entities = filter_entities_by_name(
                entities, name_filter, exact=name_exact, fuzzy=name_fuzzy
            )

        if type_filter:
            entities = filter_entities_by_type(entities, type_filter)

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
        paginated, total_pages, total_items = paginate_results(entities, page, limit)

        # Step 4: Calculate sync metadata
        # Find newest updated_at timestamp
        newest_updated_at = None
        for entity in paginated:
            if entity.get("updated_at") and (
                newest_updated_at is None or entity["updated_at"] > newest_updated_at
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


async def handle_create_entities(**params: Any) -> list[CreateEntityResult]:
    """
    Create one or more entities.

    Args:
        **params: Parameters from CreateEntitiesParams

    Returns:
        List of creation results
    """
    entities = params.get("entities", [])
    service = get_service()

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
            created = service.create_entity(
                entity_type=entity_type,
                name=entity_name,
                type=entity_input.get("type"),
                entry=entity_input.get("entry"),
                tags=entity_input.get("tags"),
                is_private=entity_input.get("is_private"),
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
            logger.error(f"Failed to create entity '{entity_input.get('name')}': {e}")
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


async def handle_update_entities(**params: Any) -> list[UpdateEntityResult]:
    """
    Update one or more entities.

    Args:
        **params: Parameters from UpdateEntitiesParams

    Returns:
        List of update results
    """
    updates = params.get("updates", [])
    service = get_service()

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
            success = service.update_entity(
                entity_id=entity_id,
                name=name,
                type=update.get("type"),
                entry=update.get("entry"),
                tags=update.get("tags"),
                is_private=update.get("is_private"),
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


async def handle_get_entities(**params: Any) -> list[GetEntityResult]:
    """
    Retrieve specific entities by ID.

    Args:
        **params: Parameters from GetEntitiesParams

    Returns:
        List of entity results
    """
    entity_ids = params.get("entity_ids", [])
    include_posts = params.get("include_posts", False)
    service = get_service()

    results = []
    for entity_id in entity_ids:
        try:
            # Get entity
            entity = service.get_entity_by_id(entity_id, include_posts)

            if entity:
                result: GetEntityResult = {
                    "id": entity["id"],
                    "entity_id": entity["entity_id"],
                    "name": entity["name"],
                    "entity_type": entity["entity_type"],
                    "type": entity.get("type"),
                    "entry": entity.get("entry"),
                    "tags": entity.get("tags", []),
                    "is_private": entity.get("is_private", False),
                    "created_at": entity.get("created_at"),
                    "updated_at": entity.get("updated_at"),
                    "success": True,
                    "error": None,
                }

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


async def handle_delete_entities(**params: Any) -> list[DeleteEntityResult]:
    """
    Delete one or more entities.

    Args:
        **params: Parameters from DeleteEntitiesParams

    Returns:
        List of deletion results
    """
    entity_ids = params.get("entity_ids", [])
    service = get_service()

    results = []
    for entity_id in entity_ids:
        try:
            # Delete entity
            success = service.delete_entity(entity_id)

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


async def handle_create_posts(**params: Any) -> list[CreatePostResult]:
    """
    Create posts on entities.

    Args:
        **params: Parameters from CreatePostsParams

    Returns:
        List of creation results
    """
    posts = params.get("posts", [])
    service = get_service()

    results = []
    for post_input in posts:
        try:
            # Create post
            created = service.create_post(
                entity_id=post_input["entity_id"],
                name=post_input["name"],
                entry=post_input.get("entry"),
                is_private=post_input.get("is_private", False),
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


async def handle_update_posts(**params: Any) -> list[UpdatePostResult]:
    """
    Update existing posts.

    Args:
        **params: Parameters from UpdatePostsParams

    Returns:
        List of update results
    """
    updates = params.get("updates", [])
    service = get_service()

    results = []
    for update in updates:
        try:
            # Update post
            success = service.update_post(
                entity_id=update["entity_id"],
                post_id=update["post_id"],
                name=update["name"],
                entry=update.get("entry"),
                is_private=update.get("is_private"),
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


async def handle_delete_posts(**params: Any) -> list[DeletePostResult]:
    """
    Delete posts from entities.

    Args:
        **params: Parameters from DeletePostsParams

    Returns:
        List of deletion results
    """
    deletions = params.get("deletions", [])
    service = get_service()

    results = []
    for deletion in deletions:
        try:
            # Delete post
            success = service.delete_post(
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


async def handle_check_entity_updates(**params: Any) -> CheckEntityUpdatesResult:
    """
    Check which entity_ids have been modified since last sync.

    Args:
        **params: Parameters from CheckEntityUpdatesParams

    Returns:
        Check result with modified and deleted entity IDs
    """
    entity_ids = params.get("entity_ids", [])
    last_synced = params.get("last_synced")
    service = get_service()

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
            batch = service.client.entities(page=page, limit=100)
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
