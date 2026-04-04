#!/usr/bin/env python3
"""Generate Smuggler of Rome v2 ANSI underlay with half-block borders and Roman theme.

Layout matches gfx_load_shell() coordinates:
  Row  1       : blue header bar (79 cols)
  Rows  2- 9   : Market   box  (col 1, w=30, h=8,  yellow/gold border)
  Rows  2- 7   : Status   box  (col 31, w=49, h=6, cyan border)
  Rows  8-12   : Actions  box  (col 31, w=49, h=5, cyan border)
  Rows 10-18   : Cargo    box  (col 1, w=30, h=9,  magenta border)
  Rows 13-22   : Street Word   (col 31, w=49, h=10, white border)
  Rows 19-22   : cols 1-30 = decorative Roman filler
"""

import os

# --- CP437 character codes ---
FULL   = 0xDB  # █
UHALF  = 0xDF  # ▀  upper half
LHALF  = 0xDC  # ▄  lower half
LSIDE  = 0xDD  # ▌  left half filled
RSIDE  = 0xDE  # ▐  right half filled
SHADE1 = 0xB0  # ░
SHADE2 = 0xB1  # ▒
SHADE3 = 0xB2  # ▓
HZ_DBL = 0xCD  # ═
VT_DBL = 0xBA  # ║
TL_DBL = 0xC9  # ╔
TR_DBL = 0xBB  # ╗
BL_DBL = 0xC8  # ╚
BR_DBL = 0xBC  # ╝
DIAMOND = 0x04 # ♦
DOT_MID = 0xFA # ·

ROWS = 23
COLS = 79

ESC = b'\x1b'


class Cell:
    __slots__ = ('ch', 'fg', 'bg', 'bold')

    def __init__(self, ch=0x20, fg=7, bg=0, bold=False):
        self.ch = ch
        self.fg = fg
        self.bg = bg
        self.bold = bold


def make_grid():
    return [[Cell() for _ in range(COLS)] for _ in range(ROWS)]


def set_cell(grid, row, col, ch, fg, bg, bold=False):
    """Set a cell (1-based row/col)."""
    r, c = row - 1, col - 1
    if 0 <= r < ROWS and 0 <= c < COLS:
        cell = grid[r][c]
        cell.ch = ch
        cell.fg = fg
        cell.bg = bg
        cell.bold = bold


def fill_rect(grid, row, col, w, h, ch, fg, bg, bold=False):
    for dr in range(h):
        for dc in range(w):
            set_cell(grid, row + dr, col + dc, ch, fg, bg, bold)


def write_text(grid, row, col, text, fg, bg, bold=False):
    for i, ch in enumerate(text):
        if isinstance(ch, int):
            set_cell(grid, row, col + i, ch, fg, bg, bold)
        else:
            set_cell(grid, row, col + i, ord(ch), fg, bg, bold)


def draw_halfblock_box(grid, row, col, w, h,
                       border_fg, border_bold,
                       title=None, title_fg=None, title_bg=None, title_bold=True):
    """Draw a panel with half-block borders.

    ▄ top / ▀ bottom / ▐ left / ▌ right.
    Title chars are written as regular text on the top border row.
    """
    bfg = border_fg
    bb  = border_bold

    # Interior: black bg spaces
    fill_rect(grid, row + 1, col + 1, w - 2, h - 2, 0x20, 7, 0)

    # Top edge: ▄ (lower half = border colour, upper half = black bg)
    for c in range(w):
        set_cell(grid, row, col + c, LHALF, bfg, 0, bb)

    # Bottom edge: ▀ (upper half = border colour, lower half = black bg)
    for c in range(w):
        set_cell(grid, row + h - 1, col + c, UHALF, bfg, 0, bb)

    # Left edge: ▐ (right half = border)
    for r in range(1, h - 1):
        set_cell(grid, row + r, col, RSIDE, bfg, 0, bb)

    # Right edge: ▌ (left half = border)
    for r in range(1, h - 1):
        set_cell(grid, row + r, col + w - 1, LSIDE, bfg, 0, bb)

    # Title plate on top-edge row
    if title:
        tfg = title_fg if title_fg is not None else 7
        tbg = title_bg if title_bg is not None else 0
        tbd = title_bold
        start = col + 2
        for i, ch in enumerate(title):
            set_cell(grid, row, start + i, ord(ch), tfg, tbg, tbd)


def draw_header(grid):
    """Row 1: gradient header bar in blue with gold title and decorative accents."""
    # Base: white on blue
    fill_rect(grid, 1, 1, COLS, 1, 0x20, 7, 4)

    # Left gradient: black→blue using shading
    set_cell(grid, 1, 1, SHADE1, 4, 0, False)
    set_cell(grid, 1, 2, SHADE2, 4, 0, False)
    set_cell(grid, 1, 3, SHADE3, 4, 0, True)
    set_cell(grid, 1, 4, FULL,   4, 0, True)

    # Right gradient: blue→black
    set_cell(grid, 1, 76, FULL,   4, 0, True)
    set_cell(grid, 1, 77, SHADE3, 4, 0, True)
    set_cell(grid, 1, 78, SHADE2, 4, 0, False)
    set_cell(grid, 1, 79, SHADE1, 4, 0, False)

    # Gold decorative ═ flanking the title
    set_cell(grid, 1, 6,  HZ_DBL, 3, 4, True)
    set_cell(grid, 1, 7,  HZ_DBL, 3, 4, True)
    set_cell(grid, 1, 8,  0x20,   3, 4, True)

    write_text(grid, 1, 9, "SMUGGLER OF ROME", 3, 4, True)

    set_cell(grid, 1, 25, 0x20,   3, 4, True)
    set_cell(grid, 1, 26, HZ_DBL, 3, 4, True)
    set_cell(grid, 1, 27, HZ_DBL, 3, 4, True)


def draw_roman_decor(grid):
    """Decorative Roman motif in the empty zone (rows 19-22, cols 1-30)."""
    # Double-line ornamental frame
    set_cell(grid, 19, 5,  TL_DBL, 1, 0, False)
    set_cell(grid, 19, 26, TR_DBL, 1, 0, False)
    set_cell(grid, 22, 5,  BL_DBL, 1, 0, False)
    set_cell(grid, 22, 26, BR_DBL, 1, 0, False)

    for c in range(6, 26):
        set_cell(grid, 19, c, HZ_DBL, 1, 0, False)
        set_cell(grid, 22, c, HZ_DBL, 1, 0, False)

    for r in (20, 21):
        set_cell(grid, r, 5,  VT_DBL, 1, 0, False)
        set_cell(grid, r, 26, VT_DBL, 1, 0, False)

    # "S · P · Q · R" centred
    motto = [ord('S'), 0x20, DOT_MID, 0x20,
             ord('P'), 0x20, DOT_MID, 0x20,
             ord('Q'), 0x20, DOT_MID, 0x20,
             ord('R')]
    start_col = 9
    for i, ch in enumerate(motto):
        set_cell(grid, 20, start_col + i, ch, 1, 0, False)

    # Shading accents on frame corners
    for cr in [(19, 4), (19, 27), (22, 4), (22, 27)]:
        set_cell(grid, cr[0], cr[1], SHADE1, 1, 0, False)

    # Column pillars flanking the motto
    set_cell(grid, 20, 7, SHADE3, 3, 0, False)
    set_cell(grid, 21, 7, SHADE2, 3, 0, False)
    set_cell(grid, 20, 24, SHADE3, 3, 0, False)
    set_cell(grid, 21, 24, SHADE2, 3, 0, False)

    # Laurel leaf hints — green diamonds
    set_cell(grid, 21, 10, DIAMOND, 2, 0, False)
    set_cell(grid, 21, 21, DIAMOND, 2, 0, False)

    # Faint laurel vine between diamonds
    for c in range(11, 21):
        set_cell(grid, 21, c, HZ_DBL, 2, 0, False)

    # Subtle ░ row at the very bottom
    for c in range(4, 28):
        set_cell(grid, 23, c, SHADE1, 0, 0, True)


def draw_junction_accents(grid):
    """Tweak cells where panels share edges for visual polish."""
    # Status↔Actions junction (row 7 bottom / row 8 top) — both cyan
    # Re-stamp to ensure clean merge (draw_halfblock_box already set these,
    # but the Actions title plate may have overwritten some top-edge cells)
    # Already handled by individual box draws — just ensure corner continuity.

    # Actions↔Street Word (row 12 / row 13) — cyan ▀ above, white ▄ below
    # The two ▀/▄ half-blocks create a nice bi-colour split line automatically.

    # Market bottom (row 9) / Cargo top (row 10) — yellow ▀ / magenta ▄
    # Also automatic from the box draws.  Just ensure the shared left/right
    # edges look clean:
    pass


def render_ansi(grid):
    """Render the cell grid to raw ANSI bytes (CP437 + escape codes)."""
    buf = []
    buf.append(ESC + b'[2J')
    buf.append(ESC + b'[H')

    last_fg = -1
    last_bg = -1
    last_bold = None

    for r in range(ROWS):
        if r > 0:
            buf.append(b'\r\n')

        for c in range(COLS):
            cell = grid[r][c]

            if cell.fg != last_fg or cell.bg != last_bg or cell.bold != last_bold:
                parts = []
                if cell.bold:
                    parts.append(b'1')
                else:
                    parts.append(b'0')
                parts.append(str(30 + cell.fg).encode())
                parts.append(str(40 + cell.bg).encode())
                buf.append(ESC + b'[' + b';'.join(parts) + b'm')
                last_fg = cell.fg
                last_bg = cell.bg
                last_bold = cell.bold

            buf.append(bytes([cell.ch]))

    buf.append(ESC + b'[0m')
    return b''.join(buf)


def main():
    grid = make_grid()

    # Black background
    fill_rect(grid, 1, 1, COLS, ROWS, 0x20, 7, 0)

    # Header
    draw_header(grid)

    # Five game panels
    draw_halfblock_box(grid, 2, 1, 30, 8,
                       border_fg=3, border_bold=True,
                       title=" Market ", title_fg=3, title_bg=0, title_bold=True)

    draw_halfblock_box(grid, 2, 31, 49, 6,
                       border_fg=6, border_bold=True,
                       title=" Status ", title_fg=6, title_bg=0, title_bold=True)

    draw_halfblock_box(grid, 8, 31, 49, 5,
                       border_fg=6, border_bold=False,
                       title=" Actions ", title_fg=0, title_bg=6, title_bold=False)

    draw_halfblock_box(grid, 10, 1, 30, 9,
                       border_fg=5, border_bold=True,
                       title=" Cargo ", title_fg=5, title_bg=0, title_bold=True)

    draw_halfblock_box(grid, 13, 31, 49, 10,
                       border_fg=7, border_bold=True,
                       title=" Street Word ", title_fg=7, title_bg=0, title_bold=True)

    # Junction polish
    draw_junction_accents(grid)

    # Roman decoration
    draw_roman_decor(grid)

    # --- Write to all three locations ---
    out = render_ansi(grid)

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    targets = [
        os.path.join(root, 'resources', 'scripts', 'smuggler', 'underlay.ans'),
        os.path.join(root, 'resources', 'install_tree', 'scripts', 'smuggler', 'underlay.ans'),
        os.path.join(root, 'build', 'scripts', 'smuggler', 'underlay.ans'),
    ]

    for p in targets:
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, 'wb') as f:
            f.write(out)
        print(f"Wrote {len(out)} bytes -> {p}")


if __name__ == '__main__':
    main()
