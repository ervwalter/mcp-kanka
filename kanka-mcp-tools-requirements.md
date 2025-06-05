# Kanka MCP Tools Requirements

This document specifies MCP (Model Context Protocol) tools needed for Kanka integration. These are tool definitions that will be exposed by an MCP server for AI agents to call.

## Required Entity Types

The MCP server should support these Kanka entity types:

1. **character** - Player characters (PCs), non-player characters (NPCs), named individuals
2. **creature** - Monster types, animals, non-unique creatures (e.g., skims, goblins, wolves)
3. **location** - Places, regions, buildings, landmarks
4. **organization** - Guilds, governments, cults, companies, groups
5. **race** - Species, ancestries (e.g., Dwarf, Norn, Dhampir, Slaan)
6. **note** - Internal content like session digests, processing logs, GM notes
7. **journal** - Session summaries, narratives, chronicles
8. **quest** - Missions, objectives, story arcs, player goals

Note on tags: Tags should be accepted as simple string arrays. The MCP server will handle creating/managing tags in Kanka as needed.

## Content Format

All `entry` parameters accept Markdown format. The MCP server should:
1. Convert Markdown to HTML for Kanka's API
2. Preserve `[entity:ID]` and `[entity:ID|text]` mention formats during conversion
3. Handle basic Markdown: headers, lists, bold, italic, links, code blocks

When returning content, the MCP server should convert HTML back to Markdown.

## API Implementation Notes

The Kanka API has limitations that the MCP server must work around:
- Search returns minimal data (name, id, entity_type only)
- List operations return full data but no server-side filtering
- All filtering must be done client-side by the MCP server
- Batch operations must be implemented as loops in the MCP server

## Required Resources

### kanka_context
Provides AI agents with understanding of Kanka's structure within the scope of this MCP server.
```
Returns: {
  description: "Kanka is a worldbuilding and campaign management tool. This MCP server provides limited access to manage core entity types and their descriptions.",
  supported_entities: {
    character: "People in your world (PCs, NPCs, etc)",
    creature: "Monster types and animals (templates, not individuals)",
    location: "Places, regions, buildings, landmarks",
    organization: "Groups, guilds, governments, companies",
    race: "Species and ancestries",
    note: "Private GM notes and session digests",
    journal: "Session summaries and campaign chronicles",
    quest: "Missions, objectives, and story arcs"
  },
  core_fields: {
    name: "Required. The entity's name",
    type: "Optional. Subtype like 'NPC', 'City', 'Guild' (user-defined)",
    entry: "Optional. Main description in Markdown format",
    tags: "Optional. String array for categorization",
    is_private: "Optional. If true, only campaign admins can see"
  },
  terminology: {
    entity_type: "The main category (character, location, etc.) - fixed list",
    type: "User-defined subtype within a category (e.g., 'NPC' for characters, 'City' for locations)"
  },
  posts: "Additional notes/comments can be attached to any entity",
  mentions: {
    description: "Cross-reference entities using [entity:ID] or [entity:ID|custom text] in entry fields",
    examples: ["[entity:1234]", "[entity:1234|the ancient dragon]"],
    note: "The MCP server preserves these during Markdown/HTML conversion"
  },
  limitations: "This MCP server only supports basic fields. Advanced features like attributes, relations, abilities, and most entity-specific fields are not available."
}
```

## Required Tools (8 total)

### 1. find_entities
Find entities by search and/or filtering
```
Parameters:
- query: string (optional) - Search term (searches names and content)
- entity_type: string (optional) - character|creature|location|organization|race|note|journal|quest
- name: string (optional) - Filter by name (can be combined with query)
- name_fuzzy: boolean (optional) - Use fuzzy matching on name filter (default: false)
- type: string (optional) - Filter by Type field (e.g., "NPC", "City")
- tags: string[] (optional) - Filter by tags (matches entities having ALL specified tags)
- date_range: {start: string, end: string} (optional) - For filtering journals by date
- include_full: boolean (optional) - Include full entity details (default: true)
- page: number (optional) - Page number for pagination (default: 1)
- limit: number (optional) - Results per page (default 25, max 100, use 0 for all)

Returns: 
- include_full=true: Array of {id, entity_id, name, entity_type, type, entry, tags, is_private, match_score}
- include_full=false: Array of {entity_id, name, entity_type}
Note: If query is provided, server searches first then fetches full details (if include_full=true)
Note: Filters are applied client-side after search/list operations
Note: match_score only included when name_fuzzy=true
Note: Set include_full=false for faster results when scanning entity names
```

### 2. create_entities
Create one or more entities
```
Parameters:
- entities: Array of:
  - entity_type: string (required) - character|creature|location|organization|race|note|journal|quest
  - name: string (required)
  - type: string (optional) - The "Type" field (e.g., "NPC", "Player Character", "Session Summary")
  - entry: string (optional) - Description in Markdown format
  - tags: string[] (optional)
  - is_private: boolean (optional) - If true, only campaign admins can see (default: false for most types, true for notes)

Returns: Array of {id, entity_id, name, mention, success, error}
Note: Partial success allowed - check each result
```

### 3. update_entities
Update one or more entities
```
Parameters:
- updates: Array of:
  - entity_id: number (required)
  - name: string (required) - Entity name (required by Kanka API even if unchanged)
  - type: string (optional) - The "Type" field
  - entry: string (optional) - Content in Markdown format
  - tags: string[] (optional)
  - is_private: boolean (optional)

Returns: Array of {entity_id, success, error}
Note: Partial success allowed - check each result
```

### 4. get_entities
Retrieve specific entities by ID with their posts
```
Parameters:
- entity_ids: number[] (required) - Array of entity IDs to retrieve
- include_posts: boolean (optional) - Include posts for each entity (default: false)

Returns: Array of {id, entity_id, name, entity_type, type, entry, tags, is_private, posts, success, error}
Note: entry field is returned in Markdown format
Note: posts field (when include_posts=true) contains array of {id, name, entry, is_private}
Note: Partial success allowed - check each result
Note: No pagination needed - retrieves specific entities by ID
```

### 5. delete_entities
Delete one or more entities
```
Parameters:
- entity_ids: number[] (required) - Array of entity IDs to delete

Returns: Array of {entity_id, success, error}
Note: Partial success allowed - check each result
Note: Deletion is permanent - use with caution
```

### 6. create_posts
Create posts on entities
```
Parameters:
- posts: Array of:
  - entity_id: number (required) - The entity ID to attach post to
  - name: string (required) - Post title
  - entry: string (optional) - Post content in Markdown format
  - is_private: boolean (optional) - Privacy setting (default: false)

Returns: Array of {post_id, entity_id, success, error}
Note: Partial success allowed - check each result
```

### 7. update_posts
Update existing posts
```
Parameters:
- updates: Array of:
  - entity_id: number (required) - The entity ID
  - post_id: number (required) - The post ID to update
  - name: string (required) - Post title (required by API even if unchanged)
  - entry: string (optional) - Post content in Markdown format
  - is_private: boolean (optional) - Privacy setting

Returns: Array of {entity_id, post_id, success, error}
Note: Partial success allowed - check each result
```

### 8. delete_posts
Delete posts from entities
```
Parameters:
- deletions: Array of:
  - entity_id: number (required) - The entity ID
  - post_id: number (required) - The post ID to delete

Returns: Array of {entity_id, post_id, success, error}
Note: Partial success allowed - check each result
```

## Usage Examples

### Handling Transcription Misspellings

**Method 1: Fuzzy name matching**
Tool: `find_entities`
Parameters:
- entity_type: "character"
- name: "Aylysh"  # Misspelling from transcript
- name_fuzzy: true

Returns: [
  {id: 789, entity_id: 1011, name: "Aelysh", entity_type: "character", type: "NPC", entry: "Grove Warden...", tags: ["elf"], is_private: false, match_score: 0.89}
]

**Method 2: Search for known misspellings in content**
Tool: `find_entities`
Parameters:
- query: "Aylysh"
- entity_type: "character"

Returns: [
  {entity_id: 1011, name: "Aelysh", entity_type: "character"}
]
(If Aelysh's entry contains the misspelling)

**Add known misspellings to character entry**
Tool: `update_entities`
Parameters:
- updates: [{
    entity_id: 1011,
    name: "Aelysh",  # Required even if not changing
    entry: "Grove Warden of the eastern woods...\n\n[Known misspellings from transcripts: Aylysh, Ailish, Alesh]"
  }]

### Batch Operations

**Create multiple entities at once**
Tool: `create_entities`
Parameters:
- entities: [
    {
      entity_type: "character",
      name: "Osanna von Carstein",
      type: "NPC",
      entry: "Vampire noble...",
      tags: ["vampire", "von-carstein"]
    },
    {
      entity_type: "note",
      name: "Digest: Session 2025-05-30",
      type: "Session Digest",
      entry: "## Chronological Log\n1. Party arrives at...",
      tags: ["digest", "draft"],
      is_private: true
    },
    {
      entity_type: "journal", 
      name: "Session 23: The Mansion Mystery",
      type: "Session Summary",
      entry: "**Date: 2025-05-30**\n\nThe party cleared out a mansion...",
      tags: ["session-summary", "published"]
    }
  ]

Returns: [
  {id: 234, entity_id: 567, name: "Osanna von Carstein", mention: "[entity:567]", success: true},
  {id: 235, entity_id: 568, name: "Digest: Session 2025-05-30", mention: "[entity:568]", success: true},
  {id: 236, entity_id: 569, name: "Session 23: The Mansion Mystery", mention: "[entity:569]", success: true}
]

### Processing Session Content

**Get all PCs for session context**
Tool: `find_entities`
Parameters:
- entity_type: "character"
- type: "Player Character"

Returns: Full details of all PCs including their entries, tags, etc.

**Get recent session summaries**
Tool: `find_entities`
Parameters:
- entity_type: "journal"
- type: "Session Summary"
- date_range: {start: "2025-05-01", end: "2025-05-31"}

Returns: Journals with dates in their entries within the specified range

**Find entities with multiple tags**
Tool: `find_entities`
Parameters:
- tags: ["vampire", "noble"]  # Finds entities that have BOTH tags

Returns: Entities tagged with both "vampire" AND "noble"

**Update multiple entities after session**
Tool: `update_entities`
Parameters:
- updates: [
    {
      entity_id: 1011,
      name: "Aelysh",  # Required even if not changing
      entry: "[existing content]\n\n## Session 23 Update\nAelysh revealed she needs elderberries for..."
    },
    {
      entity_id: 890,
      name: "Thorin Ironforge",  # Required even if not changing
      tags: ["pc", "dwarf", "cleric", "paranoid-about-fey"]
    }
  ]

### Tag Usage Examples

Tags are simple strings that help organize content. The AI will provide appropriate tags based on context, such as:

- For notes: "digest", "draft", "processed", "admin-notes", "gm-reference"
- For journals: "session-summary", "session-narrative", "chronicle", "chapter-X"  
- For entities: "pc", "npc", character names, organization affiliations, session numbers

The MCP server should accept any string as a tag and handle the details of creating/managing them in Kanka.