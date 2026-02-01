# ROSETTA Stream Parser - Installation

## Quick Install

```bash
cd ROSETTA
pip install -r requirements.txt
```

## Development Install

For development with editable install:

```bash
cd ROSETTA
pip install -e .
```

This allows you to modify the code without reinstalling.

## Dependencies

### Core Dependencies
- **Python 3.7+** - Base requirement
- **markdown-it-py** - Fast, spec-compliant markdown parser with AST
- **mdit-py-plugins** - Extensions for tables, footnotes, etc.

### Existing ROSETTA Dependencies
- **UDPipe** - Universal Dependencies parser (already installed)
- **dictionaries/** - Translation dictionaries (already present)

### Optional Development Dependencies
- **pytest** - Testing framework
- **pytest-cov** - Coverage reporting
- **black** - Code formatting
- **flake8** - Linting

## Installation Methods

### Method 1: pip (Recommended)

```bash
pip install markdown-it-py mdit-py-plugins
```

### Method 2: System Package Manager

**macOS:**
```bash
# Python from Homebrew usually works
brew install python3
pip3 install markdown-it-py mdit-py-plugins
```

**Ubuntu/Debian:**
```bash
sudo apt install python3-pip
pip3 install markdown-it-py mdit-py-plugins
```

### Method 3: Virtual Environment (Isolated)

```bash
cd ROSETTA
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Verification

Check installation:

```bash
python3 -c "from markdown_it import MarkdownIt; print('✓ markdown-it-py installed')"
python3 -c "from mdit_py_plugins import tables; print('✓ mdit-py-plugins installed')"
```

## Usage After Installation

```bash
# Run translator
python3 tools/rosetta.py fr input.md output.md

# Run tests
cd tests
python3 test_parser.py -v

# List available dictionaries
python3 tools/rosetta.py --list
```

## Troubleshooting

### ImportError: No module named 'markdown_it'

```bash
pip install --user markdown-it-py
```

### Permission Denied

Use `--user` flag or virtual environment:

```bash
pip install --user markdown-it-py mdit-py-plugins
```

### Python Version Issues

Check Python version:

```bash
python3 --version  # Should be 3.7 or higher
```

If too old, install newer Python:
- macOS: `brew install python@3.11`
- Ubuntu: `sudo apt install python3.11`

## Offline Installation

For systems without internet (Foundation use case):

1. **Download wheels on connected machine:**
```bash
pip download markdown-it-py mdit-py-plugins -d ./packages/
```

2. **Transfer `packages/` directory to offline system**

3. **Install from local files:**
```bash
pip install --no-index --find-links=./packages/ markdown-it-py mdit-py-plugins
```

## Minimal Installation (No Testing)

If you only need translation (not development):

```bash
pip install markdown-it-py
```

The plugins are optional for basic functionality.
