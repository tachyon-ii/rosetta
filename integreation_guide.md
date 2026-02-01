# ROSETTA Stream Parser Integration Guide

## File Placement

Your ROSETTA directory structure should be:

```
ROSETTA/
├── dictionaries/
│   ├── en_es.txt
│   ├── en_fr.txt
│   ├── en_zh.txt
│   ├── en_hi.txt (to be generated)
│   ├── en_ar.txt (to be generated)
│   └── find_untranslated_ranges.py
├── tools/
│   ├── normalize.py
│   ├── translate.py
│   ├── stream_parser.py         ← ADD THIS
│   └── rosetta.py                ← ADD THIS (main CLI tool)
├── tests/
│   ├── integration_test.py
│   ├── test_parser.py
│   ├── longer.txt
│   ├── spanish_test.txt
│   ├── simple.md                 ← ADD THIS
│   ├── edge_cases.md             ← ADD THIS
│   └── test_document.md          ← ADD THIS
└── udpipe/
    ├── udpipe (binary)
    └── english-ud-1.2-160523.udpipe
```

## Installation Steps

### 1. Copy Core Parser Files to tools/

```bash
cd ROSETTA
cp /path/to/outputs/rosetta_parser/stream_parser.py tools/
cp /path/to/outputs/rosetta_parser/rosetta.py tools/
chmod +x tools/rosetta.py
```

### 2. Copy Test Files to tests/

```bash
cp /path/to/outputs/rosetta_parser/tests/*.md tests/
cp /path/to/outputs/rosetta_parser/test_parser.py tests/
cp /path/to/outputs/rosetta_parser/integration_test.py tests/
```

### 3. Update test_parser.py imports

Since test_parser.py will now be in `tests/` but needs to import from `tools/`, update the import:

```python
# In tests/test_parser.py, change:
# sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# from stream_parser import ...

# To:
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'tools'))
from stream_parser import ...
```

### 4. Verify Installation

```bash
cd ROSETTA

# Test parser directly
python3 tools/stream_parser.py tests/simple.md

# Run unit tests
cd tests
python3 test_parser.py -v

# Run integration tests
python3 integration_test.py

# Test CLI tool
cd ..
python3 tools/rosetta.py --list
```

## Usage Examples

### Basic Translation

```bash
cd ROSETTA

# Translate markdown file (French)
python3 tools/rosetta.py fr input_en.md output_fr.md

# Translate via pipe (Hindi)
cat documentation_en.md | python3 tools/rosetta.py hi > documentation_hi.md

# Debug mode - see how document is chunked
python3 tools/rosetta.py --debug fr tests/test_document.md
```

### Python API

```python
# From any Python script in ROSETTA/
import sys
sys.path.append('tools')

from stream_parser import chunk_document, translate_chunks
from rosetta import ROSETTATranslator

# Option 1: Use integrated translator
translator = ROSETTATranslator('fr', rosetta_root='.')
translator.translate_file('input_en.md', 'output_fr.md')

# Option 2: Custom translation function
with open('input.md') as f:
    chunks = chunk_document(f)

def my_translator(text):
    # Your custom translation logic
    return translated_text

result = translate_chunks(chunks, my_translator)
```

## Configuration

The `rosetta.py` tool auto-detects the ROSETTA directory structure. If you need to specify paths manually:

```bash
python3 tools/rosetta.py --rosetta-root /path/to/ROSETTA fr input.md output.md
```

## Quick Start

After installation, test with:

```bash
cd ROSETTA

# 1. Check available dictionaries
python3 tools/rosetta.py --list

# 2. Test on simple document
echo "# Test\nThis is a test with \`code\` and \$x^2\$ math." > test.md
python3 tools/rosetta.py fr test.md test_fr.md
cat test_fr.md

# 3. See chunking analysis
python3 tools/rosetta.py --debug fr test.md
```

## Testing

Run the full test suite:

```bash
cd ROSETTA/tests

# Unit tests (20 tests)
python3 test_parser.py -v

# Integration tests (5 test suites)
python3 integration_test.py
```

All tests should pass:
```
Unit Tests:        20/20 passed
Integration Tests:  5/5 passed
```

## Troubleshooting

### Import Errors

If you see `ModuleNotFoundError: No module named 'stream_parser'`:

```bash
# Make sure you're running from the right directory
cd ROSETTA
python3 -c "import sys; sys.path.append('tools'); from stream_parser import chunk_document; print('OK')"
```

### Dictionary Not Found

If you see `Error: Dictionary not found: dictionaries/en_XX.txt`:

```bash
# Check available dictionaries
ls -lh dictionaries/en_*.txt

# The dictionary file must match the language code
python3 tools/rosetta.py fr ...  # requires dictionaries/en_fr.txt
```

### UDPipe Errors

If you see errors about UDPipe:

```bash
# Verify UDPipe is installed and executable
ls -l udpipe/udpipe
./udpipe/udpipe --version

# Make sure model file exists
ls -l udpipe/english-ud-1.2-160523.udpipe
```

## File Descriptions

### Core Files

- **tools/stream_parser.py** (228 lines)
  - State machine parser for markdown
  - Chunks documents into TEXT/CODE/LATEX/SVG
  - Can be used standalone or via rosetta.py

- **tools/rosetta.py** (312 lines)
  - Main CLI tool for translation
  - Integrates stream_parser with normalize → udpipe → translate pipeline
  - Supports file, stdin/stdout, and Python API usage

### Test Files

- **tests/test_parser.py** (318 lines)
  - 20 unit tests for stream_parser
  - Tests parsing accuracy, edge cases, preservation

- **tests/integration_test.py** (274 lines)
  - 5 integration test suites
  - Tests chunking, preservation, disambiguation, multiline, nesting

- **tests/simple.md** - Basic markdown with code/math
- **tests/edge_cases.md** - Boundary conditions and tricky cases
- **tests/test_document.md** - Realistic Foundation documentation

## Next Steps

1. ✅ Install files (see Installation Steps above)
2. ✅ Run tests to verify installation
3. ✅ Try translating a real Foundation document
4. ✅ Integrate into your workflow

## Notes

- The parser preserves code, math, and SVG exactly
- Only prose text is translated
- Streaming architecture handles large files efficiently
- All 25 tests passing in development environment
