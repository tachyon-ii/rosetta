#!/usr/bin/env python3
"""
ROSETTA Stream Parser
Markdown-aware translation system for the CGIOS Foundation project
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding='utf-8') if readme_file.exists() else ""

setup(
    name="rosetta-parser",
    version="1.0.0",
    description="Markdown-aware translation system that preserves code, math, and graphics",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="CGIOS Foundation",
    author_email="",
    url="https://github.com/cgios/rosetta",
    packages=find_packages(where="tools"),
    package_dir={"": "tools"},
    python_requires=">=3.7",
    install_requires=[
        "markdown-it-py>=3.0.0",
        "mdit-py-plugins>=0.4.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "rosetta=rosetta:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Text Processing :: Markup",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    keywords="markdown translation i18n localization parser",
    project_urls={
        "Bug Reports": "https://github.com/cgios/rosetta/issues",
        "Source": "https://github.com/cgios/rosetta",
    },
)
