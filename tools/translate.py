#!/usr/bin/env python3
import sys

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

def generate_candidates(word):
    """Generate lookup candidates in priority order"""
    candidates = []
    word_lower = word.lower()
    
    # 1. Exact match (lowercased)
    candidates.append(word_lower)
    
    # 2. Handle UDPipe possessive lemmatization: "you" → "your", "i" → "my", etc.
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
        candidates.append(base + 's')  # waters
        candidates.append(base)        # water
    
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
        # No POS mapping, return first translation
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

def lookup(surface, lemma, upos, dictionary):
    """Lookup with cascading fallback"""
    
    # List of possessive pronouns - if surface matches, try it first
    possessives = {'my', 'your', 'his', 'her', 'its', 'our', 'their'}
    surface_lower = surface.lower()
    
    # Special case: If surface is a possessive pronoun, prioritize surface over lemma
    if surface_lower in possessives and surface_lower != lemma.lower():
        candidates = generate_candidates(surface)
        for candidate in candidates:
            if candidate in dictionary:
                return extract_translation(dictionary[candidate], upos)
    
    # Priority 1: Try lemma with POS
    candidates = generate_candidates(lemma)
    for candidate in candidates:
        if candidate in dictionary:
            return extract_translation(dictionary[candidate], upos)
    
    # Priority 2: Try surface form (in case lemma normalization failed)
    if surface.lower() != lemma.lower():
        candidates = generate_candidates(surface)
        for candidate in candidates:
            if candidate in dictionary:
                return extract_translation(dictionary[candidate], upos)
    
    # Priority 3: Passthrough
    return surface

def main():
    if len(sys.argv) < 2:
        print("Usage: translate.py <dictionary_file>", file=sys.stderr)
        sys.exit(1)
    
    dict_file = sys.argv[1]
    dictionary = load_dictionary(dict_file)
    
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
        
        # Lookup with cascading fallback
        translation = lookup(form, lemma, upos, dictionary)
        
        print(f"{form}\t{lemma}/{upos}\t→\t{translation}")

if __name__ == '__main__':
    main()
