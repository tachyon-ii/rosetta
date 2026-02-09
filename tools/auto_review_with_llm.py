#!/usr/bin/env python3
"""
Automated duplicate review using Ollama LLM.

Uses llama3.1 to classify duplicate groups as:
- y (merge) - same concept, different phrasings
- n (reject) - different concepts, keep separate
- s (skip) - uncertain, needs human review
"""

import sys
import json
import time
import requests
from collections import defaultdict
from datetime import datetime

def load_entries(filepath):
    """Load Wiktionary entries by hash."""
    entries = {}
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            parts = line.strip().split('\t')
            if len(parts) != 4:
                continue
            hash_val, word, pos, gloss = parts
            entries[hash_val] = {
                'hash': hash_val,
                'word': word,
                'pos': pos,
                'gloss': gloss
            }
    return entries

def query_ollama(prompt, model="llama3.1:latest", url="http://localhost:11434"):
    """Query Ollama API."""
    try:
        response = requests.post(
            f"{url}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,  # Low temperature for consistent decisions
                    "num_predict": 100   # Short response
                }
            },
            timeout=30
        )

        if response.status_code == 200:
            return response.json()['response'].strip()
        else:
            return None
    except Exception as e:
        print(f"Error querying Ollama: {e}", file=sys.stderr)
        return None

def classify_duplicate(canonical, duplicates, word, pos):
    """Use LLM to classify if entries are true duplicates."""

    # Build prompt
    prompt = f"""You are a lexicographer reviewing duplicate dictionary entries.

Word: "{word}" (Part of speech: {pos})

CANONICAL ENTRY:
{canonical['gloss']}

DUPLICATE ENTRIES:
"""

    for i, dup in enumerate(duplicates, 1):
        prompt += f"{i}. {dup['gloss']}\n"

    prompt += """
Question: Are these entries describing the SAME CONCEPT with different phrasings/spellings?

Examples of TRUE duplicates (merge):
- "color of blood" vs "colour of blood" (spelling variant) → y
- "aunt of one's spouse" vs "aunt of one's wife" (same relationship) → y

Examples of FALSE duplicates (keep separate):
- "authentication server" vs "authorization server" (different meanings) → n
- "long tons (2240 lb)" vs "metric tons (2204.6 lb)" (different values) → n
- "black bullhead fish" vs "brown bullhead fish" (different species) → n

Examples to SKIP (uncertain):
- Complex cases where you're unsure → s

Respond with ONLY one letter:
y = merge (same concept, different phrasing)
n = reject (different concepts, keep separate)
s = skip (uncertain, needs human review)

Response:"""

    response = query_ollama(prompt)

    if response:
        # Extract decision (first character should be y/n/s)
        decision = response.lower().strip()[0] if response else 's'
        if decision not in ['y', 'n', 's']:
            decision = 's'  # Default to skip if unclear
        return decision, response
    else:
        return 's', "Error - no response from LLM"

def auto_review_duplicates(mapping_file, entries_file, output_file,
                          ollama_url="http://localhost:11434",
                          model="llama3.1:latest",
                          checkpoint_interval=100):
    """Automatically review duplicates using LLM."""

    print("="*80)
    print("AUTOMATED DUPLICATE REVIEW WITH LLM")
    print("="*80)
    print(f"Model: {model}")
    print(f"Ollama URL: {ollama_url}")
    print(f"Checkpoint interval: {checkpoint_interval}")
    print("="*80)

    # Load data
    print("\nLoading data...")
    with open(mapping_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    mapping = data['mapping']
    entries = load_entries(entries_file)

    # Group by canonical
    groups = defaultdict(list)
    for dup_hash, canon_hash in mapping.items():
        groups[canon_hash].append(dup_hash)

    print(f"✓ Loaded {len(groups):,} duplicate groups")
    print(f"✓ Total duplicate entries: {len(mapping):,}")

    # Load checkpoint if exists
    checkpoint_file = output_file.replace('.json', '_checkpoint.json')
    try:
        with open(checkpoint_file, 'r') as f:
            checkpoint = json.load(f)
            confirmed = checkpoint.get('confirmed', {})
            rejected = checkpoint.get('rejected', {})
            skipped = checkpoint.get('skipped', {})
            processed_groups = set(checkpoint.get('processed_groups', []))
            print(f"\n✓ Resumed from checkpoint: {len(processed_groups):,} groups already processed")
    except FileNotFoundError:
        confirmed = {}
        rejected = {}
        skipped = {}
        processed_groups = set()
        print("\n✓ Starting fresh (no checkpoint found)")

    # Process groups
    print(f"\nProcessing {len(groups) - len(processed_groups):,} remaining groups...")
    print("="*80)

    start_time = time.time()
    total_groups = len(groups)
    processed_count = len(processed_groups)

    for i, (canon_hash, dup_hashes) in enumerate(sorted(groups.items(),
                                                         key=lambda x: len(x[1]),
                                                         reverse=True), 1):

        # Skip if already processed
        if canon_hash in processed_groups:
            continue

        canonical = entries.get(canon_hash)
        if not canonical:
            processed_groups.add(canon_hash)
            continue

        duplicates = [entries.get(h) for h in dup_hashes if entries.get(h)]
        if not duplicates:
            processed_groups.add(canon_hash)
            continue

        # Get LLM classification
        decision, reasoning = classify_duplicate(
            canonical, duplicates,
            canonical['word'], canonical['pos']
        )

        processed_count += 1

        # Record decision
        if decision == 'y':
            for dup_hash in dup_hashes:
                confirmed[dup_hash] = canon_hash
            status = "✓ MERGE"
        elif decision == 'n':
            for dup_hash in dup_hashes:
                rejected[dup_hash] = canon_hash
            status = "✗ REJECT"
        else:  # 's'
            for dup_hash in dup_hashes:
                skipped[dup_hash] = canon_hash
            status = "⊙ SKIP"

        processed_groups.add(canon_hash)

        # Progress update
        elapsed = time.time() - start_time
        rate = processed_count / elapsed if elapsed > 0 else 0
        remaining = (total_groups - processed_count) / rate if rate > 0 else 0

        print(f"[{processed_count}/{total_groups}] {status} | "
              f"{canonical['word']} ({canonical['pos']}) | "
              f"{len(duplicates)+1} entries | "
              f"{rate:.1f} groups/sec | "
              f"ETA: {remaining/60:.1f}min")

        # Save checkpoint periodically
        if processed_count % checkpoint_interval == 0:
            checkpoint_data = {
                'confirmed': confirmed,
                'rejected': rejected,
                'skipped': skipped,
                'processed_groups': list(processed_groups),
                'timestamp': datetime.now().isoformat(),
                'progress': {
                    'total': total_groups,
                    'processed': processed_count,
                    'confirmed_count': len(confirmed),
                    'rejected_count': len(rejected),
                    'skipped_count': len(skipped)
                }
            }

            with open(checkpoint_file, 'w', encoding='utf-8') as f:
                json.dump(checkpoint_data, f, indent=2, ensure_ascii=False)

            print(f"    → Checkpoint saved ({processed_count} groups)")

    # Final save
    print("\n" + "="*80)
    print("SAVING FINAL RESULTS")
    print("="*80)

    results = {
        'model': model,
        'threshold': data['threshold'],
        'total_groups': total_groups,
        'confirmed': confirmed,
        'rejected': rejected,
        'skipped': skipped,
        'statistics': {
            'total_duplicates': len(mapping),
            'confirmed_count': len(confirmed),
            'rejected_count': len(rejected),
            'skipped_count': len(skipped),
            'confirmed_canonical': len(set(confirmed.values())),
            'processing_time_seconds': time.time() - start_time
        },
        'timestamp': datetime.now().isoformat()
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n✓ Saved to {output_file}")

    # Generate clean mapping (confirmed only)
    clean_mapping_file = output_file.replace('.json', '_clean_mapping.json')
    clean_data = {
        'threshold': data['threshold'],
        'model': model,
        'total_duplicates': len(confirmed),
        'unique_canonical': len(set(confirmed.values())),
        'mapping': confirmed
    }

    with open(clean_mapping_file, 'w', encoding='utf-8') as f:
        json.dump(clean_data, f, indent=2, ensure_ascii=False)

    print(f"✓ Clean mapping saved to {clean_mapping_file}")

    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Total groups processed: {total_groups:,}")
    print(f"Confirmed (merge):      {len(confirmed):,} duplicates")
    print(f"Rejected (separate):    {len(rejected):,} false positives")
    print(f"Skipped (uncertain):    {len(skipped):,} for human review")
    print(f"Processing time:        {(time.time() - start_time)/60:.1f} minutes")
    print(f"Processing rate:        {total_groups/(time.time() - start_time)*60:.1f} groups/min")
    print("="*80)
    print(f"\n✓ Use {clean_mapping_file} to update the interlingua")

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Auto-review duplicates with LLM')
    parser.add_argument('mapping_file', help='Duplicate mapping JSON file')
    parser.add_argument('entries_file', help='Wiktionary hashed file')
    parser.add_argument('output_file', help='Output results file')
    parser.add_argument('--model', default='llama3.1:latest',
                       help='Ollama model (default: llama3.1:latest)')
    parser.add_argument('--url', default='http://localhost:11434',
                       help='Ollama API URL (default: http://localhost:11434)')
    parser.add_argument('--checkpoint', type=int, default=100,
                       help='Save checkpoint every N groups (default: 100)')

    args = parser.parse_args()

    auto_review_duplicates(
        args.mapping_file,
        args.entries_file,
        args.output_file,
        ollama_url=args.url,
        model=args.model,
        checkpoint_interval=args.checkpoint
    )
