#!/usr/bin/env python3
"""
Count POS tags used in translation file.

Usage:
    python count_pos_tags.py en_vi.txt
"""

import sys
from collections import Counter

def count_pos_tags(filename):
    """Count all POS tags used in translations."""
    pos_counter = Counter()
    
    with open(filename, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            
            # Split on tab to get translation part
            parts = line.split('\t')
            if len(parts) < 2:
                continue
            
            translations = parts[1]
            
            # Split on @ to get individual translations
            for trans in translations.split('@'):
                trans = trans.strip()
                if not trans:
                    continue
                
                # Split on . to get POS tag (first part)
                pos_parts = trans.split('.')
                if len(pos_parts) > 0:
                    pos_tag = pos_parts[0].strip()
                    if pos_tag:
                        pos_counter[pos_tag] += 1
    
    return pos_counter

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python count_pos_tags.py en_vi.txt")
        sys.exit(1)
    
    counts = count_pos_tags(sys.argv[1])
    
    # Sort by count descending
    print("POS Tag\tCount")
    print("-" * 30)
    for tag, count in counts.most_common():
        print(f"{tag}\t{count}")
    
    print(f"\nTotal unique tags: {len(counts)}")
    print(f"Total translations: {sum(counts.values())}")
