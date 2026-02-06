#!/usr/bin/env python3
"""
Deduplicate semantically similar glosses in Wiktionary data.

This addresses James's hard problem: "The most significant issue here is
not duplicating concepts so that all words that mean 'that concept' point
to the same token."

Approach:
1. Extract all unique glosses
2. Compute semantic embeddings using sentence-transformers
3. Cluster similar glosses using hierarchical clustering
4. Build a mapping from original gloss to canonical gloss
5. Rehash the wiktionary file with deduplicated glosses

Example deduplication:
- "The color of blood" → canonical_hash_1
- "The colour of blood" (British) → canonical_hash_1 (same hash!)
- "Having red as its color" → canonical_hash_1 (same hash!)
- "A deep red color" → canonical_hash_2 (different enough)
"""

import sys
import pickle
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict
import numpy as np

try:
    from sentence_transformers import SentenceTransformer
    from sklearn.cluster import DBSCAN
    from sklearn.metrics.pairwise import cosine_similarity
except ImportError:
    print("Error: Required packages not installed", file=sys.stderr)
    print("Run: pip install sentence-transformers scikit-learn", file=sys.stderr)
    sys.exit(1)


class GlossDeduplicator:
    """Deduplicate semantically similar glosses."""

    def __init__(self, similarity_threshold=0.92, model_name='all-MiniLM-L6-v2'):
        """
        Initialize the deduplicator.

        Args:
            similarity_threshold: Cosine similarity threshold for clustering (0-1)
                                0.95 = very strict (nearly identical)
                                0.90 = moderate (similar meanings)
                                0.85 = loose (related concepts)
            model_name: Sentence transformer model to use
        """
        self.similarity_threshold = similarity_threshold
        self.model_name = model_name
        self.model = None

        # Gloss normalization: normalize minor variations
        self.normalize_map = {
            'color': 'colour',  # British spelling
            'labor': 'labour',
            'favor': 'favour',
            'honor': 'honour',
        }

    def normalize_gloss(self, gloss: str) -> str:
        """
        Normalize a gloss for better matching.

        Handles:
        - Spelling variations (color/colour)
        - Extra whitespace
        - Case normalization for comparison
        """
        gloss = gloss.strip().lower()

        # Apply normalization mappings
        for old, new in self.normalize_map.items():
            gloss = gloss.replace(old, new)

        return gloss

    def load_model(self):
        """Load the sentence transformer model (lazy loading)."""
        if self.model is None:
            print(f"Loading sentence transformer model: {self.model_name}...",
                  file=sys.stderr)
            self.model = SentenceTransformer(self.model_name)
            print("Model loaded successfully", file=sys.stderr)

    def extract_unique_glosses(self, input_file: str) -> Dict[str, Set[str]]:
        """
        Extract unique glosses grouped by POS.

        Returns:
            Dict mapping POS -> Set of unique glosses
        """
        glosses_by_pos = defaultdict(set)

        print(f"Extracting unique glosses from {input_file}...", file=sys.stderr)

        with open(input_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.rstrip('\n')

                if not line.strip():
                    continue

                parts = line.split('\t')
                if len(parts) < 4:
                    continue

                _, _, pos, gloss = parts[0], parts[1], parts[2], parts[3]
                glosses_by_pos[pos].add(gloss)

                if line_num % 100000 == 0:
                    print(f"Processed {line_num:,} lines...", file=sys.stderr)

        total_unique = sum(len(glosses) for glosses in glosses_by_pos.values())
        print(f"\nFound {total_unique:,} unique glosses across {len(glosses_by_pos)} POS tags",
              file=sys.stderr)

        return glosses_by_pos

    def compute_embeddings(self, glosses: List[str]) -> np.ndarray:
        """Compute embeddings for a list of glosses."""
        self.load_model()

        print(f"Computing embeddings for {len(glosses):,} glosses...", file=sys.stderr)
        embeddings = self.model.encode(glosses,
                                       show_progress_bar=True,
                                       batch_size=32,
                                       convert_to_numpy=True)

        return embeddings

    def cluster_similar_glosses(self,
                                glosses: List[str],
                                embeddings: np.ndarray) -> Dict[str, str]:
        """
        Cluster similar glosses and map each to a canonical representative.

        Returns:
            Dict mapping original gloss -> canonical gloss
        """
        print(f"Clustering {len(glosses):,} glosses with threshold {self.similarity_threshold}...",
              file=sys.stderr)

        # Compute pairwise similarities
        similarities = cosine_similarity(embeddings)

        # Convert similarities to distances for clustering
        distances = 1 - similarities

        # Use DBSCAN for clustering (density-based)
        # eps = distance threshold (1 - similarity_threshold)
        # min_samples = 1 (allow singleton clusters)
        clusterer = DBSCAN(eps=1 - self.similarity_threshold,
                          min_samples=1,
                          metric='precomputed')

        labels = clusterer.fit_predict(distances)

        # Build cluster groups
        clusters = defaultdict(list)
        for idx, label in enumerate(labels):
            clusters[label].append(idx)

        print(f"Found {len(clusters):,} clusters (reduced from {len(glosses):,} glosses)",
              file=sys.stderr)

        # Map each gloss to its canonical representative
        gloss_to_canonical = {}

        for cluster_id, indices in clusters.items():
            # Choose the shortest gloss as canonical (often simpler/clearer)
            canonical_idx = min(indices, key=lambda i: len(glosses[i]))
            canonical_gloss = glosses[canonical_idx]

            # Map all glosses in cluster to the canonical one
            for idx in indices:
                gloss_to_canonical[glosses[idx]] = canonical_gloss

        # Report some examples
        print("\nExample clusters:", file=sys.stderr)
        example_count = 0
        for cluster_id, indices in list(clusters.items())[:5]:
            if len(indices) > 1:  # Only show clusters with >1 member
                print(f"\nCluster {cluster_id} ({len(indices)} members):", file=sys.stderr)
                for idx in indices[:3]:  # Show first 3
                    print(f"  - {glosses[idx]}", file=sys.stderr)
                if len(indices) > 3:
                    print(f"  ... and {len(indices) - 3} more", file=sys.stderr)
                example_count += 1
                if example_count >= 3:
                    break

        return gloss_to_canonical

    def build_dedup_mapping(self, input_file: str) -> Tuple[Dict[str, str], Dict[str, int]]:
        """
        Build a comprehensive deduplication mapping.

        Returns:
            - gloss_to_canonical: Dict mapping gloss -> canonical gloss
            - stats: Statistics about deduplication
        """
        # Extract unique glosses by POS
        glosses_by_pos = self.extract_unique_glosses(input_file)

        # Build mapping for each POS separately
        # (different POS can have same gloss with different meanings)
        all_mappings = {}
        stats = {
            'total_unique_glosses': 0,
            'total_canonical_glosses': 0,
            'dedup_ratio': 0.0
        }

        for pos, glosses_set in glosses_by_pos.items():
            if len(glosses_set) < 2:
                # No deduplication needed
                for gloss in glosses_set:
                    all_mappings[gloss] = gloss
                continue

            print(f"\n{'='*60}", file=sys.stderr)
            print(f"Processing POS: {pos} ({len(glosses_set):,} glosses)",
                  file=sys.stderr)
            print(f"{'='*60}", file=sys.stderr)

            glosses_list = sorted(glosses_set)

            # Compute embeddings
            embeddings = self.compute_embeddings(glosses_list)

            # Cluster and build mapping
            pos_mapping = self.cluster_similar_glosses(glosses_list, embeddings)

            # Merge into all_mappings
            all_mappings.update(pos_mapping)

            # Update stats
            stats['total_unique_glosses'] += len(glosses_set)
            stats['total_canonical_glosses'] += len(set(pos_mapping.values()))

        if stats['total_unique_glosses'] > 0:
            stats['dedup_ratio'] = (stats['total_unique_glosses'] -
                                   stats['total_canonical_glosses']) / stats['total_unique_glosses']

        print(f"\n{'='*60}", file=sys.stderr)
        print("DEDUPLICATION SUMMARY", file=sys.stderr)
        print(f"{'='*60}", file=sys.stderr)
        print(f"Original unique glosses: {stats['total_unique_glosses']:,}", file=sys.stderr)
        print(f"Canonical glosses: {stats['total_canonical_glosses']:,}", file=sys.stderr)
        print(f"Deduplication ratio: {stats['dedup_ratio']:.2%}", file=sys.stderr)
        print(f"Reduction: {stats['total_unique_glosses'] - stats['total_canonical_glosses']:,} glosses",
              file=sys.stderr)

        return all_mappings, stats

    def save_mapping(self, mapping: Dict[str, str], output_file: str):
        """Save the deduplication mapping to a file."""
        print(f"\nSaving mapping to {output_file}...", file=sys.stderr)

        with open(output_file, 'wb') as f:
            pickle.dump(mapping, f, protocol=pickle.HIGHEST_PROTOCOL)

        print(f"Mapping saved ({len(mapping):,} entries)", file=sys.stderr)

    def load_mapping(self, mapping_file: str) -> Dict[str, str]:
        """Load a saved deduplication mapping."""
        print(f"Loading mapping from {mapping_file}...", file=sys.stderr)

        with open(mapping_file, 'rb') as f:
            mapping = pickle.load(f)

        print(f"Mapping loaded ({len(mapping):,} entries)", file=sys.stderr)
        return mapping


def apply_deduplication(input_file: str, output_file: str, mapping: Dict[str, str]):
    """
    Apply deduplication mapping to create rehashed wiktionary file.

    For each gloss, replace it with its canonical version and rehash.
    This ensures semantically similar glosses share the same hash.
    """
    import xxhash

    # POS to index mapping (must match hash_wiktionary.py)
    POS_MAP = {
        'noun': 0, 'verb': 1, 'adj': 2, 'adv': 3, 'affix': 4,
        'article': 5, 'character': 6, 'combining_form': 7, 'conj': 8,
        'contraction': 9, 'det': 10, 'infix': 11, 'interfix': 12,
        'intj': 13, 'name': 14, 'num': 15, 'particle': 16, 'phrase': 17,
        'prefix': 18, 'prep': 19, 'prep_phrase': 20, 'pron': 21,
        'proverb': 22, 'punct': 23, 'suffix': 24, 'symbol': 25,
    }

    # Track (word, pos, canonical_gloss) for sense indexing
    seen = defaultdict(int)
    stats = {
        'total_entries': 0,
        'deduplicated': 0,
        'unchanged': 0,
        'errors': 0
    }

    print(f"Applying deduplication mapping to {input_file}...", file=sys.stderr)

    with open(input_file, 'r', encoding='utf-8') as inf, \
         open(output_file, 'w', encoding='utf-8') as outf:

        for line_num, line in enumerate(inf, 1):
            line = line.rstrip('\n')

            if not line.strip():
                continue

            parts = line.split('\t')
            if len(parts) < 4:
                print(f"Warning: Skipping malformed line {line_num}", file=sys.stderr)
                stats['errors'] += 1
                continue

            old_hash, word, pos, gloss = parts[0], parts[1], parts[2], parts[3]

            # Look up canonical gloss
            canonical_gloss = mapping.get(gloss, gloss)

            if canonical_gloss != gloss:
                stats['deduplicated'] += 1
            else:
                stats['unchanged'] += 1

            stats['total_entries'] += 1

            # Rehash with canonical gloss
            pos_lower = pos.lower()
            if pos_lower not in POS_MAP:
                # Keep original hash if POS unknown
                outf.write(f"{old_hash}\t{word}\t{pos}\t{canonical_gloss}\n")
                continue

            pos_idx = POS_MAP[pos_lower]

            # Calculate word base hash (52 bits)
            word_lower = word.lower()
            word_hash = xxhash.xxh3_64(word_lower.encode('utf-8')).intdigest()
            word_base = word_hash & 0xFFFFFFFFFFFFF000

            # Track sense index for this word+POS+canonical_gloss combination
            key = (word_lower, pos_lower, canonical_gloss)
            sense_idx = seen[key]
            seen[key] += 1

            if sense_idx >= 64:
                print(f"Warning: Word '{word}' POS '{pos}' has >64 senses, using index 63",
                      file=sys.stderr)
                sense_idx = 63

            # Build final hash: word_base | (pos_idx << 6) | sense_idx
            final_hash = word_base | (pos_idx << 6) | sense_idx

            # Format as 16-char hex
            hash_hex = f"{final_hash:016x}"

            # Write output
            outf.write(f"{hash_hex}\t{word}\t{pos}\t{canonical_gloss}\n")

            # Progress
            if line_num % 100000 == 0:
                print(f"Processed {line_num:,} lines... ({stats['deduplicated']:,} deduplicated)",
                      file=sys.stderr)

    print(f"\n{'='*60}", file=sys.stderr)
    print("APPLICATION COMPLETE", file=sys.stderr)
    print(f"{'='*60}", file=sys.stderr)
    print(f"Total entries: {stats['total_entries']:,}", file=sys.stderr)
    print(f"Deduplicated: {stats['deduplicated']:,} ({stats['deduplicated']/stats['total_entries']:.2%})",
          file=sys.stderr)
    print(f"Unchanged: {stats['unchanged']:,} ({stats['unchanged']/stats['total_entries']:.2%})",
          file=sys.stderr)
    print(f"Errors: {stats['errors']:,}", file=sys.stderr)
    print(f"\nOutput written to: {output_file}", file=sys.stderr)


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Deduplicate semantically similar glosses in Wiktionary data',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Build deduplication mapping
  %(prog)s build wiktionary.hashed.txt gloss_mapping.pkl

  # Build with custom similarity threshold
  %(prog)s build wiktionary.hashed.txt gloss_mapping.pkl --threshold 0.90

  # Apply mapping to create deduplicated file (TODO)
  %(prog)s apply wiktionary.hashed.txt gloss_mapping.pkl wiktionary.deduped.txt

Similarity thresholds:
  0.95 - Very strict (nearly identical text)
  0.92 - Moderate (default, similar meanings)
  0.88 - Loose (related concepts)
        """
    )

    parser.add_argument('command', choices=['build', 'apply'],
                       help='Command to run')
    parser.add_argument('input_file', help='Input wiktionary file (hashed)')
    parser.add_argument('mapping_file', help='Mapping file (.pkl)')
    parser.add_argument('output_file', nargs='?',
                       help='Output file (for apply command)')
    parser.add_argument('--threshold', type=float, default=0.92,
                       help='Similarity threshold (0-1, default: 0.92)')
    parser.add_argument('--model', default='all-MiniLM-L6-v2',
                       help='Sentence transformer model (default: all-MiniLM-L6-v2)')

    args = parser.parse_args()

    deduplicator = GlossDeduplicator(
        similarity_threshold=args.threshold,
        model_name=args.model
    )

    if args.command == 'build':
        # Build deduplication mapping
        mapping, stats = deduplicator.build_dedup_mapping(args.input_file)
        deduplicator.save_mapping(mapping, args.mapping_file)

        print("\n✓ Mapping created successfully!", file=sys.stderr)
        print(f"  Use 'apply' command to create deduplicated file", file=sys.stderr)

    elif args.command == 'apply':
        if not args.output_file:
            parser.error("output_file is required for 'apply' command")

        # Load the mapping
        mapping = deduplicator.load_mapping(args.mapping_file)

        # Apply deduplication
        apply_deduplication(args.input_file, args.output_file, mapping)


if __name__ == '__main__':
    main()
