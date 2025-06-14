"""Setup script for mcp-kanka."""

import os

from setuptools import find_packages, setup

# Read version from _version.py
version_file = os.path.join("src", "mcp_kanka", "_version.py")
version_dict = {}
with open(version_file) as f:
    exec(f.read(), version_dict)
__version__ = version_dict["__version__"]

# Read the README for long description
with open("README.md", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="mcp-kanka",
    version=__version__,
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    license="MIT",
    author="Erv Walter",
    author_email="erv@ewal.net",
    description="MCP server for Kanka API integration",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ervwalter/mcp-kanka",
    project_urls={
        "Bug Reports": "https://github.com/ervwalter/mcp-kanka/issues",
        "Source": "https://github.com/ervwalter/mcp-kanka",
        "Documentation": "https://github.com/ervwalter/mcp-kanka#readme",
        "Kanka API": "https://kanka.io/en-US/docs/1.0",
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Games/Entertainment :: Role-Playing",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
        "Typing :: Typed",
    ],
    python_requires=">=3.10",
    install_requires=[
        "mcp==1.9.4",
        "python-kanka==2.2.0",
        "mistune==3.1.3",
        "beautifulsoup4==4.13.4",
        "python-dotenv==1.1.0",
        "markdownify==1.1.0",
    ],
    extras_require={
        "dev": [
            "pytest==8.4.0",
            "pytest-cov==6.2.1",
            "pytest-mock==3.14.1",
            "pytest-asyncio==1.0.0",
            "black==25.1.0",
            "isort==6.0.1",
            "ruff==0.11.13",
            "mypy==1.16.0",
            "pre-commit==4.2.0",
            "bump2version==1.0.1",
        ],
    },
    keywords="kanka mcp api worldbuilding rpg campaign tabletop ttrpg dnd pathfinder",
    entry_points={
        "console_scripts": [
            "mcp-kanka=mcp_kanka.cli:run",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
