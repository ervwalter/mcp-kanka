# MCP-Kanka

MCP (Model Context Protocol) server for Kanka API integration. This server provides AI assistants with tools to interact with Kanka campaigns, enabling CRUD operations on various entity types like characters, locations, organizations, and more.

This package is designed specifically to serve the needs of [Teghrim](https://github.com/ervwalter/teghrim) but may be useful to others working with Kanka and MCP.

## Features

- **Entity Management**: Create, read, update, and delete Kanka entities
- **Search & Filter**: Search entities by name with partial matching, filter by type/tags/date
- **Batch Operations**: Process multiple entities in a single request
- **Posts Management**: Create, update, and delete posts (notes) on entities
- **Markdown Support**: Automatic conversion between Markdown and HTML with entity mention preservation
- **Type Safety**: Full type hints and validation
- **Client-side Filtering**: Enhanced filtering beyond API limitations
- **Sync Support**: Efficient synchronization with timestamp tracking and Kanka's native lastSync feature
- **Timestamp Tracking**: All entities include created_at and updated_at timestamps

## Requirements

- Python 3.10 or higher (3.13.5 recommended)
- Kanka API token and campaign ID

## Installation

### From PyPI
```bash
pip install mcp-kanka
```

### From Source (using uv)
```bash
git clone https://github.com/ervwalter/mcp-kanka.git
cd mcp-kanka
uv sync --all-groups
uv pip install -e .
```

### From Source (using pip)
```bash
git clone https://github.com/ervwalter/mcp-kanka.git
cd mcp-kanka
pip install -e .
```

## Quick Start

### Adding to Claude Desktop

1. Set up your environment variables:
   - `KANKA_TOKEN`: Your Kanka API token
   - `KANKA_CAMPAIGN_ID`: Your campaign ID

2. Add to Claude Desktop config:
```json
{
  "mcpServers": {
    "kanka": {
      "command": "python",
      "args": ["-m", "mcp_kanka"],
      "env": {
        "KANKA_TOKEN": "your-token",
        "KANKA_CAMPAIGN_ID": "your-campaign-id"
      }
    }
  }
}
```

### Using with Claude Code CLI

```bash
claude mcp add kanka \
  -e KANKA_TOKEN="your-token" \
  -e KANKA_CAMPAIGN_ID="your-campaign-id" \
  -- python -m mcp_kanka
```

## Supported Entity Types

- **Character** - Player characters (PCs), non-player characters (NPCs)
- **Creature** - Monster types, animals, non-unique creatures
- **Location** - Places, regions, buildings, landmarks
- **Organization** - Guilds, governments, cults, companies
- **Race** - Species, ancestries
- **Note** - Internal content, session digests, GM notes (private by default)
- **Journal** - Session summaries, narratives, chronicles
- **Quest** - Missions, objectives, story arcs

## Available Tools (9 Total)

### Entity Operations

#### `find_entities`
Search and filter entities with comprehensive options and sync metadata.

**Parameters:**
- `entity_type` (optional): Type to filter by - character, creature, location, organization, race, note, journal, quest
- `query` (optional): Search term for full-text search across names and content
- `name` (optional): Filter by name (partial match by default, e.g., "Test" matches "Test Character")
- `name_exact` (optional): Use exact name matching instead of partial (default: false)
- `name_fuzzy` (optional): Enable fuzzy matching for typo tolerance (default: false)
- `type` (optional): Filter by user-defined Type field (e.g., 'NPC', 'City')
- `tags` (optional): Array of tags - returns entities having ALL specified tags
- `date_range` (optional): For journals only - filter by date range with `start` and `end` dates
- `limit` (optional): Results per page (default: 25, max: 100, use 0 for all)
- `page` (optional): Page number for pagination (default: 1)
- `include_full` (optional): Include full entity details (default: true)
- `last_synced` (optional): ISO 8601 timestamp to get only entities modified after this time

**Returns:**
```json
{
  "entities": [...],
  "sync_info": {
    "request_timestamp": "2024-01-01T12:00:00Z",
    "newest_updated_at": "2024-01-01T11:30:00Z",
    "total_count": 150,
    "returned_count": 25
  }
}
```

#### `create_entities`
Create one or more entities with markdown content.

**Parameters:**
- `entities`: Array of entities to create, each with:
  - `entity_type` (required): Type of entity to create
  - `name` (required): Entity name
  - `entry` (optional): Description in Markdown format
  - `type` (optional): User-defined Type field (e.g., 'NPC', 'Player Character')
  - `tags` (optional): Array of tag names
  - `is_hidden` (optional): If true, hidden from players (admin-only)

**Returns:** Array of created entities with their IDs and timestamps

#### `update_entities`
Update one or more existing entities.

**Parameters:**
- `updates`: Array of updates, each with:
  - `entity_id` (required): ID of entity to update
  - `name` (required): Entity name (required by Kanka API even if unchanged)
  - `entry` (optional): Updated content in Markdown format
  - `type` (optional): Updated Type field
  - `tags` (optional): Updated array of tags
  - `is_hidden` (optional): If true, hidden from players (admin-only)

**Returns:** Array of results with success/error status for each update

#### `get_entities`
Retrieve specific entities by ID with optional posts.

**Parameters:**
- `entity_ids` (required): Array of entity IDs to retrieve
- `include_posts` (optional): Include posts for each entity (default: false)

**Returns:** Array of full entity details with timestamps and optional posts

#### `delete_entities`
Delete one or more entities.

**Parameters:**
- `entity_ids` (required): Array of entity IDs to delete

**Returns:** Array of results with success/error status for each deletion

#### `check_entity_updates`
Efficiently check which entities have been modified since last sync.

**Parameters:**
- `entity_ids` (required): Array of entity IDs to check
- `last_synced` (required): ISO 8601 timestamp to check updates since

**Returns:**
```json
{
  "modified_entity_ids": [101, 103],
  "deleted_entity_ids": [102],
  "check_timestamp": "2024-01-01T12:00:00Z"
}
```

### Post Operations

#### `create_posts`
Add posts (notes) to entities.

**Parameters:**
- `posts`: Array of posts to create, each with:
  - `entity_id` (required): Entity to attach post to
  - `name` (required): Post title
  - `entry` (optional): Post content in Markdown format
  - `is_hidden` (optional): If true, hidden from players (admin-only)

**Returns:** Array of created posts with their IDs

#### `update_posts`
Modify existing posts.

**Parameters:**
- `updates`: Array of updates, each with:
  - `entity_id` (required): The entity ID
  - `post_id` (required): The post ID to update
  - `name` (required): Post title (required by API even if unchanged)
  - `entry` (optional): Updated content in Markdown format
  - `is_hidden` (optional): If true, hidden from players (admin-only)

**Returns:** Array of results with success/error status for each update

#### `delete_posts`
Remove posts from entities.

**Parameters:**
- `deletions`: Array of deletions, each with:
  - `entity_id` (required): The entity ID
  - `post_id` (required): The post ID to delete

**Returns:** Array of results with success/error status for each deletion

## Search & Filtering

The MCP server provides enhanced search capabilities:
- **Content search**: Full-text search across entity names and content (client-side)
- **Name filter**: Exact or fuzzy name matching
- **Type filter**: Filter by user-defined type field (e.g., 'NPC', 'City')
- **Tag filter**: Filter by tags (AND logic - entity must have all specified tags)
- **Date range**: Filter journals by date
- **Fuzzy matching**: Optional fuzzy name matching for more flexible searches
- **Last sync filter**: Use Kanka's native lastSync parameter to get only modified entities

Note: Content search fetches all entities and searches client-side, which may be slower for large campaigns but provides comprehensive search functionality.

## Synchronization Features

### Timestamp Support
All entities include `created_at` and `updated_at` timestamps in ISO 8601 format, enabling:
- Tracking when entities were created or last modified
- Implementing conflict resolution strategies
- Building audit trails

### Sync Metadata
The `find_entities` tool returns sync metadata including:
- `request_timestamp`: When the request was made
- `newest_updated_at`: Latest updated_at from returned entities
- `total_count`: Total matching entities
- `returned_count`: Number returned in this response

### Efficient Sync with lastSync
Use the `last_synced` parameter to fetch only entities modified after a specific time:
```python
# Example: Get entities modified in the last 24 hours
result = await find_entities(
    entity_type="character",
    last_synced="2024-01-01T00:00:00Z"
)
```

### Batch Update Checking
The `check_entity_updates` tool efficiently checks which entities have been modified:
```python
# Check which of these entities have changed
result = await check_entity_updates(
    entity_ids=[101, 102, 103],
    last_synced="2024-01-01T00:00:00Z"
)
# Returns: modified_entity_ids, deleted_entity_ids, check_timestamp
```

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/ervwalter/mcp-kanka.git
cd mcp-kanka

# Install development dependencies
make install
```

### Running Tests

```bash
# Run all tests
make test

# Run with coverage
make coverage

# Run all checks (lint + typecheck + test)
make check
```

### Code Quality

```bash
# Format code
make format

# Run linting
make lint

# Run type checking
make typecheck
```

## Programmatic Usage

In addition to being an MCP server, this package provides an operations layer that can be used directly in Python scripts:

```python
from mcp_kanka.operations import create_operations

# Create operations instance
ops = create_operations()

# Find entities
result = await ops.find_entities(
    entity_type="character",
    name="Moradin"
)

# Create an entity
results = await ops.create_entities([{
    "entity_type": "character",
    "name": "New Character",
    "type": "NPC",
    "entry": "A mysterious figure"
}])
```

This makes it easy to build sync scripts, bulk operations, or other tools that interact with Kanka.

## Configuration

The MCP server requires:
- `KANKA_TOKEN`: Your Kanka API token
- `KANKA_CAMPAIGN_ID`: The ID of your Kanka campaign

## Resources

The server provides a `kanka://context` resource that explains Kanka's structure and capabilities.

## Version History

### v0.1.0
- Initial release
- Full CRUD operations for Kanka entities
- Batch operations support
- Markdown/HTML conversion with entity mention preservation
- Sync support with timestamp tracking
- Comprehensive search and filtering capabilities

## License

MIT