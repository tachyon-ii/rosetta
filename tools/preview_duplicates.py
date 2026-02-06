#!/usr/bin/env python3
"""
Preview potential duplicate glosses before running full deduplication.

This helps validate the similarity threshold and see example clusters.
"""

import sys
import random
from collections import defaultdict
from typing import List, Tuple

try:
    from sentence_transformers import SentenceTransformer
    from sklearn.metrics.pairwise import cosine_similarity
    import numpy as np
except ImportError:
    print("Error: Required packages not installed", file=sys.stderr)
    print("Run: pip install sentence-transformers scikit-learn", file=sys.stderr)
    sys.exit(1)


def sample_glosses(input_file: str, pos_filter: str = 'adj',
                   max_samples: int = 500) -> List[str]:
    """Sample glosses from a specific POS for preview."""
    glosses = set()

    print(f"Sampling {pos_filter} glosses from {input_file}...", file=sys.stderr)

    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.rstrip('\n')
            if not line.strip():
                continue

            parts = line.split('\t')
            if len(parts) < 4:
                continue

            _, _, pos, gloss = parts[0], parts[1], parts[2], parts[3]

            if pos.lower() == pos_filter.lower():
                glosses.add(gloss)

            if len(glosses) >= max_samples * 2:
                break

    # Random sample
    glosses_list = list(glosses)
    if len(glosses_list) > max_samples:
        glosses_list = random.sample(glosses_list, max_samples)

    print(f"Sampled {len(glosses_list)} unique glosses", file=sys.stderr)
    return glosses_list


def find_similar_pairs(glosses: List[str],
                      threshold: float = 0.92,
                      model_name: str = 'all-MiniLM-L6-v2') -> List[Tuple[str, str, float]]:
    """
    Find pairs of similar glosses above threshold.

    Returns:
        List of (gloss1, gloss2, similarity_score) tuples
    """
    print(f"Loading model {model_name}...", file=sys.stderr)
    model = SentenceTransformer(model_name)

    print(f"Computing embeddings for {len(glosses)} glosses...", file=sys.stderr)
    embeddings = model.encode(glosses, show_progress_bar=True, batch_size=32)

    print("Computing similarity matrix...", file=sys.stderr)
    similarities = cosine_similarity(embeddings)

    # Find pairs above threshold
    similar_pairs = []

    for i in range(len(glosses)):
        for j in range(i + 1, len(glosses)):
            sim = similarities[i][j]
            if sim >= threshold:
                similar_pairs.append((glosses[i], glosses[j], sim))

    # Sort by similarity (highest first)
    similar_pairs.sort(key=lambda x: x[2], reverse=True)

    return similar_pairs


def display_results(pairs: List[Tuple[str, str, float]], max_display: int = 30):
    """Display similar pairs in a readable format."""
    if not pairs:
        print("\nNo similar pairs found above threshold!", file=sys.stderr)
        return

    print(f"\n{'='*80}")
    print(f"SIMILAR GLOSS PAIRS (showing {min(len(pairs), max_display)} of {len(pairs)})")
    print(f"{'='*80}\n")

    for i, (gloss1, gloss2, score) in enumerate(pairs[:max_display], 1):
        print(f"{i}. Similarity: {score:.4f}")
        print(f"   A: {gloss1}")
        print(f"   B: {gloss2}")
        print()


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Preview potential duplicate glosses',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Preview adjective duplicates
  %(prog)s wiktionary.hashed.txt --pos adj

  # Preview with different threshold
  %(prog)s wiktionary.hashed.txt --pos noun --threshold 0.90

  # Sample more glosses
  %(prog)s wiktionary.hashed.txt --pos verb --samples 1000
        """
    )

    parser.add_argument('input_file', help='Input wiktionary file (hashed)')
    parser.add_argument('--pos', default='adj',
                       help='POS tag to sample (default: adj)')
    parser.add_argument('--samples', type=int, default=500,
                       help='Number of glosses to sample (default: 500)')
    parser.add_argument('--threshold', type=float, default=0.92,
                       help='Similarity threshold (default: 0.92)')
    parser.add_argument('--max-display', type=int, default=30,
                       help='Max pairs to display (default: 30)')
    parser.add_argument('--model', default='all-MiniLM-L6-v2',
                       help='Sentence transformer model')

    args = parser.parse_args()

    # Sample glosses
    glosses = sample_glosses(args.input_file,
                            pos_filter=args.pos,
                            max_samples=args.samples)

    if len(glosses) < 2:
        print("Error: Not enough glosses found", file=sys.stderr)
        sys.exit(1)

    # Find similar pairs
    pairs = find_similar_pairs(glosses,
                              threshold=args.threshold,
                              model_name=args.model)

    # Display results
    display_results(pairs, max_display=args.max_display)

    # Summary statistics
    print(f"{'='*80}")
    print(f"SUMMARY")
    print(f"{'='*80}")
    print(f"Total glosses sampled: {len(glosses)}")
    print(f"Similar pairs found: {len(pairs)}")
    if len(glosses) > 0:
        total_possible = len(glosses) * (len(glosses) - 1) // 2
        dedup_rate = len(pairs) / total_possible if total_possible > 0 else 0
        print(f"Deduplication rate: {dedup_rate:.2%}")
    print()


if __name__ == '__main__':
    main()
