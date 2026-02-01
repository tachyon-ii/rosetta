#!/usr/bin/env python3
"""
Fast dictionary lookup for wiktionary.words.txt

Assumes file is sorted alphabetically by word (first column).
Uses early-exit linear scan - stops when past all matches.
Minimum 2 character query.
"""

import sys
import os

DICT_FILE = "wiktionary.words.txt"
MIN_QUERY_LEN = 2


def lookup_lines(filepath, query):
    """
    Find all lines starting with query.
    Simple linear scan (no early exit due to symbol sorting).
    """
    query_lower = query.lower()
    matches = []
    
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            # Extract word (first column)
            word = line.split('\t', 1)[0].lower()
            
            if word.startswith(query_lower):
                matches.append(line.rstrip('\n'))
    
    return matches


def main():
    # Find dict file
    script_dir = os.path.dirname(os.path.abspath(__file__))
    dict_path = os.path.join(script_dir, DICT_FILE)
    
    if not os.path.exists(dict_path):
        print(f"Error: {DICT_FILE} not found in {script_dir}", file=sys.stderr)
        sys.exit(1)
    
    # Interactive mode if no args
    if len(sys.argv) == 1:
        print(f"Wiktionary lookup")
        print(f"File: {dict_path}\n")
        
        while True:
            try:
                query = input("Search (q to quit): ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break
            
            if query.lower() in ('quit', 'exit', 'q'):
                break
            
            if len(query) < MIN_QUERY_LEN:
                print(f"Query too short (min {MIN_QUERY_LEN} chars)\n")
                continue
            
            matches = lookup_lines(dict_path, query)
            
            if not matches:
                print(f"No matches for '{query}'\n")
            else:
                for match in matches[:20]:
                    print(match)
                if len(matches) > 20:
                    print(f"... ({len(matches) - 20} more)")
                print()
    
    # Command-line mode
    else:
        query = sys.argv[1]
        
        if len(query) < MIN_QUERY_LEN:
            print(f"Error: Query too short (min {MIN_QUERY_LEN} chars)", file=sys.stderr)
            sys.exit(1)
        
        matches = lookup_lines(dict_path, query)
        
        for match in matches:
            print(match)
        
        if not matches:
            sys.exit(1)


if __name__ == '__main__':
    main()
