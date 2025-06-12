#!/usr/bin/env python3
"""Integration tests for the find_entities tool."""

import asyncio
import sys

from base_direct import IntegrationTestBase


class TestFindEntities(IntegrationTestBase):
    """Test the find_entities tool with real Kanka API."""

    async def test_find_all_entity_types(self):
        """Test finding entities without specifying type."""
        # First create some test entities
        created = await self.call_tool(
            "create_entities",
            entities=[
                {
                    "entity_type": "character",
                    "name": "Integration Test Character - DELETE ME",
                    "type": "Test NPC",
                },
                {
                    "entity_type": "location",
                    "name": "Integration Test Location - DELETE ME",
                    "type": "Test City",
                },
            ],
        )

        # Track for cleanup
        for result in created:
            if result["success"] and result["entity_id"]:
                self.track_entity(result["entity_id"])

        await self.wait_for_api()

        # Now search for our test entities
        response = await self.call_tool(
            "find_entities", query="Integration Test", include_full=False, limit=10
        )

        # Check response structure
        self.assert_in("entities", response)
        self.assert_in("sync_info", response)

        results = response["entities"]

        # Should find at least our 2 entities
        self.assert_greater_than(len(results), 1, "Should find multiple entities")

        # Check structure of minimal results
        for result in results:
            self.assert_in("entity_id", result)
            self.assert_in("name", result)
            self.assert_in("entity_type", result)

    async def test_find_by_entity_type(self):
        """Test finding entities filtered by type."""
        # Create a test character
        created = await self.call_tool(
            "create_entities",
            entities=[
                {
                    "entity_type": "character",
                    "name": "Integration Test Fighter - DELETE ME",
                    "type": "Warrior",
                    "entry": "A brave warrior from the integration tests.",
                    "tags": ["test", "warrior"],
                }
            ],
        )

        entity_id = None
        if created[0]["success"]:
            entity_id = created[0]["entity_id"]
            self.track_entity(entity_id)

        await self.wait_for_api()

        # Search for characters only
        response = await self.call_tool(
            "find_entities",
            query="Integration Test Fighter",
            entity_type="character",
            include_full=True,
        )

        # Check response structure
        self.assert_in("entities", response)
        self.assert_in("sync_info", response)

        results = response["entities"]

        # Should find our character
        self.assert_greater_than(len(results), 0, "Should find at least one character")

        # Find our specific character
        our_char = None
        for result in results:
            if result.get("entity_id") == entity_id:
                our_char = result
                break

        self.assert_not_none(our_char, "Should find our created character")

        # Check full details are included
        self.assert_equal(our_char["name"], "Integration Test Fighter - DELETE ME")
        self.assert_equal(our_char["type"], "Warrior")
        self.assert_in("brave warrior", our_char.get("entry", ""))
        self.assert_in("test", our_char.get("tags", []))
        self.assert_in("warrior", our_char.get("tags", []))

    async def test_find_with_name_filter(self):
        """Test finding entities with name filtering."""
        # Create test entities with similar names
        created = await self.call_tool(
            "create_entities",
            entities=[
                {
                    "entity_type": "location",
                    "name": "Integration Test Castle - DELETE ME",
                    "type": "Fortress",
                },
                {
                    "entity_type": "location",
                    "name": "Integration Test Castle Dungeon - DELETE ME",
                    "type": "Dungeon",
                },
                {
                    "entity_type": "location",
                    "name": "Integration Test Tower - DELETE ME",
                    "type": "Tower",
                },
            ],
        )

        # Track for cleanup
        for result in created:
            if result["success"] and result["entity_id"]:
                self.track_entity(result["entity_id"])

        await self.wait_for_api()

        # Search with partial name filter (default)
        response = await self.call_tool(
            "find_entities",
            entity_type="location",
            name="Test Castle",  # Partial match
            include_full=True,
        )

        results = response["entities"]

        # Should find the castle
        found_names = [r["name"] for r in results]
        self.assert_in("Integration Test Castle - DELETE ME", found_names)

        # Search with exact name filter
        response = await self.call_tool(
            "find_entities",
            entity_type="location",
            name="Integration Test Castle - DELETE ME",
            name_exact=True,
            include_full=True,
        )

        results = response["entities"]

        # Should find exactly one
        self.assert_equal(len(results), 1, "Should find exactly one castle")
        self.assert_equal(results[0]["name"], "Integration Test Castle - DELETE ME")

        # Search with fuzzy name filter
        response = await self.call_tool(
            "find_entities",
            entity_type="location",
            name="Integration Test Castel",  # Typo
            name_fuzzy=True,
            include_full=False,
        )

        results = response["entities"]

        # Should find the castle despite typo
        found_names = [r["name"] for r in results]
        self.assert_in("Integration Test Castle - DELETE ME", found_names)

    async def test_find_with_type_filter(self):
        """Test finding entities filtered by Type field."""
        # Create entities with different Type values
        created = await self.call_tool(
            "create_entities",
            entities=[
                {
                    "entity_type": "creature",
                    "name": "Integration Test Dragon - DELETE ME",
                    "type": "Dragon",
                },
                {
                    "entity_type": "creature",
                    "name": "Integration Test Goblin - DELETE ME",
                    "type": "Goblin",
                },
            ],
        )

        # Track for cleanup
        for result in created:
            if result["success"] and result["entity_id"]:
                self.track_entity(result["entity_id"])

        await self.wait_for_api()

        # Find only dragons
        response = await self.call_tool(
            "find_entities", entity_type="creature", type="Dragon", include_full=True
        )

        results = response["entities"]

        # Check results
        dragon_found = False
        goblin_found = False
        for result in results:
            if "Integration Test Dragon" in result["name"]:
                dragon_found = True
                self.assert_equal(result["type"], "Dragon")
            if "Integration Test Goblin" in result["name"]:
                goblin_found = True

        self.assert_true(dragon_found, "Should find the dragon")
        self.assert_true(not goblin_found, "Should not find the goblin")

    async def test_find_with_tag_filter(self):
        """Test finding entities filtered by tags."""
        # Create entities with tags
        created = await self.call_tool(
            "create_entities",
            entities=[
                {
                    "entity_type": "character",
                    "name": "Integration Test Hero - DELETE ME",
                    "tags": ["hero", "warrior", "test"],
                },
                {
                    "entity_type": "character",
                    "name": "Integration Test Villain - DELETE ME",
                    "tags": ["villain", "wizard", "test"],
                },
                {
                    "entity_type": "character",
                    "name": "Integration Test Sidekick - DELETE ME",
                    "tags": ["hero", "rogue", "test"],
                },
            ],
        )

        # Track for cleanup
        for result in created:
            if result["success"] and result["entity_id"]:
                self.track_entity(result["entity_id"])

        await self.wait_for_api()

        # Find entities with both "hero" and "test" tags
        response = await self.call_tool(
            "find_entities",
            entity_type="character",
            tags=["hero", "test"],
            include_full=True,
        )

        results = response["entities"]

        # Should find Hero and Sidekick but not Villain
        found_names = [r["name"] for r in results if "Integration Test" in r["name"]]
        self.assert_in("Integration Test Hero - DELETE ME", found_names)
        self.assert_in("Integration Test Sidekick - DELETE ME", found_names)
        self.assert_true("Integration Test Villain - DELETE ME" not in found_names)

    async def test_find_with_pagination(self):
        """Test pagination in find_entities."""
        # Create several entities
        entities_to_create = []
        for i in range(15):
            entities_to_create.append(
                {
                    "entity_type": "note",
                    "name": f"Integration Test Note {i:02d} - DELETE ME",
                    "is_hidden": True,
                }
            )

        created = await self.call_tool("create_entities", entities=entities_to_create)

        # Track for cleanup
        for result in created:
            if result["success"] and result["entity_id"]:
                self.track_entity(result["entity_id"])

        await self.wait_for_api()

        # Get first page with limit 5
        response1 = await self.call_tool(
            "find_entities",
            entity_type="note",
            name="Integration Test Note",
            name_fuzzy=True,
            page=1,
            limit=5,
            include_full=False,
        )

        # Get second page
        response2 = await self.call_tool(
            "find_entities",
            entity_type="note",
            name="Integration Test Note",
            name_fuzzy=True,
            page=2,
            limit=5,
            include_full=False,
        )

        page1 = response1["entities"]
        page2 = response2["entities"]

        # Check we got different results
        page1_ids = [r["entity_id"] for r in page1]
        page2_ids = [r["entity_id"] for r in page2]

        # No overlap between pages
        for entity_id in page1_ids:
            self.assert_true(entity_id not in page2_ids, "Pages should not overlap")

        # Both should have results
        self.assert_greater_than(len(page1), 0, "Page 1 should have results")
        self.assert_greater_than(len(page2), 0, "Page 2 should have results")

    async def test_find_with_content_search(self):
        """Test searching content - MCP server implements client-side content search."""
        # Create entities with search terms in different places
        created = await self.call_tool(
            "create_entities",
            entities=[
                {
                    "entity_type": "journal",
                    "name": "Integration Test Ancient History - DELETE ME",
                    "entry": "The ancient artifact was hidden in the **forgotten temple**.",
                },
                {
                    "entity_type": "journal",
                    "name": "Integration Test Travel Log - DELETE ME",
                    "entry": "We traveled through the forest and found a mysterious artifact.",
                },
                {
                    "entity_type": "character",
                    "name": "Integration Test Explorer - DELETE ME",
                    "entry": "An archaeologist specializing in ancient relics.",
                },
            ],
        )

        # Track for cleanup
        for result in created:
            if result["success"] and result["entity_id"]:
                self.track_entity(result["entity_id"])

        await self.wait_for_api()

        # Search for "artifact" - should find both journals (one in name, one in content)
        response = await self.call_tool(
            "find_entities", query="artifact", include_full=True
        )

        results = response["entities"]

        # Should find at least the two journals with "artifact"
        artifact_count = 0
        found_in_content = False

        for result in results:
            if (
                "artifact" in result.get("name", "").lower()
                or "artifact" in result.get("entry", "").lower()
            ):
                artifact_count += 1
                # Check if found in content vs name
                if (
                    "artifact" in result.get("entry", "").lower()
                    and "artifact" not in result.get("name", "").lower()
                ):
                    found_in_content = True

        self.assert_greater_than(
            artifact_count, 1, "Should find multiple entities with 'artifact'"
        )
        self.assert_true(
            found_in_content, "Should find entities with 'artifact' in content"
        )

        # Search for "archaeologist" - only in character's content
        response = await self.call_tool(
            "find_entities",
            query="archaeologist",
            entity_type="character",
            include_full=True,
        )

        results = response["entities"]

        archaeologist_found = False
        for result in results:
            if "archaeologist" in result.get("entry", "").lower():
                archaeologist_found = True
                self.assert_in("Explorer", result["name"])

        self.assert_true(
            archaeologist_found, "Should find character with 'archaeologist' in content"
        )


async def main():
    """Run all tests."""
    test = TestFindEntities()

    tests = [
        ("Find all entity types", test.test_find_all_entity_types),
        ("Find by entity type", test.test_find_by_entity_type),
        ("Find with name filter", test.test_find_with_name_filter),
        ("Find with type filter", test.test_find_with_type_filter),
        ("Find with tag filter", test.test_find_with_tag_filter),
        ("Find with pagination", test.test_find_with_pagination),
        ("Find with content search", test.test_find_with_content_search),
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
