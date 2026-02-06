#!/usr/bin/env python3
"""
Quick demo of deduplication on a small sample.

Demonstrates the complete pipeline:
1. Extract sample
2. Build mapping
3. Apply deduplication
4. Show before/after comparison
"""

import sys
import tempfile
import random
from pathlib import Path

# Import from deduplicate_glosses
import deduplicate_glosses


def extract_sample(input_file: str, sample_size: int = 5000) -> str:
    """Extract a random sample of lines from the input file."""
    print(f"\n{'='*60}")
    print(f"STEP 1: Extracting {sample_size:,} sample entries")
    print(f"{'='*60}")

    # Read all lines
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = [line for line in f if line.strip()]

    # Random sample
    if len(lines) > sample_size:
        lines = random.sample(lines, sample_size)

    # Write to temp file
    temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False,
                                           suffix='.txt', encoding='utf-8')
    temp_file.writelines(lines)
    temp_file.close()

    print(f"Sample written to: {temp_file.name}")
    print(f"Sample size: {len(lines):,} entries")

    return temp_file.name


def show_comparison(original_file: str, deduped_file: str, max_examples: int = 5):
    """Show before/after comparison of deduplication."""
    print(f"\n{'='*60}")
    print("BEFORE/AFTER COMPARISON")
    print(f"{'='*60}\n")

    # Read both files
    original = {}
    with open(original_file, 'r', encoding='utf-8') as f:
        for line in f:
            parts = line.rstrip('\n').split('\t')
            if len(parts) >= 4:
                key = (parts[1], parts[2])  # (word, pos)
                if key not in original:
                    original[key] = []
                original[key].append((parts[0], parts[3]))  # (hash, gloss)

    deduped = {}
    with open(deduped_file, 'r', encoding='utf-8') as f:
        for line in f:
            parts = line.rstrip('\n').split('\t')
            if len(parts) >= 4:
                key = (parts[1], parts[2])
                if key not in deduped:
                    deduped[key] = []
                deduped[key].append((parts[0], parts[3]))

    # Find examples where deduplication occurred
    examples_shown = 0

    for key in original:
        if key not in deduped:
            continue

        orig_entries = original[key]
        dedup_entries = deduped[key]

        # Count unique hashes before/after
        orig_hashes = set(h for h, _ in orig_entries)
        dedup_hashes = set(h for h, _ in dedup_entries)

        if len(orig_hashes) > len(dedup_hashes):
            # Deduplication occurred
            word, pos = key

            print(f"Word: {word} ({pos})")
            print(f"  Before: {len(orig_hashes)} unique hashes")
            print(f"  After:  {len(dedup_hashes)} unique hashes")
            print(f"  Reduction: {len(orig_hashes) - len(dedup_hashes)} duplicates removed")
            print()

            print("  BEFORE:")
            for hash_val, gloss in orig_entries[:3]:
                print(f"    {hash_val}: {gloss[:80]}{'...' if len(gloss) > 80 else ''}")

            print("\n  AFTER:")
            for hash_val, gloss in dedup_entries[:3]:
                print(f"    {hash_val}: {gloss[:80]}{'...' if len(gloss) > 80 else ''}")

            print()
            print("-" * 60)
            print()

            examples_shown += 1
            if examples_shown >= max_examples:
                break

    if examples_shown == 0:
        print("No significant deduplication found in sample.")
        print("Try increasing sample size or lowering threshold.")


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Demo deduplication on a small sample',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('input_file',
                       help='Input wiktionary file (hashed)')
    parser.add_argument('--sample-size', type=int, default=5000,
                       help='Number of entries to sample (default: 5000)')
    parser.add_argument('--threshold', type=float, default=0.92,
                       help='Similarity threshold (default: 0.92)')
    parser.add_argument('--model', default='all-MiniLM-L6-v2',
                       help='Sentence transformer model')

    args = parser.parse_args()

    print("\n" + "="*60)
    print("DEDUPLICATION DEMO")
    print("="*60)
    print(f"Input: {args.input_file}")
    print(f"Sample size: {args.sample_size:,}")
    print(f"Threshold: {args.threshold}")
    print(f"Model: {args.model}")

    # Step 1: Extract sample
    sample_file = extract_sample(args.input_file, args.sample_size)

    # Step 2: Build mapping
    print(f"\n{'='*60}")
    print("STEP 2: Building deduplication mapping")
    print(f"{'='*60}")

    deduplicator = deduplicate_glosses.GlossDeduplicator(
        similarity_threshold=args.threshold,
        model_name=args.model
    )

    mapping, stats = deduplicator.build_dedup_mapping(sample_file)

    # Save mapping
    mapping_file = sample_file + '.mapping.pkl'
    deduplicator.save_mapping(mapping, mapping_file)

    # Step 3: Apply deduplication
    print(f"\n{'='*60}")
    print("STEP 3: Applying deduplication")
    print(f"{'='*60}")

    deduped_file = sample_file + '.deduped.txt'
    deduplicate_glosses.apply_deduplication(sample_file, deduped_file, mapping)

    # Step 4: Show comparison
    show_comparison(sample_file, deduped_file, max_examples=5)

    print(f"\n{'='*60}")
    print("DEMO COMPLETE")
    print(f"{'='*60}")
    print(f"Sample file: {sample_file}")
    print(f"Mapping file: {mapping_file}")
    print(f"Deduplicated file: {deduped_file}")
    print()

    # Cleanup option
    print("To clean up temp files, run:")
    print(f"  rm {sample_file} {mapping_file} {deduped_file}")


if __name__ == '__main__':
    main()
