#!/usr/bin/env python3
"""
Strict validation of dictionary files.
Requirements:
- Exactly 42,000 words from 42k.txt reference
- All POS tags use ONLY Latin letters (a-z) + valid suffixes
- All translations must have valid POS tags
"""

import sys
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple

# Base POS tags (from UDPipe mapping) - LATIN LETTERS ONLY
BASE_POS_TAGS = {
    'n.', 'v.', 'vt.', 'vi.', 'a.', 'ad.', 'art.', 'prep.',
    'pron.', 'conj.', 'int.', 'num.', 'part.', 'sym.', 'punc.', 'x.'
}

# Valid suffixes - LATIN LETTERS ONLY
VALID_SUFFIXES = {'+m', '+f', '+n', '+pl'}


def is_valid_pos_tag_strict(tag: str) -> Tuple[bool, str]:
    """
    Strictly validate POS tag - ONLY Latin letters allowed.
    Returns (is_valid, error_message)
    """
    if not tag:
        return False, "empty tag"

    if not tag.endswith('.'):
        return False, "missing trailing dot"

    # Check for non-Latin characters (except the dot)
    tag_without_dot = tag[:-1]
    if not re.match(r'^[a-z+]+$', tag_without_dot):
        # Find the offending characters
        non_latin = [c for c in tag_without_dot if not (c.isascii() and (c.islower() or c == '+'))]
        return False, f"non-Latin characters: {''.join(non_latin)}"

    # Split by '+' to get base and suffixes
    parts = tag_without_dot.split('+')
    base = parts[0] + '.'

    if base not in BASE_POS_TAGS:
        return False, f"invalid base tag: {base}"

    # Validate each suffix
    for suffix in parts[1:]:
        if '+' + suffix not in VALID_SUFFIXES:
            return False, f"invalid suffix: +{suffix}"

    return True, ""


def extract_pos_tags(translation: str) -> List[str]:
    """Extract all POS tags from translation string - PERMISSIVE extraction."""
    if not translation:
        return []

    tags = []
    entries = translation.split('@')

    for entry in entries:
        # Match POS tag at start: any chars before dot, then dot
        # This will catch both Latin AND non-Latin tags
        match = re.match(r'^([^@\s]+?\.)', entry)
        if match:
            tags.append(match.group(1))

    return tags


def validate_dictionary_strict(ref_words: List[str], dict_file: Path) -> Dict:
    """
    Strictly validate a dictionary file.
    """
    print(f"\n{'='*70}")
    print(f"STRICT VALIDATION: {dict_file.name}")
    print(f"{'='*70}")

    # Parse dictionary
    dictionary = {}
    line_num = 0

    with open(dict_file, 'r', encoding='utf-8') as f:
        for line in f:
            line_num += 1
            line = line.strip()
            if not line:
                continue

            if '\t' in line:
                word, translation = line.split('\t', 1)
                dictionary[word] = (translation, line_num)
            else:
                dictionary[line] = (None, line_num)

    # Statistics
    stats = {
        'total_ref_words': len(ref_words),
        'found': 0,
        'missing': [],
        'untranslated': [],
        'invalid_pos': [],
        'non_latin_chars': []
    }

    # Check each reference word
    for word in ref_words:
        if word not in dictionary:
            stats['missing'].append(word)
        else:
            translation, line_num = dictionary[word]
            stats['found'] += 1

            if translation is None:
                stats['untranslated'].append((word, line_num))
            else:
                # Extract and validate POS tags
                pos_tags = extract_pos_tags(translation)

                for tag in pos_tags:
                    is_valid, error = is_valid_pos_tag_strict(tag)
                    if not is_valid:
                        entry = {
                            'word': word,
                            'line': line_num,
                            'tag': tag,
                            'error': error,
                            'translation': translation[:80]  # First 80 chars
                        }

                        if 'non-Latin' in error:
                            stats['non_latin_chars'].append(entry)
                        else:
                            stats['invalid_pos'].append(entry)

    # Print results
    print(f"\n📊 VALIDATION RESULTS:")
    print(f"  Reference words:  {stats['total_ref_words']:>6,}")
    print(f"  Found:            {stats['found']:>6,}")
    print(f"  Missing:          {len(stats['missing']):>6,}")
    print(f"  Untranslated:     {len(stats['untranslated']):>6,}")
    print(f"  Invalid POS:      {len(stats['invalid_pos']):>6,}")
    print(f"  Non-Latin chars:  {len(stats['non_latin_chars']):>6,}")

    # Report issues
    if stats['non_latin_chars']:
        print(f"\n🚨 NON-LATIN CHARACTERS IN POS TAGS (first 20):")
        for entry in stats['non_latin_chars'][:20]:
            print(f"    Line {entry['line']}: {entry['word']}")
            print(f"      Tag: {entry['tag']}")
            print(f"      Error: {entry['error']}")
        if len(stats['non_latin_chars']) > 20:
            print(f"    ... and {len(stats['non_latin_chars']) - 20} more")

    # Overall verdict
    if (len(stats['missing']) == 0 and
        len(stats['untranslated']) == 0 and
        len(stats['invalid_pos']) == 0 and
        len(stats['non_latin_chars']) == 0):
        print(f"\n✅ PASSED: All validations passed!")
    else:
        print(f"\n❌ FAILED: Issues found that need to be fixed")

    return stats


def main():
    script_dir = Path(__file__).parent

    # Load reference
    ref_file = script_dir / '42k.txt'
    with open(ref_file, 'r', encoding='utf-8') as f:
        ref_words = [line.strip() for line in f if line.strip()]

    print(f"✓ Loaded {len(ref_words):,} reference words from 42k.txt\n")

    # Find all dictionary files
    dict_files = sorted(script_dir.glob('en_*.txt'))

    # Exclude validation scripts, fixed files, intermediate files, and reference files
    exclude_patterns = ['validate', 'fixed', 'en_sorted.txt', '42k.txt', '.ok.', '.with_', 'devanagari', '_simple']
    dict_files = [
        f for f in dict_files
        if not any(pattern in f.name for pattern in exclude_patterns)
    ]

    print(f"Found {len(dict_files)} dictionary files to validate\n")

    # Validate each dictionary
    results = {}
    for dict_file in dict_files:
        stats = validate_dictionary_strict(ref_words, dict_file)
        results[dict_file.name] = stats

    # Print summary table
    print(f"\n{'='*70}")
    print(f"SUMMARY: All Dictionaries")
    print(f"{'='*70}")
    print(f"{'Dictionary':<20} {'Missing':<10} {'Untrans':<10} {'InvalidPOS':<12} {'NonLatin':<10}")
    print(f"{'-'*70}")

    for dict_name in sorted(results.keys()):
        stats = results[dict_name]
        missing = len(stats['missing'])
        untrans = len(stats['untranslated'])
        invalid_pos = len(stats['invalid_pos'])
        non_latin = len(stats['non_latin_chars'])

        print(f"{dict_name:<20} {missing:<10} {untrans:<10} {invalid_pos:<12} {non_latin:<10}")

    # Overall status
    print(f"{'-'*70}")
    total_issues = sum(
        len(stats['missing']) + len(stats['untranslated']) +
        len(stats['invalid_pos']) + len(stats['non_latin_chars'])
        for stats in results.values()
    )

    if total_issues == 0:
        print(f"\n✅ ALL DICTIONARIES PASSED!")
    else:
        print(f"\n❌ Total issues across all dictionaries: {total_issues:,}")


if __name__ == '__main__':
    main()
