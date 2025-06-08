#!/usr/bin/env python3
"""Integration tests for sync and timestamp features."""

import asyncio
import sys
from datetime import datetime, timezone

# Handle both direct execution and import scenarios
if __name__ == "__main__":
    from base_direct import IntegrationTestBase
else:
    from .base_direct import IntegrationTestBase


class TestSyncFeatures(IntegrationTestBase):
    """Test sync and timestamp features against real Kanka API."""

    async def test_timestamps_in_responses(self):
        """Test that entities include timestamps in responses."""
        # Create a test entity
        result = await self.call_tool(
            "create_entities",
            entities=[
                {
                    "entity_type": "character",
                    "name": "Integration Test - DELETE ME - Timestamp Test Character",
                    "type": "NPC",
                    "entry": "Testing timestamps",
                }
            ],
        )

        self.assert_equal(len(result), 1)
        self.assert_true(
            result[0]["success"], f"Create failed: {result[0].get('error')}"
        )

        entity_id = result[0]["entity_id"]
        self.track_entity(entity_id)

        # Find the entity
        find_result = await self.call_tool(
            "find_entities",
            entity_type="character",
            name="Integration Test - DELETE ME - Timestamp Test Character",
        )

        assert "entities" in find_result
        assert "sync_info" in find_result

        entities = find_result["entities"]
        assert len(entities) >= 1

        # Find our entity
        our_entity = None
        for entity in entities:
            if (
                entity["name"]
                == "Integration Test - DELETE ME - Timestamp Test Character"
            ):
                our_entity = entity
                break

        assert our_entity is not None
        assert "created_at" in our_entity
        assert "updated_at" in our_entity

        # Timestamps should be ISO format strings
        assert isinstance(our_entity["created_at"], str)
        assert isinstance(our_entity["updated_at"], str)

        # Parse to verify format
        created_at = datetime.fromisoformat(
            our_entity["created_at"].replace("Z", "+00:00")
        )
        updated_at = datetime.fromisoformat(
            our_entity["updated_at"].replace("Z", "+00:00")
        )

        # Timestamps should be recent (within last minute)
        now = datetime.now(timezone.utc)
        assert (now - created_at).total_seconds() < 60
        assert (now - updated_at).total_seconds() < 60

    async def test_sync_info_metadata(self):
        """Test that sync_info metadata is correct."""
        # Create multiple test entities
        entity_ids = []
        for i in range(3):
            result = await self.call_tool(
                "create_entities",
                entities=[
                    {
                        "entity_type": "location",
                        "name": f"Integration Test - DELETE ME - Sync Test Location {i}",
                        "type": "City",
                    }
                ],
            )
            self.assert_true(result[0]["success"])
            entity_ids.append(result[0]["entity_id"])
            self.track_entity(result[0]["entity_id"])
            await self.wait_for_api()

        # Find entities with pagination
        find_result = await self.call_tool(
            "find_entities",
            entity_type="location",
            name="Integration Test - DELETE ME - Sync Test Location",
            limit=2,  # Get only 2 of 3
        )

        sync_info = find_result["sync_info"]

        # Check sync_info fields
        assert "request_timestamp" in sync_info
        assert "newest_updated_at" in sync_info

        assert sync_info["total_count"] >= 3  # At least our 3 entities
        assert sync_info["returned_count"] == 2  # Limited to 2

        # Request timestamp should be recent
        request_time = datetime.fromisoformat(
            sync_info["request_timestamp"].replace("Z", "+00:00")
        )
        now = datetime.now(timezone.utc)
        assert (now - request_time).total_seconds() < 5

    async def test_last_synced_parameter(self):
        """Test filtering by last_synced timestamp."""
        # Create an entity
        result = await self.call_tool(
            "create_entities",
            entities=[
                {
                    "entity_type": "note",
                    "name": "Integration Test - DELETE ME - Old Note",
                    "entry": "Created first",
                }
            ],
        )
        self.assert_true(result[0]["success"])
        entity_id = result[0]["entity_id"]
        self.track_entity(entity_id)

        # Wait a moment
        await self.wait_for_api()

        # Get current timestamp for sync point
        sync_point = datetime.now(timezone.utc)
        sync_timestamp = sync_point.isoformat()

        # Wait a bit more
        await asyncio.sleep(2)

        # Update the entity (this should change updated_at)
        update_result = await self.call_tool(
            "update_entities",
            updates=[
                {
                    "entity_id": entity_id,
                    "name": "Integration Test - DELETE ME - Old Note",  # Name required
                    "entry": "Updated content",
                }
            ],
        )
        self.assert_true(update_result[0]["success"])

        # Create a new entity after sync point
        result2 = await self.call_tool(
            "create_entities",
            entities=[
                {
                    "entity_type": "note",
                    "name": "Integration Test - DELETE ME - New Note",
                    "entry": "Created after sync",
                }
            ],
        )
        self.assert_true(result2[0]["success"])
        self.track_entity(result2[0]["entity_id"])

        # Find entities modified after sync point
        # Don't use name filter with last_synced - it would require exact match
        find_result = await self.call_tool(
            "find_entities",
            entity_type="note",
            last_synced=sync_timestamp,
        )

        entities = find_result["entities"]

        # Should include both updated and newly created entities
        entity_names = [e["name"] for e in entities]
        assert (
            "Integration Test - DELETE ME - Old Note" in entity_names
        )  # Updated after sync
        assert (
            "Integration Test - DELETE ME - New Note" in entity_names
        )  # Created after sync

        # Verify all returned entities have updated_at after sync point
        for entity in entities:
            if entity["name"].startswith("Integration Test - DELETE ME"):
                updated_at = datetime.fromisoformat(
                    entity["updated_at"].replace("Z", "+00:00")
                )
                assert updated_at > sync_point

    async def test_check_entity_updates(self):
        """Test the check_entity_updates functionality."""
        # Create test entities
        entity_ids = []
        for i in range(3):
            result = await self.call_tool(
                "create_entities",
                entities=[
                    {
                        "entity_type": "creature",
                        "name": f"Integration Test - DELETE ME - Creature {i}",
                        "type": "Beast",
                    }
                ],
            )
            self.assert_true(result[0]["success"])
            entity_ids.append(result[0]["entity_id"])
            self.track_entity(result[0]["entity_id"])
            await self.wait_for_api()

        # Get sync timestamp
        sync_timestamp = datetime.now(timezone.utc).isoformat()

        # Wait and update one entity
        await asyncio.sleep(2)
        update_result = await self.call_tool(
            "update_entities",
            updates=[
                {
                    "entity_id": entity_ids[1],
                    "name": "Integration Test - DELETE ME - Creature 1",
                    "entry": "Modified content",
                }
            ],
        )
        self.assert_true(update_result[0]["success"])

        # Delete one entity
        delete_result = await self.call_tool(
            "delete_entities",
            entity_ids=[entity_ids[2]],
        )
        self.assert_true(delete_result[0]["success"])

        # Check for updates
        check_result = await self.call_tool(
            "check_entity_updates",
            entity_ids=entity_ids,
            last_synced=sync_timestamp,
        )

        # Verify results
        assert entity_ids[1] in check_result["modified_entity_ids"]  # Updated
        assert entity_ids[0] not in check_result["modified_entity_ids"]  # Not updated
        assert entity_ids[2] in check_result["deleted_entity_ids"]  # Deleted
        assert "check_timestamp" in check_result

    async def test_sync_with_no_changes(self):
        """Test sync when no entities have changed."""
        # Create an entity
        result = await self.call_tool(
            "create_entities",
            entities=[
                {
                    "entity_type": "race",
                    "name": "Integration Test - DELETE ME - Unchanged Race",
                    "type": "Humanoid",
                }
            ],
        )
        self.assert_true(result[0]["success"])
        entity_id = result[0]["entity_id"]
        self.track_entity(entity_id)

        # Wait to ensure timestamp difference
        await asyncio.sleep(2)

        # Get sync point after creation
        sync_timestamp = datetime.now(timezone.utc).isoformat()

        # Find entities - should return empty since nothing changed after sync
        find_result = await self.call_tool(
            "find_entities",
            entity_type="race",
            last_synced=sync_timestamp,
        )

        # Check that our entity is not in results
        entity_names = [e["name"] for e in find_result["entities"]]
        assert "Integration Test - DELETE ME - Unchanged Race" not in entity_names

    async def test_sync_info_newest_timestamp(self):
        """Test that sync_info correctly identifies newest updated_at."""
        # Create entities with different update times
        entity_ids = []

        # Create first entity
        result1 = await self.call_tool(
            "create_entities",
            entities=[
                {
                    "entity_type": "quest",
                    "name": "Integration Test - DELETE ME - Quest 1",
                }
            ],
        )
        self.assert_true(result1[0]["success"])
        entity_ids.append(result1[0]["entity_id"])
        self.track_entity(result1[0]["entity_id"])

        # Wait and create second entity
        await asyncio.sleep(2)
        result2 = await self.call_tool(
            "create_entities",
            entities=[
                {
                    "entity_type": "quest",
                    "name": "Integration Test - DELETE ME - Quest 2",
                }
            ],
        )
        self.assert_true(result2[0]["success"])
        entity_ids.append(result2[0]["entity_id"])
        self.track_entity(result2[0]["entity_id"])

        # Wait and update first entity (making it newest)
        await asyncio.sleep(2)
        update_result = await self.call_tool(
            "update_entities",
            updates=[
                {
                    "entity_id": entity_ids[0],
                    "name": "Integration Test - DELETE ME - Quest 1",
                    "entry": "Updated to be newest",
                }
            ],
        )
        self.assert_true(update_result[0]["success"])

        # Get all test quests
        find_result = await self.call_tool(
            "find_entities",
            entity_type="quest",
            name="Integration Test - DELETE ME - Quest",
        )

        # Find the updated entity's timestamp
        updated_entity = None
        for entity in find_result["entities"]:
            if entity["entity_id"] == entity_ids[0]:
                updated_entity = entity
                break

        assert updated_entity is not None

        # sync_info newest_updated_at should match the updated entity
        assert (
            find_result["sync_info"]["newest_updated_at"]
            == updated_entity["updated_at"]
        )


async def main():
    """Run all tests."""
    test = TestSyncFeatures()

    tests = [
        ("Timestamps in responses", test.test_timestamps_in_responses),
        ("Sync info metadata", test.test_sync_info_metadata),
        ("Last synced parameter", test.test_last_synced_parameter),
        ("Check entity updates", test.test_check_entity_updates),
        ("Sync with no changes", test.test_sync_with_no_changes),
        ("Sync info newest timestamp", test.test_sync_info_newest_timestamp),
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
