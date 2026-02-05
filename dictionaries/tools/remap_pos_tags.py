#!/usr/bin/env python3
"""
Remap unauthorized POS tags to official specification.

Usage:
    python remap_pos_tags.py en_vi.txt > en_vi_fixed.txt
"""

import sys

# Mapping from incorrect tags to correct tags
TAG_MAPPING = {
    'tn.': 'n.',      # proper noun → noun
    'tv.': 'vt.',     # transitive verb (t-prefix variant)
    'ta.': 'a.',      # adjective (t-prefix variant)
    'tad.': 'ad.',    # adverb (t-prefix variant)
    'tint.': 'int.',  # interjection (t-prefix variant)
    'tpron.': 'pron.', # pronoun (t-prefix variant)
    'tconj.': 'conj.', # conjunction (t-prefix variant)
    'tprep.': 'prep.', # preposition (t-prefix variant)
}

def remap_translation(translation):
    """Remap POS tags in a single translation string."""
    # Split on @ to get individual translations
    translations = translation.split('@')
    fixed = []
    
    for trans in translations:
        trans = trans.strip()
        if not trans:
            continue
        
        # Split on first . to get POS tag
        parts = trans.split('.', 1)
        if len(parts) == 2:
            pos_tag = parts[0] + '.'
            rest = parts[1]
            
            # Remap if needed
            if pos_tag in TAG_MAPPING:
                pos_tag = TAG_MAPPING[pos_tag]
            
            fixed.append(pos_tag + rest)
        else:
            # No POS tag found, keep as-is
            fixed.append(trans)
    
    return '@'.join(fixed)

def remap_file(filename):
    """Remap all POS tags in file."""
    with open(filename, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.rstrip('\n')
            if not line:
                print()
                continue
            
            # Split on tab
            parts = line.split('\t', 1)
            word = parts[0]
            
            if len(parts) == 2:
                translation = parts[1]
                fixed_translation = remap_translation(translation)
                print(f"{word}\t{fixed_translation}")
            else:
                # No translation - just word
                print(word)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python remap_pos_tags.py en_vi.txt", file=sys.stderr)
        sys.exit(1)
    
    remap_file(sys.argv[1])
