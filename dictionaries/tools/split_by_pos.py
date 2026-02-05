#!/usr/bin/env python3
"""
Split translation file by POS tag.

Separates entries containing a specific POS tag from those without.

Usage:
    python split_by_pos.py en_vi.txt tn.
    
Outputs:
    en_vi.with_tn.txt - entries containing tn. tag
    en_vi.ok.txt - entries without tn. tag
"""

import sys
import re

def has_pos_tag(translation, pos_tag):
    """Check if translation contains the specified POS tag."""
    if not translation:
        return False
    
    # Split on @ to get individual translations
    parts = translation.split('@')
    
    for part in parts:
        part = part.strip()
        # Check if starts with pos_tag (e.g., "tn. definition")
        if part.startswith(pos_tag):
            return True
    
    return False

def split_by_pos(input_file, pos_tag):
    """Split file into entries with/without specified POS tag."""
    
    # Extract base filename for output
    base = input_file.rsplit('.txt', 1)[0]
    pos_clean = pos_tag.rstrip('.')
    
    with_file = f"{base}.with_{pos_clean}.txt"
    ok_file = f"{base}.ok.txt"
    
    with_count = 0
    ok_count = 0
    
    with open(input_file, 'r', encoding='utf-8') as inf:
        with open(with_file, 'w', encoding='utf-8') as with_f:
            with open(ok_file, 'w', encoding='utf-8') as ok_f:
                for line in inf:
                    line = line.rstrip('\n\r')
                    
                    # Split on tab
                    parts = line.split('\t', 1)
                    word = parts[0]
                    translation = parts[1] if len(parts) > 1 else ''
                    
                    if has_pos_tag(translation, pos_tag):
                        # Has the tag
                        with_f.write(line + '\n')
                        with_count += 1
                    else:
                        # Doesn't have the tag
                        ok_f.write(line + '\n')
                        ok_count += 1
    
    # Print stats
    print(f"Entries with {pos_tag}: {with_count:,} → {with_file}")
    print(f"Entries without {pos_tag}: {ok_count:,} → {ok_file}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python split_by_pos.py <file.txt> <pos_tag>")
        print("Example: python split_by_pos.py en_vi.txt tn.")
        sys.exit(1)
    
    input_file = sys.argv[1]
    pos_tag = sys.argv[2]
    
    split_by_pos(input_file, pos_tag)
