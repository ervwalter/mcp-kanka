# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in the mcp-kanka repository.

## Project Overview

This is an MCP (Model Context Protocol) server that provides AI assistants with tools to interact with Kanka campaigns. It exposes 9 tools for CRUD operations on Kanka entities (characters, locations, organizations, etc.) and implements client-side filtering, fuzzy search, and markdown/HTML conversion.

## Key Development Commands

This project uses [uv](https://docs.astral.sh/uv/) for dependency management. All commands are wrapped in the Makefile for convenience:

```bash
# Install development environment (uses uv sync)
make install

# Sync dependencies without updating lock file
make sync

# Run tests
make test

# Format code
make format

# Run linting
make lint

# Run type checking
make typecheck

# Run everything (lint + typecheck + tests)
make check

# Generate coverage report
make coverage

# Clean up generated files
make clean
```

### Direct uv commands

```bash
# Install dependencies
uv sync --all-groups

# Run a command in the environment
uv run pytest

# Add a new dependency
uv add package-name

# Add a dev dependency
uv add --group dev package-name

# Update dependencies
uv lock --upgrade

# Build the package
uv build
```

## Git Commit Message Format

This project uses conventional commits format:
```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only changes
- `style`: Code style changes (formatting, missing semicolons, etc)
- `refactor`: Code change that neither fixes a bug nor adds a feature
- `test`: Adding missing tests or correcting existing tests
- `chore`: Changes to build process, dependencies, or auxiliary tools

**Examples:**
- `feat: add sync/timestamp features and change name filtering`
- `fix: correct pagination logic to use SDK properties`
- `chore(deps): update dependency python to v3.13.5`
- `refactor: add operations layer for reusable business logic`

**Note:** When Claude generates commits, they should include the attribution at the end of the commit body:
```
🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

## Architecture Design

The MCP server follows this structure:

1. **Server Entry Point** (`__main__.py`): MCP server initialization and tool registration
2. **Tools Module** (`tools.py`): MCP tool implementations that handle parameters and delegate to operations
3. **Operations Layer** (`operations.py`): High-level business logic operations, reusable by both MCP and external scripts
4. **Kanka Service** (`service.py`): Low-level service layer wrapping python-kanka client
5. **Content Converter** (`converter.py`): Markdown ↔ HTML conversion with mention preservation
6. **Types Module** (`types.py`): Type definitions for tool parameters and responses
7. **Utils Module** (`utils.py`): Shared utilities like fuzzy matching, filtering, pagination
8. **Resources Module** (`resources.py`): Provides the kanka://context resource

## Implementation Guidelines

### Tool Implementation Pattern

Each MCP tool should:
1. Accept parameters as defined in `kanka-mcp-tools-requirements.md`
2. Delegate to the operations layer for business logic
3. Return the operation results directly (operations handle validation and errors)
4. Operations layer handles:
   - Input validation
   - Service layer calls
   - Error handling and partial success patterns
   - Content format conversion (Markdown ↔ HTML)

### Error Handling

- Use partial success pattern for batch operations
- Return `{success: false, error: "message"}` for individual failures
- Never let exceptions bubble up to MCP framework
- Log errors appropriately for debugging

### Content Format Handling

1. **Markdown → HTML**: When sending content to Kanka API
   - Preserve `[entity:ID]` and `[entity:ID|text]` mention formats
   - Convert standard Markdown elements
   
2. **HTML → Markdown**: When returning content from Kanka API
   - Convert back to clean Markdown
   - Preserve entity mentions

### Client-Side Filtering

Since Kanka API has limited server-side filtering:
- Implement filtering in the utils module
- Support fuzzy name matching using rapidfuzz library
- Filter by tags (AND logic - must have all specified tags)
- Filter by type field (exact or fuzzy match)
- Date range filtering for journals
- Name filtering is done via API when possible (list endpoints support name parameter)

### Search Implementation

The find_entities tool now implements comprehensive content search:
- When `query` is provided, fetches full entities and searches both names and content
- Uses client-side filtering via `search_in_content()` function
- When no entity type is specified, queries all supported types
- Slower than API name filtering but provides full-text search capability
- Falls back to efficient name-only filtering when only `name` parameter is used

## Testing Strategy

1. **Unit Tests**: Test individual components in isolation
   - Mock python-kanka client responses
   - Test content conversion edge cases
   - Test filtering logic

2. **Integration Tests**: Test MCP tool integration
   - Use pytest-asyncio for async tests
   - Mock the Kanka API responses
   - Test batch operation behavior

3. **Test Data**: Use "Integration Test - DELETE ME" prefix for any test entities

## Operations Layer Usage

The operations layer provides a reusable interface for Kanka operations that can be used by both MCP tools and external scripts:

### For External Scripts
```python
from mcp_kanka.operations import create_operations

# Create operations instance
ops = create_operations()

# Use typed methods
result = await ops.find_entities(
    entity_type="character",
    name="Moradin",
    last_synced="2025-01-06T10:00:00Z"
)

# Access results
for entity in result["entities"]:
    print(f"Found: {entity['name']}")
```

### For MCP Tools
MCP tools automatically use the operations layer via delegation:
```python
async def handle_find_entities(**params):
    operations = get_operations()
    return await operations.find_entities(**params)
```

### Available Operations
- `find_entities()` - Search and filter entities
- `create_entities()` - Create one or more entities
- `update_entities()` - Update existing entities
- `get_entities()` - Retrieve specific entities by ID
- `delete_entities()` - Delete entities
- `create_posts()` - Create posts on entities
- `update_posts()` - Update existing posts
- `delete_posts()` - Delete posts
- `check_entity_updates()` - Check for modified entities since last sync

## Key Implementation Details

### Service Layer Changes
- `search_entities()` now uses list endpoints with name filtering instead of search API
- Handles entity type mapping (e.g., 'organisation' in API vs 'organization' internally)
- Implements pagination when fetching all entities (limit=0)
- Properly tracks and cleans up test entities

### Tool Implementation
- `find_entities`: Now supports full content search - fetches entities and searches client-side
- All tools use proper error handling with partial success patterns
- Batch operations return individual success/error status for each item
- Content search implemented via `search_in_content()` in utils.py

## Development Preferences

- When executing test scripts with long output, redirect to file for parsing
- Don't push to origin during long tasks - let user do it manually
- Test frequently during complex refactoring
- Clean up temporary test files after use
- Don't leave comments explaining removed/moved code
- Use python-dotenv for environment variables: `load_dotenv()`

## Code Quality Workflow

**IMPORTANT**: After making any significant code changes, ALWAYS run these commands in order:

1. **Format first**: `make format` - Runs black, isort, and ruff auto-fixes
2. **Then check**: `make check` - Runs full linting, type checking, and all tests

**Why this order matters**:
- `make format` automatically fixes many style issues that would cause `make check` to fail
- Running `make check` without formatting first often results in unnecessary failures
- This saves time and ensures consistent code style

This workflow ensures:
- Code is properly formatted (black/isort)
- Auto-fixable issues are resolved (ruff --fix)
- No remaining linting violations (ruff)
- Type checking passes (mypy)
- All tests pass (pytest)

**Never commit without running both `make format` and `make check` successfully**.

## MCP-Specific Considerations

1. **Tool Registration**: Tools are registered with proper descriptions and parameter schemas
2. **Async Handling**: All MCP tools and service methods use async/await patterns
3. **Response Format**: Tools return structured data matching TypedDict definitions
4. **Resource Exposure**: The `kanka://context` resource is implemented and provides Kanka information
5. **Tool Naming**: MCP tools are prefixed with `mcp__kanka__` when accessed from Claude

## Environment Configuration

Required environment variables:
- `KANKA_TOKEN`: Kanka API authentication token
- `KANKA_CAMPAIGN_ID`: Target campaign ID

Optional:
- `MCP_LOG_LEVEL`: Logging level (default: INFO)

## Type Safety

- Use type hints for all function parameters and returns
- Define proper TypedDict or dataclasses for complex structures
- Ensure mypy passes with strict mode

## Documentation Requirements

When implementing or modifying tools:
1. Update inline documentation with clear descriptions
2. Include parameter descriptions in tool schemas
3. Document any limitations or workarounds
4. Keep README.md updated with usage examples
5. Update KANKA_CONTEXT.md if Kanka concepts change
6. Note API limitations (e.g., search only searches names)

## Testing Infrastructure

### Integration Tests
- **IMPORTANT**: Integration tests do NOT use pytest - they are run as standalone Python scripts
- Use `base_direct.py` as the base class for all integration tests (inherits from `IntegrationTestBase`)
- Tests call MCP tools directly via `self.call_tool()` method to simulate LLM interactions
- Do NOT use helper methods like `self.create_entity()` - these don't exist in base_direct.py
- Instead, use the full tool call pattern: `await self.call_tool("create_entities", entities=[{...}])`
- Cleanup tracking ensures all test entities are deleted via `self.track_entity(entity_id)`
- Test runner provides comprehensive summaries
- **IMPORTANT**: When adding new integration test files, always add them to the `TEST_FILES` list in `tests/integration/run_integration_tests.py` to ensure they are included in the test suite

#### Integration Test Patterns
```python
# CORRECT - Use call_tool directly
result = await self.call_tool(
    "create_entities",
    entities=[
        {
            "entity_type": "character",
            "name": "Integration Test - DELETE ME - Test Character",
            "type": "NPC",
        }
    ],
)
self.track_entity(result[0]["entity_id"])

# WRONG - Don't use helper methods that don't exist
result = await self.create_entity(
    entity_type="character",
    name="Test Character",
)
```

#### Name Filtering Behavior
- **Default behavior (v1.1.0+)**: The `name` parameter does partial matching (e.g., "Test" matches "Test Character")
- **Exact matching**: Use `name_exact=True` for exact name matches (case-insensitive)
- **Fuzzy matching**: Use `name_fuzzy=True` for typo-tolerant matching (e.g., "Tset" matches "Test")
- **Important**: The MCP service applies client-side filtering after API calls
- When using `last_synced` parameter:
  - The API returns all entities modified after the timestamp
  - Then client-side filtering is applied based on name/name_exact/name_fuzzy settings

### Unit Tests  
- Mock python-kanka client responses
- Test all edge cases for filtering and conversion
- Verify error handling and partial success patterns

## Performance Considerations

- Implement pagination for large result sets
- Cache tag lookups during batch operations
- Use concurrent requests where appropriate (respecting rate limits)
- Minimize API calls by fetching full data when needed

## Security Notes

- Never log or expose API tokens
- Validate all input parameters
- Sanitize error messages before returning to clients

## CRITICAL RULES

### Visibility Handling Strategy

**RULE**: The MCP server presents a unified `is_hidden` boolean interface to LLMs, but internally uses different fields based on the Kanka API endpoint:

1. **For Entities** (characters, locations, etc.):
   - Use `is_private` field when communicating with Kanka API
   - Convert between `is_private` and `is_hidden` in the service layer
   - The `is_private` field should ONLY appear in the service layer (`service.py`)

2. **For Posts**:
   - Use `visibility_id` field when communicating with Kanka API
   - Convert between `visibility_id` (1=all, 2=admin) and `is_hidden` in the service layer

3. **For MCP Tools and Operations Layer**:
   - ALWAYS use `is_hidden` boolean in tool interfaces and operations
   - NEVER expose `is_private` or `visibility_id` to LLMs or in MCP tool responses
   - The operations layer should only deal with `is_hidden`

**Implementation Notes**:
- The service layer (`service.py`) handles all conversions between API fields and the unified `is_hidden` interface
- Tests should use `is_hidden` in their assertions and tool calls
- The term `is_private` should NEVER appear outside of `service.py`

**Reason**: The Kanka API inconsistently uses different fields for visibility across endpoints. We provide a consistent interface to LLMs while handling the API complexity internally.