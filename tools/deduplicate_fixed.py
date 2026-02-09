#!/usr/bin/env python3
"""
CORRECT deduplication approach per James's actual requirements.

Key difference from previous version:
1. Group by (word, POS) FIRST
2. Find duplicates WITHIN each group
3. Embed ONLY the gloss (not word + pos + gloss)

This ensures we ONLY deduplicate different glosses for the SAME word,
not merge different words that happen to have similar gloss templates.
"""

import sys
import json
import pickle
from pathlib import Path
from typing import Dict, List, Tuple
from collections import defaultdict
from dataclasses import dataclass

try:
    from sentence_transformers import SentenceTransformer
    import numpy as np
    from sklearn.metrics.pairwise import cosine_similarity
except ImportError:
    print("Error: Required packages not installed", file=sys.stderr)
    print("Run: pip install sentence-transformers scikit-learn", file=sys.stderr)
    sys.exit(1)


@dataclass
class WiktionaryEntry:
    """Represents a Wiktionary entry."""
    hash: str
    word: str
    pos: str
    gloss: str

    def to_dict(self) -> dict:
        return {
            'hash': self.hash,
            'word': self.word,
            'pos': self.pos,
            'gloss': self.gloss
        }


class CorrectDeduplicator:
    """
    Deduplicate glosses CORRECTLY by grouping (word, POS) first.
    """

    def __init__(self,
                 model_name: str = "all-MiniLM-L6-v2",
                 similarity_threshold: float = 0.95,
                 output_dir: str = "./dedup_data"):
        """
        Initialize deduplicator.

        Args:
            model_name: Sentence transformer model
            similarity_threshold: Similarity threshold (0-1)
            output_dir: Directory for output files
        """
        self.model_name = model_name
        self.similarity_threshold = similarity_threshold
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        self.model = None

    def initialize(self):
        """Load the sentence transformer model."""
        if self.model is None:
            print(f"Loading model: {self.model_name}...", file=sys.stderr)
            self.model = SentenceTransformer(self.model_name)
            print("✓ Model loaded", file=sys.stderr)

    def load_entries(self, filepath: str) -> List[WiktionaryEntry]:
        """Load entries from hashed Wiktionary file."""
        print(f"Loading entries from {filepath}...", file=sys.stderr)

        entries = []
        with open(filepath, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue

                parts = line.split('\t')
                if len(parts) != 4:
                    continue

                hash_val, word, pos, gloss = parts
                entries.append(WiktionaryEntry(
                    hash=hash_val,
                    word=word,
                    pos=pos,
                    gloss=gloss
                ))

                if len(entries) % 100000 == 0:
                    print(f"Loaded {len(entries):,} entries...", file=sys.stderr)

        print(f"✓ Loaded {len(entries):,} total entries", file=sys.stderr)
        return entries

    def find_duplicates(self, entries: List[WiktionaryEntry]) -> Dict[str, str]:
        """
        Find duplicates using CORRECT approach.

        Returns:
            Mapping of original_hash → canonical_hash
        """
        self.initialize()

        # Step 1: Group by (word, POS)
        print("\nStep 1: Grouping by (word, POS)...", file=sys.stderr)
        word_pos_groups = defaultdict(list)

        for entry in entries:
            key = (entry.word.lower(), entry.pos.lower())
            word_pos_groups[key].append(entry)

        print(f"✓ Found {len(word_pos_groups):,} unique (word, POS) combinations", file=sys.stderr)

        # Filter to groups with multiple entries
        multi_entry_groups = {k: v for k, v in word_pos_groups.items() if len(v) > 1}
        print(f"✓ Found {len(multi_entry_groups):,} groups with multiple entries", file=sys.stderr)

        # Step 2: Find duplicates WITHIN each group
        print("\nStep 2: Finding duplicates within each group...", file=sys.stderr)

        canonical_mapping = {}
        total_duplicates_found = 0
        total_groups_processed = 0

        for (word, pos), group_entries in multi_entry_groups.items():
            if len(group_entries) < 2:
                continue

            total_groups_processed += 1

            # Embed ONLY the glosses (not word + pos!)
            glosses = [e.gloss for e in group_entries]

            try:
                embeddings = self.model.encode(glosses, convert_to_tensor=False)
            except Exception as e:
                print(f"Error encoding glosses for '{word}' ({pos}): {e}", file=sys.stderr)
                continue

            # Find similar glosses within this group
            for i in range(len(group_entries)):
                for j in range(i + 1, len(group_entries)):
                    # Calculate cosine similarity
                    emb_i = embeddings[i].reshape(1, -1)
                    emb_j = embeddings[j].reshape(1, -1)
                    similarity = cosine_similarity(emb_i, emb_j)[0][0]

                    if similarity >= self.similarity_threshold:
                        # Found a duplicate!
                        canonical = group_entries[i]
                        duplicate = group_entries[j]

                        # Map duplicate to canonical
                        canonical_mapping[duplicate.hash] = canonical.hash
                        total_duplicates_found += 1

            if total_groups_processed % 10000 == 0:
                print(f"Processed {total_groups_processed:,} groups, "
                      f"found {total_duplicates_found:,} duplicates...", file=sys.stderr)

        print(f"\n✓ Processed {total_groups_processed:,} groups", file=sys.stderr)
        print(f"✓ Found {total_duplicates_found:,} duplicate entries", file=sys.stderr)

        return canonical_mapping

    def save_mapping(self, mapping: Dict[str, str], filename: str = "canonical_mapping.pkl"):
        """Save the canonical mapping."""
        output_file = self.output_dir / filename
        with open(output_file, 'wb') as f:
            pickle.dump(mapping, f)
        print(f"✓ Saved mapping to {output_file}", file=sys.stderr)

    def export_json(self, mapping: Dict[str, str], filename: str = "duplicates_mapping.json"):
        """Export mapping as JSON."""
        output_file = self.output_dir / filename

        # Create summary
        summary = {
            'total_duplicates': len(mapping),
            'unique_canonical': len(set(mapping.values())),
            'threshold': self.similarity_threshold,
            'mapping': mapping
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        print(f"✓ Exported to {output_file}", file=sys.stderr)


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Deduplicate Wiktionary glosses CORRECTLY')
    parser.add_argument('input_file', help='Input hashed Wiktionary file')
    parser.add_argument('--threshold', type=float, default=0.95,
                        help='Similarity threshold (default: 0.95)')
    parser.add_argument('--output-dir', default='./dedup_data',
                        help='Output directory')
    parser.add_argument('--sample', type=int, default=None,
                        help='Sample N entries for testing')

    args = parser.parse_args()

    # Initialize
    dedup = CorrectDeduplicator(
        similarity_threshold=args.threshold,
        output_dir=args.output_dir
    )

    # Load entries
    entries = dedup.load_entries(args.input_file)

    # Sample if requested
    if args.sample and len(entries) > args.sample:
        import random
        entries = random.sample(entries, args.sample)
        print(f"Sampled {len(entries):,} entries for testing", file=sys.stderr)

    # Find duplicates
    mapping = dedup.find_duplicates(entries)

    # Save results
    dedup.save_mapping(mapping)
    dedup.export_json(mapping)

    # Print summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Total entries processed: {len(entries):,}")
    print(f"Duplicate entries found: {len(mapping):,}")
    print(f"Unique canonical entries: {len(set(mapping.values())):,}")
    print(f"Reduction: {len(mapping) / len(entries) * 100:.1f}%")
    print("="*60)


if __name__ == '__main__':
    main()
