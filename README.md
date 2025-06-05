# MCP-Kanka

MCP (Model Context Protocol) server for Kanka API integration. This server provides AI assistants with tools to interact with Kanka campaigns, enabling CRUD operations on various entity types like characters, locations, organizations, and more.

## Features

- **Entity Management**: Create, read, update, and delete Kanka entities
- **Search & Filter**: Search entities by name/content with fuzzy matching support
- **Batch Operations**: Process multiple entities in a single request
- **Markdown Support**: Automatic conversion between Markdown and HTML
- **Type Safety**: Full type hints and validation

## Installation

```bash
pip install mcp-kanka
```

## Quick Start

```python
# Example usage coming soon
```

## Supported Entity Types

- Character - Player characters (PCs), non-player characters (NPCs)
- Creature - Monster types, animals, non-unique creatures
- Location - Places, regions, buildings, landmarks
- Organization - Guilds, governments, cults, companies
- Race - Species, ancestries
- Note - Internal content, session digests, GM notes
- Journal - Session summaries, narratives, chronicles

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

## License

MIT