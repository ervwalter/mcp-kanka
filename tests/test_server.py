"""Main test configuration and runner for unit tests.

This file is kept for pytest discovery. The actual unit tests are in the
tests/unit/ directory.
"""


def test_unit_tests_exist():
    """Verify that unit tests are properly organized."""
    from pathlib import Path

    unit_test_dir = Path(__file__).parent / "unit"
    assert unit_test_dir.exists(), "Unit test directory should exist"

    # Check that we have test files
    test_files = list(unit_test_dir.glob("test_*.py"))
    assert len(test_files) > 0, "Should have unit test files"

    # Expected test modules
    expected_modules = [
        "test_converter.py",
        "test_utils.py",
        "test_resources.py",
        "test_service.py",
        "test_tools.py",
    ]

    actual_modules = [f.name for f in test_files]
    for expected in expected_modules:
        assert expected in actual_modules, f"Missing expected test module: {expected}"
