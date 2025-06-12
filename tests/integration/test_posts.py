#!/usr/bin/env python3
"""Integration tests for post operations."""

import asyncio
import sys

from base_direct import IntegrationTestBase


class TestPosts(IntegrationTestBase):
    """Test post operations with real Kanka API."""

    async def test_create_post(self):
        """Test creating a post on an entity."""
        # First create an entity
        entity_result = await self.call_tool(
            "create_entities",
            entities=[
                {
                    "entity_type": "character",
                    "name": "Integration Test Character with Posts - DELETE ME",
                    "type": "NPC",
                }
            ],
        )

        self.assert_true(entity_result[0]["success"])
        entity_id = entity_result[0]["entity_id"]
        self.track_entity(entity_id)

        await self.wait_for_api()

        # Create a post on the entity
        post_result = await self.call_tool(
            "create_posts",
            posts=[
                {
                    "entity_id": entity_id,
                    "name": "Background Story",
                    "entry": "# Early Life\n\nBorn in a small **village**, this character had humble beginnings.\n\nThey met [entity:123|The Mentor] who changed their life.",
                    "is_hidden": False,
                }
            ],
        )

        self.assert_equal(len(post_result), 1)
        self.assert_true(
            post_result[0]["success"],
            f"Post creation failed: {post_result[0].get('error')}",
        )
        self.assert_not_none(post_result[0]["post_id"])

        post_id = post_result[0]["post_id"]

        await self.wait_for_api()

        # Verify by getting entity with posts
        get_result = await self.call_tool(
            "get_entities", entity_ids=[entity_id], include_posts=True
        )

        self.assert_true(get_result[0]["success"])
        entity = get_result[0]

        self.assert_in("posts", entity)
        self.assert_greater_than(len(entity["posts"]), 0)

        # Find our post
        our_post = None
        for post in entity["posts"]:
            if post["id"] == post_id:
                our_post = post
                break

        self.assert_not_none(our_post, "Should find our created post")
        self.assert_equal(our_post["name"], "Background Story")
        self.assert_in("Early Life", our_post["entry"])
        self.assert_in("small **village**", our_post["entry"])
        self.assert_in(
            "[entity:123|The Mentor]", our_post["entry"]
        )  # Mention preserved

    async def test_create_multiple_posts(self):
        """Test creating multiple posts on different entities."""
        # Create two entities
        entities_result = await self.call_tool(
            "create_entities",
            entities=[
                {
                    "entity_type": "location",
                    "name": "Integration Test Castle - DELETE ME",
                },
                {
                    "entity_type": "quest",
                    "name": "Integration Test Quest - DELETE ME",
                },
            ],
        )

        entity1_id = entities_result[0]["entity_id"]
        entity2_id = entities_result[1]["entity_id"]
        self.track_entity(entity1_id)
        self.track_entity(entity2_id)

        await self.wait_for_api()

        # Create posts on both entities
        posts_result = await self.call_tool(
            "create_posts",
            posts=[
                {
                    "entity_id": entity1_id,
                    "name": "Castle History",
                    "entry": "Built 500 years ago...",
                    "is_hidden": True,
                },
                {
                    "entity_id": entity2_id,
                    "name": "Quest Objectives",
                    "entry": "1. Find the artifact\n2. Defeat the boss",
                    "is_hidden": False,
                },
            ],
        )

        self.assert_equal(len(posts_result), 2)
        for r in posts_result:
            self.assert_true(r["success"], f"Post creation failed: {r.get('error')}")

    async def test_update_post(self):
        """Test updating an existing post."""
        # Create entity and post
        entity_result = await self.call_tool(
            "create_entities",
            entities=[
                {
                    "entity_type": "journal",
                    "name": "Integration Test Journal - DELETE ME",
                }
            ],
        )

        entity_id = entity_result[0]["entity_id"]
        self.track_entity(entity_id)

        post_result = await self.call_tool(
            "create_posts",
            posts=[
                {
                    "entity_id": entity_id,
                    "name": "Day 1",
                    "entry": "Started the journey...",
                    "is_hidden": False,
                }
            ],
        )

        post_id = post_result[0]["post_id"]

        await self.wait_for_api()

        # Update the post
        update_result = await self.call_tool(
            "update_posts",
            updates=[
                {
                    "entity_id": entity_id,
                    "post_id": post_id,
                    "name": "Day 1 - Updated",
                    "entry": "# Journey Begins\n\nStarted the journey with **great excitement**!",
                    "is_hidden": True,
                }
            ],
        )

        self.assert_true(update_result[0]["success"])

        await self.wait_for_api()

        # Verify the update
        get_result = await self.call_tool(
            "get_entities", entity_ids=[entity_id], include_posts=True
        )

        posts = get_result[0]["posts"]
        updated_post = next(p for p in posts if p["id"] == post_id)

        self.assert_equal(updated_post["name"], "Day 1 - Updated")
        self.assert_in("Journey Begins", updated_post["entry"])
        self.assert_in("**great excitement**", updated_post["entry"])
        self.assert_equal(updated_post["is_hidden"], True)

    async def test_delete_post(self):
        """Test deleting a post."""
        # Create entity with two posts
        entity_result = await self.call_tool(
            "create_entities",
            entities=[
                {
                    "entity_type": "organization",
                    "name": "Integration Test Guild - DELETE ME",
                }
            ],
        )

        entity_id = entity_result[0]["entity_id"]
        self.track_entity(entity_id)

        posts_result = await self.call_tool(
            "create_posts",
            posts=[
                {
                    "entity_id": entity_id,
                    "name": "Guild Rules",
                    "entry": "1. Be respectful\n2. Pay your dues",
                },
                {
                    "entity_id": entity_id,
                    "name": "Guild History",
                    "entry": "Founded 100 years ago...",
                },
            ],
        )

        post1_id = posts_result[0]["post_id"]
        post2_id = posts_result[1]["post_id"]

        await self.wait_for_api()

        # Delete the first post
        delete_result = await self.call_tool(
            "delete_posts",
            deletions=[
                {
                    "entity_id": entity_id,
                    "post_id": post1_id,
                }
            ],
        )

        self.assert_true(delete_result[0]["success"])

        await self.wait_for_api()

        # Verify deletion
        get_result = await self.call_tool(
            "get_entities", entity_ids=[entity_id], include_posts=True
        )

        posts = get_result[0]["posts"]
        post_ids = [p["id"] for p in posts]

        self.assert_true(post1_id not in post_ids, "Deleted post should not exist")
        self.assert_true(post2_id in post_ids, "Other post should still exist")

    async def test_post_error_handling(self):
        """Test error handling for post operations."""
        # Try to create post on non-existent entity
        result = await self.call_tool(
            "create_posts",
            posts=[
                {
                    "entity_id": 9999999,
                    "name": "Won't work",
                    "entry": "This should fail",
                }
            ],
        )

        self.assert_false(result[0]["success"])
        self.assert_not_none(result[0]["error"])

        # Create entity for other tests
        entity_result = await self.call_tool(
            "create_entities",
            entities=[
                {
                    "entity_type": "race",
                    "name": "Integration Test Race - DELETE ME",
                }
            ],
        )

        entity_id = entity_result[0]["entity_id"]
        self.track_entity(entity_id)

        # Try to update non-existent post
        update_result = await self.call_tool(
            "update_posts",
            updates=[
                {
                    "entity_id": entity_id,
                    "post_id": 9999999,
                    "name": "Won't work",
                }
            ],
        )

        self.assert_false(update_result[0]["success"])

        # Try to delete non-existent post
        delete_result = await self.call_tool(
            "delete_posts",
            deletions=[
                {
                    "entity_id": entity_id,
                    "post_id": 9999999,
                }
            ],
        )

        self.assert_false(delete_result[0]["success"])

    async def test_posts_with_private_entities(self):
        """Test posts on private entities."""
        # Create a private note
        entity_result = await self.call_tool(
            "create_entities",
            entities=[
                {
                    "entity_type": "note",
                    "name": "Integration Test Secret Note - DELETE ME",
                    "is_hidden": True,
                }
            ],
        )

        entity_id = entity_result[0]["entity_id"]
        self.track_entity(entity_id)

        # Create both public and private posts
        posts_result = await self.call_tool(
            "create_posts",
            posts=[
                {
                    "entity_id": entity_id,
                    "name": "Public Information",
                    "entry": "This can be seen by players",
                    "is_hidden": False,
                },
                {
                    "entity_id": entity_id,
                    "name": "Secret Information",
                    "entry": "This is for GMs only",
                    "is_hidden": True,
                },
            ],
        )

        for r in posts_result:
            self.assert_true(r["success"])

        await self.wait_for_api()

        # Verify both posts exist
        get_result = await self.call_tool(
            "get_entities", entity_ids=[entity_id], include_posts=True
        )

        entity = get_result[0]
        self.assert_true(entity["is_hidden"], "Entity should be private")
        self.assert_equal(len(entity["posts"]), 2, "Should have both posts")

        # Check privacy settings
        for post in entity["posts"]:
            if post["name"] == "Public Information":
                self.assert_false(post["is_hidden"])
            elif post["name"] == "Secret Information":
                self.assert_true(post["is_hidden"])

    def assert_false(self, condition: bool, message: str = ""):
        """Assert that a condition is false."""
        if condition:
            raise AssertionError(f"Expected False but got True: {message}")


async def main():
    """Run all tests."""
    test = TestPosts()

    tests = [
        ("Create post", test.test_create_post),
        ("Create multiple posts", test.test_create_multiple_posts),
        ("Update post", test.test_update_post),
        ("Delete post", test.test_delete_post),
        ("Post error handling", test.test_post_error_handling),
        ("Posts with private entities", test.test_posts_with_private_entities),
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
