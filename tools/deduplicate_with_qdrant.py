#!/usr/bin/env python3
"""
Deduplicate Wiktionary glosses using Qdrant vector database.

Per James's specification:
- Treat "word + pos + gloss" as a token stream
- Store in persistent Qdrant vector database
- Find very close duplicates using semantic search

This approach:
1. Tokenizes the full entry (word + pos + gloss)
2. Embeds the token stream using sentence-transformers
3. Stores embeddings in Qdrant for persistent, efficient search
4. Finds near-duplicates using vector similarity search
5. Builds deduplication mapping
"""

import sys
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Tuple, Set
from collections import defaultdict
from dataclasses import dataclass

try:
    from sentence_transformers import SentenceTransformer
    from qdrant_client import QdrantClient
    from qdrant_client.models import (
        Distance, VectorParams, PointStruct,
        SearchRequest, RecommendRequest, Filter, FieldCondition, MatchValue,
        QueryResponse
    )
except ImportError:
    print("Error: Required packages not installed", file=sys.stderr)
    print("Run: pip install sentence-transformers qdrant-client", file=sys.stderr)
    sys.exit(1)


@dataclass
class WiktionaryEntry:
    """Represents a Wiktionary entry."""
    hash: str
    word: str
    pos: str
    gloss: str

    def to_token_stream(self) -> str:
        """
        Convert to token stream as specified by James.

        Format: "word pos gloss"
        This allows the embedding to capture the full context.
        """
        return f"{self.word} {self.pos} {self.gloss}"

    def to_dict(self) -> dict:
        """Convert to dictionary for storage."""
        return {
            'hash': self.hash,
            'word': self.word,
            'pos': self.pos,
            'gloss': self.gloss
        }


class QdrantDeduplicator:
    """Deduplicate glosses using Qdrant vector database."""

    def __init__(self,
                 collection_name: str = "wiktionary_glosses",
                 model_name: str = "all-MiniLM-L6-v2",
                 qdrant_url: str = "http://localhost:6333",
                 use_docker: bool = True,
                 similarity_threshold: float = 0.95):
        """
        Initialize the Qdrant deduplicator.

        Args:
            collection_name: Name of Qdrant collection
            model_name: Sentence transformer model
            qdrant_url: Qdrant server URL (for Docker mode)
            use_docker: Use Docker-based Qdrant (recommended for large datasets)
            similarity_threshold: Similarity threshold for duplicates (0-1)
        """
        self.collection_name = collection_name
        self.model_name = model_name
        self.qdrant_url = qdrant_url
        self.use_docker = use_docker
        self.similarity_threshold = similarity_threshold

        self.model = None
        self.client = None

    def initialize(self):
        """Initialize the sentence transformer model and Qdrant client."""
        if self.model is None:
            print(f"Loading sentence transformer: {self.model_name}...", file=sys.stderr)
            self.model = SentenceTransformer(self.model_name)
            print("Model loaded", file=sys.stderr)

        if self.client is None:
            if self.use_docker:
                print(f"Connecting to Qdrant Docker at {self.qdrant_url}...", file=sys.stderr)
                try:
                    self.client = QdrantClient(url=self.qdrant_url)
                    # Test connection
                    self.client.get_collections()
                    print("✓ Connected to Qdrant Docker", file=sys.stderr)
                except Exception as e:
                    print(f"Error: Cannot connect to Qdrant Docker at {self.qdrant_url}", file=sys.stderr)
                    print(f"Make sure Docker is running: docker-compose up -d", file=sys.stderr)
                    raise
            else:
                print(f"WARNING: Using local Qdrant (not recommended for large datasets)", file=sys.stderr)
                print(f"Consider using Docker mode with --docker flag", file=sys.stderr)
                self.client = QdrantClient(path="./qdrant_local")
                print("Qdrant initialized (local mode)", file=sys.stderr)

    def create_collection(self, recreate: bool = False):
        """Create Qdrant collection for storing embeddings."""
        self.initialize()

        # Get vector dimension from model
        vector_size = self.model.get_sentence_embedding_dimension()

        # Check if collection exists
        collections = self.client.get_collections().collections
        collection_exists = any(c.name == self.collection_name for c in collections)

        if collection_exists:
            if recreate:
                print(f"Deleting existing collection '{self.collection_name}'...", file=sys.stderr)
                self.client.delete_collection(self.collection_name)
            else:
                print(f"Collection '{self.collection_name}' already exists", file=sys.stderr)
                return

        print(f"Creating collection '{self.collection_name}' (dim={vector_size})...", file=sys.stderr)
        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(
                size=vector_size,
                distance=Distance.COSINE
            )
        )
        print("Collection created", file=sys.stderr)

    def load_entries(self, input_file: str) -> List[WiktionaryEntry]:
        """Load Wiktionary entries from file."""
        entries = []

        print(f"Loading entries from {input_file}...", file=sys.stderr)

        with open(input_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.rstrip('\n')

                if not line.strip():
                    continue

                parts = line.split('\t')
                if len(parts) < 4:
                    continue

                entry = WiktionaryEntry(
                    hash=parts[0],
                    word=parts[1],
                    pos=parts[2],
                    gloss=parts[3]
                )
                entries.append(entry)

                if line_num % 100000 == 0:
                    print(f"Loaded {line_num:,} entries...", file=sys.stderr)

        print(f"Loaded {len(entries):,} total entries", file=sys.stderr)
        return entries

    def index_entries(self, entries: List[WiktionaryEntry], batch_size: int = 100):
        """
        Index entries in Qdrant.

        Uses James's approach: treat "word + pos + gloss" as token stream.
        """
        self.initialize()

        print(f"Indexing {len(entries):,} entries in Qdrant...", file=sys.stderr)

        # Process in batches
        for i in range(0, len(entries), batch_size):
            batch = entries[i:i+batch_size]

            # Convert to token streams (word + pos + gloss)
            token_streams = [entry.to_token_stream() for entry in batch]

            # Compute embeddings
            embeddings = self.model.encode(token_streams,
                                          show_progress_bar=False,
                                          convert_to_numpy=True)

            # Create points for Qdrant
            points = []
            for j, (entry, embedding) in enumerate(zip(batch, embeddings)):
                point_id = i + j

                points.append(PointStruct(
                    id=point_id,
                    vector=embedding.tolist(),
                    payload=entry.to_dict()
                ))

            # Upload to Qdrant
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )

            if (i + batch_size) % 10000 == 0:
                print(f"Indexed {i+batch_size:,} entries...", file=sys.stderr)

        print(f"✓ Indexing complete: {len(entries):,} entries", file=sys.stderr)

    def find_duplicates(self,
                       limit_per_entry: int = 10,
                       sample_size: int = None,
                       batch_size: int = 100) -> Dict[str, List[Tuple[str, float]]]:
        """
        Find duplicate glosses using Qdrant similarity search.

        OPTIMIZED VERSION: Uses Qdrant's recommend API (no vector downloads!)

        Returns:
            Dict mapping entry_id -> List[(similar_entry_id, similarity)]
        """
        self.initialize()

        print("Retrieving entry metadata from Qdrant...", file=sys.stderr)

        # Get all points WITHOUT vectors (metadata only - much faster!)
        all_points = []
        offset = None

        while True:
            result = self.client.scroll(
                collection_name=self.collection_name,
                limit=5000,  # Larger batches since no vectors
                offset=offset,
                with_payload=True,
                with_vectors=False  # Don't download vectors!
            )

            points, next_offset = result
            all_points.extend(points)

            if next_offset is None:
                break
            offset = next_offset

            if len(all_points) % 100000 == 0:
                print(f"Retrieved {len(all_points):,} entries...", file=sys.stderr)

        print(f"✓ Retrieved {len(all_points):,} entries (metadata only)", file=sys.stderr)

        # Optionally sample for faster testing
        if sample_size and len(all_points) > sample_size:
            import random
            all_points = random.sample(all_points, sample_size)
            print(f"Sampled {len(all_points):,} entries for duplicate detection", file=sys.stderr)

        # Group by POS for more efficient duplicate detection
        # (only words with same POS can be duplicates)
        pos_groups = defaultdict(list)
        for point in all_points:
            pos = point.payload['pos'].lower()
            pos_groups[pos].append(point)

        print(f"Grouped into {len(pos_groups)} POS categories", file=sys.stderr)

        # Find duplicates within each POS group
        # Use simple individual searches (no batch API needed)
        duplicates = {}
        total_processed = 0

        for pos, points in pos_groups.items():
            print(f"\nProcessing POS '{pos}' ({len(points):,} entries)...", file=sys.stderr)

            # Retrieve vectors for this POS group in chunks
            chunk_size = 1000  # Retrieve 1k at a time

            for chunk_start in range(0, len(points), chunk_size):
                chunk_end = min(chunk_start + chunk_size, len(points))
                chunk = points[chunk_start:chunk_end]

                # Retrieve vectors for this chunk
                chunk_ids = [p.id for p in chunk]

                try:
                    points_with_vectors = self.client.retrieve(
                        collection_name=self.collection_name,
                        ids=chunk_ids,
                        with_vectors=True
                    )
                except Exception as e:
                    print(f"Failed to retrieve vectors for chunk: {e}", file=sys.stderr)
                    continue

                # Create ID to vector mapping
                id_to_vector = {p.id: p.vector for p in points_with_vectors}

                # Search for each point individually
                for point in chunk:
                    vector = id_to_vector.get(point.id)
                    if vector is None:
                        continue

                    try:
                        # Create POS filter to only search within same POS
                        pos_filter = Filter(
                            must=[
                                FieldCondition(
                                    key="pos",
                                    match=MatchValue(value=pos)
                                )
                            ]
                        )

                        # Use query_points (correct API for this version!)
                        results = self.client.query_points(
                            collection_name=self.collection_name,
                            query=vector,
                            limit=limit_per_entry,
                            score_threshold=self.similarity_threshold,
                            query_filter=pos_filter,
                            with_payload=True
                        ).points

                        # Collect duplicates (excluding self)
                        similar = []
                        for result in results:
                            if result.id == point.id:
                                continue  # Skip self

                            if result.score >= self.similarity_threshold:
                                similar.append((result.id, result.score))

                        if similar:
                            duplicates[point.id] = similar

                    except Exception as e:
                        # Skip this point if search fails
                        pass

                    total_processed += 1
                    if total_processed % 1000 == 0:
                        print(f"Processed {total_processed:,}/{len(all_points):,} entries... (found {len(duplicates):,} with duplicates)", file=sys.stderr)

        print(f"\n✓ Found {len(duplicates):,} entries with duplicates", file=sys.stderr)
        return duplicates

    def build_canonical_mapping(self,
                                duplicates: Dict[str, List[Tuple[str, float]]]) -> Dict[str, str]:
        """
        Build mapping from entry_id to canonical entry_id.

        Groups duplicate entries and selects canonical representative.
        """
        print("Building canonical mapping...", file=sys.stderr)

        # Build undirected graph of duplicates
        graph = defaultdict(set)
        for entry_id, similar_list in duplicates.items():
            for similar_id, _ in similar_list:
                graph[entry_id].add(similar_id)
                graph[similar_id].add(entry_id)

        # Find connected components (clusters of duplicates)
        visited = set()
        clusters = []

        def dfs(node, cluster):
            visited.add(node)
            cluster.add(node)
            for neighbor in graph[node]:
                if neighbor not in visited:
                    dfs(neighbor, cluster)

        for node in graph:
            if node not in visited:
                cluster = set()
                dfs(node, cluster)
                clusters.append(cluster)

        print(f"Found {len(clusters):,} duplicate clusters", file=sys.stderr)

        # Build mapping: each entry -> canonical (lowest ID in cluster)
        canonical_mapping = {}

        for cluster in clusters:
            canonical_id = min(cluster)  # Use lowest ID as canonical
            for entry_id in cluster:
                canonical_mapping[entry_id] = canonical_id

        print(f"✓ Mapping built: {len(canonical_mapping):,} entries mapped to canonicals",
              file=sys.stderr)
        return canonical_mapping

    def export_mapping(self,
                      canonical_mapping: Dict[str, str],
                      output_file: str):
        """
        Export canonical mapping to file.

        Format: original_id -> canonical_id
        """
        print(f"Exporting mapping to {output_file}...", file=sys.stderr)

        # Get entry details from Qdrant
        mapping_data = []

        for original_id, canonical_id in canonical_mapping.items():
            # Get both entries
            original = self.client.retrieve(
                collection_name=self.collection_name,
                ids=[original_id]
            )[0].payload

            canonical = self.client.retrieve(
                collection_name=self.collection_name,
                ids=[canonical_id]
            )[0].payload

            mapping_data.append({
                'original_id': original_id,
                'canonical_id': canonical_id,
                'original_gloss': original['gloss'],
                'canonical_gloss': canonical['gloss'],
                'word': original['word'],
                'pos': original['pos']
            })

        # Write to JSON
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(mapping_data, f, indent=2, ensure_ascii=False)

        print(f"✓ Mapping exported: {len(mapping_data):,} entries", file=sys.stderr)

    def show_examples(self, duplicates: Dict[str, List[Tuple[str, float]]], max_examples: int = 10):
        """Show example duplicate clusters."""
        print(f"\n{'='*80}")
        print("EXAMPLE DUPLICATE CLUSTERS")
        print(f"{'='*80}\n")

        shown = 0
        for entry_id, similar_list in list(duplicates.items())[:max_examples]:
            if not similar_list:
                continue

            # Get original entry
            original = self.client.retrieve(
                collection_name=self.collection_name,
                ids=[entry_id]
            )[0].payload

            print(f"Cluster {shown + 1}:")
            print(f"  Original: {original['word']} ({original['pos']})")
            print(f"    → {original['gloss'][:100]}{'...' if len(original['gloss']) > 100 else ''}")
            print()

            for similar_id, score in similar_list[:3]:  # Show top 3
                similar = self.client.retrieve(
                    collection_name=self.collection_name,
                    ids=[similar_id]
                )[0].payload

                print(f"  Similar ({score:.4f}): {similar['word']} ({similar['pos']})")
                print(f"    → {similar['gloss'][:100]}{'...' if len(similar['gloss']) > 100 else ''}")
                print()

            if len(similar_list) > 3:
                print(f"  ... and {len(similar_list) - 3} more similar entries")
                print()

            print("-" * 80)
            print()

            shown += 1
            if shown >= max_examples:
                break


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Deduplicate Wiktionary glosses using Qdrant (per James\'s specification)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
  index     - Load and index entries in Qdrant
  find      - Find duplicate entries
  export    - Export deduplication mapping

Examples:
  # Start Qdrant Docker (run this first!)
  docker-compose up -d

  # Index entries in Qdrant (Docker mode - RECOMMENDED)
  %(prog)s index wiktionary.hashed.txt

  # Find duplicates
  %(prog)s find --threshold 0.95

  # Export mapping
  %(prog)s export duplicates_mapping.json

  # Stop Qdrant when done
  docker-compose down

Full pipeline:
  docker-compose up -d
  %(prog)s index wiktionary.hashed.txt
  %(prog)s find --threshold 0.95
  %(prog)s export duplicates_mapping.json
        """
    )

    parser.add_argument('command',
                       choices=['index', 'find', 'export'],
                       help='Command to execute')
    parser.add_argument('input_file', nargs='?',
                       help='Input file (for index command)')
    parser.add_argument('--collection', default='wiktionary_glosses',
                       help='Qdrant collection name')
    parser.add_argument('--qdrant-url', default='http://localhost:6333',
                       help='Qdrant server URL (default: http://localhost:6333)')
    parser.add_argument('--local', action='store_true',
                       help='Use local file-based Qdrant (NOT recommended for >20k entries)')
    parser.add_argument('--threshold', type=float, default=0.95,
                       help='Similarity threshold (default: 0.95)')
    parser.add_argument('--model', default='all-MiniLM-L6-v2',
                       help='Sentence transformer model')
    parser.add_argument('--recreate', action='store_true',
                       help='Recreate collection (for index command)')
    parser.add_argument('--sample', type=int,
                       help='Sample size for testing (optional)')
    parser.add_argument('--output', default='duplicates_mapping.json',
                       help='Output file (for export command)')

    args = parser.parse_args()

    # Initialize deduplicator
    deduplicator = QdrantDeduplicator(
        collection_name=args.collection,
        model_name=args.model,
        qdrant_url=args.qdrant_url,
        use_docker=not args.local,
        similarity_threshold=args.threshold
    )

    if args.command == 'index':
        if not args.input_file:
            parser.error("input_file is required for 'index' command")

        # Create collection
        deduplicator.create_collection(recreate=args.recreate)

        # Load entries
        entries = deduplicator.load_entries(args.input_file)

        # Sample if requested
        if args.sample and len(entries) > args.sample:
            import random
            entries = random.sample(entries, args.sample)
            print(f"Sampled {len(entries):,} entries for testing", file=sys.stderr)

        # Index in Qdrant
        deduplicator.index_entries(entries)

        print("\n✓ Indexing complete! Use 'find' command to detect duplicates.", file=sys.stderr)

    elif args.command == 'find':
        # Find duplicates
        duplicates = deduplicator.find_duplicates(sample_size=args.sample)

        # Show examples
        deduplicator.show_examples(duplicates, max_examples=10)

        # Build canonical mapping
        canonical_mapping = deduplicator.build_canonical_mapping(duplicates)

        # Save mapping to temp file for export
        import pickle
        temp_mapping_file = "./qdrant_data/canonical_mapping.pkl"
        with open(temp_mapping_file, 'wb') as f:
            pickle.dump(canonical_mapping, f)

        print(f"\n✓ Duplicate detection complete!")
        print(f"  Mapping saved to: {temp_mapping_file}")
        print(f"  Use 'export' command to export human-readable mapping.")

    elif args.command == 'export':
        # Load mapping
        import pickle
        temp_mapping_file = "./qdrant_data/canonical_mapping.pkl"

        try:
            with open(temp_mapping_file, 'rb') as f:
                canonical_mapping = pickle.load(f)
        except FileNotFoundError:
            print("Error: No mapping found. Run 'find' command first.", file=sys.stderr)
            sys.exit(1)

        # Export
        deduplicator.export_mapping(canonical_mapping, args.output)

        print(f"\n✓ Mapping exported to {args.output}")


if __name__ == '__main__':
    main()
