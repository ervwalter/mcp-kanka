"""CLI entry point for mcp-kanka."""

import asyncio

from .__main__ import main


def run() -> None:
    """Entry point for the console script."""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Error: {e}")
        exit(1)
