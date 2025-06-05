"""Type definitions for the Kanka MCP server."""

from typing import Literal, Optional, TypedDict

# Supported entity types
EntityType = Literal[
    "character",
    "creature",
    "location",
    "organization",
    "race",
    "note",
    "journal",
    "quest",
]


# Request types
class DateRange(TypedDict):
    """Date range for filtering."""

    start: str
    end: str


class FindEntitiesParams(TypedDict, total=False):
    """Parameters for find_entities tool."""

    query: Optional[str]
    entity_type: Optional[EntityType]
    name: Optional[str]
    name_fuzzy: Optional[bool]
    type: Optional[str]
    tags: Optional[list[str]]
    date_range: Optional[DateRange]
    include_full: Optional[bool]
    page: Optional[int]
    limit: Optional[int]


class EntityInput(TypedDict):
    """Input for creating an entity."""

    entity_type: EntityType
    name: str
    type: Optional[str]
    entry: Optional[str]
    tags: Optional[list[str]]
    is_private: Optional[bool]


class CreateEntitiesParams(TypedDict):
    """Parameters for create_entities tool."""

    entities: list[EntityInput]


class EntityUpdate(TypedDict):
    """Update for an entity."""

    entity_id: int
    name: str
    type: Optional[str]
    entry: Optional[str]
    tags: Optional[list[str]]
    is_private: Optional[bool]


class UpdateEntitiesParams(TypedDict):
    """Parameters for update_entities tool."""

    updates: list[EntityUpdate]


class GetEntitiesParams(TypedDict):
    """Parameters for get_entities tool."""

    entity_ids: list[int]
    include_posts: Optional[bool]


class DeleteEntitiesParams(TypedDict):
    """Parameters for delete_entities tool."""

    entity_ids: list[int]


class PostInput(TypedDict):
    """Input for creating a post."""

    entity_id: int
    name: str
    entry: Optional[str]
    is_private: Optional[bool]


class CreatePostsParams(TypedDict):
    """Parameters for create_posts tool."""

    posts: list[PostInput]


class PostUpdate(TypedDict):
    """Update for a post."""

    entity_id: int
    post_id: int
    name: str
    entry: Optional[str]
    is_private: Optional[bool]


class UpdatePostsParams(TypedDict):
    """Parameters for update_posts tool."""

    updates: list[PostUpdate]


class PostDeletion(TypedDict):
    """Deletion for a post."""

    entity_id: int
    post_id: int


class DeletePostsParams(TypedDict):
    """Parameters for delete_posts tool."""

    deletions: list[PostDeletion]


# Response types
class EntityMinimal(TypedDict):
    """Minimal entity data returned when include_full=false."""

    entity_id: int
    name: str
    entity_type: EntityType


class EntityFull(TypedDict, total=False):
    """Full entity data returned when include_full=true."""

    id: int
    entity_id: int
    name: str
    entity_type: EntityType
    type: Optional[str]
    entry: Optional[str]
    tags: list[str]
    is_private: bool
    match_score: Optional[float]  # Only when name_fuzzy=true


class PostData(TypedDict):
    """Post data structure."""

    id: int
    name: str
    entry: Optional[str]
    is_private: bool


class EntityWithPosts(EntityFull):
    """Entity with posts included."""

    posts: Optional[list[PostData]]


class CreateEntityResult(TypedDict):
    """Result of creating an entity."""

    id: Optional[int]
    entity_id: Optional[int]
    name: str
    mention: Optional[str]
    success: bool
    error: Optional[str]


class UpdateEntityResult(TypedDict):
    """Result of updating an entity."""

    entity_id: int
    success: bool
    error: Optional[str]


class GetEntityResult(TypedDict, total=False):
    """Result of getting an entity."""

    id: Optional[int]
    entity_id: int
    name: Optional[str]
    entity_type: Optional[EntityType]
    type: Optional[str]
    entry: Optional[str]
    tags: Optional[list[str]]
    is_private: Optional[bool]
    posts: Optional[list[PostData]]
    success: bool
    error: Optional[str]


class DeleteEntityResult(TypedDict):
    """Result of deleting an entity."""

    entity_id: int
    success: bool
    error: Optional[str]


class CreatePostResult(TypedDict):
    """Result of creating a post."""

    post_id: Optional[int]
    entity_id: int
    success: bool
    error: Optional[str]


class UpdatePostResult(TypedDict):
    """Result of updating a post."""

    entity_id: int
    post_id: int
    success: bool
    error: Optional[str]


class DeletePostResult(TypedDict):
    """Result of deleting a post."""

    entity_id: int
    post_id: int
    success: bool
    error: Optional[str]


# Kanka context resource structure
class KankaContextFields(TypedDict):
    """Core fields description."""

    name: str
    type: str
    entry: str
    tags: str
    is_private: str


class KankaContextTerminology(TypedDict):
    """Terminology description."""

    entity_type: str
    type: str


class KankaContextMentions(TypedDict):
    """Mentions description."""

    description: str
    examples: list[str]
    note: str


class KankaContext(TypedDict):
    """Kanka context resource structure."""

    description: str
    supported_entities: dict[str, str]
    core_fields: KankaContextFields
    terminology: KankaContextTerminology
    posts: str
    mentions: KankaContextMentions
    limitations: str
