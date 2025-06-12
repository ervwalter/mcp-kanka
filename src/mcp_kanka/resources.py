"""Resources provided by the Kanka MCP server."""

import json

from .types import KankaContext


def get_kanka_context() -> str:
    """
    Get the Kanka context resource.

    Returns:
        JSON string with Kanka context information
    """
    context: KankaContext = {
        "description": "Kanka is a worldbuilding and campaign management tool. This MCP server provides limited access to manage core entity types and their descriptions.",
        "supported_entities": {
            "character": "People in your world (PCs, NPCs, etc)",
            "creature": "Monster types and animals (templates, not individuals)",
            "location": "Places, regions, buildings, landmarks",
            "organization": "Groups, guilds, governments, companies",
            "race": "Species and ancestries",
            "note": "Private GM notes and session digests",
            "journal": "Session summaries and campaign chronicles",
            "quest": "Missions, objectives, and story arcs",
        },
        "core_fields": {
            "name": "Required. The entity's name",
            "type": "Optional. Subtype like 'NPC', 'City', 'Guild' (user-defined)",
            "entry": "Optional. Main description in Markdown format",
            "tags": "Optional. String array for categorization",
            "is_hidden": "Optional. If true, hidden from players (admin-only)",
        },
        "terminology": {
            "entity_type": "The main category (character, location, etc.) - fixed list",
            "type": "User-defined subtype within a category (e.g., 'NPC' for characters, 'City' for locations)",
        },
        "posts": "Additional notes/comments can be attached to any entity",
        "mentions": {
            "description": "Cross-reference entities using [entity:ID] or [entity:ID|custom text] in entry fields",
            "examples": ["[entity:1234]", "[entity:1234|the ancient dragon]"],
            "note": "The MCP server preserves these during Markdown/HTML conversion",
        },
        "limitations": "This MCP server only supports basic fields. Advanced features like attributes, relations, abilities, and most entity-specific fields are not available.",
    }

    return json.dumps(context, indent=2)
