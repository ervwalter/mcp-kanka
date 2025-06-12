#!/usr/bin/env python3
"""Integration tests for create, update, and delete entity tools."""

import asyncio
import sys

from base_direct import IntegrationTestBase


class TestCreateUpdateDelete(IntegrationTestBase):
    """Test entity CRUD operations with real Kanka API."""

    async def test_create_single_entity(self):
        """Test creating a single entity with all fields."""
        # Create a character with all fields
        result = await self.call_tool(
            "create_entities",
            entities=[
                {
                    "entity_type": "character",
                    "name": "Integration Test Hero - DELETE ME",
                    "type": "Player Character",
                    "entry": "# Background\n\nA brave **hero** from the integration tests.\n\nHas connections to [entity:123|The King].",
                    "tags": ["hero", "test", "player"],
                    "is_hidden": False,
                }
            ],
        )

        self.assert_equal(len(result), 1)
        self.assert_true(
            result[0]["success"], f"Create failed: {result[0].get('error')}"
        )

        entity_id = result[0]["entity_id"]
        self.assert_not_none(entity_id)
        self.track_entity(entity_id)

        # Verify the entity was created correctly
        await self.wait_for_api()

        get_result = await self.call_tool("get_entities", entity_ids=[entity_id])
        self.assert_equal(len(get_result), 1)
        self.assert_true(get_result[0]["success"])

        entity = get_result[0]
        self.assert_equal(entity["name"], "Integration Test Hero - DELETE ME")
        self.assert_equal(entity["type"], "Player Character")
        self.assert_in("brave **hero**", entity["entry"])
        self.assert_in("[entity:123|The King]", entity["entry"])  # Mention preserved
        self.assert_in("hero", entity["tags"])
        self.assert_in("test", entity["tags"])
        self.assert_equal(entity["is_hidden"], False)

    async def test_create_multiple_entities(self):
        """Test creating multiple entities in one call."""
        # Create multiple entities of different types
        result = await self.call_tool(
            "create_entities",
            entities=[
                {
                    "entity_type": "location",
                    "name": "Integration Test City - DELETE ME",
                    "type": "Capital",
                    "entry": "The grand capital of the test realm.",
                },
                {
                    "entity_type": "organization",
                    "name": "Integration Test Guild - DELETE ME",
                    "type": "Merchant Guild",
                    "tags": ["guild", "test"],
                },
                {
                    "entity_type": "quest",
                    "name": "Integration Test Quest - DELETE ME",
                    "type": "Main Quest",
                    "is_hidden": True,
                },
            ],
        )

        self.assert_equal(len(result), 3)

        # Check all succeeded and track for cleanup
        for i, r in enumerate(result):
            self.assert_true(r["success"], f"Entity {i} failed: {r.get('error')}")
            self.assert_not_none(r["entity_id"])
            self.track_entity(r["entity_id"])

        # Verify different entity types were created
        self.assert_equal(result[0]["name"], "Integration Test City - DELETE ME")
        self.assert_equal(result[1]["name"], "Integration Test Guild - DELETE ME")
        self.assert_equal(result[2]["name"], "Integration Test Quest - DELETE ME")

    async def test_update_entity(self):
        """Test updating an existing entity."""
        # First create an entity
        create_result = await self.call_tool(
            "create_entities",
            entities=[
                {
                    "entity_type": "character",
                    "name": "Integration Test Update Me - DELETE ME",
                    "type": "NPC",
                    "entry": "Original description",
                    "tags": ["original"],
                    "is_hidden": False,
                }
            ],
        )

        self.assert_true(create_result[0]["success"])
        entity_id = create_result[0]["entity_id"]
        self.track_entity(entity_id)

        await self.wait_for_api()

        # Update the entity
        update_result = await self.call_tool(
            "update_entities",
            updates=[
                {
                    "entity_id": entity_id,
                    "name": "Integration Test Updated - DELETE ME",  # Required by API
                    "type": "Boss NPC",
                    "entry": "# Updated Description\n\nThis character has been **updated**!",
                    "tags": ["updated", "boss"],
                    "is_hidden": True,
                }
            ],
        )

        self.assert_equal(len(update_result), 1)
        self.assert_true(
            update_result[0]["success"],
            f"Update failed: {update_result[0].get('error')}",
        )

        await self.wait_for_api()

        # Verify the update
        get_result = await self.call_tool("get_entities", entity_ids=[entity_id])
        entity = get_result[0]

        self.assert_equal(entity["name"], "Integration Test Updated - DELETE ME")
        self.assert_equal(entity["type"], "Boss NPC")
        self.assert_in("Updated Description", entity["entry"])
        self.assert_in("updated", entity["tags"])
        self.assert_in("boss", entity["tags"])
        self.assert_equal(entity["is_hidden"], True)

    async def test_partial_update(self):
        """Test updating only some fields of an entity."""
        # Create an entity
        create_result = await self.call_tool(
            "create_entities",
            entities=[
                {
                    "entity_type": "location",
                    "name": "Integration Test Partial Update - DELETE ME",
                    "type": "Village",
                    "entry": "A small village",
                    "tags": ["village", "small"],
                }
            ],
        )

        entity_id = create_result[0]["entity_id"]
        self.track_entity(entity_id)

        await self.wait_for_api()

        # Update only the type and add a tag
        update_result = await self.call_tool(
            "update_entities",
            updates=[
                {
                    "entity_id": entity_id,
                    "name": "Integration Test Partial Update - DELETE ME",  # Required
                    "type": "Town",  # Changed
                    "tags": ["village", "small", "growing"],  # Added one
                }
            ],
        )

        self.assert_true(update_result[0]["success"])

        await self.wait_for_api()

        # Verify partial update
        get_result = await self.call_tool("get_entities", entity_ids=[entity_id])
        entity = get_result[0]

        self.assert_equal(entity["type"], "Town")  # Changed
        self.assert_in("A small village", entity["entry"])  # Unchanged
        self.assert_in("growing", entity["tags"])  # New tag added

    async def test_delete_entity(self):
        """Test deleting a single entity."""
        # Create an entity to delete
        create_result = await self.call_tool(
            "create_entities",
            entities=[
                {
                    "entity_type": "note",
                    "name": "Integration Test Delete Me - DELETE ME",
                    "entry": "This will be deleted",
                    "is_hidden": True,
                }
            ],
        )

        entity_id = create_result[0]["entity_id"]
        # Track it in case delete fails
        self.track_entity(entity_id)

        await self.wait_for_api()

        # Delete the entity
        delete_result = await self.call_tool("delete_entities", entity_ids=[entity_id])

        self.assert_equal(len(delete_result), 1)
        self.assert_true(
            delete_result[0]["success"],
            f"Delete failed: {delete_result[0].get('error')}",
        )
        self.assert_equal(delete_result[0]["entity_id"], entity_id)

        # Remove from tracking since it was successfully deleted
        if delete_result[0]["success"]:
            self._created_entities.remove(entity_id)

        await self.wait_for_api()

        # Verify it's gone
        get_result = await self.call_tool("get_entities", entity_ids=[entity_id])
        self.assert_false(get_result[0]["success"])
        self.assert_in("not found", get_result[0]["error"].lower())

    async def test_batch_operations(self):
        """Test batch create, update, and delete operations."""
        # Batch create
        create_result = await self.call_tool(
            "create_entities",
            entities=[
                {
                    "entity_type": "creature",
                    "name": f"Integration Test Monster {i} - DELETE ME",
                    "type": "Goblin",
                }
                for i in range(5)
            ],
        )

        # Collect entity IDs
        entity_ids = []
        for r in create_result:
            self.assert_true(r["success"])
            entity_ids.append(r["entity_id"])

        await self.wait_for_api()

        # Batch update first 3
        update_result = await self.call_tool(
            "update_entities",
            updates=[
                {
                    "entity_id": entity_ids[i],
                    "name": f"Integration Test Monster {i} - DELETE ME",
                    "type": "Hobgoblin",  # Evolved!
                }
                for i in range(3)
            ],
        )

        for r in update_result:
            self.assert_true(r["success"])

        await self.wait_for_api()

        # Batch delete last 2
        delete_result = await self.call_tool(
            "delete_entities", entity_ids=entity_ids[3:]
        )

        for r in delete_result:
            self.assert_true(r["success"])

        # Track remaining for cleanup
        for entity_id in entity_ids[:3]:
            self.track_entity(entity_id)

        # Verify the updates
        get_result = await self.call_tool("get_entities", entity_ids=entity_ids[:3])
        for r in get_result:
            self.assert_true(r["success"])
            self.assert_equal(r["type"], "Hobgoblin")

    async def test_error_handling(self):
        """Test error handling in CRUD operations."""
        # Try to create with missing required field
        result = await self.call_tool(
            "create_entities",
            entities=[
                {
                    "entity_type": "character",
                    # Missing required "name" field
                    "type": "NPC",
                }
            ],
        )

        self.assert_equal(len(result), 1)
        self.assert_false(result[0]["success"])
        self.assert_not_none(result[0]["error"])

        # Try to update non-existent entity
        update_result = await self.call_tool(
            "update_entities",
            updates=[
                {
                    "entity_id": 9999999,  # Doesn't exist
                    "name": "Won't work",
                }
            ],
        )

        self.assert_false(update_result[0]["success"])
        self.assert_in("not found", update_result[0]["error"].lower())

        # Try to delete non-existent entity
        delete_result = await self.call_tool("delete_entities", entity_ids=[9999999])

        self.assert_false(delete_result[0]["success"])
        self.assert_not_none(delete_result[0]["error"])

    def assert_false(self, condition: bool, message: str = ""):
        """Assert that a condition is false."""
        if condition:
            raise AssertionError(f"Expected False but got True: {message}")


async def main():
    """Run all tests."""
    test = TestCreateUpdateDelete()

    tests = [
        ("Create single entity", test.test_create_single_entity),
        ("Create multiple entities", test.test_create_multiple_entities),
        ("Update entity", test.test_update_entity),
        ("Partial update", test.test_partial_update),
        ("Delete entity", test.test_delete_entity),
        ("Batch operations", test.test_batch_operations),
        ("Error handling", test.test_error_handling),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        if await test.run_test(test_name, test_func):
            passed += 1
        else:
            failed += 1

    print(f"\n{'='*60}")
    print(f"Test Results: {passed} passed, {failed} failed")
    print(f"{'='*60}")

    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
