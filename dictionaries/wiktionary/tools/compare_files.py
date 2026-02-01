#!/usr/bin/env python3
"""
Compare two dictionary files and show which words are missing.
Reports words in file1 that don't appear in file2.
"""

import sys

def get_words(filename):
    """Extract unique words (first column) from file."""
    words = set()
    with open(filename, 'r', encoding='utf-8') as f:
        for line in f:
            parts = line.split('\t', 1)
            if parts:
                words.add(parts[0])
    return words

if len(sys.argv) != 3:
    print("Usage: compare_files.py <file1> <file2>")
    print("Shows words in file1 that are missing from file2")
    sys.exit(1)

file1 = sys.argv[1]
file2 = sys.argv[2]

print(f"Loading {file1}...", file=sys.stderr)
words1 = get_words(file1)
print(f"Found {len(words1):,} unique words", file=sys.stderr)

print(f"Loading {file2}...", file=sys.stderr)
words2 = get_words(file2)
print(f"Found {len(words2):,} unique words", file=sys.stderr)

# Find missing words
missing = words1 - words2
print(f"\n{len(missing):,} words in {file1} but not in {file2}:", file=sys.stderr)
print()

# Output missing words sorted
for word in sorted(missing):
    print(word)
