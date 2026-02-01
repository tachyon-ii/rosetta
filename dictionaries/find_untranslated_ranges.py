#!/usr/bin/env python3

import sys

def is_untranslated(word, trans):
    if not trans:
        return True
    t = trans.strip()
    if not t:
        return True
    if t == word:
        return True
    return False

def print_ranges(indices):
    if not indices:
        return
    start = prev = indices[0]
    for i in indices[1:]:
        if i == prev + 1:
            prev = i
        else:
            print(f"{start}-{prev}")
            start = prev = i
    print(f"{start}-{prev}")

def main(path):
    untranslated = []

    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for lineno, line in enumerate(f, start=1):
            line = line.rstrip("\n")
            if "\t" not in line:
                untranslated.append(lineno)
                continue

            word, trans = line.split("\t", 1)
            if is_untranslated(word, trans):
                untranslated.append(lineno)

    print_ranges(untranslated)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: find_untranslated_ranges.py <dictionary.tsv>", file=sys.stderr)
        sys.exit(1)
    main(sys.argv[1])

