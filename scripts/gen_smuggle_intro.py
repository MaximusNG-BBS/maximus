#!/usr/bin/env python3
"""Generate a Smuggler of Rome intro ANSI with Roman skyline and title art."""

import os

# CP437 characters
FULL = 0xDB
UHALF = 0xDF
LHALF = 0xDC
LSIDE = 0xDD
RSIDE = 0xDE
SHADE1 = 0xB0
SHADE2 = 0xB1
SHADE3 = 0xB2
HZ_DBL = 0xCD
VT_DBL = 0xBA
TL_DBL = 0xC9
TR_DBL = 0xBB
BL_DBL = 0xC8
BR_DBL = 0xBC
DOT_MID = 0xFA
DIAMOND = 0x04

ROWS = 24
COLS = 79
ESC = b"\x1b"


class Cell:
    __slots__ = ("ch", "fg", "bg", "bold")

    def __init__(self, ch=0x20, fg=7, bg=0, bold=False):
        self.ch = ch
        self.fg = fg
        self.bg = bg
        self.bold = bold


def make_grid():
    return [[Cell() for _ in range(COLS)] for _ in range(ROWS)]


def set_cell(grid, row, col, ch, fg, bg, bold=False):
    r = row - 1
    c = col - 1
    if 0 <= r < ROWS and 0 <= c < COLS:
        cell = grid[r][c]
        cell.ch = ch
        cell.fg = fg
        cell.bg = bg
        cell.bold = bold


def fill_rect(grid, row, col, width, height, ch, fg, bg, bold=False):
    for dr in range(height):
        for dc in range(width):
            set_cell(grid, row + dr, col + dc, ch, fg, bg, bold)


def write_text(grid, row, col, text, fg, bg, bold=False):
    for i, ch in enumerate(text):
        if isinstance(ch, int):
            set_cell(grid, row, col + i, ch, fg, bg, bold)
        else:
            set_cell(grid, row, col + i, ord(ch), fg, bg, bold)


def write_shadow_text(grid, row, col, text, fg, bg, shadow_fg, shadow_bg, bold=False):
    write_text(grid, row + 1, col + 1, text, shadow_fg, shadow_bg, False)
    write_text(grid, row, col, text, fg, bg, bold)


def draw_stars(grid):
    stars = [
        (2, 6, ord("."), 7, 0, False),
        (2, 18, DOT_MID, 3, 0, True),
        (2, 34, ord("."), 6, 0, False),
        (2, 58, DOT_MID, 7, 0, True),
        (3, 10, DOT_MID, 6, 0, False),
        (3, 27, ord("."), 7, 0, False),
        (3, 50, DOT_MID, 3, 0, True),
        (3, 70, ord("."), 7, 0, False),
        (4, 15, ord("."), 6, 0, False),
        (4, 43, DOT_MID, 7, 0, True),
        (4, 64, ord("."), 3, 0, False),
    ]
    for row, col, ch, fg, bg, bold in stars:
        set_cell(grid, row, col, ch, fg, bg, bold)


def draw_moon(grid):
    moon = [
        (2, 68, SHADE1, 3, 0, False),
        (2, 69, SHADE2, 3, 0, True),
        (2, 70, SHADE1, 3, 0, False),
        (3, 67, SHADE1, 3, 0, False),
        (3, 68, FULL, 3, 0, True),
        (3, 69, FULL, 3, 0, True),
        (3, 70, SHADE3, 3, 0, True),
        (4, 68, SHADE2, 3, 0, True),
        (4, 69, FULL, 3, 0, True),
        (4, 70, SHADE1, 3, 0, False),
    ]
    for row, col, ch, fg, bg, bold in moon:
        set_cell(grid, row, col, ch, fg, bg, bold)


def draw_banner(grid):
    fill_rect(grid, 5, 11, 58, 5, 0x20, 7, 1, False)

    for c in range(13, 67):
        set_cell(grid, 5, c, HZ_DBL, 3, 1, True)
        set_cell(grid, 9, c, HZ_DBL, 3, 1, True)

    set_cell(grid, 5, 11, TL_DBL, 3, 1, True)
    set_cell(grid, 5, 68, TR_DBL, 3, 1, True)
    set_cell(grid, 9, 11, BL_DBL, 3, 1, True)
    set_cell(grid, 9, 68, BR_DBL, 3, 1, True)

    for r in range(6, 9):
        set_cell(grid, r, 11, VT_DBL, 3, 1, True)
        set_cell(grid, r, 68, VT_DBL, 3, 1, True)

    write_text(grid, 6, 24, "SMUGGLER", 3, 1, True)
    write_text(grid, 7, 30, "OF ROME", 7, 1, True)
    write_text(grid, 8, 24, "MAXIMUS IMPERIUM  " + chr(DOT_MID) + "  SHADOW TRADE", 6, 1, False)

    write_text(grid, 5, 14, [DIAMOND, 0x20, DIAMOND], 2, 1, False)
    write_text(grid, 5, 61, [DIAMOND, 0x20, DIAMOND], 2, 1, False)


def draw_forum(grid):
    # Distant skyline
    fill_rect(grid, 11, 1, COLS, 2, 0x20, 7, 0, False)
    for c in range(1, COLS + 1):
        if c % 2 == 0:
            set_cell(grid, 12, c, SHADE1, 1, 0, False)

    # Temple roof
    roof_left = 22
    roof_right = 58
    for c in range(roof_left + 1, roof_right):
        set_cell(grid, 13, c, HZ_DBL, 7, 0, False)
    set_cell(grid, 13, roof_left, ord("/"), 7, 0, True)
    set_cell(grid, 13, roof_right, ord("\\"), 7, 0, True)

    for offset in range(0, 8):
        set_cell(grid, 12 - (offset // 2), 40 - offset, ord("/"), 8, 0, False)
        set_cell(grid, 12 - (offset // 2), 40 + offset, ord("\\"), 8, 0, False)

    fill_rect(grid, 14, 23, 34, 1, FULL, 7, 0, False)

    # Columns
    for base in (25, 30, 35, 40, 45, 50, 55):
        for row in range(15, 20):
            set_cell(grid, row, base, FULL, 7, 0, True)
            set_cell(grid, row, base + 1, FULL, 8, 0, False)

    fill_rect(grid, 20, 21, 38, 1, FULL, 8, 0, False)
    fill_rect(grid, 21, 18, 44, 1, SHADE3, 8, 0, False)
    fill_rect(grid, 22, 15, 50, 1, SHADE2, 8, 0, False)

    # Side colonnades / market ruins
    for row in range(15, 22):
        set_cell(grid, row, 7, SHADE3 if row < 20 else SHADE2, 8, 0, False)
        set_cell(grid, row, 8, SHADE2, 8, 0, False)
        set_cell(grid, row, 72, SHADE2, 8, 0, False)
        set_cell(grid, row, 73, SHADE3 if row < 20 else SHADE2, 8, 0, False)

    write_text(grid, 16, 5, "merchant fires", 6, 0, False)
    write_text(grid, 16, 65, "late litters", 5, 0, False)

    # Foreground street
    fill_rect(grid, 23, 1, COLS, 1, SHADE2, 0, 0, True)
    fill_rect(grid, 24, 1, COLS, 1, SHADE1, 0, 0, True)


def draw_laurals(grid):
    for col in range(8, 16):
        set_cell(grid, 8 + ((col + 1) % 2), col, DIAMOND, 2, 0, False)
    for col in range(64, 72):
        set_cell(grid, 8 + (col % 2), col, DIAMOND, 2, 0, False)


def draw_footer(grid):
    write_text(grid, 23, 23, "Trade contraband. Outrun the watch. Rise through Rome.", 7, 0, False)
    write_text(grid, 24, 27, "Press any key to enter the market", 3, 0, True)


def render_ansi(grid):
    buf = []
    buf.append(ESC + b"[2J")
    buf.append(ESC + b"[H")

    last_fg = -1
    last_bg = -1
    last_bold = None

    for r in range(ROWS):
        if r > 0:
            buf.append(b"\r\n")

        for c in range(COLS):
            cell = grid[r][c]
            if cell.fg != last_fg or cell.bg != last_bg or cell.bold != last_bold:
                parts = [b"1" if cell.bold else b"0",
                         str(30 + cell.fg).encode(),
                         str(40 + cell.bg).encode()]
                buf.append(ESC + b"[" + b";".join(parts) + b"m")
                last_fg = cell.fg
                last_bg = cell.bg
                last_bold = cell.bold
            buf.append(bytes([cell.ch]))

    buf.append(ESC + b"[0m")
    return b"".join(buf)


def main():
    grid = make_grid()
    fill_rect(grid, 1, 1, COLS, ROWS, 0x20, 7, 0, False)
    fill_rect(grid, 1, 1, COLS, 10, 0x20, 7, 4, False)
    fill_rect(grid, 11, 1, COLS, 14, 0x20, 7, 0, False)

    draw_stars(grid)
    draw_moon(grid)
    draw_banner(grid)
    draw_laurals(grid)
    draw_forum(grid)
    draw_footer(grid)

    out = render_ansi(grid)

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    targets = [
        os.path.join(root, "resources", "scripts", "smuggler", "intro.ans"),
        os.path.join(root, "resources", "install_tree", "scripts", "smuggler", "intro.ans"),
        os.path.join(root, "build", "scripts", "smuggler", "intro.ans"),
    ]

    for path in targets:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as handle:
            handle.write(out)
        print(f"Wrote {len(out)} bytes -> {path}")


if __name__ == "__main__":
    main()
