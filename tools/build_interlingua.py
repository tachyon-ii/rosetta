#!/usr/bin/env python3
"""
Build interlingua translation files from hashed wiktionary and existing dictionaries.
Maps existing en_XX.txt dictionaries to the wiktionary hash space.
"""

import sys
import gzip
from collections import defaultdict

# POS mapping from existing dictionaries to wiktionary format
DICT_TO_WIKT_POS = {
    'n.': 'noun',
    'v.': 'verb',
    'vt.': 'verb',
    'vi.': 'verb',
    'a.': 'adj',
    'ad.': 'adv',
    'art.': 'article',
    'prep.': 'prep',
    'pron.': 'pron',
    'conj.': 'conj',
    'int.': 'intj',
    'num.': 'num',
    'part.': 'particle',
}

def load_hashed_wiktionary(hashed_file):
    """
    Load hashed wiktionary: hash -> (word, pos, gloss)
    Also build reverse index: (word, pos) -> [hashes]
    """
    hash_to_entry = {}
    word_pos_to_hashes = defaultdict(list)
    
    print(f"Loading hashed wiktionary from {hashed_file}...")
    
    try:
        with open(hashed_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                parts = line.strip().split('\t')
                if len(parts) < 4:
                    continue
                
                hash_hex, word, pos, gloss = parts[0], parts[1], parts[2], parts[3]
                
                word_lower = word.lower()
                pos_lower = pos.lower()
                
                hash_to_entry[hash_hex] = (word, pos, gloss)
                word_pos_to_hashes[(word_lower, pos_lower)].append(hash_hex)
                
                if line_num % 100000 == 0:
                    print(f"  Loaded {line_num:,} entries...")
    except FileNotFoundError:
        print(f"Error: File {hashed_file} not found!")
        print("Run: python3 tools/hash_wiktionary.py first")
        sys.exit(1)
    
    print(f"Loaded {len(hash_to_entry):,} hashed entries")
    print(f"Covering {len(word_pos_to_hashes):,} unique (word, pos) pairs")
    
    return hash_to_entry, word_pos_to_hashes

def parse_dictionary_line(line):
    """
    Parse existing dictionary format: word<TAB>pos.translation@pos.translation
    Returns: word, [(pos, translation), ...]
    """
    parts = line.strip().split('\t')
    if len(parts) < 2:
        return None, []
    
    word = parts[0].lower()
    translations = []
    
    # Parse: a.相似的,同样的@vt.喜欢,愿意@vi.喜欢
    pos_groups = parts[1].split('@')
    
    for group in pos_groups:
        if '.' not in group:
            continue
        
        pos_part, trans_part = group.split('.', 1)
        
        # Get first translation (ignore variants)
        trans = trans_part.split(',')[0]
        
        # Remove gender markers (_m, _f, _n)
        trans = trans.split('_')[0]
        
        # Handle empty translations (like art.—)
        if not trans or trans == '—':
            trans = ''
        
        translations.append((pos_part, trans))
    
    return word, translations

def build_translation_file(hashed_wiktionary, word_pos_to_hashes, 
                          dict_file, lang_code, output_file):
    """
    Map existing dictionary to hashed interlingua format.
    Output: hash<TAB>translation
    """
    print(f"\nBuilding {lang_code} translation file...")
    
    hash_to_entry, _ = hashed_wiktionary
    
    # Load existing dictionary
    translations = {}  # (word, pos) -> translation
    
    try:
        with open(dict_file, 'r', encoding='utf-8') as f:
            for line in f:
                word, trans_list = parse_dictionary_line(line)
                if not word:
                    continue
                
                for pos, trans in trans_list:
                    # Map POS to wiktionary format
                    wikt_pos = DICT_TO_WIKT_POS.get(pos, None)
                    if not wikt_pos:
                        continue
                    
                    key = (word, wikt_pos)
                    if key not in translations:
                        translations[key] = trans
    except FileNotFoundError:
        print(f"  Warning: {dict_file} not found, skipping")
        return
    
    print(f"  Loaded {len(translations):,} translations")
    
    # Map to hashes
    matched = 0
    unmatched = 0
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"# Interlingua translation file: English -> {lang_code}\n")
        f.write(f"# Format: hash<TAB>translation\n")
        f.write(f"hash\ttranslation\n")
        
        for (word, pos), trans in sorted(translations.items()):
            key = (word, pos)
            
            if key in word_pos_to_hashes:
                # Use first hash (primary sense)
                hashes = word_pos_to_hashes[key]
                hash_hex = hashes[0]  # Primary sense
                
                if trans:  # Only write non-empty translations
                    f.write(f"{hash_hex}\t{trans}\n")
                    matched += 1
            else:
                unmatched += 1
    
    print(f"  Matched: {matched:,} | Unmatched: {unmatched:,}")
    coverage = (matched / (matched + unmatched) * 100) if (matched + unmatched) > 0 else 0
    print(f"  Coverage: {coverage:.1f}%")

def build_reverse_dictionaries(word_pos_to_hashes, output_dir):
    """
    Create reverse lookup files: lang -> hash mappings
    This allows any_lang -> any_lang translation
    """
    print("\nCreating reverse lookup indices...")
    
    # This would be for future enhancement
    # For now, we rely on the hash-based lookup
    pass

def main():
    # Paths
    hashed_wikt = 'dictionaries/wiktionary/wiktionary.hashed.txt'
    output_dir = 'dictionaries/lingua'
    
    # Create output directory
    import os
    os.makedirs(output_dir, exist_ok=True)
    
    # Load hashed wiktionary
    hashed_wiktionary = load_hashed_wiktionary(hashed_wikt)
    hash_to_entry, word_pos_to_hashes = hashed_wiktionary
    
    # Language mappings
    languages = [
        ('zh', 'dictionaries/en_zh.txt'),
        ('es', 'dictionaries/en_es.txt'),
        ('hi', 'dictionaries/en_hi.txt'),
        ('ar', 'dictionaries/en_ar.txt'),
        ('fr', 'dictionaries/en_fr.txt'),
        ('bn', 'dictionaries/en_bn.txt'),
        ('pt', 'dictionaries/en_pt.txt'),
        ('ru', 'dictionaries/en_ru.txt'),
        ('de', 'dictionaries/en_de.txt'),
        ('ja', 'dictionaries/en_ja.txt'),
        ('id', 'dictionaries/en_id.txt'),
        ('ur', 'dictionaries/en_ur.txt'),
        ('vi', 'dictionaries/en_vi.txt'),
        ('mr', 'dictionaries/en_mr.txt'),
    ]
    
    print("\n" + "=" * 70)
    print("BUILDING INTERLINGUA TRANSLATION FILES")
    print("=" * 70)
    
    # Build translation files
    for lang_code, dict_file in languages:
        output_file = f'{output_dir}/en_{lang_code}.txt'
        build_translation_file(hashed_wiktionary, word_pos_to_hashes,
                              dict_file, lang_code, output_file)
    
    print("\n" + "=" * 70)
    print("✓ INTERLINGUA BUILD COMPLETE")
    print("=" * 70)
    print(f"\nOutput files in: {output_dir}/")
    print("Next step: Test with tools/interlingua_translate.py")

if __name__ == '__main__':
    main()