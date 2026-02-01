#!/usr/bin/env python3
"""
Smart dictionary splitter with auto-pass for short glosses.

Short glosses (≤8 words): Written directly to output file
Long glosses (>8 words): Split into per-word files for LLM processing

Directory structure:
    raw/0000/word
    raw/0001/word
    ...
    raw/NNNN/word

Each directory contains ~1140 words.
Non-alphanumeric chars in filenames converted to underscore.
"""

import os
import sys
import re
import argparse


WORD_THRESHOLD = 8  # Auto-pass glosses with ≤8 words


def sanitize_filename(word):
    """
    Convert non-alphanumeric characters to underscore.
    
    Examples:
        don't -> don_t
        pre-thing -> pre_thing
        multi word phrase -> multi_word_phrase
    """
    return re.sub(r'[^a-z0-9]', '_', word.lower())


def get_output_path(word, index, base_dir):
    """
    Calculate output path for word based on its index.
    
    Args:
        word: The word (will be sanitized for filename)
        index: Sequential index (0, 1, 2, ...)
        base_dir: Base directory (e.g., "raw")
    
    Returns:
        Path like: raw/0000/word
    """
    dir_num = index // 1140
    dir_path = os.path.join(base_dir, f"{dir_num:04d}")
    filename = sanitize_filename(word)
    return os.path.join(dir_path, filename)


def count_words_in_gloss(gloss):
    """Count words in gloss string."""
    return len(gloss.split())


def split_dictionary_smart(input_file, output_dir, output_file):
    """
    Split dictionary with smart filtering.
    
    For each line:
      - If gloss ≤8 words: Append to output_file
      - If gloss >8 words: Add to word file for LLM processing
    """
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    stats = {
        'total_lines': 0,
        'auto_passed': 0,
        'needs_processing': 0,
        'words_created': set()  # Track unique words
    }
    
    # Track word indices
    word_index = {}  # {word: index}
    next_index = [0]
    
    with open(input_file, 'r', encoding='utf-8') as inf, \
         open(output_file, 'a', encoding='utf-8') as outf:
        
        for line_num, line in enumerate(inf, 1):
            stats['total_lines'] += 1
            
            if not line.strip():
                continue
            
            parts = line.split('\t', 2)
            if len(parts) < 3:
                continue
            
            word, pos, gloss = parts
            word_count = count_words_in_gloss(gloss)
            
            if word_count <= WORD_THRESHOLD:
                # Auto-pass - write directly to output
                outf.write(line)
                stats['auto_passed'] += 1
            else:
                # Needs processing - append to word file
                
                # Get or assign word index
                if word not in word_index:
                    word_index[word] = next_index[0]
                    next_index[0] += 1
                    stats['words_created'].add(word)
                
                # Get file path and append (open/close each time)
                output_path = get_output_path(word, word_index[word], output_dir)
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                
                with open(output_path, 'a', encoding='utf-8') as wf:
                    wf.write(line)
                
                stats['needs_processing'] += 1
            
            # Progress update
            if line_num % 100000 == 0:
                print(f"Processed {line_num:,} lines...", file=sys.stderr)
    
    # Final stats
    print("\n" + "="*70, file=sys.stderr)
    print("Smart Split Complete:", file=sys.stderr)
    print("="*70, file=sys.stderr)
    print(f"Total lines processed:      {stats['total_lines']:,}", file=sys.stderr)
    print(f"Auto-passed (≤{WORD_THRESHOLD} words):     {stats['auto_passed']:,} ({stats['auto_passed']*100/stats['total_lines']:.1f}%)", file=sys.stderr)
    print(f"Needs LLM (>{WORD_THRESHOLD} words):       {stats['needs_processing']:,} ({stats['needs_processing']*100/stats['total_lines']:.1f}%)", file=sys.stderr)
    print(f"Word files created:         {len(stats['words_created']):,}", file=sys.stderr)
    print("="*70, file=sys.stderr)


def process_word(word, lines, index, output_dir, auto_pass_file, stats):
    """
    REMOVED - No longer needed. Processing done line-by-line.
    """
    pass


def main():
    parser = argparse.ArgumentParser(
        description='Smart split: auto-pass short glosses, split long ones for LLM'
    )
    parser.add_argument('input', help='Input dictionary file')
    parser.add_argument('output_dir', help='Output directory for files needing LLM (e.g., "raw")')
    parser.add_argument('output_file', help='Output file for auto-passed entries (e.g., "clean/wiktionary.txt")')
    
    args = parser.parse_args()
    
    split_dictionary_smart(args.input, args.output_dir, args.output_file)


if __name__ == '__main__':
    main()
