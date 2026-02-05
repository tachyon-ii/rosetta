# ROSETTA - Offline Translation for CGIOS

**Lighthouse, not life plan.** A minimal translation system for civilization reboot scenarios.

## Philosophy

When everything is available, nothing is sacred. ROSETTA provides "good enough" translation to make English-language knowledge accessible across linguistic boundaries. Component-by-component translation is transparent, teachable, and verifiable - better than black-box systems when trust is low.

## Language Coverage

**Key insight:** Top 5 languages cover 4.2B people (~50% of humanity). Top 10 cover 5.6B (~70%). Beyond that: diminishing returns.

| #  | Language                | L1 (M) | L2 (M) | Total (M) | Cumulative (M) | Gender | Status | Priority | Skip |
|----|-------------------------|--------|--------|-----------|----------------|--------|--------|----------|------|
| 1  | English                 | 390    | 1,138  | 1,528     | 1,528          | -      | ✓ Ref  | -        | -    |
| 2  | Mandarin Chinese        | 990    | 194    | 1,184     | 2,712          | None   | ✓ Done | -        | -    |
| 3  | Hindi                   | 345    | 264    | 609       | 3,321          | 2      | ✓ Done | HIGH     | -    |
| 4  | Spanish                 | 484    | 74     | 558       | 3,879          | 2      | ✓ Done | HIGH     | -    |
| 5  | Standard Arabic         | 0      | 335    | 335       | 4,214          | 2      | ✓ Done | HIGH     | -    |
| 6  | French                  | 74     | 238    | 312       | 4,526          | 2      | ✓ Done | MEDIUM   | -    |
| 7  | Bengali                 | 242    | 43     | 284       | 4,810          | 2      | ✓ Done | MEDIUM   | -    |
| 8  | Portuguese              | 250    | 17     | 267       | 5,077          | 2      | ✓ Done | MEDIUM   | -    |
| 9  | Russian                 | 145    | 108    | 253       | 5,330          | 3      | ✓ Done | MEDIUM   | -    |
| 10 | Indonesian              | 75     | 177    | 252       | 5,582          | None   | ✓ Done | MEDIUM   | -    |
| 11 | Urdu                    | 78     | 168    | 246       | 5,828          | 2      | TODO   | LOW      | -    |
| 12 | German                  | 76     | 58     | 134       | 5,962          | 3      | TODO   | LOW      | -    |
| 13 | Japanese                | 124    | 2      | 126       | 6,088          | None   | TODO   | LOW      | -    |
| 14 | Nigerian Pidgin         | 5      | 116    | 121       | 6,209          | None   | TODO   | LOW      | [1]  |
| 15 | Egyptian Arabic         | 84     | 35     | 119       | 6,328          | 2      | TODO   | LOW      | [2]  |
| 16 | Marathi                 | 83     | 16     | 99        | 6,427          | 2      | TODO   | LOW      | -    |
| 17 | Vietnamese              | 86     | 11     | 97        | 6,524          | None   | TODO   | LOW      | -    |
| 18 | Telugu                  | 83     | 13     | 96        | 6,620          | 2-3    | TODO   | LOW      | -    |
| 19 | Hausa                   | 58     | 36     | 94        | 6,714          | Min    | TODO   | LOW      | -    |
| 20 | Turkish                 | 85     | 6      | 91        | 6,805          | None   | TODO   | LOW      | -    |
| 21 | Western Punjabi         | —      | —      | 90        | 6,895          | 2      | TODO   | LOW      | -    |
| 22 | Swahili                 | 4      | 83     | 87        | 6,982          | Class  | TODO   | LOW      | -    |
| 23 | Tagalog                 | 33     | 54     | 87        | 7,069          | None   | TODO   | LOW      | -    |
| 24 | Tamil                   | 79     | 8      | 86        | 7,155          | 5      | TODO   | LOW      | -    |
| 25 | Yue Chinese (Cantonese) | 85     | 1      | 86        | 7,241          | None   | TODO   | LOW      | -    |
| 26 | Wu Chinese              | 83     | <1     | 83        | 7,324          | None   | TODO   | LOW      | [3]  |
| 27 | Iranian Persian         | 65     | 17     | 83        | 7,407          | 2      | TODO   | LOW      | -    |
| 28 | Korean                  | 81     | <1     | 82        | 7,489          | None   | TODO   | LOW      | -    |
| 29 | Thai                    | 27     | 44     | 71        | 7,560          | None   | TODO   | LOW      | -    |
| 30 | Javanese                | —      | —      | 69        | 7,629          | None   | TODO   | LOW      | -    |
| 31 | Italian                 | 63     | 3      | 66        | 7,695          | 2      | TODO   | LOW      | -    |
| 32 | Gujarati                | 58     | 5      | 62        | 7,757          | 2      | TODO   | LOW      | -    |
| 33 | Levantine Arabic        | 58     | 3      | 60        | 7,817          | 2      | TODO   | LOW      | [2]  |
| 34 | Amharic                 | 35     | 25     | 60        | 7,877          | 2      | TODO   | LOW      | -    |
| 35 | Kannada                 | 44     | 15     | 59        | 7,936          | 2      | TODO   | LOW      | -    |
| 36 | Bhojpuri                | 53     | <1     | 53        | 7,989          | 2      | TODO   | LOW      | -    |
| 37 | Sudanese Arabic         | 41     | 11     | 52        | 8,041          | 2      | TODO   | LOW      | [2]  |

---

**Skip Footnotes:**

[1] **Nigerian Pidgin** - English-based creole without standardized orthography; questionable utility for written knowledge preservation despite large speaker base

[2] **Arabic dialects** (Egyptian, Levantine, Sudanese) - Regional variants largely covered by Modern Standard Arabic for written/formal contexts; MSA provides literacy foundation while Egyptian serves as media lingua franca

[3] **Wu Chinese** - Regional variant (Shanghai area) with limited international presence; Mandarin + Cantonese provide better coverage for Chinese diaspora and cross-regional communication

**Coverage milestones:**
- **Top 5:** 4.2B people (~50% of humanity) - ✓ COMPLETE
- **Top 10:** 5.6B people (~70% of humanity) - 90% complete (Indonesian WIP)
- **Top 20:** 6.8B people (~85% of humanity)
- **All 37:** 8.0B "language usages" (but massive overlap)

**Economics:** ~1-2MB per language. 40 languages < 200MB total.

**Status:** First 9 languages completed (English through Russian), covering 5.3B people. Indonesian (#10) in progress, which will complete the top 10 milestone at 5.6B coverage.

## How It Works
```bash
Input text → normalize.py → UDPipe → translate.py → Output
```

**Example:**
```bash
echo "I like water." | \
  ./tools/normalize.py | \
  ./udpipe/udpipe --tokenize --tag udpipe/english-ud-1.2-160523.udpipe | \
  ./tools/translate.py dictionaries/en_zh.txt
```

**Output:**
```
I       I/PRON    → 我
like    like/VERB → 喜欢
water   water/NOUN→ 水
```

## Dictionary Format

**File:** Tab-separated values (TSV), UTF-8 encoded

**Structure:**
```
word<TAB>pos.translation,translation@pos.translation
```

**With Gender Support (languages with grammatical gender):**
```
word<TAB>pos.translation_masculine,translation_feminine@pos.translation
```

**Example (Chinese - no gender):**
```
like    a.相似的,同样的@vt.喜欢,愿意,想@vi.喜欢,希望@n.爱好@prep.象,如同
water   n.水,雨水,海水@vt.浇水@vi.流泪
```

**Example (French - 2 genders m/f):**
```
like    a.semblable,similaire@vt.aimer,vouloir@vi.aimer,souhaiter@n.goût_m,préférence_f@prep.comme
water   n.eau_f@vt.arroser@vi.larmoyer
```

**Example (Russian - 3 genders m/f/n):**
```
like    a.подобный_m,подобная_f,подобное_n@vt.любить,хотеть@n.склонность_f
water   n.вода_f@vt.поливать
```

**Normalization rules:**
- All headwords lowercase
- Hyphens removed (compound into single word: `any-thing` → `anything`)
- Pipe-separated variants collapsed to first alternative
- Duplicates removed (first occurrence wins)

**Part-of-Speech tags:**

| Dictionary | UDPipe | Meaning                      | Notes                           |
|------------|--------|------------------------------|----------------------------------|
| n.         | NOUN   | noun (common)                |                                  |
| n.         | PROPN  | proper noun                  | Both map to n. in dictionary     |
| v.         | VERB   | verb (general)               |                                  |
| vt.        | VERB   | transitive verb              | Subtype of VERB                  |
| vi.        | VERB   | intransitive verb            | Subtype of VERB                  |
| v.         | AUX    | auxiliary verb               | Maps to v. (helper verbs)        |
| a.         | ADJ    | adjective                    |                                  |
| ad.        | ADV    | adverb                       |                                  |
| art.       | DET    | article/determiner           |                                  |
| prep.      | ADP    | adposition (prep/postpos)    |                                  |
| pron.      | PRON   | pronoun                      |                                  |
| conj.      | CCONJ  | coordinating conjunction     | "and", "but", "or"               |
| conj.      | SCONJ  | subordinating conjunction    | "because", "if", "that"          |
| int.       | INTJ   | interjection                 |                                  |
| num.       | NUM    | numeral                      | New tag needed                   |
| part.      | PART   | particle                     | New tag needed                   |
| sym.       | SYM    | symbol                       | New tag needed (optional)        |
| punc.      | PUNCT  | punctuation                  | New tag needed (optional)        |
| x.         | X      | other/foreign                | New tag needed (optional)        |

## Repository Structure
```
ROSETTA/
├── README.md                    # This file
├── dictionaries/
│   ├── dict-sorted.txt          # English reference (82,765 words)
│   ├── en_zh.txt                # English→Chinese (✓ Done)
│   ├── en_hi.txt                # English→Hindi (✓ Done)
│   ├── en_es.txt                # English→Spanish (✓ Done)
│   ├── en_ar.txt                # English→Arabic (✓ Done)
│   ├── en_fr.txt                # English→French (✓ Done)
│   ├── en_bn.txt                # English→Bengali (✓ Done)
│   ├── en_pt.txt                # English→Portuguese (✓ Done)
│   ├── en_ru.txt                # English→Russian (✓ Done)
│   └── en_id.txt                # English→Indonesian (WIP)
├── tools/
│   ├── normalize.py             # Pre-processor (strip possessives, hyphens)
│   ├── translate.py             # POS-aware dictionary lookup with gender support
│   └── rosetta.py               # Markdown translator with structure preservation
├── udpipe/
│   ├── udpipe                   # Binary (16MB)
│   └── english-ud-1.2-160523.udpipe
└── tests/
    ├── test_edge_cases.md       # Comprehensive markdown test document
    └── test_runner.py           # Automated test validation
```

## Dependencies

- **UDPipe:** ~16MB model + ~6MB binaries (Mac/Linux/Windows)
- **Python 3:** Already budgeted in foundation (100MB)
- **Dictionaries:** ~1-2MB per target language

## Creating New Dictionaries

1. **Find bilingual EN→X dictionary** (any format)
2. **Convert to ROSETTA format:**
   - Normalize headwords (lowercase, strip hyphens)
   - Structure as `word\tpos.translation@pos.translation`
3. **Test against 82k reference** to identify gaps
4. **Fill critical gaps** (top 10-40k) via LLM if needed
5. **Ship it** (1-2MB file)

## Output Format

Interlinear word-by-word gloss:
```
SURFACE_FORM<TAB>LEMMA/POS<TAB>→<TAB>TRANSLATION
```

This is intentionally **literal**, not fluent. Users can:
- See original tokens
- Verify POS tags
- Learn patterns
- Trust the system (no hidden processing)

## Next Steps

### Immediate (Top 10 Completion)
1. ✓ Spanish dictionary (558M speakers) - DONE
2. ✓ Hindi dictionary (609M speakers) - DONE
3. ✓ Arabic dictionary (335M speakers) - DONE
4. Complete Indonesian dictionary (252M speakers) - IN PROGRESS

### Future Expansion (Optional)
5. Urdu dictionary (246M speakers) - shares script with Arabic
6. Standard German dictionary (134M speakers)
7. Japanese dictionary (126M speakers)
8. Continue down priority list as resources permit

### Technical Improvements
- [x] Add gender support for grammatical gender languages
- [x] Markdown translator with structure preservation
- [ ] Fine-tune blockquote rendering
- [ ] Optimize table separator handling
- [ ] Perfect math expression preservation

## License

Foundation knowledge for civilization continuity. Use freely.
