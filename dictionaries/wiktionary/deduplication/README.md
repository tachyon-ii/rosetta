# Wiktionary Deduplication

## Summary

**Date:** 2026-02-10
**Method:** Semantic deduplication using sentence embeddings + LLM review

### Results

- **Original entries:** 1,670,474
- **Deduplicated entries:** 1,658,488
- **Duplicates removed:** 11,986 (0.72%)
- **Confidence:** 97.5% (LLM validated)

### Approach

1. **Correct semantic matching:**
   - Grouped entries by (word, POS) first
   - Embedded only glosses (not word + pos)
   - Found duplicates within each word only
   - Threshold: 0.85 cosine similarity

2. **Automated LLM review:**
   - Used Ollama llama3.1 for classification
   - Confirmed: 11,986 true duplicates (97.5%)
   - Rejected: 388 false positives (3.2%)
   - Skipped: 11 uncertain cases (0.09%)

3. **Quality validation:**
   - Spelling variants: ✓ (color/colour)
   - Different phrasings: ✓ (lieutenant colonel)
   - False positives filtered: ✓ (authserv, gigaton)

### Files

- `deduplication_stats.json` - Statistics by POS
- `auto_review_results_clean_mapping.json` - Hash mapping (11,986 duplicates)

### Implementation

Duplicates were removed from the main wiktionary.hashed.txt file.
Original backup available on server at:
`/data2000/deduplication_applied/backups/`

Can be restored if needed.

### Tools Used

- sentence-transformers (all-MiniLM-L6-v2)
- Ollama llama3.1 (local LLM for validation)
- Python scripts in tools/
