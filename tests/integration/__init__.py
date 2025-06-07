"""Integration tests package initialization."""

import sys
from pathlib import Path

# Add necessary paths at package import time
integration_dir = Path(__file__).parent
src_dir = integration_dir.parent.parent / "src"

for path in [integration_dir, src_dir]:
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))
