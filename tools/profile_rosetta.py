#!/usr/bin/env python3
"""
ROSETTA Translator Profiler
Measures time spent in each phase of translation
"""

import sys
import time
from pathlib import Path
from contextlib import contextmanager

# Add tools to path
sys.path.insert(0, str(Path(__file__).parent))

from rosetta import ROSETTAMarkdownTranslator


class Timer:
    """Simple context manager timer"""
    def __init__(self, name):
        self.name = name
        self.start = None
        self.elapsed = None
    
    def __enter__(self):
        self.start = time.perf_counter()
        return self
    
    def __exit__(self, *args):
        self.elapsed = time.perf_counter() - self.start
        print(f"  {self.name:30s}: {self.elapsed*1000:7.2f}ms")


class ProfilingTranslator(ROSETTAMarkdownTranslator):
    """Translator with detailed timing information"""
    
    def translate_document(self, input_stream, output_stream):
        """Translate with timing for each phase"""
        print("\n=== Translation Profile ===\n")
        
        with Timer("1. Read input"):
            markdown_text = input_stream.read()
        
        print(f"  Input size: {len(markdown_text)} bytes")
        print()
        
        with Timer("2. Parse markdown to AST"):
            tokens = self.md.parse(markdown_text)
        
        print(f"  Tokens parsed: {len(tokens)}")
        print()
        
        with Timer("3. Extract translatable text"):
            text_items = self._extract_translatable_text(tokens)
        
        print(f"  Text chunks: {len(text_items)}")
        if text_items:
            total_chars = sum(len(item['text']) for item in text_items)
            print(f"  Total text chars: {total_chars}")
        print()
        
        if not text_items:
            output_stream.write(markdown_text)
            return
        
        # Batch translate with detailed timing
        texts_to_translate = [item['text'] for item in text_items]
        combined = '\n'.join(texts_to_translate)
        
        print(f"  Combined text size: {len(combined)} bytes")
        print()
        
        with Timer("4. Batch translation (total)"):
            with Timer("   4a. normalize.py subprocess"):
                import subprocess
                norm_proc = subprocess.Popen(
                    [sys.executable, str(self.normalize)],
                    stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    text=True
                )
                normalized, _ = norm_proc.communicate(input=combined)
            
            print(f"      Normalized size: {len(normalized)} bytes")
            
            with Timer("   4b. udpipe subprocess"):
                udpipe_proc = subprocess.Popen(
                    [str(self.udpipe), '--tokenize', '--tag', str(self.udpipe_model)],
                    stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    text=True
                )
                tagged, _ = udpipe_proc.communicate(input=normalized)
            
            print(f"      Tagged size: {len(tagged)} bytes")
            
            with Timer("   4c. translate.py subprocess"):
                trans_proc = subprocess.Popen(
                    [sys.executable, str(self.translate_tool), str(self.dict_file)],
                    stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    text=True
                )
                translated, _ = trans_proc.communicate(input=tagged)
            
            print(f"      Translated size: {len(translated)} bytes")
            
            with Timer("   4d. Parse translations"):
                translations = []
                for line in translated.split('\n'):
                    if '→' in line:
                        parts = line.split('→')
                        if len(parts) == 2:
                            trans = parts[1].strip()
                            if trans and not all(c in '!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~' for c in trans):
                                translations.append(trans)
            
            print(f"      Translations extracted: {len(translations)}")
            
            with Timer("   4e. Reconstruct with whitespace"):
                import re
                tokens_split = re.split(r'([a-zA-Z0-9]+)', combined)
                trans_idx = 0
                result = []
                for token in tokens_split:
                    if token and re.match(r'^[a-zA-Z0-9]+$', token):
                        if trans_idx < len(translations):
                            result.append(translations[trans_idx])
                            trans_idx += 1
                        else:
                            result.append(token)
                    else:
                        result.append(token)
                translated_combined = ''.join(result)
        
        print()
        translations_list = translated_combined.split('\n')
        
        with Timer("5. Map translations to items"):
            for i, item in enumerate(text_items):
                if i < len(translations_list):
                    item['translation'] = translations_list[i]
        
        with Timer("6. Rebuild markdown"):
            result = self._render_tokens(tokens, text_items)
        
        print(f"  Output size: {len(result)} bytes")
        print()
        
        with Timer("7. Write output"):
            output_stream.write(result)
        
        print("\n=== Profile Complete ===\n")


def main():
    """Profile a translation"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Profile ROSETTA translation')
    parser.add_argument('lang', help='Target language')
    parser.add_argument('input', help='Input file')
    parser.add_argument('output', nargs='?', default='-', help='Output file')
    parser.add_argument('--rosetta-root', help='ROSETTA root path')
    
    args = parser.parse_args()
    
    try:
        print(f"\nProfiling translation: {args.input} -> {args.lang}")
        
        translator = ProfilingTranslator(args.lang, args.rosetta_root)
        
        with open(args.input, 'r', encoding='utf-8') as inf:
            if args.output == '-':
                outf = sys.stdout
            else:
                outf = open(args.output, 'w', encoding='utf-8')
            
            translator.translate_document(inf, outf)
            
            if args.output != '-':
                outf.close()
    
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
