#!/usr/bin/env python3
"""Run all integration tests for the MCP Kanka server."""

import re
import subprocess
import sys
import time
from pathlib import Path

# Test files to run
TEST_FILES = [
    "test_find_entities.py",
    "test_create_update_delete.py",
    "test_posts.py",
    "test_sync_features.py",
    "test_visibility.py",
    "test_embed_preservation.py",
]


def parse_test_output(output: str) -> tuple[list[tuple[str, bool]], int, int]:
    """
    Parse test output to extract individual test results.

    Returns:
        Tuple of (test_results, passed_count, failed_count)
        where test_results is a list of (test_name, passed) tuples
    """
    test_results = []

    # Look for test result lines
    # Format: "✓ Test name passed" or "✗ Test name failed"
    for line in output.split("\n"):
        if line.strip().startswith("✓"):
            # Extract test name (remove ✓ and "passed")
            match = re.match(r"✓\s+(.+?)\s+passed", line.strip())
            if match:
                test_name = match.group(1)
                test_results.append((test_name, True))
        elif line.strip().startswith("✗"):
            # Extract test name (remove ✗ and "failed:")
            match = re.match(r"✗\s+(.+?)\s+failed:", line.strip())
            if match:
                test_name = match.group(1)
                test_results.append((test_name, False))

    # Also look for summary line "Test Results: X passed, Y failed"
    summary_match = re.search(
        r"Test Results:\s*(\d+)\s*passed,\s*(\d+)\s*failed", output
    )
    if summary_match:
        passed = int(summary_match.group(1))
        failed = int(summary_match.group(2))
    else:
        # Count from parsed results
        passed = sum(1 for _, success in test_results if success)
        failed = sum(1 for _, success in test_results if not success)

    return test_results, passed, failed


def run_test_file(test_file: str) -> tuple[bool, list[tuple[str, bool]], str]:
    """
    Run a single test file and return results.

    Returns:
        Tuple of (success, test_results, output)
    """
    test_path = Path(__file__).parent / test_file

    print(f"\n{'='*60}")
    print(f"Running {test_file}")
    print(f"{'='*60}")

    result = subprocess.run(
        [sys.executable, str(test_path)],
        capture_output=True,
        text=True,
    )

    # Print output as it was
    print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)

    # Parse test results from output
    test_results, passed, failed = parse_test_output(result.stdout)

    return result.returncode == 0, test_results, result.stdout


def main():
    """Run all integration tests."""
    print("MCP Kanka Integration Test Suite")
    print("=" * 60)
    print(f"Start time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Load environment if available
    try:
        from dotenv import load_dotenv

        env_path = Path(__file__).parent / ".env"
        if env_path.exists():
            load_dotenv(env_path)
            print(f"Loaded environment from {env_path}")
    except ImportError:
        pass

    all_test_results = []
    test_file_results = []

    for test_file in TEST_FILES:
        success, test_results, output = run_test_file(test_file)
        test_file_results.append((test_file, success))

        # Add test file prefix to results for grouping
        suite_name = (
            test_file.replace("test_", "").replace(".py", "").replace("_", " ").title()
        )
        for test_name, passed in test_results:
            all_test_results.append((f"{suite_name}: {test_name}", passed))

    # Print detailed summary
    print("\n" + "=" * 60)
    print("INTEGRATION TEST SUMMARY")
    print("=" * 60)

    # Group results by suite
    if all_test_results:
        current_suite = ""
        for test_name, passed in all_test_results:
            suite = test_name.split(":")[0]
            if suite != current_suite:
                current_suite = suite
                print(f"\n{suite} Tests:")

            # Extract just the test name part
            test_only = test_name.split(": ", 1)[1] if ": " in test_name else test_name
            status = "✓ PASSED" if passed else "✗ FAILED"
            print(f"  {test_only}: {status}")

    # Calculate totals
    total_tests = len(all_test_results)
    passed_tests = sum(1 for _, passed in all_test_results if passed)
    failed_tests = total_tests - passed_tests

    # File-level summary
    passed_files = sum(1 for _, success in test_file_results if success)
    failed_files = len(test_file_results) - passed_files

    print(f"\nTotal Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {failed_tests}")
    if total_tests > 0:
        print(f"Success Rate: {passed_tests/total_tests*100:.1f}%")

    print(
        f"\nTest Files: {len(test_file_results)} total ({passed_files} passed, {failed_files} failed)"
    )

    print(f"\nEnd time: {time.strftime('%Y-%m-%d %H:%M:%S')}")

    # Optional: Run cleanup check
    print("\nChecking for leftover test entities...")
    try:
        from clean_campaign import clean_test_entities

        leftover_count = clean_test_entities()
        if leftover_count > 0:
            print(
                f"WARNING: Found and cleaned {leftover_count} leftover test entities!"
            )
            print("Some tests may not be cleaning up properly.")
    except Exception as e:
        print(f"Could not run cleanup check: {e}")

    return failed_tests == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
