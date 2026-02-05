#!/usr/bin/env python3
"""Debug Portuguese validation to see actual invalid tags."""
import sys
import re
from pathlib import Path

# Base POS tags (from UDPipe mapping) - LATIN LETTERS ONLY
BASE_POS_TAGS = {
    'n.', 'v.', 'vt.', 'vi.', 'a.', 'ad.', 'art.', 'prep.',
    'pron.', 'conj.', 'int.', 'num.', 'part.', 'sym.', 'punc.', 'x.'
}

# Valid suffixes - LATIN LETTERS ONLY
VALID_SUFFIXES = {'+m', '+f', '+n', '+pl'}

def is_valid_pos_tag_strict(tag: str):
    """Strictly validate POS tag."""
    if not tag or not tag.endswith('.'):
        return False, f"missing dot: {tag}"

    tag_without_dot = tag[:-1]
    if not re.match(r'^[a-z+]+$', tag_without_dot):
        return False, f"non-Latin chars"

    parts = tag_without_dot.split('+')
    base = parts[0] + '.'

    if base not in BASE_POS_TAGS:
        return False, f"invalid base: {base}"

    for suffix in parts[1:]:
        if '+' + suffix not in VALID_SUFFIXES:
            return False, f"invalid suffix: +{suffix}"

    return True, ""

def extract_pos_tags(translation: str):
    """Extract all POS tags from translation string."""
    if not translation:
        return []
    tags = []
    entries = translation.split('@')
    for entry in entries:
        match = re.match(r'^([^@\s]+?\.)', entry)
        if match:
            tags.append(match.group(1))
    return tags

# Process Portuguese
dict_file = Path('en_pt.txt')
invalid_tags = {}

with open(dict_file, 'r', encoding='utf-8') as f:
    for line_num, line in enumerate(f, 1):
        line = line.strip()
        if '\t' in line:
            word, translation = line.split('\t', 1)
            pos_tags = extract_pos_tags(translation)
            for tag in pos_tags:
                is_valid, error = is_valid_pos_tag_strict(tag)
                if not is_valid:
                    if tag not in invalid_tags:
                        invalid_tags[tag] = []
                    if len(invalid_tags[tag]) < 3:  # Keep first 3 examples
                        invalid_tags[tag].append((word, line_num))

print(f"Found {len(invalid_tags)} unique invalid tags:\n")
for tag in sorted(invalid_tags.keys()):
    examples = invalid_tags[tag]
    print(f"{tag} ({len(examples)} examples shown):")
    for word, line_num in examples:
        print(f"  Line {line_num}: {word}")
    print()
