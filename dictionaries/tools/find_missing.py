#!/usr/bin/env python3
"""
Output words with translations if available, otherwise just the word.

Usage:
    python merge_translations.py 42k.txt en_vi.txt > en_vi_merged.txt
"""

import sys

def load_translations(translated_file):
    """Load translations as dict: word -> translation."""
    translations = {}
    with open(translated_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split('\t', 1)
            if len(parts) == 2:
                word, translation = parts
                translations[word] = translation
    return translations

def merge_output(source_file, translated_file):
    """Output word\ttranslation if exists, otherwise just word."""
    translations = load_translations(translated_file)
    
    with open(source_file, 'r', encoding='utf-8') as f:
        for line in f:
            word = line.strip()
            if not word:
                continue
            
            if word in translations:
                # Has translation
                print(f"{word}\t{translations[word]}")
            else:
                # No translation - just output word
                print(word)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python merge_translations.py 42k.txt en_vi.txt")
        sys.exit(1)
    
    merge_output(sys.argv[1], sys.argv[2])
