# Publishing mcp-kanka

This document outlines the process for publishing new releases of mcp-kanka to PyPI.

## Prerequisites

1. Ensure you have the necessary permissions on PyPI
2. Have `bump2version` installed: `pip install bump2version`
3. Make sure all tests pass: `make check`
4. Ensure CHANGELOG.md is up to date (create if it doesn't exist)

## Release Process

### 1. Update Version

Use bump2version to update the version number. It will:
- Update the version in `src/mcp_kanka/_version.py`
- Update the version in `pyproject.toml`
- Create a git commit with the version change
- Create a git tag

For a patch release (0.1.0 → 0.1.1):
```bash
bump2version patch
```

For a minor release (0.1.0 → 0.2.0):
```bash
bump2version minor
```

For a major release (0.1.0 → 1.0.0):
```bash
bump2version major
```

### 2. Push Changes and Tag

```bash
git push origin main
git push origin --tags
```

### 3. Create GitHub Release

1. Go to the GitHub repository
2. Click on "Releases" → "Create a new release"
3. Select the tag you just pushed
4. Title the release with the version number (e.g., "v0.1.0")
5. Add release notes based on CHANGELOG.md
6. Click "Publish release"

This will trigger the publish workflow which will:
- Run all tests on multiple Python versions
- Build the package
- Publish to PyPI using trusted publishing

### 4. Verify the Release

1. Check that the package appears on PyPI: https://pypi.org/project/mcp-kanka/
2. Test installation in a clean environment:
   ```bash
   pip install mcp-kanka
   ```

## Manual Publishing (if needed)

If the automated workflow fails, you can publish manually:

1. Clean previous builds:
   ```bash
   rm -rf dist/ build/ *.egg-info
   ```

2. Build the package:
   ```bash
   python -m build
   ```

3. Check the package:
   ```bash
   twine check dist/*
   ```

4. Upload to Test PyPI first (optional):
   ```bash
   twine upload --repository-url https://test.pypi.org/legacy/ dist/*
   ```

5. Upload to PyPI:
   ```bash
   twine upload dist/*
   ```

## Post-Release

1. Update the README.md if needed to reflect the new version
2. Start development on the next version
3. Update CHANGELOG.md with a new "Unreleased" section