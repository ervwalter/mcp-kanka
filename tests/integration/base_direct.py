"""Base class for MCP integration tests using direct tool calls."""

import asyncio
import os
from collections.abc import Callable
from typing import Any

from setup_test_env import setup_environment

from mcp_kanka.resources import get_kanka_context
from mcp_kanka.tools import (
    handle_check_entity_updates,
    handle_create_entities,
    handle_create_posts,
    handle_delete_entities,
    handle_delete_posts,
    handle_find_entities,
    handle_get_entities,
    handle_update_entities,
    handle_update_posts,
)

# Setup environment when module is imported
setup_environment()


class IntegrationTestBase:
    """Base class for integration tests that call MCP tools directly."""

    def __init__(self):
        self.token = os.environ.get("KANKA_TOKEN")
        self.campaign_id = os.environ.get("KANKA_CAMPAIGN_ID")
        self._cleanup_tasks: list[tuple[str, Callable]] = []
        self._created_entities: list[int] = []  # Track entities for cleanup

    async def call_tool(self, tool_name: str, **arguments: Any) -> Any:
        """Call an MCP tool by name and return the result."""
        tool_map = {
            "find_entities": handle_find_entities,
            "create_entities": handle_create_entities,
            "update_entities": handle_update_entities,
            "get_entities": handle_get_entities,
            "delete_entities": handle_delete_entities,
            "create_posts": handle_create_posts,
            "update_posts": handle_update_posts,
            "delete_posts": handle_delete_posts,
            "check_entity_updates": handle_check_entity_updates,
        }

        if tool_name not in tool_map:
            raise ValueError(f"Unknown tool: {tool_name}")

        handler = tool_map[tool_name]
        return await handler(**arguments)

    def get_kanka_context(self) -> dict[str, Any]:
        """Get the Kanka context resource."""
        import json

        return json.loads(get_kanka_context())

    def register_cleanup(self, description: str, cleanup_func: Callable):
        """Register a cleanup task to be executed later."""
        self._cleanup_tasks.append((description, cleanup_func))

    def track_entity(self, entity_id: int):
        """Track an entity for cleanup."""
        self._created_entities.append(entity_id)

    async def cleanup_entities(self):
        """Clean up all tracked entities."""
        if not self._created_entities:
            return

        print(f"\nCleaning up {len(self._created_entities)} entities...")

        # Track which entities were successfully deleted
        deleted_entities = []

        # Delete in batches
        batch_size = 10
        for i in range(0, len(self._created_entities), batch_size):
            batch = self._created_entities[i : i + batch_size]
            try:
                result = await self.call_tool("delete_entities", entity_ids=batch)

                # Track individual successes
                if isinstance(result, list):
                    successes = 0
                    for j, r in enumerate(result):
                        if r.get("success"):
                            successes += 1
                            deleted_entities.append(batch[j])
                    print(f"  Deleted {successes}/{len(batch)} entities")

            except Exception as e:
                print(f"  Failed to delete batch: {e}")

        # Only remove successfully deleted entities from tracking
        for entity_id in deleted_entities:
            self._created_entities.remove(entity_id)

        # Report any remaining entities that couldn't be deleted
        if self._created_entities:
            print(
                f"  WARNING: {len(self._created_entities)} entities could not be deleted:"
            )
            for entity_id in self._created_entities[:5]:  # Show first 5
                print(f"    - Entity ID: {entity_id}")
            if len(self._created_entities) > 5:
                print(f"    ... and {len(self._created_entities) - 5} more")

        # Don't clear the list - keep tracking failed deletions
        # self._created_entities.clear()

    async def setup(self):
        """Set up the test environment."""
        # Nothing special needed for direct calls
        pass

    async def teardown(self):
        """Clean up the test environment."""
        # Execute cleanup tasks
        for description, cleanup_func in self._cleanup_tasks:
            try:
                if asyncio.iscoroutinefunction(cleanup_func):
                    await cleanup_func()
                else:
                    cleanup_func()
                print(f"  ✓ {description}")
            except Exception as e:
                print(f"  ✗ {description} failed: {e}")

        # Clean up entities
        await self.cleanup_entities()

    async def run_test(self, test_name: str, test_func):
        """Run a single test with proper setup and teardown."""
        print(f"\nRunning {test_name}...")
        try:
            await self.setup()
            await test_func()
            print(f"✓ {test_name} passed")
            return True
        except Exception as e:
            print(f"✗ {test_name} failed: {e}")
            import traceback

            traceback.print_exc()
            return False
        finally:
            await self.teardown()

    def assert_equal(self, actual: Any, expected: Any, message: str = ""):
        """Assert that two values are equal."""
        if actual != expected:
            raise AssertionError(f"{message}\nExpected: {expected}\nActual: {actual}")

    def assert_true(self, condition: bool, message: str = ""):
        """Assert that a condition is true."""
        if not condition:
            raise AssertionError(f"Assertion failed: {message}")

    def assert_in(self, item: Any, container: Any, message: str = ""):
        """Assert that an item is in a container."""
        if item not in container:
            raise AssertionError(f"{message}\n{item} not found in {container}")

    def assert_not_none(self, value: Any, message: str = ""):
        """Assert that a value is not None."""
        if value is None:
            raise AssertionError(f"Value is None: {message}")

    def assert_greater_than(self, value: Any, threshold: Any, message: str = ""):
        """Assert that a value is greater than a threshold."""
        if not value > threshold:
            raise AssertionError(f"{message}\n{value} is not greater than {threshold}")

    async def wait_for_api(self, seconds: float = 1.0):
        """Wait a bit to avoid rate limiting and allow for eventual consistency."""
        await asyncio.sleep(seconds)
