#!/usr/bin/env python3
"""
Normalize English text before UDPipe processing.
- Removes possessive 's
- Removes hyphens from compound words (any-thing → anything)
- Normalizes possessive pronouns to lowercase for correct lemmatization
"""
import sys
import re

for line in sys.stdin:
    # Remove possessive 's
    line = re.sub(r"'s\b", '', line)
    
    # Remove hyphens between word characters
    # any-thing → anything
    # fire-water → firewater
    line = re.sub(r'\b(\w+)-(\w+)\b', r'\1\2', line)
    
    # Normalize possessive pronouns to lowercase
    # This prevents UDPipe from lemmatizing "Your" → "you"
    # We want "your" → "your" for dictionary lookup
    line = re.sub(r'\b(My|Your|His|Her|Its|Our|Their)\b', 
                  lambda m: m.group(1).lower(), line)
    
    print(line, end='')
