"""Helper module to set up test environment for integration tests."""

import os
import sys
from pathlib import Path


def setup_environment():
    """Set up the test environment for running integration tests."""
    # Add the project src to the Python path
    current_dir = Path(__file__).parent
    project_dir = current_dir.parent.parent
    src_dir = project_dir / "src"

    for path in [str(src_dir), str(project_dir)]:
        if path not in sys.path:
            sys.path.insert(0, path)

    # Try to load environment variables from .env file
    try:
        from dotenv import load_dotenv

        env_file = current_dir / ".env"
        if env_file.exists():
            load_dotenv(env_file)
            print(f"Loaded environment from {env_file}")
    except ImportError:
        # dotenv not available, continue without it
        pass

    # Check for required environment variables
    if not os.environ.get("KANKA_TOKEN"):
        print("ERROR: KANKA_TOKEN environment variable is required")
        print("Please set it to your Kanka API token")
        print("You can create a .env file from .env.example")
        sys.exit(1)

    if not os.environ.get("KANKA_CAMPAIGN_ID"):
        print("ERROR: KANKA_CAMPAIGN_ID environment variable is required")
        print("Please set it to your campaign ID")
        print("You can create a .env file from .env.example")
        sys.exit(1)

    # Optional: Set log level
    if not os.environ.get("MCP_LOG_LEVEL"):
        os.environ["MCP_LOG_LEVEL"] = "INFO"
