# Fix: Local Console Cursor Position Tracking

## Problem

When running `max` in local console mode (`-c -k`), the name input field during login is positioned one line too high, and after entering a name, subsequent text overlaps the banner logo at the top of the screen.

**Remote works fine. Local-after-login works fine. Only the initial login screen in local mode is broken.**

## Root Cause

In `Mdm_putc()` (`src/max/core/max_outr.c:238-262`), when `usr.video == GRAPH_ANSI`, raw ANSI ESC sequences are passed through to the modem/comm layer and **return early** before reaching the cursor-tracking code that updates `current_line`/`current_col`/`display_line`/`display_col`.

When the logo `.ans` file is displayed via `Display_File()` → `Banner()`, all ANSI cursor movement sequences (ESC[H, ESC[row;colH, etc.) pass through `Mdm_putc` without updating the global position variables. After the logo finishes, `current_line`/`current_col` are stale (likely still 1,1 from the CLS).

- **Remote**: Terminal handles cursor positioning itself; Maximus's internal tracking is wrong but the remote terminal compensates because all positioning is relative.
- **Local**: `ui_prompt_field()` reads `current_line`/`current_col` (at `ui_field.c:885-886`) and uses `Goto()` for absolute positioning. Stale values = wrong position.

## Fix Location

`src/max/core/max_outr.c`, inside `Mdm_putc()`, the ANSI passthrough block at lines ~238-262.

## Fix Approach

Add a small CSI parameter buffer. When in `ansi_state==2` (collecting CSI), buffer parameter bytes. When the final byte arrives, parse the sequence and update `current_line`/`current_col`/`display_line`/`display_col` for cursor-affecting commands before returning.

### CSI sequences to handle

| Final Byte | Sequence | Tracking Update |
|------------|----------|----------------|
| `H` or `f` | ESC[row;colH — Cursor Position | `current_line=row; current_col=col; display_line=row; display_col=col;` (default 1,1) |
| `A` | ESC[nA — Cursor Up | `current_line -= n; display_line -= n;` (default n=1, clamp ≥1) |
| `B` | ESC[nB — Cursor Down | `current_line += n; display_line += n;` (default n=1, clamp ≤TermLength) |
| `C` | ESC[nC — Cursor Forward | `current_col += n; display_col += n;` (default n=1) |
| `D` | ESC[nD — Cursor Back | `current_col -= n; display_col -= n;` (default n=1, clamp ≥1) |
| `J` | ESC[2J — Erase Display | If param==2: `current_line=current_col=display_line=display_col=1;` |
| `G` | ESC[nG — Cursor Horizontal Absolute | `current_col=n; display_col=n;` (default n=1) |
| `d` | ESC[nd — Cursor Vertical Absolute | `current_line=n; display_line=n;` (default n=1) |
| `K` | ESC[nK — Erase in Line | No cursor change |

### Implementation Details

1. Add static locals inside `Mdm_putc`:
   - `static char ansi_csi_buf[16]` — parameter buffer
   - `static int ansi_csi_len` — current length

2. In `ansi_state==2`:
   - If byte is a parameter byte (0x30-0x3F) or intermediate (0x20-0x2F), buffer it
   - If byte is a final byte (0x40-0x7E), parse params and update tracking, then reset

3. Helper: parse semicolon-separated decimal params from `ansi_csi_buf`

4. Apply tracking updates based on the final byte per the table above

5. Keep the existing `CMDM_PPUTcw()` calls and `return` for remote output — we just add tracking before the return.

### Clamping

- `current_line`: clamp to [1, TermLength()]
- `current_col`: clamp to [1, TermWidth()]
- `display_line`/`display_col`: mirror `current_line`/`current_col`

## Files Changed

- `src/max/core/max_outr.c` — modify the ANSI passthrough block in `Mdm_putc()`

## Testing

1. `make build && make install`
2. Run `MAX_INSTALL_PATH=/home/limpingninja/maximus/build build/bin/max -c -k`
3. Verify: logo displays, name prompt appears on correct line
4. Type an invalid name → verify "not found" text doesn't overlap logo
5. Complete login → verify everything renders correctly
