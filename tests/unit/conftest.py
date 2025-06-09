"""Pytest configuration for unit tests."""

import sys
from pathlib import Path

import pytest

# Add the src directory to Python path
src_path = Path(__file__).parent.parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))


@pytest.fixture(autouse=True)
def reset_singletons():
    """Reset global singletons before each test."""
    # Import here to avoid issues
    import mcp_kanka.operations
    import mcp_kanka.service

    # Reset before test
    mcp_kanka.service._service = None
    mcp_kanka.operations._operations = None

    yield

    # Reset after test
    mcp_kanka.service._service = None
    mcp_kanka.operations._operations = None
