# Integration Tests

This directory contains integration tests for the MCP Kanka server that test against the real Kanka API.

## Running Tests

1. Set up environment variables:
   ```bash
   export KANKA_TOKEN="your-kanka-api-token"
   export KANKA_CAMPAIGN_ID="your-test-campaign-id"
   ```
   
   Or create a `.env` file in this directory with:
   ```
   KANKA_TOKEN=your-kanka-api-token
   KANKA_CAMPAIGN_ID=your-test-campaign-id
   ```

2. Clean the test campaign (recommended):
   ```bash
   python clean_campaign.py
   ```

3. Run all tests:
   ```bash
   python run_integration_tests.py
   ```

4. Run specific test files:
   ```bash
   python test_create_update_delete.py
   python test_find_entities.py
   python test_posts.py
   ```

## Known Issues

### Search API Limitations

1. **Eventual Consistency**: The Kanka search API has eventual consistency. Entities created might not appear in search results immediately. Tests wait 1 second after creation, but this might not always be enough.

2. **Content Search**: The search API might not search within entry content, only entity names and certain fields.

3. **No Limit Parameter**: The search API doesn't support limiting results, it returns all matches.

### Entity ID Resolution

The `get_entity_by_id` method needs to scan through recent entities to find the entity type because:
- The `/entities` endpoint doesn't support filtering by entity_id
- We need to know the entity type to use the type-specific endpoint

This can be slow and might miss very old entities.

### Tag Resolution

Tags are returned as IDs from the API and need to be resolved to names. This requires additional API calls which can slow down operations.

## Test Structure

- `base_direct.py`: Base class for tests that call MCP tools directly
- `test_create_update_delete.py`: Tests for CRUD operations
- `test_find_entities.py`: Tests for search and filtering
- `test_posts.py`: Tests for post operations on entities

## Cleanup

All test entities are created with "Integration Test" and "DELETE ME" in their names. The cleanup functions track entity IDs and delete them after tests complete.

If tests fail and leave orphaned entities, run:
```bash
python clean_campaign.py
```