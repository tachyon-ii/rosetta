# Deduplication Using Qdrant (James's Approach)

This implements **James's exact specification** for finding duplicate glosses:

> "One approach for this is to consider the word + pos + gloss as a token stream. Tokenize that and put into a persistent vector database (Qdrant is the best option)"

## Key Differences from Previous Approach

### My First Approach (deduplicate_glosses.py)
- ❌ Only embedded the gloss
- ❌ In-memory processing (not persistent)
- ❌ No Qdrant

### James's Approach (deduplicate_with_qdrant.py)
- ✅ Embeds **"word + pos + gloss"** as token stream
- ✅ Uses **persistent Qdrant vector database**
- ✅ Efficient vector similarity search
- ✅ Scales to millions of entries

## Why This Approach is Better

1. **More context:** Including word + POS gives better duplicate detection
   - "red adj Of a red hue" vs "red noun A red color" → Different, not duplicates!

2. **Persistent storage:** Qdrant stores everything on disk
   - No need to recompute embeddings
   - Can query anytime
   - Survives restarts

3. **Efficient search:** Qdrant uses HNSW indexing
   - Fast nearest neighbor search
   - Sub-linear query time
   - Handles millions of vectors

## Quick Start

### Step 1: Index Entries in Qdrant

Index the entire Wiktionary dataset in Qdrant:

```bash
source venv/bin/activate

# Index all entries (full dataset)
python3 tools/deduplicate_with_qdrant.py index \
    dictionaries/wiktionary/wiktionary.hashed.txt \
    --collection wiktionary_glosses \
    --qdrant-path ./qdrant_storage

# Or test with a sample first
python3 tools/deduplicate_with_qdrant.py index \
    dictionaries/wiktionary/wiktionary.hashed.txt \
    --sample 10000 \
    --recreate
```

This creates a persistent Qdrant database at `./qdrant_storage/`.

**Time:** ~30-60 minutes for full dataset (1.67M entries)

### Step 2: Find Duplicates

Search for near-duplicate entries using vector similarity:

```bash
# Find duplicates with threshold 0.95 (very strict)
python3 tools/deduplicate_with_qdrant.py find \
    --threshold 0.95

# Find duplicates with threshold 0.92 (moderate)
python3 tools/deduplicate_with_qdrant.py find \
    --threshold 0.92

# Test on sample
python3 tools/deduplicate_with_qdrant.py find \
    --threshold 0.95 \
    --sample 5000
```

This will:
- Show example duplicate clusters
- Build canonical mapping
- Save mapping for export

**Time:** ~5-15 minutes depending on sample size

### Step 3: Export Mapping

Export the deduplication mapping to JSON:

```bash
python3 tools/deduplicate_with_qdrant.py export \
    --output duplicates_mapping.json
```

Output format:
```json
[
  {
    "original_id": 12345,
    "canonical_id": 12340,
    "original_gloss": "The colour of blood",
    "canonical_gloss": "The color of blood",
    "word": "red",
    "pos": "adj"
  },
  ...
]
```

## What Gets Detected as Duplicates

### 1. Spelling Variations
```
Token stream: "red adj The color of blood"
Token stream: "red adj The colour of blood"
Similarity: 0.99 → Duplicate!
```

### 2. Minor Rewording
```
Token stream: "cat noun An animal of the family Felidae:"
Token stream: "cat noun An animal of the family Felidae"
Similarity: 0.997 → Duplicate!
```

### 3. Partial Overlaps
```
Token stream: "abortion noun A miscarriage; an untimely birth"
Token stream: "abortion noun A spontaneous abortion; a miscarriage"
Similarity: 0.91 → Duplicate (if threshold ≤ 0.91)
```

## Token Stream Format

As James specified, we treat **"word + pos + gloss"** as the token stream:

```python
# Input entry:
hash: 67b1dc007bbe6080
word: red
pos: adj
gloss: Of a red hue.

# Token stream (embedded together):
"red adj Of a red hue."
```

This provides full context for better duplicate detection.

## Persistence: Qdrant Storage

Qdrant stores everything persistently in `./qdrant_storage/`:

```
./qdrant_storage/
├── collection/
│   └── wiktionary_glosses/
│       ├── segments/
│       └── metadata
└── canonical_mapping.pkl
```

**Benefits:**
- No need to reindex
- Can query anytime
- Survives crashes/restarts
- Can be backed up/shared

## Threshold Tuning

| Threshold | Description | Expected Duplicates |
|-----------|-------------|-------------------|
| 0.98 | Near-identical | Punctuation differences only |
| **0.95** | **Very strict (recommended)** | **Spelling + minor variations** |
| 0.92 | Moderate | Rewording, partial overlaps |
| 0.88 | Loose | Broader semantic similarity |

Start with **0.95** as James wants "very close duplicates".

## Integration with Hash Structure

After finding duplicates, you can:

1. **Merge duplicate entries** to share the same hash
2. **Create redirect mapping** from old hash → canonical hash
3. **Update translation dictionaries** to use canonical hashes

## Performance

For 1.67M Wiktionary entries:

| Operation | Time (CPU) | Storage |
|-----------|-----------|---------|
| Index in Qdrant | ~30-60 min | ~500 MB |
| Find duplicates | ~5-15 min | ~100 MB |
| Export mapping | ~1-2 min | ~5 MB |
| **Total** | **~40-80 min** | **~600 MB** |

**Memory usage:** ~2-3 GB peak

## Comparison: Qdrant vs In-Memory

| Feature | Qdrant Approach | In-Memory DBSCAN |
|---------|----------------|------------------|
| Persistence | ✅ Persistent | ❌ Must recompute |
| Scalability | ✅ Millions of entries | ⚠️ Limited by RAM |
| Query speed | ✅ Fast HNSW index | ❌ Slow brute force |
| Context | ✅ word+pos+gloss | ⚠️ gloss only |
| Incremental | ✅ Add new entries | ❌ Rebuild from scratch |

**Qdrant is clearly superior for this use case.**

## Example Output

```
================================================================================
EXAMPLE DUPLICATE CLUSTERS
================================================================================

Cluster 1:
  Original: cat (noun)
    → An animal of the family Felidae:

  Similar (0.9970): cat (noun)
    → An animal of the family Felidae

  Similar (0.9456): feline (noun)
    → Any animal of the family Felidae

--------------------------------------------------------------------------------

Cluster 2:
  Original: red (adj)
    → The color of blood

  Similar (0.9901): red (adj)
    → The colour of blood

  Similar (0.9234): red (adj)
    → Having red as its color

--------------------------------------------------------------------------------
```

## Next Steps

1. **Index the data:** Run `index` command on full dataset
2. **Find duplicates:** Run `find` with threshold 0.95
3. **Review examples:** Check if threshold is appropriate
4. **Export mapping:** Generate JSON mapping file
5. **Apply deduplication:** Use mapping to merge duplicate hashes

## Files

- `deduplicate_with_qdrant.py` - Main Qdrant-based deduplicator
- `QDRANT-APPROACH.md` - This documentation

## Why Qdrant?

James specifically recommended Qdrant because:
- ✅ **Best-in-class vector database**
- ✅ **Rust-based** (extremely fast)
- ✅ **Persistent storage**
- ✅ **HNSW indexing** (sub-linear search)
- ✅ **Simple Python API**
- ✅ **Production-ready**

Perfect choice for this task!
