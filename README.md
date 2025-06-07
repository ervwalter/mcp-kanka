# MCP-Kanka

MCP (Model Context Protocol) server for Kanka API integration. This server provides AI assistants with tools to interact with Kanka campaigns, enabling CRUD operations on various entity types like characters, locations, organizations, and more.

## Features

- **Entity Management**: Create, read, update, and delete Kanka entities
- **Search & Filter**: Search entities by name with partial matching, filter by type/tags/date
- **Batch Operations**: Process multiple entities in a single request
- **Posts Management**: Create, update, and delete posts (notes) on entities
- **Markdown Support**: Automatic conversion between Markdown and HTML with entity mention preservation
- **Type Safety**: Full type hints and validation
- **Client-side Filtering**: Enhanced filtering beyond API limitations

## Installation

### From PyPI (when published)
```bash
pip install mcp-kanka
```

### From Source
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

## Available Tools

### Entity Operations
- `find_entities` - Search and filter entities by name, type, tags, date range
- `create_entities` - Create one or more entities with markdown content
- `update_entities` - Update existing entities
- `get_entities` - Retrieve specific entities by ID with optional posts
- `delete_entities` - Delete one or more entities

### Post Operations
- `create_posts` - Add posts (notes) to entities
- `update_posts` - Modify existing posts
- `delete_posts` - Remove posts from entities

## Search & Filtering

The MCP server provides enhanced search capabilities:
- **Content search**: Full-text search across entity names and content (client-side)
- **Name filter**: Exact or fuzzy name matching
- **Type filter**: Filter by user-defined type field (e.g., 'NPC', 'City')
- **Tag filter**: Filter by tags (AND logic - entity must have all specified tags)
- **Date range**: Filter journals by date
- **Fuzzy matching**: Optional fuzzy name matching for more flexible searches

Note: Content search fetches all entities and searches client-side, which may be slower for large campaigns but provides comprehensive search functionality.

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

## Configuration

The MCP server requires:
- `KANKA_TOKEN`: Your Kanka API token
- `KANKA_CAMPAIGN_ID`: The ID of your Kanka campaign

## Resources

The server provides a `kanka://context` resource that explains Kanka's structure and capabilities.

## License

MIT