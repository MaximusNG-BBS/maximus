"""Common UI helpers."""

from __future__ import annotations

from notorious_doorkit import writeln

from .maxui import UI_LCYAN, UI_LGREEN, UI_LMAGENTA, UI_WHITE, UI_YELLOW, ui_box
from .layout import SCREEN_WIDTH


def divider() -> None:
    writeln("=" * SCREEN_WIDTH)


def panel_colors(name: str) -> int:
    if name == "market":
        return UI_YELLOW
    if name == "status":
        return UI_LCYAN
    if name == "actions":
        return UI_LCYAN
    if name == "cargo":
        return UI_LMAGENTA
    if name == "triumph":
        return UI_LGREEN
    return UI_WHITE


def draw_box(x: int, y: int, width: int, height: int, title: str, border_attr: int) -> None:
    ui_box(y, x, width, height, border_attr, title)
