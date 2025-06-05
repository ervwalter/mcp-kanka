"""MCP tool implementations for Kanka operations."""

import logging
from typing import Any, Optional, Union

from .service import KankaService
from .types import (
    CreateEntityResult,
    CreatePostResult,
    DeleteEntityResult,
    DeletePostResult,
    EntityFull,
    EntityMinimal,
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
_service: Optional[KankaService] = None


def get_service() -> KankaService:
    """Get or create the Kanka service instance."""
    global _service
    if _service is None:
        _service = KankaService()
    return _service


async def handle_find_entities(**params: Any) -> list[Union[EntityMinimal, EntityFull]]:
    """
    Find entities by search and/or filtering.

    Args:
        **params: Parameters from FindEntitiesParams

    Returns:
        List of entities
    """
    # Parse parameters
    query = params.get("query")
    entity_type = params.get("entity_type")
    name_filter = params.get("name")
    name_fuzzy = params.get("name_fuzzy", False)
    type_filter = params.get("type")
    tags = params.get("tags", [])
    date_range = params.get("date_range")
    include_full = params.get("include_full", True)
    page = params.get("page", 1)
    limit = params.get("limit", 25)

    service = get_service()

    try:
        # Step 1: Get entities (either by search or list)
        if query:
            # Use search API (returns minimal data)
            search_results = service.search_entities(query, entity_type, limit=1000)

            if not include_full:
                # Just return search results
                entities = search_results
            else:
                # Fetch full details for each result
                entities = []
                for result in search_results:
                    full_entity = service.get_entity_by_id(result["entity_id"])
                    if full_entity:
                        entities.append(full_entity)
        else:
            # List entities of specific type
            if not entity_type:
                # No entity type specified, can't list all
                return []

            # Get all entities of this type
            entity_objects = service.list_entities(entity_type, page=1, limit=0)

            # Convert to dictionaries
            entities = []
            for obj in entity_objects:
                entity_dict = service._entity_to_dict(obj, entity_type)
                entities.append(entity_dict)

        # Step 2: Apply client-side filters
        if name_filter:
            entities = filter_entities_by_name(entities, name_filter, name_fuzzy)

        if type_filter:
            entities = filter_entities_by_type(entities, type_filter)

        if tags:
            entities = filter_entities_by_tags(entities, tags)

        if date_range and entity_type == "journal":
            start = date_range.get("start")
            end = date_range.get("end")
            if start and end:
                entities = filter_journals_by_date_range(entities, start, end)

        # If we used search but didn't get full details, search in content
        if query and not include_full:
            entities = search_in_content(entities, query)

        # Step 3: Paginate results
        paginated, total_pages, total_items = paginate_results(entities, page, limit)

        # Step 4: Format results based on include_full
        if not include_full:
            # Return minimal data
            return [
                {
                    "entity_id": e["entity_id"],
                    "name": e["name"],
                    "entity_type": e["entity_type"],
                }
                for e in paginated
            ]
        else:
            # Return full data
            return paginated

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
    for entity_input in entities:
        try:
            # Create entity
            created = service.create_entity(
                entity_type=entity_input["entity_type"],
                name=entity_input["name"],
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
            error_result: CreateEntityResult = {
                "id": None,
                "entity_id": None,
                "name": entity_input.get("name", ""),
                "mention": None,
                "success": False,
                "error": str(e),
            }
            results.append(error_result)

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
        try:
            # Update entity
            success = service.update_entity(
                entity_id=update["entity_id"],
                name=update["name"],
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
            error_result: UpdateEntityResult = {
                "entity_id": update["entity_id"],
                "success": False,
                "error": str(e),
            }
            results.append(error_result)

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
