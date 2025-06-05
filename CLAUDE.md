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

The MCP server should follow this structure:

1. **Server Entry Point** (`__main__.py`): MCP server initialization and tool registration
2. **Tools Module** (`tools.py`): MCP tool implementations using @mcp.tool decorator
3. **Kanka Service** (`service.py`): Business logic layer wrapping python-kanka client
4. **Content Converter** (`converter.py`): Markdown ↔ HTML conversion with mention preservation
5. **Types Module** (`types.py`): Type definitions for tool parameters and responses
6. **Utils Module** (`utils.py`): Shared utilities like fuzzy matching, filtering

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
- Implement filtering in the service layer
- Support fuzzy name matching using appropriate library
- Filter by tags (AND logic - must have all specified tags)
- Filter by type field (exact or fuzzy match)
- Date range filtering for journals

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

1. **Tool Registration**: Tools must be registered with proper descriptions and parameter schemas
2. **Async Handling**: MCP tools are async - use proper async/await patterns
3. **Response Format**: Follow MCP response conventions for structured data
4. **Resource Exposure**: Implement the `kanka_context` resource as specified

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