"""MEX-style UI helpers built on Doorkit's shadow screen."""

from __future__ import annotations

from dataclasses import dataclass

from notorious_doorkit.screen import Cell, ScreenBlock, ShadowScreen, get_screen, gettext, puttext, set_screen


UI_BLACK = 0
UI_BLUE = 1
UI_GREEN = 2
UI_CYAN = 3
UI_RED = 4
UI_MAGENTA = 5
UI_BROWN = 6
UI_GRAY = 7
UI_DKGRAY = 8
UI_LBLUE = 9
UI_LGREEN = 10
UI_LCYAN = 11
UI_LRED = 12
UI_LMAGENTA = 13
UI_YELLOW = 14
UI_WHITE = 15


_UPDATE_DEPTH = 0


@dataclass(frozen=True)
class UiRegion:
    left: int
    top: int
    right: int
    bottom: int


def reset_screen(*, width: int = 80, height: int = 25, attr: int | None = None) -> ShadowScreen:
    screen = ShadowScreen(width=width, height=height)
    if attr is not None:
        screen.clear(attr=attr)
    set_screen(screen)
    return screen


def ui_make_attr(fg: int, bg: int) -> int:
    return ((int(bg) & 0x0F) << 4) | (int(fg) & 0x0F)


def ui_begin_update() -> None:
    global _UPDATE_DEPTH
    _UPDATE_DEPTH += 1


def ui_end_update() -> None:
    global _UPDATE_DEPTH
    if _UPDATE_DEPTH > 0:
        _UPDATE_DEPTH -= 1


def ui_fill_rect(row: int, col: int, width: int, height: int, ch: str, attr: int) -> None:
    screen = get_screen()
    fill = " " if not ch else str(ch)[0]
    for rr in range(row, row + height):
        for cc in range(col, col + width):
            screen.set_cell(rr, cc, fill, attr)


def ui_write_padded(row: int, col: int, width: int, s: str, attr: int) -> None:
    screen = get_screen()
    text = ("" if s is None else str(s))[:width].ljust(width)
    for idx, ch in enumerate(text):
        screen.set_cell(row, col + idx, ch, attr)


def ui_box(row: int, col: int, width: int, height: int, attr: int, title: str = "") -> None:
    screen = get_screen()
    left = col
    right = col + width - 1
    top = row
    bottom = row + height - 1
    tl, tr, bl, br, hz, vt = "╔", "╗", "╚", "╝", "═", "║"

    screen.set_cell(top, left, tl, attr)
    screen.set_cell(top, right, tr, attr)
    screen.set_cell(bottom, left, bl, attr)
    screen.set_cell(bottom, right, br, attr)

    for cc in range(left + 1, right):
        screen.set_cell(top, cc, hz, attr)
        screen.set_cell(bottom, cc, hz, attr)

    for rr in range(top + 1, bottom):
        screen.set_cell(rr, left, vt, attr)
        screen.set_cell(rr, right, vt, attr)

    if title:
        title_text = f" {title} "
        max_len = max(0, width - 4)
        title_text = title_text[:max_len]
        start = left + 2
        for idx, ch in enumerate(title_text):
            if start + idx < right:
                screen.set_cell(top, start + idx, ch, attr)


def ui_paint_region(left: int, top: int, right: int, bottom: int) -> None:
    get_screen().paint_region(left, top, right, bottom)


def ui_invalidate_region(left: int, top: int, right: int, bottom: int) -> None:
    screen = get_screen()
    if not hasattr(screen, "_painted_cells"):
        return

    l = max(1, int(left))
    t = max(1, int(top))
    r = min(int(right), int(screen.width))
    b = min(int(bottom), int(screen.height))

    for rr in range(t, b + 1):
        for cc in range(l, r + 1):
            idx = (rr - 1) * int(screen.width) + (cc - 1)
            if 0 <= idx < len(screen._painted_cells):
                screen._painted_cells[idx] = Cell("\0", -1)


def ui_gettext(key: str, left: int, top: int, right: int, bottom: int) -> ScreenBlock:
    return gettext(left, top, right, bottom)


def ui_puttext(block: ScreenBlock, left: int, top: int) -> None:
    puttext(left, top, block)
