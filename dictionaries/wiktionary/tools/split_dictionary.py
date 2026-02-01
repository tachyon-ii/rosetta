#!/usr/bin/env python3
"""
Split Wiktionary extracted file into per-word files distributed across numbered directories.

Directory structure:
    raw/0000/word
    raw/0001/word
    ...
    raw/1139/word

Each directory contains ~1140 words.
Non-alphanumeric chars in filenames converted to underscore.
"""

import os
import sys
import re
import argparse


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


def split_dictionary(input_file, output_base_dir):
    """
    Split dictionary file into per-word files.
    
    Each unique word gets its own file containing all its POS+gloss entries.
    """
    os.makedirs(output_base_dir, exist_ok=True)
    
    current_word = None
    current_lines = []
    word_index = 0
    
    with open(input_file, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            if not line.strip():
                continue
            
            parts = line.split('\t', 1)
            if not parts:
                continue
            
            word = parts[0]
            
            # New word detected
            if word != current_word:
                # Write previous word's file if exists
                if current_word is not None and current_lines:
                    output_path = get_output_path(current_word, word_index, output_base_dir)
                    os.makedirs(os.path.dirname(output_path), exist_ok=True)
                    
                    with open(output_path, 'w', encoding='utf-8') as out:
                        out.writelines(current_lines)
                    
                    word_index += 1
                    
                    # Progress update every 1000 words
                    if word_index % 1000 == 0:
                        print(f"Processed {word_index} words (line {line_num})", file=sys.stderr)
                
                # Start collecting new word
                current_word = word
                current_lines = [line]
            else:
                # Same word, accumulate lines
                current_lines.append(line)
        
        # Write final word
        if current_word is not None and current_lines:
            output_path = get_output_path(current_word, word_index, output_base_dir)
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as out:
                out.writelines(current_lines)
            
            word_index += 1
    
    print(f"\nComplete! Processed {word_index} unique words", file=sys.stderr)
    print(f"Created {(word_index // 1140) + 1} directories", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(
        description='Split dictionary into per-word files in numbered directories'
    )
    parser.add_argument('input', help='Input dictionary file (word\\tpos\\tgloss format)')
    parser.add_argument('output_dir', help='Output base directory (e.g., "raw")')
    
    args = parser.parse_args()
    
    split_dictionary(args.input, args.output_dir)


if __name__ == '__main__':
    main()
