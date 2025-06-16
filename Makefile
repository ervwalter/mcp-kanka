.PHONY: install test lint format typecheck check clean coverage help sync

# Default target
help:
	@echo "Available commands:"
	@echo "  make install   - Install development dependencies with uv"
	@echo "  make sync      - Sync dependencies with uv.lock"
	@echo "  make test      - Run all tests"
	@echo "  make lint      - Run code linting"
	@echo "  make typecheck - Run type checking with mypy"
	@echo "  make format    - Format code with black and sort imports with isort"
	@echo "  make check     - Run all checks (lint + typecheck + test)"
	@echo "  make clean     - Clean up temporary files"
	@echo "  make coverage  - Run tests with coverage report"

# Install development dependencies and sync with lock file
install:
	uv sync --all-groups

# Sync dependencies without updating lock file
sync:
	uv sync --all-groups

# Run all tests
test:
	uv run pytest tests/ -v

# Run tests for CI (with coverage)
test-ci:
	uv run pytest tests/ -v --cov=mcp_kanka --cov-report=xml --cov-report=term

# Run linting
lint:
	uv run ruff check .

# Check formatting without modifying files
format-check:
	uv run black --check .
	uv run isort --check-only .

# Run type checking
typecheck:
	uv run mypy src --ignore-missing-imports

# Format code
format:
	uv run black .
	uv run isort .
	uv run ruff check --fix .

# Run pre-commit hooks on all files
pre-commit:
	uv run pre-commit run --all-files

# Run all checks
check: lint typecheck test

# Clean up temporary files
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name "htmlcov" -exec rm -rf {} +
	find . -type d -name "dist" -exec rm -rf {} +
	find . -type d -name "build" -exec rm -rf {} +

# Run tests with coverage
coverage:
	uv run pytest tests/ -v --cov=mcp_kanka --cov-report=html --cov-report=term