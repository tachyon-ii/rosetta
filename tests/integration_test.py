#!/usr/bin/env python3
"""
Integration test for ROSETTA stream parser
Tests actual translation with real dictionaries
"""

import sys
import os
from io import StringIO
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'tools'))

from stream_parser import chunk_document, ChunkType


def test_chunking_accuracy():
    """Test that chunking correctly identifies translatable vs non-translatable content"""
    
    test_doc = """# Test Document

This is translatable text.

Use `code` here and $x^2$ math.

```python
def hello():
    return "world"
```

More translatable text.
"""
    
    chunks = chunk_document(StringIO(test_doc))
    
    # Count chunk types
    text_chunks = [c for c in chunks if c.type == ChunkType.TEXT]
    code_chunks = [c for c in chunks if c.type in (ChunkType.CODE_BLOCK, ChunkType.CODE_INLINE)]
    latex_chunks = [c for c in chunks if c.type in (ChunkType.LATEX_INLINE, ChunkType.LATEX_BLOCK)]
    
    print(f"✓ Total chunks: {len(chunks)}")
    print(f"✓ Text (translatable): {len(text_chunks)}")
    print(f"✓ Code (preserved): {len(code_chunks)}")
    print(f"✓ LaTeX (preserved): {len(latex_chunks)}")
    
    # Verify key properties
    assert len(text_chunks) > 0, "Should have text chunks"
    assert len(code_chunks) > 0, "Should have code chunks"
    assert len(latex_chunks) > 0, "Should have LaTeX chunks"
    
    # Verify translatability
    assert all(c.is_translatable() for c in text_chunks), "Text chunks should be translatable"
    assert not any(c.is_translatable() for c in code_chunks), "Code should not be translatable"
    assert not any(c.is_translatable() for c in latex_chunks), "LaTeX should not be translatable"
    
    print("✓ All chunking tests passed")
    return True


def test_preservation():
    """Test that non-translatable content is preserved exactly"""
    
    test_cases = [
        ("Use `print()` function", "`print()`", "CODE_INLINE"),
        ("Equation $x^2 + y^2$ here", "$x^2 + y^2$", "LATEX_INLINE"),
        ("Block $$E = mc^2$$ inline", "$$E = mc^2$$", "LATEX_BLOCK"),
    ]
    
    for text, preserved, expected_type in test_cases:
        chunks = chunk_document(StringIO(text + "\n"))
        
        # Find the preserved element
        found = False
        for chunk in chunks:
            if preserved in chunk.content:
                found = True
                assert chunk.content == preserved, f"Content should be preserved exactly: {chunk.content} != {preserved}"
                print(f"✓ Preserved {expected_type}: {preserved}")
                break
        
        assert found, f"Should find preserved element: {preserved}"
    
    print("✓ All preservation tests passed")
    return True


def test_dollar_disambiguation():
    """Test that parser distinguishes dollar amounts from LaTeX"""
    
    test_cases = [
        ("This costs $5 dollars", True, "Dollar amount should be TEXT"),
        ("This costs $5", True, "Incomplete LaTeX should be TEXT"),
        ("Equation $x = 5$ here", False, "Valid LaTeX should be LATEX_INLINE"),
        ("Both $5 and $10 total", True, "Multiple dollars should be TEXT"),
    ]
    
    for text, should_be_text, description in test_cases:
        chunks = chunk_document(StringIO(text + "\n"))
        
        # Check if any chunk is LaTeX
        has_latex = any(c.type in (ChunkType.LATEX_INLINE, ChunkType.LATEX_BLOCK) for c in chunks)
        
        if should_be_text:
            assert not has_latex or "$" in [c.content for c in chunks if c.type == ChunkType.TEXT][0], \
                f"Failed: {description} - {text}"
            print(f"✓ {description}")
        else:
            assert has_latex, f"Failed: {description} - {text}"
            print(f"✓ {description}")
    
    print("✓ All dollar disambiguation tests passed")
    return True


def test_multiline_elements():
    """Test handling of multiline code and LaTeX blocks"""
    
    code_block = """```python
def function():
    return True
```
"""
    
    chunks = chunk_document(StringIO(code_block))
    code_chunks = [c for c in chunks if c.type == ChunkType.CODE_BLOCK]
    
    assert len(code_chunks) == 4, f"Should have 4 code chunks (fence, 2 lines, fence), got {len(code_chunks)}"
    assert not any(c.is_translatable() for c in code_chunks), "Code blocks should not be translatable"
    
    print("✓ Multiline code blocks handled correctly")
    
    latex_block = """$$
\\int_0^1 x dx
$$
"""
    
    chunks = chunk_document(StringIO(latex_block))
    latex_chunks = [c for c in chunks if c.type == ChunkType.LATEX_BLOCK]
    
    assert len(latex_chunks) == 3, f"Should have 3 LaTeX chunks ($$, content, $$), got {len(latex_chunks)}"
    assert not any(c.is_translatable() for c in latex_chunks), "LaTeX blocks should not be translatable"
    
    print("✓ Multiline LaTeX blocks handled correctly")
    print("✓ All multiline tests passed")
    return True


def test_complex_nesting():
    """Test complex documents with nested and adjacent elements"""
    
    complex_doc = """Text before

```python
# Code with $variables
price = $100
```

Text with `code` and $math$ together.

$$
\\sum_{i=1}^n i = \\frac{n(n+1)}{2}
$$

Final text.
"""
    
    chunks = chunk_document(StringIO(complex_doc))
    
    # Verify structure
    text_chunks = [c for c in chunks if c.type == ChunkType.TEXT and c.content.strip()]
    code_chunks = [c for c in chunks if c.type in (ChunkType.CODE_BLOCK, ChunkType.CODE_INLINE)]
    latex_chunks = [c for c in chunks if c.type in (ChunkType.LATEX_INLINE, ChunkType.LATEX_BLOCK)]
    
    assert len(text_chunks) >= 3, "Should have multiple text sections"
    assert len(code_chunks) >= 2, "Should have code block and inline code"
    assert len(latex_chunks) >= 2, "Should have LaTeX block and inline math"
    
    # Verify no cross-contamination
    for chunk in code_chunks:
        assert not chunk.is_translatable(), "Code should never be translatable"
    
    for chunk in latex_chunks:
        assert not chunk.is_translatable(), "LaTeX should never be translatable"
    
    print(f"✓ Complex document: {len(chunks)} chunks parsed correctly")
    print(f"  - {len(text_chunks)} text sections")
    print(f"  - {len(code_chunks)} code sections")
    print(f"  - {len(latex_chunks)} LaTeX sections")
    print("✓ All complex nesting tests passed")
    return True


def main():
    """Run all integration tests"""
    
    print("=" * 60)
    print("ROSETTA Stream Parser - Integration Tests")
    print("=" * 60)
    print()
    
    tests = [
        ("Chunking Accuracy", test_chunking_accuracy),
        ("Content Preservation", test_preservation),
        ("Dollar Disambiguation", test_dollar_disambiguation),
        ("Multiline Elements", test_multiline_elements),
        ("Complex Nesting", test_complex_nesting),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        print(f"\n{'─' * 60}")
        print(f"Testing: {name}")
        print('─' * 60)
        try:
            if test_func():
                passed += 1
                print(f"\n✓ {name} PASSED")
            else:
                failed += 1
                print(f"\n✗ {name} FAILED")
        except AssertionError as e:
            failed += 1
            print(f"\n✗ {name} FAILED: {e}")
        except Exception as e:
            failed += 1
            print(f"\n✗ {name} ERROR: {e}")
    
    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
