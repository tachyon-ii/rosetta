#!/usr/bin/env python3
"""
Count POS tags in wiktionary.txt (second column, tab-delimited).

Usage:
    python count_wiktionary_pos.py wiktionary.txt
"""

import sys
from collections import Counter

def count_pos_tags(filename):
    """Count POS tags in second column of wiktionary.txt."""
    pos_counter = Counter()
    total_lines = 0
    
    with open(filename, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            
            total_lines += 1
            
            # Split on tab
            parts = line.split('\t')
            
            # Should have at least 3 columns: word, pos, gloss
            if len(parts) >= 2:
                pos_tag = parts[1]
                pos_counter[pos_tag] += 1
    
    return pos_counter, total_lines

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python count_wiktionary_pos.py wiktionary.txt")
        sys.exit(1)
    
    counts, total = count_pos_tags(sys.argv[1])
    
    # Sort by count descending
    print("POS Tag\tCount\t% of Total")
    print("-" * 40)
    for tag, count in counts.most_common():
        pct = (count / total * 100) if total > 0 else 0
        print(f"{tag}\t{count}\t{pct:.1f}%")
    
    print("-" * 40)
    print(f"Total unique tags: {len(counts)}")
    print(f"Total entries: {total}")
