# Gloss Deduplication System

## The Problem (from James)

> "The most significant issue here is not duplicating concepts so that all words that mean 'that concept' point to the same token."

**Example duplicates in Wiktionary:**
```
"The color of blood" (American English)
"The colour of blood" (British English)
"Having red as its color"
"Of a red hue"
```

All of these glosses describe essentially the same concept but get different hashes in the current system. This means:
- Wasted storage (multiple hashes for the same concept)
- Poor translation (can't leverage semantic equivalence)
- Fragmented knowledge (related concepts are isolated)

## The Solution

Use **semantic embeddings** and **clustering** to identify glosses that mean the same thing, then assign them the same hash.

### How It Works

1. **Extract unique glosses** from the Wiktionary data
2. **Compute semantic embeddings** using sentence-transformers (all-MiniLM-L6-v2)
3. **Cluster similar glosses** using DBSCAN with cosine similarity
4. **Map each gloss** to a canonical representative
5. **Rehash the dictionary** so duplicate glosses share the same hash

### Example Results

From actual Wiktionary data:

```
Similarity: 99.7%
- "An animal of the family Felidae:"
- "An animal of the family Felidae"
→ Same hash!

Similarity: 94.0%
- "The fourth digestive compartment of the stomach of a cow or other ruminant, after the omasum;"
- "The fourth digestive compartment of the stomach of a cow or other ruminant, after the omasum; the lining of said compartment, considered as a foodstuff."
→ Same hash! (one is a superset of the other)

Similarity: 90.7%
- "A miscarriage; an untimely birth; an abortion."
- "A spontaneous abortion; a miscarriage."
→ Same hash! (same concept, different wording)
```

## Usage

### Step 1: Preview Duplicates

Before running the full deduplication, preview what will be deduplicated:

```bash
# Activate venv
source venv/bin/activate

# Preview adjective duplicates
python3 tools/preview_duplicates.py \
    dictionaries/wiktionary/wiktionary.hashed.txt \
    --pos adj \
    --samples 500 \
    --threshold 0.92

# Preview noun duplicates with looser threshold
python3 tools/preview_duplicates.py \
    dictionaries/wiktionary/wiktionary.hashed.txt \
    --pos noun \
    --samples 500 \
    --threshold 0.88
```

### Step 2: Build Deduplication Mapping

Build a complete mapping from all glosses to their canonical representatives:

```bash
# Build mapping (this takes ~1-2 hours for full dataset)
python3 tools/deduplicate_glosses.py build \
    dictionaries/wiktionary/wiktionary.hashed.txt \
    dictionaries/wiktionary/gloss_mapping.pkl \
    --threshold 0.92

# Build with custom threshold (stricter)
python3 tools/deduplicate_glosses.py build \
    dictionaries/wiktionary/wiktionary.hashed.txt \
    dictionaries/wiktionary/gloss_mapping.pkl \
    --threshold 0.95
```

The script will output statistics like:
```
Original unique glosses: 250,000
Canonical glosses: 235,000
Deduplication ratio: 6.0%
Reduction: 15,000 glosses
```

### Step 3: Apply Deduplication

Use the mapping to create a deduplicated dictionary:

```bash
# Apply deduplication
python3 tools/deduplicate_glosses.py apply \
    dictionaries/wiktionary/wiktionary.hashed.txt \
    dictionaries/wiktionary/gloss_mapping.pkl \
    dictionaries/wiktionary/wiktionary.deduped.txt
```

The output file will have:
- Same format as input (hash, word, pos, gloss)
- Duplicate glosses replaced with canonical version
- Same hash for semantically equivalent glosses

## Similarity Thresholds

The threshold controls how similar glosses must be to be considered duplicates:

| Threshold | Strictness | Use Case |
|-----------|------------|----------|
| 0.95 | Very strict | Only near-identical text (punctuation differences) |
| 0.92 | **Moderate (recommended)** | Similar meanings, different wording |
| 0.88 | Loose | Related concepts |
| 0.85 | Very loose | Broad semantic similarity (may over-cluster) |

## Technical Details

### Embedding Model

- **Model:** sentence-transformers/all-MiniLM-L6-v2
- **Size:** ~80MB
- **Speed:** ~500 sentences/second on CPU
- **Quality:** Good balance of speed and accuracy

### Clustering Algorithm

- **Algorithm:** DBSCAN (Density-Based Spatial Clustering)
- **Metric:** Cosine similarity
- **Advantage:** Doesn't require specifying number of clusters
- **Advantage:** Handles varying cluster sizes naturally

### Why Process by POS?

Glosses are clustered separately for each part-of-speech because:
- "bank" (noun) = "financial institution"
- "bank" (verb) = "to tilt an aircraft"

These should NOT be deduplicated even if the text is similar.

## Performance

Estimated processing time for full Wiktionary (1.67M entries):

| Step | Time (CPU) | Memory |
|------|-----------|--------|
| Extract unique glosses | ~1 min | ~500 MB |
| Compute embeddings | ~30-60 min | ~2 GB |
| Clustering | ~10-30 min | ~2 GB |
| Apply mapping | ~2-5 min | ~1 GB |
| **Total** | **~1-2 hours** | **~2 GB** |

GPU acceleration (if available) can reduce embedding time to ~5-10 minutes.

## Integration with Hash Structure

The current hash structure allocates:
- **Bits 63-12:** Word hash (52 bits)
- **Bits 11-6:** POS index (6 bits)
- **Bits 5-0:** Sense index (6 bits)

Deduplication affects the **sense index**: semantically similar glosses will now share the same sense index, reducing the total number of unique hashes.

**Before deduplication:**
```
67b1dc007bbe6080  red  adj  Of a red hue.
67b1dc007bbe6081  red  adj  Having a red color.
67b1dc007bbe6082  red  adj  Being red in color.
```
(3 different hashes)

**After deduplication:**
```
67b1dc007bbe6080  red  adj  Of a red hue.
67b1dc007bbe6080  red  adj  Of a red hue.
67b1dc007bbe6080  red  adj  Of a red hue.
```
(same hash!)

## Next Steps

1. **Test on sample data** - Validate threshold and review clusters
2. **Run full deduplication** - Process entire Wiktionary
3. **Evaluate results** - Measure deduplication ratio and quality
4. **Integrate with translation** - Use deduplicated hashes for better translation
5. **Iterate** - Tune threshold based on results

## Files Created

- `tools/deduplicate_glosses.py` - Main deduplication tool
- `tools/preview_duplicates.py` - Preview duplicates before processing
- `tools/DEDUPLICATION.md` - This documentation

## References

- Sentence Transformers: https://www.sbert.net/
- DBSCAN: https://en.wikipedia.org/wiki/DBSCAN
- xxh3 hashing: https://github.com/Cyan4973/xxHash

## Questions?

This addresses James's hard problem of concept deduplication. The system uses state-of-the-art NLP embeddings to identify semantic similarity and cluster equivalent glosses together.
