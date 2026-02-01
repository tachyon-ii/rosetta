# ROSETTA Translator Edge Cases Test Document

This document contains challenging markdown structures to test translation robustness.

## 1. Nested Lists

### Unordered nested lists

- Level 1 item one
- Level 1 item two
  - Level 2 item one
  - Level 2 item two
    - Level 3 item one
    - Level 3 item two
  - Level 2 item three
- Level 1 item three

### Ordered nested lists

1. First level one
2. First level two
   1. Second level one
   2. Second level two
      1. Third level one
      2. Third level two
   3. Second level three
3. First level three

### Mixed nested lists

1. Ordered item one
   - Unordered sub-item
   - Another unordered sub-item
2. Ordered item two
   1. Ordered sub-item
   2. Another ordered sub-item
      - Nested unordered
      - More nested unordered

---

## 2. Complex Tables

### Table with alignment

| Left aligned | Center aligned | Right aligned |
|:-------------|:--------------:|--------------:|
| Left text    | Center text    | Right text    |
| Short        | Mid            | Long text here|

### Table with inline code

| Command | Description | Example |
|---------|-------------|---------|
| `ls`    | List files  | `ls -la` |
| `cd`    | Change dir  | `cd /home` |
| `pwd`   | Print dir   | `pwd` |

### Table with math

| Formula | Description | Value |
|---------|-------------|-------|
| $x^2$   | Square      | 4     |
| $\sqrt{x}$ | Root     | 2     |
| $e^{i\pi}$ | Euler    | -1    |

### Empty cells

| Column A | Column B | Column C |
|----------|----------|----------|
| Data     |          | More     |
|          | Middle   |          |
| Last     | Row      | Data     |

---

## 3. Code in Lists

### Code blocks in lists

1. First step
   
   ```python
   def hello():
       print("world")
   ```

2. Second step
   
   ```bash
   cd /home
   ls -la
   ```

3. Third step with inline `code here` in text

### Multiple code blocks

- Item with code:
  
   ```
   code block 1
   ```
  
   And more text.
  
   ```
   code block 2
   ```

---

## 4. Mixed Content

### Lists with everything

1. **Bold text** and *italic text*
2. Text with `inline code` in it
3. Text with $x = y^2$ math in it
4. Text with [a link](https://example.com)
5. Text with <span>HTML</span> tags

### Table with mixed content

| Type | Example | Notes |
|------|---------|-------|
| Code | `print()` | Function call |
| Math | $\int_0^1 x dx$ | Integral |
| Link | [Click](http://example.com) | External |
| Bold | **Important** | Emphasis |

---

## 5. HTML Blocks

<div class="warning">
This is a warning box with HTML.
</div>

Regular markdown text continues here.

<table>
<tr><td>HTML table</td><td>Not markdown</td></tr>
</table>

More markdown text.

---

## 6. Special Characters

### Unicode and symbols

- Emoji: 🎉 🔥 ✨ 🚀
- Arrows: → ← ↑ ↓ ⇒ ⇐
- Math: ∞ ∑ ∫ √ ≠ ≈ ≤ ≥
- Currency: $ € £ ¥ ₹
- Accents: café, naïve, résumé

### Edge case punctuation

Text with... ellipsis and—em dash—and quotes "like this" and 'like this'.

---

## 7. Long Lines

This is a very long line of text that should not be broken up during translation even though it contains many words and extends far beyond typical line length limits used in most editors which usually wrap around eighty characters but this line just keeps going and going to test how the translator handles very long continuous text without any natural break points or paragraph boundaries.

---

## 8. Blockquotes

> This is a blockquote with `code` in it.
> 
> It continues on multiple lines.
> 
> > And has nested blockquotes.
> > 
> > With $x = 5$ math too.

---

## 9. Horizontal Rules

Text before rule.

---

Text after rule.

***

Another section.

---

## 10. Adjacent Code Blocks

```python
def first():
    pass
```

```python
def second():
    pass
```

No text between them.

---

## 11. Inline Code Edge Cases

### Backticks in various contexts

- Start `code` end
- Multiple `code1` and `code2` in line
- With punctuation `code`, `code`. `code`! `code`?
- Empty `` or single space ` ` 
- With special chars `$PATH` and `~/dir`

---

## 12. Math Edge Cases

### Dollar signs that are NOT math

- Cost is $5 and $10 for total $15
- Price: $100, discount: $20
- Variables like $x and $y (but these ARE math if they have operators)

### Math that SHOULD be preserved

- Equation: $x^2 + y^2 = z^2$
- Inline: $\frac{1}{2}$
- Block:

$$
\int_0^\infty e^{-x^2} dx = \frac{\sqrt{\pi}}{2}
$$

---

## 13. URLs and Links

### Various link formats

- Inline link: [Example](https://example.com)
- Reference link: [Example][ref]
- URL only: https://example.com
- Autolink: <https://example.com>
- Email: <user@example.com>

[ref]: https://example.com "Title"

### Links with code

- Link to [`documentation`](https://docs.example.com)
- Link with math [$x^2$](https://example.com)

---

## 14. Escaped Characters

### Markdown escaping

- Literal asterisks: \*not bold\*
- Literal underscore: \_not italic\_
- Literal backtick: \`not code\`
- Literal dollar: \$not math\$

---

## 15. Footnotes

This text has a footnote[^1].

This has another[^note].

[^1]: First footnote text.

[^note]: Named footnote text with `code` and $math$.

---

## 16. Task Lists

- [x] Completed task
- [ ] Incomplete task
- [x] Another completed
  - [ ] Nested incomplete
  - [x] Nested completed

---

## 17. Definition Lists

Term 1
: Definition for term 1

Term 2
: Definition for term 2
: Second definition for term 2

---

## 18. Strikethrough

This text has ~~strikethrough~~ in it.

~~Entire line struck through~~

---

## 19. Superscript and Subscript

- Superscript: x^2^ and e^10^
- Subscript: H~2~O and log~10~

---

## 20. Mixed Everything

Here's a **bold text** with `code` and $x^2$ math, followed by a [link](https://example.com) and some ~~strikethrough~~ text with emoji 🎉.

| **Header** | `Code` | $Math$ | [Link](http://example.com) |
|------------|--------|--------|----------------------------|
| **Bold**   | `cmd`  | $x^2$  | [More](http://example.com) |

1. List with **bold** and `code`
   
   ```python
   def mixed():
       return "everything"
   ```
   
   And $x = y$ math.

> Blockquote with everything: **bold**, `code`, $math$, [link](http://example.com)

---

## Test Summary

This document tests:
- ✓ Nested lists (3 levels deep)
- ✓ Complex tables (alignment, empty cells, mixed content)
- ✓ Code blocks in lists
- ✓ HTML blocks
- ✓ Unicode and special characters
- ✓ Long lines without breaks
- ✓ Blockquotes (nested)
- ✓ Horizontal rules
- ✓ Adjacent code blocks
- ✓ Inline code edge cases
- ✓ Math vs dollar signs disambiguation
- ✓ Various link formats
- ✓ Escaped characters
- ✓ Footnotes
- ✓ Task lists
- ✓ Definition lists
- ✓ Strikethrough
- ✓ Superscript/subscript
- ✓ Mixed everything

