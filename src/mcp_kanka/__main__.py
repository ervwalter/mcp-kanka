#!/usr/bin/env python3
"""
Kanka MCP Server

An MCP server that provides tools for interacting with Kanka campaigns.
"""

import asyncio
import logging
import os
from typing import Any

import mcp.server.stdio
import mcp.types as types
from dotenv import load_dotenv
from mcp.server import Server
from pydantic import AnyUrl

from .resources import get_kanka_context
from .tools import (
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

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=os.getenv("MCP_LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create the MCP server instance
app: Server[None] = Server("mcp-kanka")


@app.list_resources()  # type: ignore[no-untyped-call, misc]
async def list_resources() -> list[types.Resource]:
    """List available resources."""
    return [
        types.Resource(
            uri=AnyUrl("kanka://context"),
            name="Kanka Context",
            description="Information about Kanka's structure and this MCP server's capabilities",
            mimeType="application/json",
        )
    ]


@app.read_resource()  # type: ignore[no-untyped-call, misc]
async def read_resource(uri: str) -> str:
    """Read a resource by URI."""
    if uri == "kanka://context":
        return get_kanka_context()
    raise ValueError(f"Unknown resource: {uri}")


@app.list_tools()  # type: ignore[no-untyped-call, misc]
async def list_tools() -> list[types.Tool]:
    """List available tools."""
    return [
        types.Tool(
            name="find_entities",
            description="Find entities by search and/or filtering",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search term (searches names and content)",
                    },
                    "entity_type": {
                        "type": "string",
                        "enum": [
                            "character",
                            "creature",
                            "location",
                            "organization",
                            "race",
                            "note",
                            "journal",
                            "quest",
                        ],
                        "description": "Entity type to filter by",
                    },
                    "name": {
                        "type": "string",
                        "description": "Filter by name (partial match by default, e.g. 'Test' matches 'Test Character')",
                    },
                    "name_exact": {
                        "type": "boolean",
                        "description": "Use exact matching on name filter (case-insensitive)",
                        "default": False,
                    },
                    "name_fuzzy": {
                        "type": "boolean",
                        "description": "Use fuzzy matching on name filter (typo-tolerant)",
                        "default": False,
                    },
                    "type": {
                        "type": "string",
                        "description": "Filter by Type field (e.g., 'NPC', 'City')",
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Filter by tags (matches entities having ALL specified tags)",
                    },
                    "date_range": {
                        "type": "object",
                        "properties": {
                            "start": {"type": "string", "format": "date"},
                            "end": {"type": "string", "format": "date"},
                        },
                        "description": "For filtering journals by date",
                    },
                    "include_full": {
                        "type": "boolean",
                        "description": "Include full entity details",
                        "default": True,
                    },
                    "page": {
                        "type": "integer",
                        "description": "Page number for pagination",
                        "default": 1,
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Results per page (default 25, max 100, use 0 for all)",
                        "default": 25,
                    },
                    "last_synced": {
                        "type": "string",
                        "description": "ISO 8601 timestamp to get only entities modified after this time",
                    },
                },
            },
        ),
        types.Tool(
            name="create_entities",
            description="Create one or more entities",
            inputSchema={
                "type": "object",
                "properties": {
                    "entities": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "entity_type": {
                                    "type": "string",
                                    "enum": [
                                        "character",
                                        "creature",
                                        "location",
                                        "organization",
                                        "race",
                                        "note",
                                        "journal",
                                        "quest",
                                    ],
                                    "description": "Entity type",
                                },
                                "name": {
                                    "type": "string",
                                    "description": "Entity name",
                                },
                                "type": {
                                    "type": "string",
                                    "description": "The Type field (e.g., 'NPC', 'Player Character')",
                                },
                                "entry": {
                                    "type": "string",
                                    "description": "Description in Markdown format",
                                },
                                "tags": {"type": "array", "items": {"type": "string"}},
                                "is_hidden": {
                                    "type": "boolean",
                                    "description": "If true, hidden from players (admin-only)",
                                },
                            },
                            "required": ["entity_type", "name"],
                        },
                    }
                },
                "required": ["entities"],
            },
        ),
        types.Tool(
            name="update_entities",
            description="Update one or more entities",
            inputSchema={
                "type": "object",
                "properties": {
                    "updates": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "entity_id": {
                                    "type": "integer",
                                    "description": "Entity ID",
                                },
                                "name": {
                                    "type": "string",
                                    "description": "Entity name (required by Kanka API even if unchanged)",
                                },
                                "type": {
                                    "type": "string",
                                    "description": "The Type field",
                                },
                                "entry": {
                                    "type": "string",
                                    "description": "Content in Markdown format",
                                },
                                "tags": {"type": "array", "items": {"type": "string"}},
                                "is_hidden": {"type": "boolean"},
                            },
                            "required": ["entity_id", "name"],
                        },
                    }
                },
                "required": ["updates"],
            },
        ),
        types.Tool(
            name="get_entities",
            description="Retrieve specific entities by ID with their posts",
            inputSchema={
                "type": "object",
                "properties": {
                    "entity_ids": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "Array of entity IDs to retrieve",
                    },
                    "include_posts": {
                        "type": "boolean",
                        "description": "Include posts for each entity",
                        "default": False,
                    },
                },
                "required": ["entity_ids"],
            },
        ),
        types.Tool(
            name="delete_entities",
            description="Delete one or more entities",
            inputSchema={
                "type": "object",
                "properties": {
                    "entity_ids": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "Array of entity IDs to delete",
                    }
                },
                "required": ["entity_ids"],
            },
        ),
        types.Tool(
            name="create_posts",
            description="Create posts on entities",
            inputSchema={
                "type": "object",
                "properties": {
                    "posts": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "entity_id": {
                                    "type": "integer",
                                    "description": "The entity ID to attach post to",
                                },
                                "name": {"type": "string", "description": "Post title"},
                                "entry": {
                                    "type": "string",
                                    "description": "Post content in Markdown format",
                                },
                                "is_hidden": {
                                    "type": "boolean",
                                    "description": "If true, hidden from players (admin-only)",
                                },
                            },
                            "required": ["entity_id", "name"],
                        },
                    }
                },
                "required": ["posts"],
            },
        ),
        types.Tool(
            name="update_posts",
            description="Update existing posts",
            inputSchema={
                "type": "object",
                "properties": {
                    "updates": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "entity_id": {
                                    "type": "integer",
                                    "description": "The entity ID",
                                },
                                "post_id": {
                                    "type": "integer",
                                    "description": "The post ID to update",
                                },
                                "name": {
                                    "type": "string",
                                    "description": "Post title (required by API even if unchanged)",
                                },
                                "entry": {
                                    "type": "string",
                                    "description": "Post content in Markdown format",
                                },
                                "is_hidden": {
                                    "type": "boolean",
                                    "description": "If true, hidden from players (admin-only)",
                                },
                            },
                            "required": ["entity_id", "post_id", "name"],
                        },
                    }
                },
                "required": ["updates"],
            },
        ),
        types.Tool(
            name="delete_posts",
            description="Delete posts from entities",
            inputSchema={
                "type": "object",
                "properties": {
                    "deletions": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "entity_id": {
                                    "type": "integer",
                                    "description": "The entity ID",
                                },
                                "post_id": {
                                    "type": "integer",
                                    "description": "The post ID to delete",
                                },
                            },
                            "required": ["entity_id", "post_id"],
                        },
                    }
                },
                "required": ["deletions"],
            },
        ),
        types.Tool(
            name="check_entity_updates",
            description="Check which entity_ids have been modified since last sync",
            inputSchema={
                "type": "object",
                "properties": {
                    "entity_ids": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "Array of entity IDs to check",
                    },
                    "last_synced": {
                        "type": "string",
                        "description": "ISO 8601 timestamp to check updates since",
                    },
                },
                "required": ["entity_ids", "last_synced"],
            },
        ),
    ]


@app.call_tool()  # type: ignore[no-untyped-call, misc]
async def call_tool(name: str, arguments: dict[str, Any]) -> list[types.TextContent]:
    """Handle tool calls."""
    logger.info(f"Tool called: {name} with arguments: {arguments}")

    try:
        result: Any
        if name == "find_entities":
            result = await handle_find_entities(**arguments)
        elif name == "create_entities":
            result = await handle_create_entities(**arguments)
        elif name == "update_entities":
            result = await handle_update_entities(**arguments)
        elif name == "get_entities":
            result = await handle_get_entities(**arguments)
        elif name == "delete_entities":
            result = await handle_delete_entities(**arguments)
        elif name == "create_posts":
            result = await handle_create_posts(**arguments)
        elif name == "update_posts":
            result = await handle_update_posts(**arguments)
        elif name == "delete_posts":
            result = await handle_delete_posts(**arguments)
        elif name == "check_entity_updates":
            result = await handle_check_entity_updates(**arguments)
        else:
            raise ValueError(f"Unknown tool: {name}")

        return [types.TextContent(type="text", text=str(result))]
    except Exception as e:
        logger.error(f"Error in tool {name}: {str(e)}", exc_info=True)
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]


async def main() -> None:
    """Main entry point for the MCP server."""
    # Validate required environment variables
    if not os.getenv("KANKA_TOKEN"):
        logger.error("KANKA_TOKEN environment variable is required")
        raise ValueError("KANKA_TOKEN environment variable is required")

    if not os.getenv("KANKA_CAMPAIGN_ID"):
        logger.error("KANKA_CAMPAIGN_ID environment variable is required")
        raise ValueError("KANKA_CAMPAIGN_ID environment variable is required")

    logger.info("Starting Kanka MCP server...")

    # Run the server
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options(),
        )


if __name__ == "__main__":
    asyncio.run(main())
