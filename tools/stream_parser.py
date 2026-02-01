#!/usr/bin/env python3
"""
ROSETTA Stream Parser
Parses markdown documents, translating prose while preserving:
- Code blocks (```...```)
- Inline code (`...`)
- LaTeX inline ($...$)
- LaTeX blocks ($$...$$)
- SVG blocks (<svg>...</svg>)
- HTML tags
"""

import re
from enum import Enum, auto
from typing import List, Tuple, TextIO
from dataclasses import dataclass


class ChunkType(Enum):
    """Types of content chunks"""
    TEXT = auto()           # Translatable prose
    CODE_INLINE = auto()    # `code`
    CODE_BLOCK = auto()     # ```code```
    LATEX_INLINE = auto()   # $math$
    LATEX_BLOCK = auto()    # $$math$$
    SVG = auto()            # <svg>...</svg>
    HTML = auto()           # <tag>...</tag>


@dataclass
class Chunk:
    """A parsed content chunk"""
    type: ChunkType
    content: str
    line_number: int
    
    def is_translatable(self) -> bool:
        """Returns True if this chunk should be translated"""
        return self.type == ChunkType.TEXT


class MarkdownStreamParser:
    """
    Streaming markdown parser with state machine.
    Chunks content into translatable and non-translatable segments.
    """
    
    def __init__(self):
        self.chunks = []
        self.line_number = 0
        self.in_code_block = False
        self.in_latex_block = False
        self.code_fence_marker = None  # Track ``` or ~~~
        
    def parse_line(self, line: str) -> List[Chunk]:
        """Parse a single line into chunks"""
        self.line_number += 1
        chunks = []
        
        # Check for code block boundaries
        code_fence_match = re.match(r'^(```|~~~)', line)
        if code_fence_match:
            fence = code_fence_match.group(1)
            if not self.in_code_block:
                # Starting code block
                self.in_code_block = True
                self.code_fence_marker = fence
                chunks.append(Chunk(ChunkType.CODE_BLOCK, line, self.line_number))
                return chunks
            elif fence == self.code_fence_marker:
                # Ending code block
                self.in_code_block = False
                self.code_fence_marker = None
                chunks.append(Chunk(ChunkType.CODE_BLOCK, line, self.line_number))
                return chunks
        
        # Inside code block - don't parse further
        if self.in_code_block:
            chunks.append(Chunk(ChunkType.CODE_BLOCK, line, self.line_number))
            return chunks
        
        # Check for LaTeX block boundaries
        if line.strip().startswith('$$'):
            if not self.in_latex_block:
                self.in_latex_block = True
            else:
                self.in_latex_block = False
            chunks.append(Chunk(ChunkType.LATEX_BLOCK, line, self.line_number))
            return chunks
        
        # Inside LaTeX block - don't parse further
        if self.in_latex_block:
            chunks.append(Chunk(ChunkType.LATEX_BLOCK, line, self.line_number))
            return chunks
        
        # Parse inline elements
        chunks.extend(self._parse_inline(line))
        return chunks
    
    def _parse_inline(self, line: str) -> List[Chunk]:
        """Parse inline elements (code, latex, svg, html)"""
        chunks = []
        pos = 0
        
        # Patterns in priority order
        patterns = [
            # Inline code: `code` (non-greedy, no nested backticks)
            (ChunkType.CODE_INLINE, r'`([^`]+)`'),
            
            # LaTeX blocks: $$...$$ (must come before inline)
            (ChunkType.LATEX_BLOCK, r'\$\$([^$]+?)\$\$'),
            
            # LaTeX inline: $...$ 
            # Must contain typical math: operators, superscript/subscript, backslash, greek letters, or equals
            # This avoids matching "$5 and $10" while catching "$x = 5$"
            (ChunkType.LATEX_INLINE, r'\$([^$\n]*(?:[\\^_{}=+*/><\[\]()]|\\[a-zA-Z]+)[^$\n]*?)\$'),
            
            # SVG blocks: <svg...>...</svg> (multiline handled separately)
            (ChunkType.SVG, r'<svg[^>]*>.*?</svg>'),
            
            # HTML tags: <tag>...</tag>
            (ChunkType.HTML, r'<([a-zA-Z][a-zA-Z0-9]*)[^>]*>.*?</\1>'),
        ]
        
        text_start = 0
        
        while pos < len(line):
            earliest_match = None
            earliest_pos = len(line)
            match_type = None
            
            # Find earliest match among all patterns
            for chunk_type, pattern in patterns:
                match = re.search(pattern, line[pos:], re.DOTALL)
                if match and match.start() < earliest_pos:
                    earliest_match = match
                    earliest_pos = match.start()
                    match_type = chunk_type
            
            if earliest_match:
                # Add any text before the match
                if pos + earliest_pos > text_start:
                    text = line[text_start:pos + earliest_pos]
                    if text:
                        chunks.append(Chunk(ChunkType.TEXT, text, self.line_number))
                
                # Add the matched element
                chunks.append(Chunk(
                    match_type,
                    earliest_match.group(0),
                    self.line_number
                ))
                
                pos += earliest_pos + len(earliest_match.group(0))
                text_start = pos
            else:
                # No more matches, rest is text
                break
        
        # Add remaining text
        if text_start < len(line):
            text = line[text_start:]
            if text:
                chunks.append(Chunk(ChunkType.TEXT, text, self.line_number))
        
        return chunks
    
    def parse_stream(self, input_stream: TextIO) -> List[Chunk]:
        """Parse entire stream into chunks"""
        chunks = []
        for line in input_stream:
            chunks.extend(self.parse_line(line))
        return chunks
    
    def reset(self):
        """Reset parser state"""
        self.chunks = []
        self.line_number = 0
        self.in_code_block = False
        self.in_latex_block = False
        self.code_fence_marker = None


def chunk_document(input_stream: TextIO) -> List[Chunk]:
    """
    Convenience function to parse a document into chunks.
    
    Args:
        input_stream: Input text stream
        
    Returns:
        List of Chunk objects
    """
    parser = MarkdownStreamParser()
    return parser.parse_stream(input_stream)


def translate_chunks(chunks: List[Chunk], translate_func) -> str:
    """
    Translate chunks using provided translation function.
    
    Args:
        chunks: List of parsed chunks
        translate_func: Function(text: str) -> str for translation
        
    Returns:
        Fully translated document as string
    """
    result = []
    for chunk in chunks:
        if chunk.is_translatable():
            result.append(translate_func(chunk.content))
        else:
            result.append(chunk.content)
    return ''.join(result)


if __name__ == '__main__':
    import sys
    
    # Demo mode - just chunk and display
    if len(sys.argv) > 1:
        with open(sys.argv[1]) as f:
            chunks = chunk_document(f)
            
        print(f"Parsed {len(chunks)} chunks:")
        for i, chunk in enumerate(chunks):
            translatable = "✓" if chunk.is_translatable() else "✗"
            preview = chunk.content[:50].replace('\n', '\\n')
            print(f"{i:3d} {translatable} {chunk.type.name:15s} L{chunk.line_number:3d}: {preview}")
    else:
        print("Usage: stream_parser.py <markdown_file>")
        print("Parses markdown and displays chunk analysis")
