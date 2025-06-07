# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in the mcp-kanka repository.

## Project Overview

This is an MCP (Model Context Protocol) server that provides AI assistants with tools to interact with Kanka campaigns. It exposes 8 tools for CRUD operations on Kanka entities (characters, locations, organizations, etc.) and implements client-side filtering, fuzzy search, and markdown/HTML conversion.

## Key Development Commands

```bash
# Install development environment
make install

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

## Architecture Design

The MCP server follows this structure:

1. **Server Entry Point** (`__main__.py`): MCP server initialization and tool registration
2. **Tools Module** (`tools.py`): MCP tool implementations that handle parameters and call service methods
3. **Kanka Service** (`service.py`): Business logic layer wrapping python-kanka client
4. **Content Converter** (`converter.py`): Markdown ↔ HTML conversion with mention preservation
5. **Types Module** (`types.py`): Type definitions for tool parameters and responses
6. **Utils Module** (`utils.py`): Shared utilities like fuzzy matching, filtering, pagination
7. **Resources Module** (`resources.py`): Provides the kanka://context resource

## Implementation Guidelines

### Tool Implementation Pattern

Each MCP tool should:
1. Accept parameters as defined in `kanka-mcp-tools-requirements.md`
2. Validate input parameters
3. Call the service layer for business logic
4. Handle errors gracefully and return partial success where appropriate
5. Convert content formats (Markdown ↔ HTML) as needed

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

**IMPORTANT**: After making any significant code changes, always run:

1. **Format first**: `make format` - Runs black and isort to format code
2. **Verify quality**: `make check` - Runs full linting, type checking, and all tests

This ensures:
- Code is properly formatted (black/isort)
- No linting violations (ruff)
- Type checking passes (mypy)
- All tests pass (pytest)

**Never commit without running `make check` successfully**.

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
- Use `base_direct.py` for direct MCP server testing
- Tests run the actual MCP server via subprocess
- Cleanup tracking ensures all test entities are deleted
- Test runner provides comprehensive summaries

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
- Use is_private flag appropriately for sensitive content