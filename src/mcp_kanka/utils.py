"""Utility functions for the Kanka MCP server."""

import re
from datetime import datetime
from difflib import SequenceMatcher
from typing import Any


def fuzzy_match_score(s1: str, s2: str) -> float:
    """
    Calculate fuzzy match score between two strings.

    Args:
        s1: First string
        s2: Second string

    Returns:
        Match score between 0 and 1
    """
    # Normalize strings for comparison
    s1_normalized = s1.lower().strip()
    s2_normalized = s2.lower().strip()

    # Use SequenceMatcher for fuzzy matching
    return SequenceMatcher(None, s1_normalized, s2_normalized).ratio()


def filter_entities_by_name(
    entities: list[dict[str, Any]],
    name_filter: str,
    exact: bool = False,
    fuzzy: bool = False,
    threshold: float = 0.7,
) -> list[dict[str, Any]]:
    """
    Filter entities by name with optional exact or fuzzy matching.

    Args:
        entities: List of entities
        name_filter: Name to filter by
        exact: Use exact matching (case-insensitive)
        fuzzy: Use fuzzy matching (similarity scoring)
        threshold: Minimum score for fuzzy matches

    Returns:
        Filtered entities (with match_score if fuzzy)
    """
    if not name_filter:
        return entities

    if fuzzy:
        # Calculate scores and filter
        results = []
        for entity in entities:
            score = fuzzy_match_score(entity.get("name", ""), name_filter)
            if score >= threshold:
                # Add score to entity
                entity_with_score = entity.copy()
                entity_with_score["match_score"] = round(score, 2)
                results.append(entity_with_score)

        # Sort by score descending
        results.sort(key=lambda x: x["match_score"], reverse=True)
        return results
    elif exact:
        # Exact match (case-insensitive)
        name_lower = name_filter.lower()
        return [e for e in entities if e.get("name", "").lower() == name_lower]
    else:
        # Partial match (case-insensitive) - default behavior matching API
        name_lower = name_filter.lower()
        return [e for e in entities if name_lower in e.get("name", "").lower()]


def filter_entities_by_type(
    entities: list[dict[str, Any]], type_filter: str
) -> list[dict[str, Any]]:
    """
    Filter entities by Type field.

    Args:
        entities: List of entities
        type_filter: Type to filter by

    Returns:
        Filtered entities
    """
    if not type_filter:
        return entities

    # Case-insensitive exact match
    type_lower = type_filter.lower()
    return [e for e in entities if (e.get("type") or "").lower() == type_lower]


def filter_entities_by_tags(
    entities: list[dict[str, Any]], required_tags: list[str]
) -> list[dict[str, Any]]:
    """
    Filter entities by tags (must have ALL specified tags).

    Args:
        entities: List of entities
        required_tags: Tags that entities must have

    Returns:
        Filtered entities
    """
    if not required_tags:
        return entities

    # Normalize required tags
    required_tags_lower = {tag.lower() for tag in required_tags}

    results = []
    for entity in entities:
        entity_tags = entity.get("tags", [])
        if not entity_tags:
            continue

        # Normalize entity tags
        entity_tags_lower = {tag.lower() for tag in entity_tags}

        # Check if entity has all required tags
        if required_tags_lower.issubset(entity_tags_lower):
            results.append(entity)

    return results


def parse_date_from_entry(entry: str) -> datetime | None:
    """
    Try to parse a date from an entry text.

    Looks for patterns like:
    - **Date: 2025-05-30**
    - Date: 2025-05-30
    - 2025-05-30 at the beginning

    Args:
        entry: Entry text

    Returns:
        Parsed datetime or None
    """
    if not entry:
        return None

    # Patterns to try
    patterns = [
        r"\*\*Date:\s*(\d{4}-\d{2}-\d{2})\*\*",  # **Date: 2025-05-30**
        r"Date:\s*(\d{4}-\d{2}-\d{2})",  # Date: 2025-05-30
        r"^(\d{4}-\d{2}-\d{2})",  # 2025-05-30 at start
    ]

    for pattern in patterns:
        match = re.search(pattern, entry, re.MULTILINE | re.IGNORECASE)
        if match:
            try:
                return datetime.strptime(match.group(1), "%Y-%m-%d")
            except ValueError:
                continue

    return None


def filter_journals_by_date_range(
    entities: list[dict[str, Any]], start_date: str, end_date: str
) -> list[dict[str, Any]]:
    """
    Filter journal entities by date range found in their entries.

    Args:
        entities: List of journal entities
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)

    Returns:
        Filtered entities
    """
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError:
        # Invalid date format, return all
        return entities

    results = []
    for entity in entities:
        entry = entity.get("entry", "")
        if not entry:
            continue

        # Try to parse date from entry
        entry_date = parse_date_from_entry(entry)
        if entry_date and start <= entry_date <= end:
            results.append(entity)

    return results


def paginate_results(
    items: list[Any], page: int = 1, limit: int = 25
) -> tuple[list[Any], int, int]:
    """
    Paginate a list of items.

    Args:
        items: List to paginate
        page: Page number (1-based)
        limit: Items per page (0 for all)

    Returns:
        Tuple of (paginated items, total pages, total items)
    """
    total_items = len(items)

    if limit == 0:
        # Return all items
        return items, 1, total_items

    # Calculate pagination
    limit = min(limit, 100)  # Max 100 per page
    page = max(page, 1)

    total_pages = (total_items + limit - 1) // limit
    start_idx = (page - 1) * limit
    end_idx = start_idx + limit

    paginated_items = items[start_idx:end_idx]

    return paginated_items, total_pages, total_items


def search_in_content(
    entities: list[dict[str, Any]], query: str
) -> list[dict[str, Any]]:
    """
    Search for query in entity names and content.

    Args:
        entities: List of entities
        query: Search query

    Returns:
        Matching entities
    """
    if not query:
        return entities

    query_lower = query.lower()
    results = []

    for entity in entities:
        # Check name
        if query_lower in entity.get("name", "").lower():
            results.append(entity)
            continue

        # Check entry content
        if query_lower in (entity.get("entry") or "").lower():
            results.append(entity)
            continue

        # Check type field
        if query_lower in (entity.get("type") or "").lower():
            results.append(entity)

    return results
