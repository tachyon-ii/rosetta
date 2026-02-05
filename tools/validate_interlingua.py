#!/usr/bin/env python3
"""
Validate interlingua coverage and quality.
"""

import os

def validate_coverage(lingua_dir='dictionaries/lingua'):
    """Check coverage statistics for each language."""

    print("=" * 70)
    print("ROSETTA INTERLINGUA COVERAGE REPORT")
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

    total = 0

    for lang_code, lang_name in languages:
        file_path = f'{lingua_dir}/en_{lang_code}.txt'

        if not os.path.exists(file_path):
            print(f"\n{lang_name:15} ({lang_code}): FILE NOT FOUND")
            continue

        count = 0
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.startswith('#') and not line.startswith('hash'):
                    count += 1

        total += count
        print(f"{lang_name:15} ({lang_code}): {count:6,} translations")

    print("=" * 70)
    print(f"{'TOTAL':15} {'':5} {total:6,} translations across {len(languages)} languages")
    print("=" * 70)

    # Calculate estimated storage
    avg_size = 30  # Average bytes per translation entry
    estimated_mb = (total * avg_size) / (1024 * 1024)
    print(f"\nEstimated storage: {estimated_mb:.2f} MB")

    # Test a few translations
    print("\n" + "=" * 70)
    print("TESTING INTERLINGUA TRANSLATIONS")
    print("=" * 70)

    test_cases = [
        ("English → Chinese", "like", "en", "zh"),
        ("Chinese → Spanish", "喜欢", "zh", "es"),
        ("Spanish → Arabic", "gustar", "es", "ar"),
        ("Chinese → Hindi", "喜欢", "zh", "hi"),
    ]

    import subprocess

    for description, word, source, target in test_cases:
        result = subprocess.run(
            ['python3', 'tools/interlingua_translate.py', word, source, target],
            capture_output=True,
            text=True
        )

        if result.returncode == 0 and "No translation found" not in result.stdout:
            # Extract just the first translation
            lines = result.stdout.strip().split('\n')
            translation = None
            for line in lines:
                if line and not line.startswith('=') and not line.startswith("'") and not line.startswith('   '):
                    if line[0].isdigit() and '. ' in line:
                        translation = line.split('. ', 1)[1]
                        break

            if translation:
                print(f"\n✓ {description:25} {word:10} → {translation}")
            else:
                print(f"\n✓ {description:25} {word:10} → [found]")
        else:
            print(f"\n✗ {description:25} {word:10} → [NOT FOUND]")

    print("\n" + "=" * 70)

if __name__ == '__main__':
    validate_coverage()
