# AVATAR-Aware String Width Calculation

## Problem Statement

No existing function in Maximus correctly computes the visible display width of a string that contains AVATAR RLE sequences (`\x19<char><count>`). This prevents using CP437 glyphs like ↑ (`0x18`) and ↓ (`0x19`) in language strings where width calculations are needed (e.g., dynamic padding via `$D|!1\xC4`).

## Current Functions and Their Limitations

### 1. `stravtlen()` — [`src/max/core/max_misc.c:770`](src/max/core/max_misc.c:770)

- Only handles 3-byte `\x16\x01<attr>` AVATAR attribute sequences
- Does **NOT** handle `\x19` RLE, ANSI ESC, pipe colors, or MCI codes
- Assumes all `\x16` sequences are exactly 3 bytes (wrong for goto, clear area, etc.)
- Legacy function, still called from `max_fbbs.c` and `ui_field.c`

### 2. `qpop_visible_len()` — [`src/max/msg/med_qpop.c:87`](src/max/msg/med_qpop.c:87)

- Handles MCI pipe codes and theme codes via `MciExpand()` + `MciStrip()`
- Does **NOT** handle AVATAR `\x16` or `\x19` sequences
- Static/private to quote popup

### 3. `Strip_Ansi()` — [`src/max/core/max_misc.c:411`](src/max/core/max_misc.c:411)

- Only replaces ESC bytes with `<` — not a width function
- Does not strip AVATAR

### 4. `ui_shadowbuf_normalize_line()` — [`src/max/display/ui_shadowbuf.c:344`](src/max/display/ui_shadowbuf.c:344)

- Best existing candidate — handles `\x16\x01<attr>`, ANSI SGR, pipe colors, MCI themes
- Output cell count **IS** the visible width
- Does **NOT** handle `\x19` RLE — would count all 3 bytes as visible characters
- Does **NOT** handle multi-byte AVATAR commands beyond `\x16\x01` (goto is 4 bytes, clear area is 5+)
- Allocates memory (caller must free cells)

### 5. `MciStrip()` — [`src/max/display/mci.c:748`](src/max/display/mci.c:748)

- Only strips pipe-style MCI codes (`|##`, `|xx`, `$D`, `|[...`)
- Does not understand AVATAR byte sequences at all

## AVATAR Control Byte Summary

| Byte | Command | Total Length | Currently Handled |
|------|---------|-------------|-------------------|
| `\x16\x01<attr>` | Set attribute | 3 bytes | ✅ `stravtlen`, `normalize_line` |
| `\x16\x02` | Blink on | 2 bytes | ❌ |
| `\x16\x03`–`\x06` | Cursor movement | 2 bytes each | ❌ |
| `\x16\x07` | Clear to EOL | 2 bytes | ❌ |
| `\x16\x08<row><col>` | Goto position | 4 bytes | ❌ |
| `\x16\x0C<attr><lines><cols>` | Clear area | 5 bytes | ❌ |
| `\x16\x0D<attr><char><lines><cols>` | Fill area | 6 bytes | ❌ |
| `\x16\x0F` | Clear to EOS | 2 bytes | ❌ |
| `\x16\x19<len><pattern><count>` | Pattern repeat | 4+ bytes | ❌ |
| `\x19<char><count>` | Simple RLE | 3 bytes, displays `count` chars | ❌ |

## Proposed Solution

**Add `\x19` RLE handling to `ui_shadowbuf_normalize_line()`** as the primary fix, since this function is already the most comprehensive and is used by the shadow buffer / scrolling region system.

When `normalize_line()` encounters `\x19`:

1. Read the next byte as `rle_char`
2. Read the byte after as `rle_count`
3. Emit `rle_count` cells of `(rle_char, current_attr)` into the output
4. Advance the input pointer by 3

Additionally, handle multi-byte AVATAR commands for completeness:

- `\x16\x02` through `\x16\x07`: skip the 2-byte command (no visible output)
- `\x16\x08<row><col>`: skip 4 bytes
- `\x16\x0C<attr><lines><cols>`: skip 5 bytes
- `\x16\x0D<attr><char><lines><cols>`: skip 6 bytes
- `\x16\x0F`: skip 2 bytes
- `\x16\x19<len><pattern><count>`: skip `len + 4` bytes, emit `count * len` cells

## Convenience Wrapper

Create a new utility function accessible system-wide:

```c
/**
 * @brief Compute the visible display width of a string containing
 *        any combination of AVATAR, ANSI, pipe, and MCI sequences.
 *
 * @param text  Input string (may contain \x16, \x19, ESC[, |xx, etc.)
 * @return      Visible column width.
 */
int visible_width(const char *text);
```

Implementation: calls `ui_shadowbuf_normalize_line()`, extracts `out_count`, frees the cells, returns the count. Declare in [`ui_shadowbuf.h`](src/max/display/ui_shadowbuf.h).

## Impact

Once `ui_shadowbuf_normalize_line()` handles `\x19` RLE:

- `qpop_visible_len()` in the quote popup can be replaced with `visible_width()` or can use normalize_line directly
- Language strings can safely use `\x19\x19\x01` (↓ via RLE) and `\x18` (↑) with correct width calculation
- The scrolling region and shadow buffer will correctly render RLE sequences in any content
- `stravtlen()` callers could eventually migrate to the new function

## Implementation Steps

1. Add `\x19` RLE handling to [`ui_shadowbuf_normalize_line()`](src/max/display/ui_shadowbuf.c:344) in [`ui_shadowbuf.c`](src/max/display/ui_shadowbuf.c)
2. Add remaining multi-byte AVATAR command handling (skip non-visible commands)
3. Add [`int visible_width(const char *text)`](src/max/display/ui_shadowbuf.c) wrapper to [`ui_shadowbuf.c`](src/max/display/ui_shadowbuf.c) / [`ui_shadowbuf.h`](src/max/display/ui_shadowbuf.h)
4. Update [`qpop_visible_len()`](src/max/msg/med_qpop.c:87) to use `visible_width()` (or inline the normalize_line call)
5. Update quote window lang strings to use `\x18` and `\x19\x19\x01` for arrow glyphs
6. Build and test
7. Optionally: migrate [`stravtlen()`](src/max/core/max_misc.c:770) callers to `visible_width()`

## Files to Modify

- [`src/max/display/ui_shadowbuf.c`](src/max/display/ui_shadowbuf.c) — add RLE and multi-byte AVATAR handling
- [`src/max/display/ui_shadowbuf.h`](src/max/display/ui_shadowbuf.h) — add `visible_width()` declaration
- [`src/max/msg/med_qpop.c`](src/max/msg/med_qpop.c) — update `qpop_visible_len()` to use new function
- Language TOML files — update arrow glyphs once width calculation is fixed
