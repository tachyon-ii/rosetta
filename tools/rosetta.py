#!/usr/bin/env python3
"""
ROSETTA Markdown Translator - Proper AST Implementation
Correctly preserves ALL markdown structure while translating only text content
"""

import sys
import os
import subprocess
import re
import string
from io import StringIO
from pathlib import Path
from typing import List, Dict, Any, Tuple

from markdown_it import MarkdownIt
from markdown_it.token import Token


class ROSETTAMarkdownTranslator:
    """
    AST-based markdown translator with proper structure preservation.
    Handles tables, lists, headers, code blocks, etc. correctly.
    """
    
    def __init__(self, target_lang: str, rosetta_root: str = None):
        """Initialize translator."""
        self.target_lang = target_lang
        
        if rosetta_root is None:
            self.rosetta_root = Path(__file__).parent.parent
        else:
            self.rosetta_root = Path(rosetta_root)
        
        self.dict_file = self.rosetta_root / 'dictionaries' / f'en_{target_lang}.txt'
        self.normalize = self.rosetta_root / 'tools' / 'normalize.py'
        self.translate_tool = self.rosetta_root / 'tools' / 'translate.py'
        self.udpipe = self.rosetta_root / 'udpipe' / 'udpipe'
        self.udpipe_model = self.rosetta_root / 'udpipe' / 'english-ud-1.2-160523.udpipe'
        
        self._validate_paths()
        
        # Initialize markdown parser with table support
        # Use 'gfm-like' preset or explicitly enable tables
        self.md = MarkdownIt('commonmark', {'breaks': False, 'html': True})
        self.md.enable('table')  # Enable table parsing
    
    def _validate_paths(self):
        """Validate required files exist"""
        required = {
            'Dictionary': self.dict_file,
            'Normalize': self.normalize,
            'Translate': self.translate_tool,
            'UDPipe': self.udpipe,
            'Model': self.udpipe_model,
        }
        
        missing = [f"{name}: {path}" for name, path in required.items() if not path.exists()]
        if missing:
            raise FileNotFoundError("Missing:\n" + "\n".join(f"  - {m}" for m in missing))
    
    @staticmethod
    def _increment_string(s):
        """Increments a string in the sequence a, ..., z, aa, ab, ..., az, ba, ..."""
        if not s:
            return 'a'
        
        alphabet = string.ascii_lowercase
        last_char = s[-1]
        
        if last_char != 'z':
            new_last_char = alphabet[alphabet.index(last_char) + 1]
            return s[:-1] + new_last_char
        else:
            prefix = s[:-1]
            if prefix:
                return ROSETTAMarkdownTranslator._increment_string(prefix) + 'a'
            else:
                return 'aa'
    
    def translate_document(self, input_stream, output_stream):
        """Translate markdown document preserving all structure."""
        markdown_text = input_stream.read()
        
        # Placeholder tracking - ONE counter for all replacements
        placeholder_map = {}
        counter = ['a']  # Shared across all phases, starts at 'a'
        
        def make_placeholder(content):
            """Create placeholder and store original content.
            
            Format: rosettablock{seq} where seq is a, b, ..., z, aa, ab, ...
            All lowercase letters - UDPipe will treat as single token.
            """
            placeholder = f'rosettablock{counter[0]}'
            placeholder_map[placeholder] = content
            counter[0] = self._increment_string(counter[0])
            return placeholder
        
        # STEP 1: Replace math, inline code, and links in raw markdown (BEFORE parsing)
        # These are delimiter-wrapped content that should pass through unchanged.
        
        # Track which placeholders are links (need text translation later)
        link_placeholders = {}
        
        # Block math first (to avoid matching $$ as two inline $)
        markdown_with_placeholders = re.sub(
            r'\$\$[^\$]+\$\$',
            lambda m: make_placeholder(m.group(0)),
            markdown_text,
            flags=re.DOTALL
        )
        
        # Inline math - but be careful not to match currency!
        # Currency pattern: $5, $10, $100, $1.50, $1,000 - digit immediately after $
        # Math pattern: $x$, $x^2$, $\frac{1}{2}$ - letter/backslash after $
        markdown_with_placeholders = re.sub(
            r'\$(?!\d)([^\$\n]+)\$',
            lambda m: make_placeholder(m.group(0)),
            markdown_with_placeholders
        )
        
        # Inline code - backtick-wrapped content (but not code fences ```)
        # Match `content` but not ```content```
        markdown_with_placeholders = re.sub(
            r'(?<!`)`([^`\n]+)`(?!`)',
            lambda m: make_placeholder(m.group(0)),
            markdown_with_placeholders
        )
        
        # Markdown links - [text](url) and [text](url "title")
        # Store these separately so we can translate the text later
        def make_link_placeholder(m):
            placeholder = make_placeholder(m.group(0))
            link_placeholders[placeholder] = m.group(0)
            return placeholder
        
        markdown_with_placeholders = re.sub(
            r'\[([^\]]*)\]\(([^)]+)\)',
            make_link_placeholder,
            markdown_with_placeholders
        )
        
        # Reference-style link definitions - [ref]: url "title"
        markdown_with_placeholders = re.sub(
            r'^\[([^\]]+)\]:\s*(\S+)(?:\s+"[^"]*")?\s*$',
            lambda m: make_placeholder(m.group(0)),
            markdown_with_placeholders,
            flags=re.MULTILINE
        )
        
        # Autolinks - <https://...> and <email@...>
        markdown_with_placeholders = re.sub(
            r'<(https?://[^>]+|[^>]+@[^>]+)>',
            lambda m: make_placeholder(m.group(0)),
            markdown_with_placeholders
        )
        
        # STEP 2: Parse markdown to AST
        tokens = self.md.parse(markdown_with_placeholders)
        
        # STEP 3: Walk AST and replace code/SVG with placeholders
        # Uses same make_placeholder, so counter continues from where math left off
        self._replace_code_in_ast(tokens, placeholder_map, counter)
        
        # STEP 4: Extract translatable text from AST (now has placeholders)
        text_items = self._extract_translatable_text(tokens)
        
        if not text_items:
            # No translatable content
            result = markdown_with_placeholders
            # Restore placeholders
            for placeholder, original in placeholder_map.items():
                result = result.replace(placeholder, original)
            output_stream.write(result)
            return
        
        # STEP 5: Translate (placeholders pass through)
        # Batch translate all text through a single pipeline for performance.
        # Use a marker to preserve line boundaries through UDPipe.
        # The marker must: (1) survive as a single token, (2) not get translated
        LINE_MARKER = 'XLINEBREAKX'
        
        texts_to_translate = [item['text'] for item in text_items]
        combined = f' {LINE_MARKER} '.join(texts_to_translate)
        translated_combined = self._translate_batch(combined)
        
        # Split back on the marker
        translations = translated_combined.split(LINE_MARKER)
        translations = [t.strip() for t in translations]
        
        for i, item in enumerate(text_items):
            if i < len(translations):
                item['translation'] = translations[i]
        
        # STEP 6: Render markdown (with placeholders)
        result = self._render_tokens(tokens, text_items)
        
        # STEP 6.5: Translate link text
        # Links were preserved as placeholders with full [text](url) structure.
        # Now we translate just the text portion and update the placeholder map.
        if link_placeholders:
            # Extract link texts
            link_texts = []
            link_keys = list(link_placeholders.keys())
            for placeholder in link_keys:
                link_md = link_placeholders[placeholder]
                # Extract text from [text](url)
                match = re.match(r'\[([^\]]*)\]\(([^)]+)\)', link_md)
                if match:
                    link_texts.append(match.group(1))
                else:
                    link_texts.append('')
            
            # Batch translate link texts (single pipeline call)
            if any(link_texts):
                combined_links = f' {LINE_MARKER} '.join(link_texts)
                translated_links = self._translate_batch(combined_links)
                translated_link_texts = [t.strip() for t in translated_links.split(LINE_MARKER)]
                
                # Update placeholder_map with translated links
                for i, placeholder in enumerate(link_keys):
                    if i < len(translated_link_texts):
                        link_md = link_placeholders[placeholder]
                        match = re.match(r'\[([^\]]*)\]\(([^)]+)\)', link_md)
                        if match:
                            translated_text = translated_link_texts[i]
                            url_part = match.group(2)
                            # Reconstruct link with translated text
                            placeholder_map[placeholder] = f'[{translated_text}]({url_part})'
        
        # STEP 7: Replace all placeholders with original content
        # Sort by length descending so longer sequences (aa, ab) are replaced before shorter (a, b)
        # This prevents 'rosettablocka' from matching inside 'rosettablockaa'
        for placeholder in sorted(placeholder_map.keys(), key=len, reverse=True):
            original = placeholder_map[placeholder]
            
            # Check if placeholder appears with leading indentation
            # Pattern: start of line, whitespace, placeholder
            indent_pattern = re.compile(r'^([ \t]*)' + re.escape(placeholder), re.MULTILINE)
            
            def replace_with_indent(match):
                indent = match.group(1)
                if indent and '\n' in original:
                    # Apply indent to all lines of original content
                    lines = original.split('\n')
                    # All lines get the same indent
                    indented_lines = [indent + line for line in lines]
                    return '\n'.join(indented_lines)
                else:
                    return indent + original
            
            result = indent_pattern.sub(replace_with_indent, result)
            # Also handle any remaining non-indented occurrences
            result = result.replace(placeholder, original)
        
        output_stream.write(result)
    
    
    def _replace_code_in_ast(self, tokens: List[Token], placeholder_map: dict, counter: list):
        """
        Walk AST and replace code/SVG content with placeholders.
        Uses shared counter that continues from math replacement phase.
        """
        for token in tokens:
            # Replace fence blocks (code blocks)
            # Store the CONTENT only, let the renderer add the fences
            if token.type == 'fence':
                placeholder = f'rosettablock{counter[0]}'
                # Strip trailing newlines - renderer will add appropriate newline
                placeholder_map[placeholder] = token.content.rstrip('\n')
                counter[0] = self._increment_string(counter[0])
                token.content = placeholder
                # Keep token.info (language) intact for rendering
            
            # Replace inline HTML/SVG elements
            # Note: code_inline is already handled in raw markdown phase
            if token.type == 'inline' and token.children:
                for child in token.children:
                    if child.type in ('html_inline', 'html_block'):
                        placeholder = f'rosettablock{counter[0]}'
                        placeholder_map[placeholder] = child.content
                        counter[0] = self._increment_string(counter[0])
                        child.content = placeholder
    
    def _extract_translatable_text(self, tokens: List[Token]) -> List[Dict]:
        """
        Extract translatable text from tokens.
        Returns list of dicts with text and token reference.
        """
        items = []
        self._extract_from_tokens(tokens, items)
        return items
    
    def _extract_from_tokens(self, tokens: List[Token], items: List[Dict], depth=0):
        """Recursively extract text from token tree."""
        for token in tokens:
            # Skip code blocks entirely
            if token.type in ('fence', 'code_block', 'html_block'):
                continue
            
            # Extract from inline content
            if token.type == 'inline' and token.children:
                text = self._extract_from_inline(token.children)
                if text.strip():
                    items.append({
                        'text': text,
                        'token': token,
                        'translation': None
                    })
            
            # Recurse into children if present
            if hasattr(token, 'children') and token.children:
                self._extract_from_tokens(token.children, items, depth + 1)
    
    def _extract_from_inline(self, inline_tokens: List[Token]) -> str:
        """
        Extract text from inline tokens.
        Math and inline code are already replaced with placeholders in raw markdown.
        HTML content is replaced in AST phase.
        """
        parts = []
        
        for token in inline_tokens:
            if token.type == 'text':
                parts.append(token.content)
            elif token.type == 'code_inline':
                # After raw markdown replacement, this token's content might still
                # contain a placeholder (if it was `code`) or might be empty/changed
                # Just pass through whatever is there
                parts.append(token.content)
            elif token.type == 'html_inline':
                # Content is a placeholder from AST phase
                parts.append(token.content)
            elif token.type in ('softbreak', 'hardbreak'):
                parts.append(' ')
            # Skip formatting open/close tags - structure only
        
        return ''.join(parts)
    
    def _render_tokens(self, tokens: List[Token], text_items: List[Dict]) -> str:
        """Render tokens back to markdown with translations."""
        result = []
        item_idx = [0]  # Use list to allow modification in nested function
        
        def render_token_list(token_list):
            """
            Render tokens with context tracking using state variables.
            """
            i = 0
            list_depth = 0  # Track how deep we are in lists
            blockquote_depth = 0  # Track how deep we are in blockquotes
            
            while i < len(token_list):
                token = token_list[i]
                
                # Calculate indentation based on list depth
                indent = '   ' * list_depth if list_depth > 0 else ''
                # Calculate blockquote prefix
                bq_prefix = '> ' * blockquote_depth if blockquote_depth > 0 else ''
                
                # Headings
                if token.type == 'heading_open':
                    level = int(token.tag[1])  # h1->1, h2->2
                    result.append('\n' if result else '')  # Blank line before heading
                    result.append(bq_prefix + '#' * level + ' ')
                    i += 1
                    continue
                
                if token.type == 'heading_close':
                    result.append('\n\n')
                    i += 1
                    continue
                
                # Paragraphs
                if token.type == 'paragraph_open':
                    if blockquote_depth > 0:
                        result.append(bq_prefix)
                    elif list_depth > 0:
                        result.append(indent)
                    i += 1
                    continue
                
                if token.type == 'paragraph_close':
                    result.append('\n')
                    if blockquote_depth > 0:
                        result.append(bq_prefix + '\n')
                    elif list_depth == 0:
                        result.append('\n')
                    i += 1
                    continue
                
                # Code blocks - content is a placeholder, don't mangle it
                if token.type == 'fence':
                    result.append(indent + '```' + (token.info or '') + '\n')
                    # Content is a placeholder - output with newline
                    # Original content has trailing newlines stripped, so we add one
                    result.append(indent + token.content + '\n')
                    result.append(indent + '```\n')
                    if list_depth == 0:
                        result.append('\n')
                    i += 1
                    continue
                
                if token.type == 'code_block':
                    result.append(indent + '    ' + token.content)  # Indented code
                    if list_depth == 0:
                        result.append('\n')
                    i += 1
                    continue
                
                # HTML blocks
                if token.type == 'html_block':
                    result.append(indent + token.content)
                    i += 1
                    continue
                
                # Lists - track depth
                if token.type in ('bullet_list_open', 'ordered_list_open'):
                    if list_depth == 0:
                        result.append('\n')  # Blank line before top-level list
                    list_depth += 1
                    i += 1
                    continue
                
                if token.type in ('bullet_list_close', 'ordered_list_close'):
                    list_depth -= 1
                    if list_depth == 0:
                        result.append('\n')  # Blank line after top-level list
                    i += 1
                    continue
                
                if token.type == 'list_item_open':
                    # Use previous indent level (before the item itself)
                    item_indent = '   ' * (list_depth - 1) if list_depth > 1 else ''
                    marker = token.markup
                    if marker in ('-', '*', '+'):
                        result.append(item_indent + f'{marker} ')
                    else:
                        # Ordered list - always use 1.
                        result.append(item_indent + '1. ')
                    i += 1
                    continue
                
                if token.type == 'list_item_close':
                    # NO extra newline after list item
                    i += 1
                    continue
                
                # Tables
                if token.type == 'table_open':
                    result.append('\n')  # Blank before table
                    i += 1
                    continue
                
                if token.type == 'table_close':
                    result.append('\n')  # Blank after table
                    i += 1
                    continue
                
                if token.type == 'thead_open':
                    i += 1
                    continue
                
                if token.type == 'thead_close':
                    # Add separator row after header
                    # Count columns by counting th_open tokens
                    col_count = 0
                    j = i - 1
                    while j >= 0:
                        if token_list[j].type == 'thead_open':
                            break
                        if token_list[j].type == 'th_open':
                            col_count += 1
                        j -= 1
                    
                    if col_count > 0:
                        result.append('| ' + ' | '.join(['---'] * col_count) + ' |\n')
                    i += 1
                    continue
                
                if token.type == 'tbody_open':
                    i += 1
                    continue
                
                if token.type == 'tbody_close':
                    i += 1
                    continue
                
                if token.type == 'tr_open':
                    result.append('| ')
                    i += 1
                    continue
                
                if token.type == 'tr_close':
                    result.append('\n')
                    i += 1
                    continue
                
                if token.type in ('th_open', 'td_open'):
                    i += 1
                    continue
                
                if token.type in ('th_close', 'td_close'):
                    result.append(' | ')
                    i += 1
                    continue
                
                # Inline content (the actual text)
                if token.type == 'inline':
                    # Find corresponding translation
                    if item_idx[0] < len(text_items):
                        item = text_items[item_idx[0]]
                        if item['token'] == token:
                            translated = item['translation'] or item['text']
                            result.append(self._render_inline(token.children, translated))
                            item_idx[0] += 1
                    i += 1
                    continue
                
                # Horizontal rule
                if token.type == 'hr':
                    result.append('\n---\n\n')
                    i += 1
                    continue
                
                # Blockquote
                if token.type == 'blockquote_open':
                    blockquote_depth += 1
                    i += 1
                    continue
                
                if token.type == 'blockquote_close':
                    blockquote_depth -= 1
                    if blockquote_depth == 0:
                        result.append('\n')
                    i += 1
                    continue
                
                # Default: skip unknown tokens
                i += 1
        
        render_token_list(tokens)
        return ''.join(result)
    
    def _render_inline(self, inline_tokens: List[Token], translated_text: str) -> str:
        """
        Render inline content.
        Placeholders (including `code` and $math$ with their delimiters) will be
        restored at the end.
        """
        return translated_text
    
    def _translate_batch(self, text: str) -> str:
        """
        Batch translate text through ROSETTA pipeline.
        Text already has rosettablock{seq} placeholders which pass through unchanged.
        """
        if not text.strip():
            return text
        
        try:
            # Pipeline: normalize → udpipe → translate
            norm_proc = subprocess.Popen(
                [sys.executable, str(self.normalize)],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True
            )
            normalized, _ = norm_proc.communicate(input=text)
            
            udpipe_proc = subprocess.Popen(
                [str(self.udpipe), '--tokenize', '--tag', str(self.udpipe_model)],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True
            )
            tagged, _ = udpipe_proc.communicate(input=normalized)
            
            trans_proc = subprocess.Popen(
                [sys.executable, str(self.translate_tool), str(self.dict_file)],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True
            )
            translated_output, _ = trans_proc.communicate(input=tagged)
            
            # Parse output: each line is "word<TAB>POS<TAB>→<TAB>translation"
            # We just want the translated words in order
            result_words = []
            for line in translated_output.strip().split('\n'):
                if not line.strip():
                    continue
                # Lines with → are translations
                if '→' in line:
                    parts = line.split('→', 1)
                    if len(parts) == 2:
                        translation = parts[1].strip()
                        if translation:
                            result_words.append(translation)
                        else:
                            # No translation, keep original
                            result_words.append(parts[0].strip())
            
            return ' '.join(result_words)
            
        except Exception as e:
            print(f"Translation error: {e}", file=sys.stderr)
            return text
    
    def translate_file(self, input_path: str, output_path: str):
        """Translate file."""
        with open(input_path, 'r', encoding='utf-8') as inf:
            with open(output_path, 'w', encoding='utf-8') as outf:
                self.translate_document(inf, outf)


def main():
    """CLI"""
    import argparse
    
    parser = argparse.ArgumentParser(description='ROSETTA markdown translator')
    parser.add_argument('lang', nargs='?', help='Target language')
    parser.add_argument('input', nargs='?', default='-', help='Input file')
    parser.add_argument('output', nargs='?', default='-', help='Output file')
    parser.add_argument('--rosetta-root', help='ROSETTA root path')
    
    args = parser.parse_args()
    
    if not args.lang:
        parser.print_help()
        sys.exit(1)
    
    try:
        translator = ROSETTAMarkdownTranslator(args.lang, args.rosetta_root)
        
        input_stream = sys.stdin if args.input == '-' else open(args.input, 'r', encoding='utf-8')
        output_stream = sys.stdout if args.output == '-' else open(args.output, 'w', encoding='utf-8')
        
        translator.translate_document(input_stream, output_stream)
        
        if args.input != '-':
            input_stream.close()
        if args.output != '-':
            output_stream.close()
            
    except ImportError:
        print("Error: Install markdown-it-py: pip install markdown-it-py", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
