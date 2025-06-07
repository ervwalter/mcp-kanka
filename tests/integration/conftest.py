"""Pytest configuration for integration tests."""

import sys
from pathlib import Path

# Add the src directory to Python path
src_path = Path(__file__).parent.parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# Add integration test directory to path
integration_path = Path(__file__).parent
if str(integration_path) not in sys.path:
    sys.path.insert(0, str(integration_path))
