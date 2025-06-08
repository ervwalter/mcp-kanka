"""Base class for MCP server integration tests."""

import asyncio
import json
import os
import subprocess
import sys
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from setup_test_env import setup_environment

# Setup environment when module is imported
setup_environment()


# Import MCP components directly


class MCPIntegrationTestBase:
    """Base class for MCP integration tests that interact with the server via subprocess."""

    def __init__(self):
        self.server_process: subprocess.Popen | None = None
        self.token = os.environ.get("KANKA_TOKEN")
        self.campaign_id = os.environ.get("KANKA_CAMPAIGN_ID")
        self._cleanup_tasks: list[tuple[str, Callable]] = []
        self._created_entities: list[int] = []  # Track entities for cleanup

    async def start_server(self):
        """Start the MCP server as a subprocess."""
        # Find the server module
        server_path = (
            Path(__file__).parent.parent.parent / "src" / "mcp_kanka" / "__main__.py"
        )

        # Start the server
        self.server_process = subprocess.Popen(
            [sys.executable, str(server_path)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=0,
            env=os.environ.copy(),
        )

        # Wait a bit for server to start
        await asyncio.sleep(1)

        # Send initialization
        await self._send_request(
            {
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {"protocolVersion": "0.1.0", "capabilities": {}},
                "id": 1,
            }
        )

        # Read initialization response
        response = await self._read_response()
        if not response or "result" not in response:
            raise RuntimeError("Failed to initialize MCP server")

    async def stop_server(self):
        """Stop the MCP server."""
        if self.server_process:
            self.server_process.terminate()
            self.server_process.wait(timeout=5)
            self.server_process = None

    async def _send_request(self, request: dict[str, Any]):
        """Send a JSON-RPC request to the server."""
        if not self.server_process or not self.server_process.stdin:
            raise RuntimeError("Server not started")

        json_str = json.dumps(request)
        self.server_process.stdin.write(json_str + "\\n")
        self.server_process.stdin.flush()

    async def _read_response(self) -> dict[str, Any] | None:
        """Read a JSON-RPC response from the server."""
        if not self.server_process or not self.server_process.stdout:
            raise RuntimeError("Server not started")

        line = self.server_process.stdout.readline()
        if line:
            try:
                return json.loads(line.strip())
            except json.JSONDecodeError:
                print(f"Failed to parse response: {line}")
                return None
        return None

    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        """Call an MCP tool and return the result."""
        request_id = int(time.time() * 1000)  # Use timestamp as ID

        await self._send_request(
            {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {"name": tool_name, "arguments": arguments},
                "id": request_id,
            }
        )

        response = await self._read_response()
        if not response:
            raise RuntimeError(f"No response from tool {tool_name}")

        if "error" in response:
            raise RuntimeError(f"Tool error: {response['error']}")

        if "result" in response:
            # Extract the actual content from the response
            content = response["result"].get("content", [])
            if content and isinstance(content, list) and len(content) > 0:
                # Return the text content
                return json.loads(content[0].get("text", "{}"))
            return response["result"]

        raise RuntimeError(f"Invalid response from tool {tool_name}")

    async def get_resource(self, uri: str) -> Any:
        """Get an MCP resource."""
        request_id = int(time.time() * 1000)

        await self._send_request(
            {
                "jsonrpc": "2.0",
                "method": "resources/read",
                "params": {"uri": uri},
                "id": request_id,
            }
        )

        response = await self._read_response()
        if not response:
            raise RuntimeError(f"No response for resource {uri}")

        if "error" in response:
            raise RuntimeError(f"Resource error: {response['error']}")

        if "result" in response:
            # Parse the JSON content
            content = response["result"].get("contents", [])
            if content and isinstance(content, list):
                return json.loads(content[0].get("text", "{}"))
            return response["result"]

        raise RuntimeError(f"Invalid response for resource {uri}")

    def register_cleanup(self, description: str, cleanup_func: Callable):
        """Register a cleanup task to be executed later."""
        self._cleanup_tasks.append((description, cleanup_func))

    def track_entity(self, entity_id: int):
        """Track an entity for cleanup."""
        self._created_entities.append(entity_id)

    async def cleanup_entities(self):
        """Clean up all tracked entities."""
        if not self._created_entities:
            return

        print(f"\\nCleaning up {len(self._created_entities)} entities...")

        # Delete in batches
        batch_size = 10
        for i in range(0, len(self._created_entities), batch_size):
            batch = self._created_entities[i : i + batch_size]
            try:
                result = await self.call_tool("delete_entities", {"entity_ids": batch})

                # Count successes
                if isinstance(result, list):
                    successes = sum(1 for r in result if r.get("success"))
                    print(f"  Deleted {successes}/{len(batch)} entities")

            except Exception as e:
                print(f"  Failed to delete batch: {e}")

        self._created_entities.clear()

    async def setup(self):
        """Set up the test environment."""
        await self.start_server()

    async def teardown(self):
        """Clean up the test environment."""
        # Execute cleanup tasks
        for description, cleanup_func in self._cleanup_tasks:
            try:
                if asyncio.iscoroutinefunction(cleanup_func):
                    await cleanup_func()
                else:
                    cleanup_func()
                print(f"  ✓ {description}")
            except Exception as e:
                print(f"  ✗ {description} failed: {e}")

        # Clean up entities
        await self.cleanup_entities()

        # Stop server
        await self.stop_server()

    async def run_test(self, test_name: str, test_func):
        """Run a single test with proper setup and teardown."""
        print(f"\\nRunning {test_name}...")
        try:
            await self.setup()
            await test_func()
            print(f"✓ {test_name} passed")
            return True
        except Exception as e:
            print(f"✗ {test_name} failed: {e}")
            import traceback

            traceback.print_exc()
            return False
        finally:
            await self.teardown()

    def assert_equal(self, actual: Any, expected: Any, message: str = ""):
        """Assert that two values are equal."""
        if actual != expected:
            raise AssertionError(f"{message}\\nExpected: {expected}\\nActual: {actual}")

    def assert_true(self, condition: bool, message: str = ""):
        """Assert that a condition is true."""
        if not condition:
            raise AssertionError(f"Assertion failed: {message}")

    def assert_in(self, item: Any, container: Any, message: str = ""):
        """Assert that an item is in a container."""
        if item not in container:
            raise AssertionError(f"{message}\\n{item} not found in {container}")

    def assert_not_none(self, value: Any, message: str = ""):
        """Assert that a value is not None."""
        if value is None:
            raise AssertionError(f"Value is None: {message}")

    async def wait_for_api(self, seconds: float = 0.5):
        """Wait a bit to avoid rate limiting."""
        await asyncio.sleep(seconds)

    # Helper methods for common operations
    async def create_entity(self, **kwargs):
        """Helper to create a single entity."""
        result = await self.call_tool("create_entities", {"entities": [kwargs]})
        if result and len(result) > 0:
            if result[0]["success"]:
                self.track_entity(result[0]["entity_id"])
            return result[0]
        raise RuntimeError("Failed to create entity")

    async def find_entities(self, **kwargs):
        """Helper to find entities."""
        return await self.call_tool("find_entities", kwargs)

    async def update_entity(self, entity_id: int, **kwargs):
        """Helper to update an entity."""
        update = {"entity_id": entity_id, **kwargs}
        result = await self.call_tool("update_entities", {"updates": [update]})
        if result and len(result) > 0:
            return result[0]
        raise RuntimeError("Failed to update entity")

    async def delete_entity(self, entity_id: int):
        """Helper to delete an entity."""
        result = await self.call_tool("delete_entities", {"entity_ids": [entity_id]})
        if result and len(result) > 0:
            return result[0]
        raise RuntimeError("Failed to delete entity")

    async def check_entity_updates(self, **kwargs):
        """Helper to check entity updates."""
        return await self.call_tool("check_entity_updates", kwargs)
