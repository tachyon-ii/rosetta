#!/usr/bin/env python3
"""
Interlingua translation: Any language -> Any language via hash space.
"""

import sys
from collections import defaultdict

def load_master(hashed_file):
    """Load hash -> (word, pos, gloss) mapping."""
    master = {}
    with open(hashed_file, 'r', encoding='utf-8') as f:
        for line in f:
            parts = line.strip().split('\t')
            if len(parts) >= 4:
                hash_hex, word, pos, gloss = parts[0], parts[1], parts[2], parts[3]
                master[hash_hex] = (word, pos, gloss)
    return master

def load_translation(lang_file):
    """Load hash -> translation mapping."""
    trans = {}
    reverse = defaultdict(list)  # translation -> [hashes]

    with open(lang_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.startswith('#') or line.startswith('hash'):
                continue

            parts = line.strip().split('\t')
            if len(parts) >= 2:
                hash_hex, translation = parts[0], parts[1]
                trans[hash_hex] = translation
                reverse[translation.lower()].append(hash_hex)

    return trans, reverse

def translate(word, source_lang, target_lang,
              master_file='dictionaries/wiktionary/wiktionary.hashed.txt',
              lingua_dir='dictionaries/lingua'):
    """
    Translate word from source to target language.
    """
    # Load files
    master = load_master(master_file)

    # Handle English as source - use master file
    if source_lang == 'en':
        source_hashes = []
        word_lower = word.lower()
        # Find all hashes for this English word
        for hash_hex, (eng_word, pos, gloss) in master.items():
            if eng_word.lower() == word_lower:
                source_hashes.append(hash_hex)
    else:
        source_trans, source_reverse = load_translation(f'{lingua_dir}/en_{source_lang}.txt')
        word_lower = word.lower()
        source_hashes = source_reverse.get(word_lower, [])

    if not source_hashes:
        return []

    # Load target translations
    if target_lang == 'en':
        # Target is English - return the English words from master
        results = []
        for hash_hex in source_hashes:
            if hash_hex in master:
                eng_word, pos, gloss = master[hash_hex]
                results.append({
                    'hash': hash_hex,
                    'translation': eng_word,
                    'english': eng_word,
                    'pos': pos,
                    'gloss': gloss[:60] + '...' if len(gloss) > 60 else gloss
                })
        return results
    else:
        target_trans, _ = load_translation(f'{lingua_dir}/en_{target_lang}.txt')
        # Translate via hash
        results = []
        for hash_hex in source_hashes:
            if hash_hex in target_trans:
                eng_word, pos, gloss = master.get(hash_hex, ('?', '?', '?'))
                results.append({
                    'hash': hash_hex,
                    'translation': target_trans[hash_hex],
                    'english': eng_word,
                    'pos': pos,
                    'gloss': gloss[:60] + '...' if len(gloss) > 60 else gloss
                })

        return results

def main():
    if len(sys.argv) < 4:
        print("Usage: interlingua_translate.py <word> <source_lang> <target_lang>")
        print("")
        print("Examples:")
        print("  interlingua_translate.py water en zh      # English -> Chinese")
        print("  interlingua_translate.py agua es zh       # Spanish -> Chinese")
        print("  interlingua_translate.py 水 zh es         # Chinese -> Spanish")
        print("")
        print("Available languages: zh, es, hi, ar, fr, bn, pt, ru, de, ja, id, ur, vi, mr")
        sys.exit(1)

    word = sys.argv[1]
    source = sys.argv[2]
    target = sys.argv[3]

    try:
        results = translate(word, source, target)

        if results:
            print(f"\n'{word}' ({source}) → ({target}):")
            print("=" * 60)
            for i, r in enumerate(results, 1):
                print(f"\n{i}. {r['translation']}")
                print(f"   via English: {r['english']} ({r['pos']})")
                print(f"   meaning: {r['gloss']}")
                print(f"   hash: {r['hash']}")
        else:
            print(f"\nNo translation found for '{word}' from {source} to {target}")
            print("This could mean:")
            print("  1. Word not in source language dictionary")
            print("  2. Word exists in source but not in target")
            print("  3. Word not in wiktionary hash space")

    except FileNotFoundError as e:
        print(f"\nError: {e}")
        print("\nMake sure you've run:")
        print("  1. python3 tools/hash_wiktionary.py ...")
        print("  2. python3 tools/build_interlingua.py")

if __name__ == '__main__':
    main()
