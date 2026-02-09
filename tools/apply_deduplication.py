#!/usr/bin/env python3
"""
Apply deduplication to Wiktionary file.

This script:
1. Creates backups of original files
2. Removes duplicate entries (keeps canonical only)
3. Generates statistics and reports
4. Creates restoration script
"""

import sys
import json
import shutil
from pathlib import Path
from datetime import datetime
from collections import defaultdict

def load_clean_mapping(mapping_file):
    """Load the confirmed duplicates mapping."""
    with open(mapping_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data['mapping']

def apply_deduplication(wiktionary_file, mapping_file, output_dir):
    """
    Apply deduplication to Wiktionary file.

    Args:
        wiktionary_file: Original wiktionary.hashed.txt
        mapping_file: Clean mapping with confirmed duplicates
        output_dir: Directory for outputs and backups
    """

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    print("="*80)
    print("WIKTIONARY DEDUPLICATION - IMPLEMENTATION")
    print("="*80)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("="*80)

    # Step 1: Create backup
    print("\nStep 1: Creating backup...")
    backup_dir = output_path / "backups"
    backup_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = backup_dir / f"wiktionary.hashed.backup_{timestamp}.txt"

    shutil.copy2(wiktionary_file, backup_file)
    print(f"✓ Backup created: {backup_file}")

    # Step 2: Load mapping
    print("\nStep 2: Loading deduplication mapping...")
    mapping = load_clean_mapping(mapping_file)
    duplicate_hashes = set(mapping.keys())

    print(f"✓ Loaded {len(mapping):,} confirmed duplicates")
    print(f"✓ Canonical entries: {len(set(mapping.values())):,}")

    # Step 3: Process Wiktionary file
    print("\nStep 3: Creating deduplicated file...")

    deduplicated_file = output_path / "wiktionary.hashed.deduplicated.txt"
    removed_file = output_path / "removed_duplicates.txt"

    total_lines = 0
    kept_lines = 0
    removed_lines = 0

    # Statistics by POS
    removed_by_pos = defaultdict(int)
    removed_entries = []

    with open(wiktionary_file, 'r', encoding='utf-8') as f_in, \
         open(deduplicated_file, 'w', encoding='utf-8') as f_out, \
         open(removed_file, 'w', encoding='utf-8') as f_removed:

        for line in f_in:
            total_lines += 1

            parts = line.strip().split('\t')
            if len(parts) != 4:
                # Keep malformed lines as-is
                f_out.write(line)
                kept_lines += 1
                continue

            hash_val, word, pos, gloss = parts

            if hash_val in duplicate_hashes:
                # This is a duplicate - remove it
                f_removed.write(line)
                removed_lines += 1
                removed_by_pos[pos] += 1

                # Store for statistics
                canonical_hash = mapping[hash_val]
                removed_entries.append({
                    'duplicate_hash': hash_val,
                    'canonical_hash': canonical_hash,
                    'word': word,
                    'pos': pos,
                    'gloss': gloss
                })
            else:
                # Keep this entry
                f_out.write(line)
                kept_lines += 1

            if total_lines % 100000 == 0:
                print(f"  Processed {total_lines:,} lines...")

    print(f"✓ Deduplicated file created: {deduplicated_file}")
    print(f"✓ Removed entries saved: {removed_file}")

    # Step 4: Generate statistics
    print("\nStep 4: Generating statistics...")

    stats = {
        'timestamp': datetime.now().isoformat(),
        'original_file': str(wiktionary_file),
        'backup_file': str(backup_file),
        'deduplicated_file': str(deduplicated_file),
        'mapping_file': str(mapping_file),
        'statistics': {
            'total_entries': total_lines,
            'kept_entries': kept_lines,
            'removed_entries': removed_lines,
            'reduction_pct': (removed_lines / total_lines * 100) if total_lines > 0 else 0
        },
        'removed_by_pos': dict(removed_by_pos)
    }

    stats_file = output_path / "deduplication_stats.json"
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)

    print(f"✓ Statistics saved: {stats_file}")

    # Step 5: Create restoration script
    print("\nStep 5: Creating restoration script...")

    restore_script = output_path / "restore_from_backup.sh"
    with open(restore_script, 'w', encoding='utf-8') as f:
        f.write(f"""#!/bin/bash
# Restoration script - restores original Wiktionary file
# Created: {datetime.now().isoformat()}

echo "RESTORING FROM BACKUP"
echo "===================="
echo ""
echo "This will restore the original Wiktionary file from backup."
echo "Backup: {backup_file}"
echo "Target: {wiktionary_file}"
echo ""
read -p "Are you sure? (yes/no): " confirm

if [ "$confirm" = "yes" ]; then
    cp "{backup_file}" "{wiktionary_file}"
    echo "✓ Restored from backup"
    echo "✓ Original file restored: {wiktionary_file}"
else
    echo "✗ Restoration cancelled"
fi
""")

    restore_script.chmod(0o755)
    print(f"✓ Restoration script created: {restore_script}")

    # Step 6: Create replacement script
    print("\nStep 6: Creating replacement script...")

    replace_script = output_path / "replace_with_deduplicated.sh"
    with open(replace_script, 'w', encoding='utf-8') as f:
        f.write(f"""#!/bin/bash
# Replace original with deduplicated version
# Created: {datetime.now().isoformat()}

echo "REPLACE WITH DEDUPLICATED VERSION"
echo "=================================="
echo ""
echo "This will replace the original Wiktionary file with the deduplicated version."
echo "Deduplicated: {deduplicated_file}"
echo "Target: {wiktionary_file}"
echo "Removes: {removed_lines:,} duplicate entries"
echo ""
echo "Backup available at: {backup_file}"
echo ""
read -p "Are you sure? (yes/no): " confirm

if [ "$confirm" = "yes" ]; then
    cp "{deduplicated_file}" "{wiktionary_file}"
    echo "✓ Replaced with deduplicated version"
    echo "✓ Original backed up at: {backup_file}"
    echo "✓ To restore: bash {restore_script}"
else
    echo "✗ Replacement cancelled"
fi
""")

    replace_script.chmod(0o755)
    print(f"✓ Replacement script created: {replace_script}")

    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Original entries:     {total_lines:,}")
    print(f"Kept (canonical):     {kept_lines:,}")
    print(f"Removed (duplicates): {removed_lines:,}")
    print(f"Reduction:            {removed_lines / total_lines * 100:.2f}%")

    print("\nTop 10 POS with most duplicates removed:")
    for pos, count in sorted(removed_by_pos.items(),
                            key=lambda x: x[1],
                            reverse=True)[:10]:
        pct = count / removed_lines * 100 if removed_lines > 0 else 0
        print(f"  {pos:15} {count:6,} ({pct:5.2f}%)")

    print("\n" + "="*80)
    print("FILES CREATED")
    print("="*80)
    print(f"✓ Backup:              {backup_file}")
    print(f"✓ Deduplicated:        {deduplicated_file}")
    print(f"✓ Removed entries:     {removed_file}")
    print(f"✓ Statistics:          {stats_file}")
    print(f"✓ Restore script:      {restore_script}")
    print(f"✓ Replace script:      {replace_script}")

    print("\n" + "="*80)
    print("NEXT STEPS")
    print("="*80)
    print(f"1. Review the deduplicated file: {deduplicated_file}")
    print(f"2. Check statistics: {stats_file}")
    print(f"3. To replace original: bash {replace_script}")
    print(f"4. To restore backup:   bash {restore_script}")
    print("="*80)

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Apply deduplication to Wiktionary')
    parser.add_argument('wiktionary_file', help='Original wiktionary.hashed.txt')
    parser.add_argument('mapping_file', help='Clean mapping JSON (confirmed duplicates)')
    parser.add_argument('--output-dir', default='./deduplication_applied',
                       help='Output directory (default: ./deduplication_applied)')

    args = parser.parse_args()

    apply_deduplication(args.wiktionary_file, args.mapping_file, args.output_dir)
