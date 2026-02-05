#!/usr/bin/env python3
"""
Reverse dictionaries: Create xx_en.txt from en_xx.txt
Enables direct foreign language → English lookup
"""

import os
from collections import defaultdict

def reverse_dictionary(input_file, output_file, lang_code):
    """
    Reverse en_XX.txt to XX_en.txt

    Input format:  word<TAB>pos.translation@pos.translation
    Output format: translation<TAB>pos.word@pos.word
    """
    reverse_map = defaultdict(list)

    print(f"Processing {lang_code}...")

    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            if '\t' not in line:
                continue

            word, defs = line.strip().split('\t', 1)

            # Parse translations: art.—@prep.的@conj.和
            entries = defs.split('@')
            for entry in entries:
                if '.' not in entry:
                    continue

                pos_part, trans_part = entry.split('.', 1)

                # Handle multiple translations separated by comma
                translations = trans_part.split(',')

                for trans in translations:
                    # Remove gender markers (_m, _f, _n)
                    trans = trans.split('_')[0].strip()

                    # Skip empty or placeholder translations
                    if trans and trans != '—':
                        # Store as: foreign_word -> [(pos, english_word), ...]
                        reverse_map[trans].append(f"{pos_part}.{word}")

    # Write reverse file
    with open(output_file, 'w', encoding='utf-8') as f:
        for foreign_word in sorted(reverse_map.keys()):
            # Join all English translations with @
            english_entries = '@'.join(reverse_map[foreign_word])
            f.write(f"{foreign_word}\t{english_entries}\n")

    print(f"  Created {output_file}: {len(reverse_map):,} entries")
    return len(reverse_map)

def main():
    """Reverse all language dictionaries"""

    print("=" * 70)
    print("REVERSING DICTIONARIES: Creating XX_en.txt files")
    print("=" * 70)

    languages = [
        ('zh', 'Chinese'),
        ('es', 'Spanish'),
        ('hi', 'Hindi'),
        ('ar', 'Arabic'),
        ('fr', 'French'),
        ('bn', 'Bengali'),
        ('pt', 'Portuguese'),
        ('ru', 'Russian'),
        ('de', 'German'),
        ('ja', 'Japanese'),
        ('id', 'Indonesian'),
        ('ur', 'Urdu'),
        ('vi', 'Vietnamese'),
        ('mr', 'Marathi')
    ]

    total_entries = 0
    successful = 0

    for lang_code, lang_name in languages:
        input_file = f'dictionaries/en_{lang_code}.txt'
        output_file = f'dictionaries/{lang_code}_en.txt'

        if os.path.exists(input_file):
            entries = reverse_dictionary(input_file, output_file, lang_code)
            total_entries += entries
            successful += 1
        else:
            print(f"  Warning: {input_file} not found, skipping {lang_name}")

    print("\n" + "=" * 70)
    print(f"✓ REVERSED {successful} DICTIONARIES")
    print("=" * 70)
    print(f"Total reverse entries: {total_entries:,}")
    print("\nReverse dictionaries created in dictionaries/ directory")
    print("Format: {lang}_en.txt (e.g., zh_en.txt, es_en.txt)")

if __name__ == '__main__':
    main()
