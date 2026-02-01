# ROSETTA Stream Parser

Markdown-aware translation system that preserves code, mathematics, and SVG graphics while translating prose.

## Architecture

```
Input Markdown
     ↓
Stream Parser (state machine)
     ↓
Chunks: [TEXT, CODE, LATEX, SVG]
     ↓
Translate TEXT chunks only
     ↓
Reassemble document
     ↓
Output Markdown
```

## Features

- **Stateful parsing**: Correctly handles nested and multiline elements
- **Preservation**: Code blocks, inline code, LaTeX (inline/block), SVG, HTML tags
- **Translation**: Only prose text is translated
- **Streaming**: Memory-efficient line-by-line processing
- **Comprehensive tests**: 20+ test cases covering edge cases

## Installation

```bash
# Assumes ROSETTA directory structure:
# ROSETTA/
#   ├── dictionaries/
#   ├── tools/
#   ├── udpipe/
#   └── rosetta_parser/  (this directory)

cd ROSETTA/rosetta_parser
python3 -m pytest test_parser.py -v
```

## Usage

### Command Line

```bash
# File to file
./rosetta.py fr input_en.md output_fr.md

# Stdin to stdout
cat input_en.md | ./rosetta.py fr > output_fr.md

# List available languages
./rosetta.py --list

# Debug mode (show chunks without translating)
./rosetta.py --debug fr input.md
```

### Python API

```python
from stream_parser import chunk_document, translate_chunks

# Parse document
with open('input.md') as f:
    chunks = chunk_document(f)

# Translate using custom function
def my_translator(text):
    # Your translation logic here
    return translated_text

result = translate_chunks(chunks, my_translator)
print(result)
```

### Integrated ROSETTA Pipeline

```python
from rosetta import ROSETTATranslator

translator = ROSETTATranslator('fr')  # French

# Translate file
translator.translate_file('input_en.md', 'output_fr.md')

# Translate stream
import sys
translator.translate_document(sys.stdin, sys.stdout)
```

## Supported Elements

### Preserved (Not Translated)

| Element | Syntax | Example |
|---------|--------|---------|
| Code blocks | ` ```...``` ` or `~~~...~~~` | ` ```python\ncode\n``` ` |
| Inline code | `` `...` `` | `` Use `print()` `` |
| LaTeX inline | `$...$` | `The equation $x^2 + y^2 = z^2$` |
| LaTeX blocks | `$$...$$` | `$$\int_0^\infty e^{-x} dx$$` |
| SVG inline | `<svg>...</svg>` | `<svg width="10">...</svg>` |
| HTML tags | `<tag>...</tag>` | `<div class="box">...</div>` |

### Translated

- Plain text paragraphs
- Headings
- Lists
- Emphasis (bold, italic)
- Links (link text only, URLs preserved)
- All prose content

## Edge Cases Handled

✓ Dollar amounts (`$5` and `$10`) vs LaTeX (`$x = 5$`)  
✓ Code with dollar signs (`` `$PATH` ``)  
✓ LaTeX with backticks (`$f'(x)$`)  
✓ Unclosed blocks (treated as continuing to EOF)  
✓ Multiple inline elements on same line  
✓ Nested fence markers (``` inside ~~~)  
✓ Empty lines and whitespace  

## Testing

### Run Test Suite

```bash
# All tests
python3 test_parser.py

# Verbose output
python3 test_parser.py -v

# Specific test
python3 -m pytest test_parser.py::TestStreamParser::test_inline_code -v
```

### Test Files

- `tests/simple.md` - Basic elements
- `tests/edge_cases.md` - Boundary conditions
- `tests/test_document.md` - Realistic document

### Chunk Analysis

```bash
# See how document is chunked
python3 stream_parser.py tests/test_document.md

# Example output:
#   0 ✓ TEXT            L  1: # Foundation Project Overview
#   1 ✗ CODE_INLINE     L  3: `normalize.py`
#   2 ✓ TEXT            L  3:  script to process
#   3 ✗ LATEX_INLINE    L  5: $f(x) = x^2$
```

## Performance

- **Parsing**: ~100K lines/sec (Python stream processing)
- **Translation**: Depends on UDPipe + dictionary lookup
- **Memory**: O(1) for streaming, O(n) for chunk list

## Implementation Details

### State Machine

```python
States:
- TEXT (default)
- CODE_BLOCK (inside ```)
- LATEX_BLOCK (inside $$)

Transitions:
- TEXT + ``` → CODE_BLOCK
- CODE_BLOCK + ``` → TEXT
- TEXT + $$ → LATEX_BLOCK
- LATEX_BLOCK + $$ → TEXT
```

### Inline Parsing

Priority order (highest first):
1. Inline code: `` `...` ``
2. LaTeX blocks: `$$...$$`
3. LaTeX inline: `$...$`
4. SVG: `<svg>...</svg>`
5. HTML: `<tag>...</tag>`

### Translation Integration

```
Text Chunk
    ↓
normalize.py (ROSETTA)
    ↓
udpipe --tokenize --tag
    ↓
translate.py (dictionary lookup)
    ↓
Translated Text
```

## Limitations

1. **Multiline inline elements**: SVG/HTML spanning multiple lines may not parse correctly
2. **Malformed markdown**: Parser assumes well-formed input
3. **Language detection**: Must specify target language explicitly
4. **RTL languages**: Right-to-left rendering handled by client, not parser

## Future Enhancements

- [ ] Multiline SVG/HTML detection
- [ ] Configurable preservation rules
- [ ] Translation memory/caching
- [ ] Parallel chunk translation
- [ ] Progress indicators for large files
- [ ] Automatic language detection from filename

## License

Part of the CGIOS Foundation project.

## See Also

- `ROSETTA/tools/normalize.py` - Text normalization
- `ROSETTA/tools/translate.py` - Dictionary-based translation
- UDPipe - Universal Dependencies parser
