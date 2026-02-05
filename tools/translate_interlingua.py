#!/usr/bin/env python3
"""
Enhanced translation with interlingua fallback.
Uses traditional dictionaries first, falls back to interlingua for missing words.
"""

import sys
from collections import defaultdict

# Map UDPipe UPOS → dictionary POS prefixes
POS_MAP = {
    'NOUN': 'n',
    'VERB': 'v',
    'ADJ': 'a',
    'ADV': 'ad',
    'PRON': 'pron',
    'DET': 'art',
    'ADP': 'prep',
    'CCONJ': 'conj',
    'SCONJ': 'conj',
    'INTJ': 'int',
    'NUM': 'NUM',
}

# Map dictionary POS to wiktionary POS for interlingua lookup
DICT_TO_WIKT_POS = {
    'n': 'noun',
    'v': 'verb',
    'a': 'adj',
    'ad': 'adv',
    'pron': 'pron',
    'art': 'article',
    'prep': 'prep',
    'conj': 'conj',
    'int': 'intj',
}

def load_dictionary(filename):
    """Load dictionary into dict[word] = definitions"""
    dictionary = {}
    with open(filename, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if '\t' in line:
                word, defs = line.split('\t', 1)
                dictionary[word] = defs
    return dictionary

def load_interlingua_master(hashed_file):
    """Load wiktionary hash -> (word, pos, gloss) mapping"""
    master = {}
    word_pos_to_hashes = defaultdict(list)

    try:
        with open(hashed_file, 'r', encoding='utf-8') as f:
            for line in f:
                parts = line.strip().split('\t')
                if len(parts) >= 4:
                    hash_hex, word, pos, gloss = parts[0], parts[1], parts[2], parts[3]
                    master[hash_hex] = (word, pos, gloss)
                    word_pos_to_hashes[(word.lower(), pos.lower())].append(hash_hex)
        return master, word_pos_to_hashes
    except FileNotFoundError:
        return None, None

def load_interlingua_translation(lang_file):
    """Load interlingua translation hash -> word mapping"""
    trans = {}
    try:
        with open(lang_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith('#') or line.startswith('hash'):
                    continue
                parts = line.strip().split('\t')
                if len(parts) >= 2:
                    hash_hex, translation = parts[0], parts[1]
                    trans[hash_hex] = translation
        return trans
    except FileNotFoundError:
        return None

def generate_candidates(word):
    """Generate lookup candidates in priority order"""
    candidates = []
    word_lower = word.lower()

    # 1. Exact match (lowercased)
    candidates.append(word_lower)

    # 2. Handle UDPipe possessive lemmatization
    possessive_map = {
        'i': 'my',
        'you': 'your',
        'he': 'his',
        'she': 'her',
        'it': 'its',
        'we': 'our',
        'they': 'their',
    }
    if word_lower in possessive_map:
        candidates.append(possessive_map[word_lower])

    # 3. Handle possessives: water's → waters, water
    if word_lower.endswith("'s"):
        base = word_lower[:-2]
        candidates.append(base + 's')
        candidates.append(base)

    # 4. Handle hyphens: any-thing → anything
    if '-' in word_lower:
        candidates.append(word_lower.replace('-', ''))

    # Remove duplicates while preserving order
    seen = set()
    result = []
    for c in candidates:
        if c not in seen:
            seen.add(c)
            result.append(c)

    return result

def extract_translation(defs, upos):
    """Extract translation from definitions with POS awareness"""
    pos_prefix = POS_MAP.get(upos)

    if not pos_prefix:
        first_entry = defs.split('@')[0]
        return first_entry.split('.', 1)[1].split(',')[0] if '.' in first_entry else defs

    # Try to match POS
    entries = defs.split('@')
    for entry in entries:
        if '.' in entry:
            entry_pos = entry.split('.')[0]
            if entry_pos.startswith(pos_prefix):
                trans = entry.split('.', 1)[1].split(',')[0]
                return trans

    # Fallback: return first translation
    first_entry = entries[0]
    if '.' in first_entry:
        return first_entry.split('.', 1)[1].split(',')[0]
    return first_entry

def lookup_interlingua(word, upos, word_pos_to_hashes, target_trans):
    """
    Lookup word in interlingua system.
    Returns translation or None.
    """
    if not word_pos_to_hashes or not target_trans:
        return None

    # Map UPOS to dictionary POS, then to wiktionary POS
    dict_pos = POS_MAP.get(upos)
    if not dict_pos:
        return None

    wikt_pos = DICT_TO_WIKT_POS.get(dict_pos)
    if not wikt_pos:
        return None

    # Look up in hash space
    key = (word.lower(), wikt_pos)
    if key in word_pos_to_hashes:
        hashes = word_pos_to_hashes[key]
        # Try first hash (primary sense)
        if hashes[0] in target_trans:
            return target_trans[hashes[0]]

    return None

def lookup(surface, lemma, upos, dictionary, word_pos_to_hashes=None, target_trans=None):
    """
    Lookup with cascading fallback:
    1. Try traditional dictionary
    2. If not found, try interlingua system
    3. If still not found, passthrough
    """

    # List of possessive pronouns
    possessives = {'my', 'your', 'his', 'her', 'its', 'our', 'their'}
    surface_lower = surface.lower()

    # Special case: possessive pronouns
    if surface_lower in possessives and surface_lower != lemma.lower():
        candidates = generate_candidates(surface)
        for candidate in candidates:
            if candidate in dictionary:
                return extract_translation(dictionary[candidate], upos)

    # Priority 1: Try lemma with POS in traditional dictionary
    candidates = generate_candidates(lemma)
    for candidate in candidates:
        if candidate in dictionary:
            return extract_translation(dictionary[candidate], upos)

    # Priority 2: Try surface form in traditional dictionary
    if surface.lower() != lemma.lower():
        candidates = generate_candidates(surface)
        for candidate in candidates:
            if candidate in dictionary:
                return extract_translation(dictionary[candidate], upos)

    # Priority 3: Try interlingua system (if available)
    if word_pos_to_hashes and target_trans:
        # Try lemma first
        trans = lookup_interlingua(lemma, upos, word_pos_to_hashes, target_trans)
        if trans:
            return trans

        # Try surface form
        if surface.lower() != lemma.lower():
            trans = lookup_interlingua(surface, upos, word_pos_to_hashes, target_trans)
            if trans:
                return trans

    # Priority 4: Passthrough
    return surface

def main():
    if len(sys.argv) < 2:
        print("Usage: translate_interlingua.py <dictionary_file> [--use-interlingua]", file=sys.stderr)
        sys.exit(1)

    dict_file = sys.argv[1]
    use_interlingua = '--use-interlingua' in sys.argv

    # Load traditional dictionary
    dictionary = load_dictionary(dict_file)

    # Optionally load interlingua system
    word_pos_to_hashes = None
    target_trans = None

    if use_interlingua:
        # Extract language code from dictionary filename: en_zh.txt -> zh
        import re
        match = re.search(r'en_([a-z]{2})\.txt', dict_file)
        if match:
            lang_code = match.group(1)

            # Load interlingua master and target translations
            master, word_pos_to_hashes = load_interlingua_master(
                'dictionaries/wiktionary/wiktionary.hashed.txt'
            )
            target_trans = load_interlingua_translation(
                f'dictionaries/lingua/en_{lang_code}.txt'
            )

            if word_pos_to_hashes and target_trans:
                print(f"# Interlingua system loaded for {lang_code}", file=sys.stderr)

    # Process UDPipe CoNLL-U output
    for line in sys.stdin:
        if line.startswith('#'):
            print(line, end='')
            continue

        if not line.strip():
            continue

        cols = line.strip().split('\t')
        if len(cols) < 4:
            continue

        word_id, form, lemma, upos = cols[0:4]

        if upos == 'PUNCT':
            continue

        # Lookup with cascading fallback (including interlingua if enabled)
        translation = lookup(form, lemma, upos, dictionary,
                           word_pos_to_hashes, target_trans)

        print(f"{form}\t{lemma}/{upos}\t→\t{translation}")

if __name__ == '__main__':
    main()
