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

## Required Tools (6 total)

### 1. search_entities
Search for entities by name/content
```
Parameters:
- query: string (required) - Search term (searches names and content in Kanka)
- entity_type: string (optional) - character|creature|location|organization|race|note|journal (client-side filter)
- limit: number (optional) - Max results (default 10, use 0 for all)

Returns: Array of {entity_id, name, entity_type}
Note: This uses Kanka's native search - no fuzzy matching
```

### 2. list_entities
List entities with full details and filtering
```
Parameters:
- entity_type: string (optional) - character|creature|location|organization|race|note|journal
- name: string (optional) - Filter by name (client-side)
- name_fuzzy: boolean (optional) - Use fuzzy matching on name filter (default: false)
- type: string (optional) - Filter by Type field (e.g., "NPC", "City") - client-side
- tag: string (optional) - Filter by tag - client-side
- date_range: {start: string, end: string} (optional) - For filtering journals by date in entry
- limit: number (optional) - Max results (default 25, use 0 for all)

Returns: Array of {id, entity_id, name, entity_type, type, entry, tags, is_private, match_score}
Note: entry field is returned in Markdown format
Note: match_score only included when name_fuzzy=true
```

### 3. create_entities
Create one or more entities
```
Parameters:
- entities: Array of:
  - entity_type: string (required) - character|creature|location|organization|race|note|journal
  - name: string (required)
  - type: string (optional) - The "Type" field (e.g., "NPC", "Player Character", "Session Summary")
  - entry: string (optional) - Description in Markdown format
  - tags: string[] (optional)
  - is_private: boolean (optional) - If true, only campaign admins can see (default: false for most types, true for notes)

Returns: Array of {id, entity_id, name, mention, success, error}
Note: Partial success allowed - check each result
```

### 4. update_entities
Update one or more entities
```
Parameters:
- updates: Array of:
  - entity_id: number (required)
  - name: string (optional)
  - type: string (optional) - The "Type" field
  - entry: string (optional) - Content in Markdown format
  - tags: string[] (optional)
  - is_private: boolean (optional)

Returns: Array of {entity_id, success, error}
Note: Partial success allowed - check each result
```

### 5. get_entities
Retrieve one or more entities by ID
```
Parameters:
- entity_ids: number[] (required) - Array of entity IDs to retrieve

Returns: Array of {id, entity_id, name, entity_type, type, entry, tags, is_private, success, error}
Note: entry field is returned in Markdown format
Note: Partial success allowed - check each result
```

### 6. delete_entities
Delete one or more entities
```
Parameters:
- entity_ids: number[] (required) - Array of entity IDs to delete

Returns: Array of {entity_id, success, error}
Note: Partial success allowed - check each result
Note: Deletion is permanent - use with caution
```

## Usage Examples

### Handling Transcription Misspellings

**Method 1: Fuzzy name matching via list**
Tool: `list_entities`
Parameters:
- entity_type: "character"
- name: "Aylysh"  # Misspelling from transcript
- name_fuzzy: true

Returns: [
  {id: 789, entity_id: 1011, name: "Aelysh", entity_type: "character", type: "NPC", entry: "Grove Warden...", tags: ["elf"], is_private: false, match_score: 0.89}
]

**Method 2: Search for known misspellings in content**
Tool: `search_entities`
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
Tool: `list_entities`
Parameters:
- entity_type: "character"
- type: "Player Character"

Returns: Full details of all PCs including their entries, tags, etc.

**Get recent session summaries**
Tool: `list_entities`
Parameters:
- entity_type: "journal"
- type: "Session Summary"
- date_range: {start: "2025-05-01", end: "2025-05-31"}

Returns: Journals with dates in their entries within the specified range

**Update multiple entities after session**
Tool: `update_entities`
Parameters:
- updates: [
    {
      entity_id: 1011,
      entry: "[existing content]\n\n## Session 23 Update\nAelysh revealed she needs elderberries for..."
    },
    {
      entity_id: 890,
      tags: ["pc", "dwarf", "cleric", "paranoid-about-fey"]
    }
  ]

### Tag Usage Examples

Tags are simple strings that help organize content. The AI will provide appropriate tags based on context, such as:

- For notes: "digest", "draft", "processed", "admin-notes", "gm-reference"
- For journals: "session-summary", "session-narrative", "chronicle", "chapter-X"  
- For entities: "pc", "npc", character names, organization affiliations, session numbers

The MCP server should accept any string as a tag and handle the details of creating/managing them in Kanka.