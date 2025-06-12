#!/usr/bin/env python3
"""Integration tests for visibility handling (is_hidden)."""

import asyncio
import sys

from base_direct import IntegrationTestBase


class TestVisibility(IntegrationTestBase):
    """Test visibility handling for entities and posts."""

    async def test_create_entity_with_is_hidden(self):
        """Test creating entities with different is_hidden values."""
        # Create a hidden entity
        created = await self.call_tool(
            "create_entities",
            entities=[
                {
                    "entity_type": "character",
                    "name": "Integration Test Hidden Character - DELETE ME",
                    "type": "NPC",
                    "entry": "This is a hidden character.",
                    "is_hidden": True,
                }
            ],
        )

        assert created[0]["success"] is True
        hidden_entity_id = created[0]["entity_id"]
        self.track_entity(hidden_entity_id)

        # Create a visible entity
        created = await self.call_tool(
            "create_entities",
            entities=[
                {
                    "entity_type": "character",
                    "name": "Integration Test Visible Character - DELETE ME",
                    "type": "NPC",
                    "entry": "This is a visible character.",
                    "is_hidden": False,
                }
            ],
        )

        assert created[0]["success"] is True
        visible_entity_id = created[0]["entity_id"]
        self.track_entity(visible_entity_id)

        await self.wait_for_api()

        # Get both entities and verify is_hidden
        results = await self.call_tool(
            "get_entities",
            entity_ids=[hidden_entity_id, visible_entity_id],
            include_posts=False,
        )

        # Find our entities
        hidden_result = None
        visible_result = None
        for result in results:
            if result["entity_id"] == hidden_entity_id:
                hidden_result = result
            elif result["entity_id"] == visible_entity_id:
                visible_result = result

        assert hidden_result is not None, "Hidden entity not found"
        assert visible_result is not None, "Visible entity not found"

        # Verify is_hidden values
        assert (
            hidden_result["is_hidden"] is True
        ), "Hidden entity should have is_hidden=True"
        assert (
            visible_result["is_hidden"] is False
        ), "Visible entity should have is_hidden=False"

    async def test_update_entity_visibility(self):
        """Test updating entity visibility."""
        # Create an entity that starts visible
        created = await self.call_tool(
            "create_entities",
            entities=[
                {
                    "entity_type": "location",
                    "name": "Integration Test Location - DELETE ME",
                    "type": "City",
                    "is_hidden": False,
                }
            ],
        )

        assert created[0]["success"] is True
        entity_id = created[0]["entity_id"]
        self.track_entity(entity_id)

        await self.wait_for_api()

        # Update it to be hidden
        updated = await self.call_tool(
            "update_entities",
            updates=[
                {
                    "entity_id": entity_id,
                    "name": "Integration Test Location - DELETE ME",
                    "is_hidden": True,
                }
            ],
        )

        assert updated[0]["success"] is True

        await self.wait_for_api()

        # Get entity and verify it's now hidden
        results = await self.call_tool(
            "get_entities",
            entity_ids=[entity_id],
            include_posts=False,
        )

        assert results[0]["success"] is True
        assert results[0]["is_hidden"] is True, "Entity should be hidden after update"

        # Update it back to visible
        updated = await self.call_tool(
            "update_entities",
            updates=[
                {
                    "entity_id": entity_id,
                    "name": "Integration Test Location - DELETE ME",
                    "is_hidden": False,
                }
            ],
        )

        assert updated[0]["success"] is True

        await self.wait_for_api()

        # Verify it's visible again
        results = await self.call_tool(
            "get_entities",
            entity_ids=[entity_id],
            include_posts=False,
        )

        assert results[0]["success"] is True
        assert (
            results[0]["is_hidden"] is False
        ), "Entity should be visible after second update"

    async def test_create_post_with_is_hidden(self):
        """Test creating posts with different is_hidden values."""
        # First create an entity to attach posts to
        created = await self.call_tool(
            "create_entities",
            entities=[
                {
                    "entity_type": "organization",
                    "name": "Integration Test Guild - DELETE ME",
                    "type": "Guild",
                }
            ],
        )

        assert created[0]["success"] is True
        entity_id = created[0]["entity_id"]
        self.track_entity(entity_id)

        await self.wait_for_api()

        # Create a hidden post
        post_result = await self.call_tool(
            "create_posts",
            posts=[
                {
                    "entity_id": entity_id,
                    "name": "Secret Guild Meeting Notes",
                    "entry": "These are confidential notes.",
                    "is_hidden": True,
                }
            ],
        )

        assert post_result[0]["success"] is True
        hidden_post_id = post_result[0]["post_id"]

        # Create a visible post
        post_result = await self.call_tool(
            "create_posts",
            posts=[
                {
                    "entity_id": entity_id,
                    "name": "Public Guild Announcement",
                    "entry": "This is a public announcement.",
                    "is_hidden": False,
                }
            ],
        )

        assert post_result[0]["success"] is True
        visible_post_id = post_result[0]["post_id"]

        await self.wait_for_api()

        # Get entity with posts
        results = await self.call_tool(
            "get_entities",
            entity_ids=[entity_id],
            include_posts=True,
        )

        assert results[0]["success"] is True
        posts = results[0].get("posts", [])
        assert len(posts) >= 2, "Should have at least 2 posts"

        # Find our posts
        hidden_post = None
        visible_post = None
        for post in posts:
            if post["id"] == hidden_post_id:
                hidden_post = post
            elif post["id"] == visible_post_id:
                visible_post = post

        assert hidden_post is not None, "Hidden post not found"
        assert visible_post is not None, "Visible post not found"

        # Verify is_hidden values
        assert (
            hidden_post["is_hidden"] is True
        ), "Hidden post should have is_hidden=True"
        assert (
            visible_post["is_hidden"] is False
        ), "Visible post should have is_hidden=False"

    async def test_update_post_visibility(self):
        """Test updating post visibility."""
        # Create an entity
        created = await self.call_tool(
            "create_entities",
            entities=[
                {
                    "entity_type": "quest",
                    "name": "Integration Test Quest - DELETE ME",
                    "type": "Main Quest",
                }
            ],
        )

        assert created[0]["success"] is True
        entity_id = created[0]["entity_id"]
        self.track_entity(entity_id)

        await self.wait_for_api()

        # Create a post that starts visible
        post_result = await self.call_tool(
            "create_posts",
            posts=[
                {
                    "entity_id": entity_id,
                    "name": "Quest Progress",
                    "entry": "Initial progress notes.",
                    "is_hidden": False,
                }
            ],
        )

        assert post_result[0]["success"] is True
        post_id = post_result[0]["post_id"]

        await self.wait_for_api()

        # Update post to be hidden
        update_result = await self.call_tool(
            "update_posts",
            updates=[
                {
                    "entity_id": entity_id,
                    "post_id": post_id,
                    "name": "Quest Progress",
                    "is_hidden": True,
                }
            ],
        )

        assert update_result[0]["success"] is True

        await self.wait_for_api()

        # Get entity with posts and verify visibility
        results = await self.call_tool(
            "get_entities",
            entity_ids=[entity_id],
            include_posts=True,
        )

        assert results[0]["success"] is True
        posts = results[0].get("posts", [])

        # Find our post
        our_post = None
        for post in posts:
            if post["id"] == post_id:
                our_post = post
                break

        assert our_post is not None, "Post not found"
        assert our_post["is_hidden"] is True, "Post should be hidden after update"

    async def test_note_entity_default_hidden(self):
        """Test that note entities default to hidden."""
        # Create a note without specifying is_hidden
        created = await self.call_tool(
            "create_entities",
            entities=[
                {
                    "entity_type": "note",
                    "name": "Integration Test GM Note - DELETE ME",
                    "entry": "This is a GM-only note.",
                }
            ],
        )

        assert created[0]["success"] is True
        entity_id = created[0]["entity_id"]
        self.track_entity(entity_id)

        await self.wait_for_api()

        # Get the note and verify it's hidden by default
        results = await self.call_tool(
            "get_entities",
            entity_ids=[entity_id],
            include_posts=False,
        )

        assert results[0]["success"] is True
        assert results[0]["is_hidden"] is True, "Notes should default to is_hidden=True"

    async def test_find_entities_includes_visibility(self):
        """Test that find_entities returns is_hidden field."""
        # Create a few entities with different visibility
        created = await self.call_tool(
            "create_entities",
            entities=[
                {
                    "entity_type": "creature",
                    "name": "Integration Test Visibility Dragon - DELETE ME",
                    "type": "Dragon",
                    "is_hidden": True,
                },
                {
                    "entity_type": "creature",
                    "name": "Integration Test Visibility Goblin - DELETE ME",
                    "type": "Goblin",
                    "is_hidden": False,
                },
            ],
        )

        # Track for cleanup
        for result in created:
            if result["success"]:
                self.track_entity(result["entity_id"])

        await self.wait_for_api()

        # Find them
        results = await self.call_tool(
            "find_entities",
            name="Integration Test Visibility",
            entity_type="creature",
            include_full=True,
        )

        entities = results["entities"]
        assert len(entities) >= 2, "Should find at least our 2 creatures"

        # Check that is_hidden is included
        for entity in entities:
            if "Dragon" in entity.get("name", ""):
                assert entity["is_hidden"] is True, "Dragon should be hidden"
            elif "Goblin" in entity.get("name", ""):
                assert entity["is_hidden"] is False, "Goblin should be visible"


async def main():
    """Run all tests."""
    test = TestVisibility()

    tests = [
        ("Create entity with is_hidden", test.test_create_entity_with_is_hidden),
        ("Update entity visibility", test.test_update_entity_visibility),
        ("Create post with is_hidden", test.test_create_post_with_is_hidden),
        ("Update post visibility", test.test_update_post_visibility),
        ("Note entity default hidden", test.test_note_entity_default_hidden),
        (
            "Find entities includes visibility",
            test.test_find_entities_includes_visibility,
        ),
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
