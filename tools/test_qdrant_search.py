#!/usr/bin/env python3
"""
Quick test to see if Qdrant search is actually working.
"""

import sys
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue

# Connect to Qdrant
client = QdrantClient(url="http://localhost:6333")

# Get a sample point
print("Getting sample points...")
result = client.scroll(
    collection_name="wiktionary_glosses",
    limit=10,
    with_payload=True,
    with_vectors=True
)

points = result[0]

if not points:
    print("No points found!")
    sys.exit(1)

print(f"Found {len(points)} sample points\n")

# Test search with the first point
test_point = points[0]
print(f"Test point ID: {test_point.id}")
print(f"Word: {test_point.payload['word']}")
print(f"POS: {test_point.payload['pos']}")
print(f"Gloss: {test_point.payload['gloss'][:100]}...")
print()

# Test 1: Search WITHOUT filter (should find itself + similar)
print("=" * 60)
print("TEST 1: Search without filter (threshold 0.90)")
print("=" * 60)
try:
    results = client.search(
        collection_name="wiktionary_glosses",
        query_vector=test_point.vector,
        limit=5,
        score_threshold=0.90,
        with_payload=True
    )
    print(f"Found {len(results)} results:")
    for r in results:
        print(f"  Score: {r.score:.4f} | {r.payload['word']} ({r.payload['pos']}) | {r.payload['gloss'][:80]}")
except Exception as e:
    print(f"ERROR: {e}")

print()

# Test 2: Search WITH POS filter
print("=" * 60)
print("TEST 2: Search with POS filter (threshold 0.90)")
print("=" * 60)
try:
    pos_filter = Filter(
        must=[
            FieldCondition(
                key="pos",
                match=MatchValue(value=test_point.payload['pos'])
            )
        ]
    )

    results = client.search(
        collection_name="wiktionary_glosses",
        query_vector=test_point.vector,
        limit=5,
        score_threshold=0.90,
        query_filter=pos_filter,
        with_payload=True
    )
    print(f"Found {len(results)} results:")
    for r in results:
        print(f"  Score: {r.score:.4f} | {r.payload['word']} ({r.payload['pos']}) | {r.payload['gloss'][:80]}")
except Exception as e:
    print(f"ERROR with query_filter: {e}")
    print("\nTrying with 'filter' parameter instead...")
    try:
        results = client.search(
            collection_name="wiktionary_glosses",
            query_vector=test_point.vector,
            limit=5,
            score_threshold=0.90,
            filter=pos_filter,  # Different parameter name!
            with_payload=True
        )
        print(f"Found {len(results)} results:")
        for r in results:
            print(f"  Score: {r.score:.4f} | {r.payload['word']} ({r.payload['pos']}) | {r.payload['gloss'][:80]}")
    except Exception as e2:
        print(f"ERROR with 'filter': {e2}")

print()

# Test 3: Lower threshold
print("=" * 60)
print("TEST 3: Lower threshold (0.70)")
print("=" * 60)
try:
    results = client.search(
        collection_name="wiktionary_glosses",
        query_vector=test_point.vector,
        limit=10,
        score_threshold=0.70,
        with_payload=True
    )
    print(f"Found {len(results)} results:")
    for r in results[:5]:
        print(f"  Score: {r.score:.4f} | {r.payload['word']} ({r.payload['pos']}) | {r.payload['gloss'][:80]}")
    if len(results) > 5:
        print(f"  ... and {len(results) - 5} more")
except Exception as e:
    print(f"ERROR: {e}")

print()
print("=" * 60)
print("DIAGNOSIS")
print("=" * 60)
print("If Test 1 found 0 results, vectors might not be stored correctly")
print("If Test 2 failed, query_filter parameter is wrong - use 'filter' instead")
print("If Test 3 found many results, threshold 0.90 is too strict")
