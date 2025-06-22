"""Integration tests for HTML embed preservation functionality."""

import pytest
from base_direct import IntegrationTestBase


class TestEmbedPreservation(IntegrationTestBase):
    """Test that HTML embeds are preserved when creating and retrieving entities."""

    @pytest.mark.asyncio
    async def test_create_entity_with_youtube_embed(self):
        """Test creating an entity with a YouTube embed preserves the HTML."""
        # Create a character with a YouTube embed in the entry
        character_data = {
            "entity_type": "character",
            "name": "Integration Test - DELETE ME - Character with Video",
            "type": "NPC",
            "entry": """# Character Background

This character appears in the following video:

<iframe width="560" height="315" src="https://www.youtube.com/embed/dQw4w9WgXcQ"
        title="YouTube video player" frameborder="0"
        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
        allowfullscreen></iframe>

They are known for their legendary deeds.""",
        }

        result = await self.call_tool("create_entities", entities=[character_data])
        assert len(result) == 1
        created = result[0]
        assert created["success"] is True
        entity_id = created["entity_id"]
        self.track_entity(entity_id)

        # Retrieve the entity to verify the embed is preserved
        get_result = await self.call_tool("get_entities", entity_ids=[entity_id])
        assert len(get_result) == 1
        entity = get_result[0]

        # Check that the YouTube embed is preserved in the entry
        print(f"DEBUG: Entity entry content:\n{entity['entry']}")
        assert "https://www.youtube.com/embed/dQw4w9WgXcQ" in entity["entry"]
        assert "<iframe" in entity["entry"]
        # Check for the closing tag more flexibly
        assert "</iframe>" in entity["entry"]
        assert "Character Background" in entity["entry"]

    @pytest.mark.asyncio
    async def test_create_entity_with_multiple_iframe_embeds(self):
        """Test creating an entity with multiple iframe embeds."""
        location_data = {
            "entity_type": "location",
            "name": "Integration Test - DELETE ME - Media Gallery",
            "type": "Library",
            "entry": """# The Media Gallery

This location contains various embedded content:

## Interactive Map
<iframe src="https://www.example.com/map" width="600" height="400"></iframe>

## Video Tour
<iframe width="560" height="315" src="https://www.youtube.com/embed/tour123"></iframe>

## Virtual Museum
<iframe src="https://museum.example.com/virtual-tour" width="800" height="600" frameborder="0"></iframe>

Visit the gallery to experience these artifacts firsthand.""",
        }

        result = await self.call_tool("create_entities", entities=[location_data])
        assert len(result) == 1
        created = result[0]
        assert created["success"] is True
        entity_id = created["entity_id"]
        self.track_entity(entity_id)

        # Retrieve the entity
        get_result = await self.call_tool("get_entities", entity_ids=[entity_id])
        assert len(get_result) == 1
        entity = get_result[0]

        # Verify all iframe embeds are preserved
        print(f"DEBUG: Entity entry content:\n{entity['entry']}")
        assert '<iframe src="https://www.example.com/map"' in entity["entry"]
        assert "https://www.youtube.com/embed/tour123" in entity["entry"]
        assert "https://museum.example.com/virtual-tour" in entity["entry"]
        assert entity["entry"].count("<iframe") == 3  # Should have 3 iframes

    @pytest.mark.asyncio
    async def test_update_entity_preserves_embeds(self):
        """Test that updating an entity preserves existing embeds."""
        # First create an entity with an embed
        quest_data = {
            "entity_type": "quest",
            "name": "Integration Test - DELETE ME - Video Quest",
            "entry": """Watch this tutorial:

<iframe src="https://youtube.com/embed/tutorial123"></iframe>

Then proceed to the next step.""",
        }

        create_result = await self.call_tool("create_entities", entities=[quest_data])
        entity_id = create_result[0]["entity_id"]
        self.track_entity(entity_id)

        # Update the entity with additional content
        update_data = {
            "entity_id": entity_id,
            "name": "Integration Test - DELETE ME - Video Quest",
            "entry": """Watch this tutorial:

<iframe src="https://youtube.com/embed/tutorial123"></iframe>

Then proceed to the next step.

## Update: New Information

Here's an additional resource:

<iframe src="https://vimeo.com/video/456789"></iframe>

Good luck!""",
        }

        update_result = await self.call_tool("update_entities", updates=[update_data])
        print(f"DEBUG: Update result: {update_result}")
        assert len(update_result) > 0
        assert update_result[0]["success"] is True

        # Verify both embeds are preserved
        get_result = await self.call_tool("get_entities", entity_ids=[entity_id])
        entity = get_result[0]

        assert "https://youtube.com/embed/tutorial123" in entity["entry"]
        assert "https://vimeo.com/video/456789" in entity["entry"]
        assert entity["entry"].count("<iframe") == 2

    @pytest.mark.asyncio
    async def test_embeds_with_entity_mentions(self):
        """Test that embeds and entity mentions work together."""
        # Create a referenced entity first
        ref_result = await self.call_tool(
            "create_entities",
            entities=[
                {
                    "entity_type": "character",
                    "name": "Integration Test - DELETE ME - Video Creator",
                }
            ],
        )
        ref_entity_id = ref_result[0]["entity_id"]
        self.track_entity(ref_entity_id)

        # Create entity with both embeds and mentions
        note_data = {
            "entity_type": "note",
            "name": "Integration Test - DELETE ME - Media Note",
            "entry": f"""# Media Collection

Created by [entity:{ref_entity_id}|the Video Creator].

## Featured Video

<iframe width="560" height="315" src="https://www.youtube.com/embed/test123"></iframe>

This video was recorded at [entity:99999|Unknown Location] and features
[entity:{ref_entity_id}] as the narrator.

## Additional Resources

<iframe src="https://player.vimeo.com/video/987654" width="640" height="360"></iframe>""",
        }

        result = await self.call_tool("create_entities", entities=[note_data])
        entity_id = result[0]["entity_id"]
        self.track_entity(entity_id)

        # Verify both embeds and mentions are preserved
        get_result = await self.call_tool("get_entities", entity_ids=[entity_id])
        entity = get_result[0]

        # Check embeds
        print(f"DEBUG: Entity entry content:\n{entity['entry']}")
        assert "https://www.youtube.com/embed/test123" in entity["entry"]
        assert "https://player.vimeo.com/video/987654" in entity["entry"]
        assert entity["entry"].count("<iframe") == 2  # Should have 2 iframes

        # Check entity mentions
        assert f"[entity:{ref_entity_id}|the Video Creator]" in entity["entry"]
        assert f"[entity:{ref_entity_id}]" in entity["entry"]
        assert "[entity:99999|Unknown Location]" in entity["entry"]

    @pytest.mark.asyncio
    async def test_search_entities_with_embeds(self):
        """Test that searching for entities returns content with embeds preserved."""
        # Create an entity with searchable content and embeds
        journal_data = {
            "entity_type": "journal",
            "name": "Integration Test - DELETE ME - Battle Report",
            "entry": """# Battle of the Embedded Plains

The battle was fierce and well-documented:

<iframe src="https://battle-sim.example.com/replay/12345" width="800" height="600"></iframe>

Key participants included brave warriors from across the realm.""",
        }

        result = await self.call_tool("create_entities", entities=[journal_data])
        entity_id = result[0]["entity_id"]
        self.track_entity(entity_id)

        # Wait a bit for indexing
        await self.wait_for_api(2.0)

        # Search for the entity - use query to search content
        search_result = await self.call_tool(
            "find_entities",
            entity_type="journal",
            query="battle",  # Simplified query
            include_full=True,  # Need full content for query search
        )

        print(f"DEBUG: Search result: {search_result}")

        # Find our entity in results
        found = False
        for entity in search_result["entities"]:
            if entity["entity_id"] == entity_id:
                found = True
                # In full search results, we should have the entry with embeds
                assert "entry" in entity
                assert "https://battle-sim.example.com/replay/12345" in entity["entry"]
                assert "<iframe" in entity["entry"]
                break

        assert found, "Created entity not found in search results"


async def main():
    """Run all embed preservation tests."""

    test = TestEmbedPreservation()

    tests = [
        (
            "Create entity with YouTube embed",
            test.test_create_entity_with_youtube_embed,
        ),
        (
            "Create entity with multiple iframe embeds",
            test.test_create_entity_with_multiple_iframe_embeds,
        ),
        ("Update entity preserves embeds", test.test_update_entity_preserves_embeds),
        ("Embeds with entity mentions", test.test_embeds_with_entity_mentions),
        ("Search entities with embeds", test.test_search_entities_with_embeds),
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
    import asyncio
    import sys

    success = asyncio.run(main())
    sys.exit(0 if success else 1)
