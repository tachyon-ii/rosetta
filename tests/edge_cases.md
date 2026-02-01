# Edge Cases Test Document

## Nested and Adjacent Elements

Text with `code` and $math$ and more `code` on same line.

Inline $$\sum_{i=1}^n i$$ LaTeX block.

## Unclosed Elements

This has `unclosed code

This has $unclosed math

## Multiple Dollars

This costs $5 and $10 and $15 total.

But this is $x = 5$ real math.

## Code Blocks with Math

```python
# This $x$ is not math
price = $100  # Neither is this
```

## Math with Code-like Content

The derivative $f'(x)$ uses prime notation.

Backticks in math: $f`g$ composition.

## SVG Elements

Inline: <svg width="10" height="10"><circle cx="5" cy="5" r="3"/></svg> icon.

Block:
<svg width="50" height="50">
  <rect x="0" y="0" width="50" height="50"/>
</svg>

## Empty Lines and Whitespace

Text before


Text after multiple empty lines.

## Special Characters in Text

Use the `@` symbol for separation.

Cost is $5–$10 range.

## Fence Variations

```python
code block 1
```

~~~javascript
code block 2
~~~

```
plain code block
```

## Mixed Complexity

The algorithm runs in $O(n \log n)$ time using the `quicksort` function:

```python
def quicksort(arr):
    # Implementation with $pivot$
    return sorted(arr)
```

Where $n$ is array size and `arr` is the input.
