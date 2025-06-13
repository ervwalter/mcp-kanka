"""
Kanka MCP Server

An MCP server that provides tools for interacting with Kanka campaigns.
"""

from ._version import __version__
from .converter import ContentConverter
from .operations import KankaOperations, create_operations
from .resources import get_kanka_context
from .service import KankaService
from .tools import (
    handle_create_entities,
    handle_create_posts,
    handle_delete_entities,
    handle_delete_posts,
    handle_find_entities,
    handle_get_entities,
    handle_update_entities,
    handle_update_posts,
)
from .types import (
    CreateEntitiesParams,
    CreateEntityResult,
    CreatePostResult,
    CreatePostsParams,
    DeleteEntitiesParams,
    DeleteEntityResult,
    DeletePostResult,
    DeletePostsParams,
    EntityFull,
    EntityMinimal,
    EntityType,
    FindEntitiesParams,
    GetEntitiesParams,
    GetEntityResult,
    UpdateEntitiesParams,
    UpdateEntityResult,
    UpdatePostResult,
    UpdatePostsParams,
)
from .utils import (
    filter_entities_by_name,
    filter_entities_by_tags,
    filter_entities_by_type,
    filter_journals_by_date_range,
    fuzzy_match_score,
    paginate_results,
    parse_date_from_entry,
    search_in_content,
)

__all__ = [
    # Version
    "__version__",
    # Converter
    "ContentConverter",
    # Operations
    "KankaOperations",
    "create_operations",
    # Resources
    "get_kanka_context",
    # Service
    "KankaService",
    # Tools
    "handle_create_entities",
    "handle_create_posts",
    "handle_delete_entities",
    "handle_delete_posts",
    "handle_find_entities",
    "handle_get_entities",
    "handle_update_entities",
    "handle_update_posts",
    # Types
    "CreateEntitiesParams",
    "CreateEntityResult",
    "CreatePostResult",
    "CreatePostsParams",
    "DeleteEntitiesParams",
    "DeleteEntityResult",
    "DeletePostResult",
    "DeletePostsParams",
    "EntityFull",
    "EntityMinimal",
    "EntityType",
    "FindEntitiesParams",
    "GetEntitiesParams",
    "GetEntityResult",
    "UpdateEntitiesParams",
    "UpdateEntityResult",
    "UpdatePostResult",
    "UpdatePostsParams",
    # Utils
    "filter_entities_by_name",
    "filter_entities_by_tags",
    "filter_entities_by_type",
    "filter_journals_by_date_range",
    "fuzzy_match_score",
    "paginate_results",
    "parse_date_from_entry",
    "search_in_content",
]
