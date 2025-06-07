# MCP Kanka Tests

This directory contains comprehensive tests for the MCP Kanka server.

## Test Structure

```
tests/
├── unit/              # Unit tests with mocked dependencies
│   ├── test_converter.py    # Content conversion tests
│   ├── test_utils.py        # Utility function tests
│   ├── test_resources.py    # Resource endpoint tests
│   ├── test_service.py      # Service layer tests (mocked Kanka client)
│   └── test_tools.py        # Tool handler tests (mocked service)
│
├── integration/       # Integration tests using real Kanka API
│   ├── test_find_entities.py        # Search and filter tests
│   ├── test_create_update_delete.py # CRUD operation tests
│   ├── test_posts.py                # Post operation tests
│   └── run_integration_tests.py     # Run all integration tests
│
└── test_server.py     # Main test file for pytest discovery
```

## Running Tests

### Unit Tests

Unit tests use mocked dependencies and don't require Kanka API access:

```bash
# Run all unit tests
make test

# Run specific unit test file
pytest tests/unit/test_converter.py -v

# Run with coverage
make coverage
```

### Integration Tests

Integration tests require a real Kanka campaign and API token.

1. **Setup Environment**:
   ```bash
   cd tests/integration
   cp .env.example .env
   # Edit .env with your Kanka API token and campaign ID
   ```

2. **Run All Integration Tests**:
   ```bash
   python tests/integration/run_integration_tests.py
   ```

3. **Run Individual Test Files**:
   ```bash
   python tests/integration/test_find_entities.py
   python tests/integration/test_create_update_delete.py
   python tests/integration/test_posts.py
   ```

## Test Coverage Goals

### Unit Tests
- **converter.py**: Markdown/HTML conversion with entity mention preservation
- **utils.py**: Fuzzy matching, filtering, pagination, search functions
- **resources.py**: Kanka context resource generation
- **service.py**: All service methods with mocked KankaClient
- **tools.py**: All tool handlers with mocked service layer

### Integration Tests
- **find_entities**: Search, filtering, pagination, all parameter combinations
- **create_entities**: Single/batch creation, all entity types, error handling
- **update_entities**: Full/partial updates, batch operations
- **get_entities**: With/without posts, batch retrieval
- **delete_entities**: Single/batch deletion, cascading posts
- **posts**: CRUD operations on entity posts

## Writing New Tests

### Unit Tests
```python
from unittest.mock import Mock, patch
import pytest

class TestNewFeature:
    def test_something(self):
        # Arrange
        mock_dependency = Mock()
        mock_dependency.method.return_value = "expected"
        
        # Act
        result = function_under_test(mock_dependency)
        
        # Assert
        assert result == "expected"
```

### Integration Tests
```python
class TestNewIntegration(IntegrationTestBase):
    async def test_real_api_call(self):
        # Create test data
        result = await self.call_tool("create_entities", entities=[{
            "entity_type": "character",
            "name": "Integration Test - DELETE ME",
        }])
        
        # Track for cleanup
        self.track_entity(result[0]["entity_id"])
        
        # Test behavior
        # ...assertions...
```

## Important Notes

1. **Test Isolation**: Each test should be independent and clean up after itself
2. **Test Data**: Always use "Integration Test - DELETE ME" prefix for test entities
3. **Rate Limiting**: Use `wait_for_api()` between API calls in integration tests
4. **Error Testing**: Include tests for error conditions and edge cases
5. **Async Tests**: Integration tests are async - use proper async/await patterns

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure you're running tests from the project root or have proper PYTHONPATH
2. **API Rate Limits**: Add delays between API calls using `wait_for_api()`
3. **Cleanup Failures**: Check that entity IDs are properly tracked for cleanup
4. **Environment Variables**: Verify .env file is loaded and variables are set

### Debug Mode

Set environment variable for more verbose output:
```bash
export MCP_LOG_LEVEL=DEBUG
```

To keep test entities for inspection:
```bash
export KANKA_TEST_DEFER_CLEANUP=true
```