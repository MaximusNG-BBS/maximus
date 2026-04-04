"""Prompt helpers."""

from __future__ import annotations

from notorious_doorkit.forms import InputField
from notorious_doorkit.input import EDIT_FLAG_ALLOW_CANCEL, EDIT_RETURN_ACCEPT, edit_str

from .maxui import UI_BLACK, UI_CYAN, UI_WHITE, UI_YELLOW, ui_begin_update, ui_end_update, ui_gettext, ui_invalidate_region, ui_make_attr, ui_paint_region, ui_puttext, ui_write_padded
from .panels import clear_action_area


def pause(prompt: str = "Press ENTER to continue...") -> None:
    field = InputField(prompt=prompt, max_length=1, default="")
    field.get_input()


def prompt_number(prompt: str, max_length: int = 8) -> int:
    block = ui_gettext("smuggle_num", 32, 9, 78, 11)

    ui_begin_update()
    clear_action_area()
    ui_write_padded(9, 33, 45, "Enter amount", ui_make_attr(UI_YELLOW, UI_BLACK))
    ui_write_padded(10, 33, 34, prompt[:34], ui_make_attr(UI_WHITE, UI_BLACK))
    ui_end_update()
    ui_paint_region(32, 9, 78, 11)

    code, value = edit_str(
        "",
        "X" * max_length,
        10,
        79 - max_length,
        ui_make_attr(UI_WHITE, UI_BLACK),
        ui_make_attr(UI_BLACK, UI_CYAN),
        " ",
        flags=EDIT_FLAG_ALLOW_CANCEL,
    )

    ui_puttext(block, 32, 9)
    ui_invalidate_region(32, 9, 78, 11)
    ui_paint_region(32, 9, 78, 11)

    if code != EDIT_RETURN_ACCEPT:
        return 0

    value = value.strip()
    if not value:
        return 0

    try:
        return int(value)
    except ValueError:
        return 0
