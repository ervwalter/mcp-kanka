#!/usr/bin/env python3
"""Clean all entities from the test campaign."""

import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from kanka import KankaClient

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

# Load environment variables
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
else:
    load_dotenv()


async def clean_campaign():
    """Remove all entities from the test campaign."""
    token = os.environ.get("KANKA_TOKEN")
    campaign_id = os.environ.get("KANKA_CAMPAIGN_ID")

    if not token or not campaign_id:
        print("Error: KANKA_TOKEN and KANKA_CAMPAIGN_ID must be set")
        return

    client = KankaClient(token=token, campaign_id=int(campaign_id))

    # Entity types to clean
    entity_types = [
        ("characters", client.characters),
        ("creatures", client.creatures),
        ("locations", client.locations),
        ("organisations", client.organisations),
        ("races", client.races),
        ("notes", client.notes),
        ("journals", client.journals),
        ("quests", client.quests),
        ("families", client.families),
        ("calendars", client.calendars),
        ("events", client.events),
        ("tags", client.tags),
    ]

    print(f"Cleaning campaign {campaign_id}...")

    for entity_type_name, manager in entity_types:
        print(f"\nCleaning {entity_type_name}...")
        deleted_count = 0

        try:
            # Get all entities of this type
            page = 1
            while True:
                entities = manager.list(page=page, limit=100)
                if not entities:
                    break

                for entity in entities:
                    try:
                        manager.delete(entity.id)
                        deleted_count += 1
                        print(f"  Deleted {entity.name} (ID: {entity.id})")
                    except Exception as e:
                        print(f"  Failed to delete {entity.name}: {e}")

                if len(entities) < 100:
                    break
                page += 1

            print(f"  Total {entity_type_name} deleted: {deleted_count}")

        except Exception as e:
            print(f"  Error listing {entity_type_name}: {e}")

    print("\nCampaign cleanup complete!")


async def clean_test_entities_async():
    """Remove only test entities (with 'Integration Test' and 'DELETE ME' in name)."""
    token = os.environ.get("KANKA_TOKEN")
    campaign_id = os.environ.get("KANKA_CAMPAIGN_ID")

    if not token or not campaign_id:
        return 0

    client = KankaClient(token=token, campaign_id=int(campaign_id))

    # Entity types to clean
    entity_types = [
        ("characters", client.characters),
        ("creatures", client.creatures),
        ("locations", client.locations),
        ("organisations", client.organisations),
        ("races", client.races),
        ("notes", client.notes),
        ("journals", client.journals),
        ("quests", client.quests),
        ("families", client.families),
        ("calendars", client.calendars),
        ("events", client.events),
        ("tags", client.tags),
    ]

    total_deleted = 0

    for _, manager in entity_types:
        deleted_count = 0

        try:
            # Get all entities of this type
            page = 1
            while True:
                entities = manager.list(page=page, limit=100)
                if not entities:
                    break

                for entity in entities:
                    # Only delete test entities
                    if "Integration Test" in entity.name and "DELETE ME" in entity.name:
                        try:
                            manager.delete(entity.id)
                            deleted_count += 1
                        except Exception:
                            pass  # Silently skip failures

                if len(entities) < 100:
                    break
                page += 1

            total_deleted += deleted_count

        except Exception:
            pass  # Silently skip errors

    return total_deleted


def clean_test_entities():
    """Synchronous wrapper that returns count of deleted test entities."""
    return asyncio.run(clean_test_entities_async())


if __name__ == "__main__":
    asyncio.run(clean_campaign())
