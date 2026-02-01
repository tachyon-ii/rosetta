#!/usr/bin/env python3
"""
Split wiktionary into words and phrases based on presence of spaces.

Single words → wiktionary.words.txt
Multi-word phrases → wiktionary.phrases.txt
"""

import sys

def split_wiktionary(input_file, words_file, phrases_file):
    """
    Split dictionary by word/phrase status.
    """
    stats = {
        'total': 0,
        'words': 0,
        'phrases': 0
    }
    
    with open(input_file, 'r', encoding='utf-8') as inf, \
         open(words_file, 'w', encoding='utf-8') as words_f, \
         open(phrases_file, 'w', encoding='utf-8') as phrases_f:
        
        for line in inf:
            stats['total'] += 1
            
            if not line.strip():
                continue
            
            # Extract word (first column)
            parts = line.split('\t', 1)
            if not parts:
                continue
            
            word = parts[0]
            
            # Check for spaces (phrases)
            if ' ' in word:
                phrases_f.write(line)
                stats['phrases'] += 1
            else:
                words_f.write(line)
                stats['words'] += 1
            
            # Progress
            if stats['total'] % 100000 == 0:
                print(f"Processed {stats['total']:,} lines...", file=sys.stderr)
    
    # Final stats
    print("\n" + "="*70, file=sys.stderr)
    print("Split complete:", file=sys.stderr)
    print("="*70, file=sys.stderr)
    print(f"Total entries:    {stats['total']:,}", file=sys.stderr)
    print(f"Words (no space): {stats['words']:,} ({stats['words']*100/stats['total']:.1f}%)", file=sys.stderr)
    print(f"Phrases (space):  {stats['phrases']:,} ({stats['phrases']*100/stats['total']:.1f}%)", file=sys.stderr)
    print("="*70, file=sys.stderr)


if __name__ == '__main__':
    if len(sys.argv) != 4:
        print("Usage: split_words_phrases.py <input> <words_output> <phrases_output>")
        print("Example: split_words_phrases.py wiktionary.txt wiktionary.words.txt wiktionary.phrases.txt")
        sys.exit(1)
    
    split_wiktionary(sys.argv[1], sys.argv[2], sys.argv[3])
