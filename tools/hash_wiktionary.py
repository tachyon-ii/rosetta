#!/usr/bin/env python3
"""
Add xxh3 hashes to wiktionary files with structured allocation.

Input:  word<TAB>pos<TAB>gloss
Output: xxh3<TAB>word<TAB>pos<TAB>gloss

HASH STRUCTURE (64 bits):
==========================
Bits 63-12: Word hash (52 bits) - xxh3_64(word.lower())
Bits 11-6:  POS index (6 bits)  - 64 possible POS types
Bits 5-0:   Sense index (6 bits) - 64 senses per word+POS

Example: d0764a3f5c259b42
         └─────┬─────┘└┬┘
           word hash   │└─ Sense 2 (bits 5-0)
                       └── POS 1 (bits 11-6, verb)

Operations:
-----------
Extract word base:  hash & 0xFFFFFFFFFFFFF000
Extract POS index:  (hash & 0x0000000000000FC0) >> 6
Extract sense idx:  hash & 0x000000000000003F

Query all POS for word:
  base = word_hash & 0xFFFFFFFFFFFFF000
  for pos in range(64):
    check: base | (pos << 6)

Query all senses for word+POS:
  base = (word_hash & 0xFFFFFFFFFFFFF000) | (pos_idx << 6)
  for sense in range(64):
    check: base | sense

POS MAPPING (26 types, 0-25):
==============================
 0: noun           14: name
 1: verb           15: num
 2: adj            16: particle
 3: adv            17: phrase
 4: affix          18: prefix
 5: article        19: prep
 6: character      20: prep_phrase
 7: combining_form 21: pron
 8: conj           22: proverb
 9: contraction    23: punct
10: det            24: suffix
11: infix          25: symbol
12: interfix
13: intj

CAPACITY:
=========
- 4.5 quadrillion unique words (2^52)
- 64 POS types (room for 38 more)
- 64 senses per word+POS
"""

import sys
import xxhash

# POS to index mapping (noun=0, verb=1, then alphabetical)
POS_MAP = {
    'noun': 0,
    'verb': 1,
    'adj': 2,
    'adv': 3,
    'affix': 4,
    'article': 5,
    'character': 6,
    'combining_form': 7,
    'conj': 8,
    'contraction': 9,
    'det': 10,
    'infix': 11,
    'interfix': 12,
    'intj': 13,
    'name': 14,
    'num': 15,
    'particle': 16,
    'phrase': 17,
    'prefix': 18,
    'prep': 19,
    'prep_phrase': 20,
    'pron': 21,
    'proverb': 22,
    'punct': 23,
    'suffix': 24,
    'symbol': 25,
}

def hash_wiktionary(input_file, output_file):
    """
    Add xxh3 hashes to wiktionary entries with structured allocation.
    """
    # Track (word, pos) occurrences for multi-sense indexing
    seen = {}
    unknown_pos = set()
    
    with open(input_file, 'r', encoding='utf-8') as inf, \
         open(output_file, 'w', encoding='utf-8') as outf:
        
        for line_num, line in enumerate(inf, 1):
            line = line.rstrip('\n')
            
            if not line.strip():
                continue
            
            parts = line.split('\t')
            if len(parts) < 3:
                print(f"Warning: Skipping malformed line {line_num}", file=sys.stderr)
                continue
            
            word, pos, gloss = parts[0], parts[1], parts[2]
            
            # Get POS index
            pos_lower = pos.lower()
            if pos_lower not in POS_MAP:
                unknown_pos.add(pos_lower)
                print(f"Warning: Unknown POS '{pos}' at line {line_num}, skipping", file=sys.stderr)
                continue
            
            pos_idx = POS_MAP[pos_lower]
            
            # Calculate word base hash (52 bits)
            word_lower = word.lower()
            word_hash = xxhash.xxh3_64(word_lower.encode('utf-8')).intdigest()
            word_base = word_hash & 0xFFFFFFFFFFFFF000  # Zero lower 12 bits
            
            # Track sense index for this word+POS
            key = (word_lower, pos_lower)
            if key in seen:
                seen[key] += 1
            else:
                seen[key] = 0
            
            sense_idx = seen[key]
            
            if sense_idx >= 64:
                print(f"Warning: Word '{word}' POS '{pos}' has >64 senses, skipping sense {sense_idx}", file=sys.stderr)
                continue
            
            # Build final hash: word_base | (pos_idx << 6) | sense_idx
            final_hash = word_base | (pos_idx << 6) | sense_idx
            
            # Format as 16-char hex
            hash_hex = f"{final_hash:016x}"
            
            # Write output
            outf.write(f"{hash_hex}\t{word}\t{pos}\t{gloss}\n")
            
            # Progress
            if line_num % 100000 == 0:
                print(f"Processed {line_num:,} lines...", file=sys.stderr)
        
        if unknown_pos:
            print(f"\nWarning: Found {len(unknown_pos)} unknown POS types:", file=sys.stderr)
            for pos in sorted(unknown_pos):
                print(f"  - {pos}", file=sys.stderr)
    
    print(f"\nComplete! Processed {line_num:,} entries", file=sys.stderr)


def main():
    if len(sys.argv) != 3:
        print("Usage: hash_wiktionary.py <input_file> <output_file>", file=sys.stderr)
        print("", file=sys.stderr)
        print("Input format:  word<TAB>pos<TAB>gloss", file=sys.stderr)
        print("Output format: xxh3<TAB>word<TAB>pos<TAB>gloss", file=sys.stderr)
        print("", file=sys.stderr)
        print("Example: ./hash_wiktionary.py wiktionary.txt wiktionary.hashed.txt", file=sys.stderr)
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    try:
        hash_wiktionary(input_file, output_file)
    except FileNotFoundError:
        print(f"Error: Input file '{input_file}' not found", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
