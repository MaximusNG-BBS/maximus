"""Popup and modal-style flows."""

from __future__ import annotations

import textwrap
from typing import Iterable

from notorious_doorkit import AdvancedLightbarMenu, LightbarItem, RawInput, clear_screen, writeln
from notorious_doorkit.text import sgr_from_pc_attr

from ..models import GameState, ScoreEntry, SpecialOffer
from .common import divider
from .maxui import (
    UI_BLACK,
    UI_BLUE,
    UI_CYAN,
    UI_LGREEN,
    UI_WHITE,
    UI_YELLOW,
    ui_begin_update,
    ui_box,
    ui_end_update,
    ui_fill_rect,
    ui_gettext,
    ui_invalidate_region,
    ui_make_attr,
    ui_paint_region,
    ui_puttext,
    ui_write_padded,
)
from .prompts import pause


def _modal_choice(items: list[LightbarItem]) -> int | None:
    menu = AdvancedLightbarMenu(
        items=items,
        selected_color=sgr_from_pc_attr(ui_make_attr(UI_BLACK, UI_CYAN)),
        normal_color=sgr_from_pc_attr(ui_make_attr(UI_WHITE, UI_BLACK)),
        hotkey_color=sgr_from_pc_attr(ui_make_attr(UI_YELLOW, UI_BLACK)),
        hotkey_highlight_color=sgr_from_pc_attr(ui_make_attr(UI_YELLOW, UI_CYAN)),
        hotkey_format="[X]",
        wrap=True,
    )
    return menu.run()


def _wait_any_key() -> None:
    with RawInput() as inp:
        inp.get_key()


def show_scores(entries: Iterable[ScoreEntry]) -> None:
    block = ui_gettext("smuggle_scores", 20, 8, 59, 17)
    fill_attr = ui_make_attr(UI_WHITE, UI_BLACK)
    border_attr = ui_make_attr(UI_LGREEN, UI_BLUE)
    hint_attr = ui_make_attr(UI_YELLOW, UI_BLACK)
    rows = list(entries)

    ui_begin_update()
    ui_fill_rect(8, 20, 40, 10, " ", fill_attr)
    ui_box(8, 20, 40, 10, border_attr, "Top Smugglers")
    ui_write_padded(9, 22, 24, "Name", border_attr)
    ui_write_padded(9, 48, 10, "Net Worth", border_attr)
    for idx in range(5):
        row = 10 + idx
        if idx < len(rows):
            ui_write_padded(row, 22, 24, f"{idx + 1}. {rows[idx].name[:21]}", fill_attr)
            ui_write_padded(row, 48, 10, f"{rows[idx].value:>10}", fill_attr)
        else:
            ui_write_padded(row, 22, 36, "", fill_attr)
    ui_write_padded(15, 22, 36, "Press any key to return", hint_attr)
    ui_end_update()
    ui_paint_region(20, 8, 59, 17)
    _wait_any_key()
    ui_puttext(block, 20, 8)
    ui_invalidate_region(20, 8, 59, 17)
    ui_paint_region(20, 8, 59, 17)


def title_bestowal_notice(text: str) -> None:
    block = ui_gettext("smuggle_bestowal_notice", 18, 7, 62, 15)
    fill_attr = ui_make_attr(UI_WHITE, UI_BLACK)
    border_attr = ui_make_attr(UI_BLACK, UI_CYAN)
    hint_attr = ui_make_attr(UI_YELLOW, UI_BLACK)
    body = textwrap.wrap(text, width=41)[:4]

    ui_begin_update()
    ui_fill_rect(7, 18, 45, 9, " ", fill_attr)
    ui_box(7, 18, 45, 9, border_attr, "Word Spreads")
    for idx, line in enumerate(body):
        ui_write_padded(9 + idx, 20, 41, line, fill_attr)
    ui_write_padded(14, 20, 41, "Press any key to continue", hint_attr)
    ui_end_update()
    ui_paint_region(18, 7, 62, 15)
    _wait_any_key()
    ui_puttext(block, 18, 7)
    ui_invalidate_region(18, 7, 62, 15)
    ui_paint_region(18, 7, 62, 15)


def confirm_identity_component(component: str, value: str) -> bool:
    block = ui_gettext("smuggle_bestowal_confirm", 18, 7, 62, 15)
    fill_attr = ui_make_attr(UI_WHITE, UI_BLACK)
    border_attr = ui_make_attr(UI_BLACK, UI_CYAN)
    prompt_attr = ui_make_attr(UI_YELLOW, UI_BLACK)

    ui_begin_update()
    ui_fill_rect(7, 18, 45, 9, " ", fill_attr)
    ui_box(7, 18, 45, 9, border_attr, "Bestowal")
    ui_write_padded(9, 20, 41, f"New {component}: {value}"[:41], fill_attr)
    ui_write_padded(11, 20, 41, f"Do you wish to accept this {component}"[:41], prompt_attr)
    ui_write_padded(12, 20, 41, "and encourage its use?", prompt_attr)
    ui_end_update()
    ui_paint_region(18, 7, 62, 15)
    choice = _modal_choice(
        [
            LightbarItem("Yes", x=27, y=13, width=8, justify="left"),
            LightbarItem("No", x=39, y=13, width=8, justify="left"),
        ]
    )
    ui_puttext(block, 18, 7)
    ui_invalidate_region(18, 7, 62, 15)
    ui_paint_region(18, 7, 62, 15)
    return choice == 0


def prompt_special_offer(offer: SpecialOffer) -> bool:
    block = ui_gettext("smuggle_offer", 18, 7, 62, 15)
    fill_attr = ui_make_attr(UI_WHITE, UI_BLACK)
    border_attr = ui_make_attr(UI_BLACK, UI_CYAN)
    prompt_attr = ui_make_attr(UI_YELLOW, UI_BLACK)

    body = textwrap.wrap(f"{offer.prompt} for {offer.price} denarii.", width=41)[:3]
    ui_begin_update()
    ui_fill_rect(7, 18, 45, 9, " ", fill_attr)
    ui_box(7, 18, 45, 9, border_attr, offer.title)
    for idx, line in enumerate(body):
        ui_write_padded(9 + idx, 20, 41, line, fill_attr)
    ui_write_padded(12, 20, 41, "Take the offer?", prompt_attr)
    ui_end_update()
    ui_paint_region(18, 7, 62, 15)

    choice = _modal_choice(
        [
            LightbarItem("Yes", x=27, y=13, width=8, justify="left"),
            LightbarItem("No", x=39, y=13, width=8, justify="left"),
        ]
    )

    ui_puttext(block, 18, 7)
    ui_invalidate_region(18, 7, 62, 15)
    ui_paint_region(18, 7, 62, 15)
    return choice == 0


def show_varro_enforcement(outcome: str) -> None:
    """Display a dramatic Varro enforcement popup. Blocks until keypress."""
    block = ui_gettext("smuggle_varro", 14, 6, 66, 17)
    fill_attr = ui_make_attr(UI_WHITE, UI_BLACK)
    border_attr = ui_make_attr(UI_YELLOW, UI_BLACK)
    danger_attr = ui_make_attr(UI_WHITE, UI_BLACK)
    hint_attr = ui_make_attr(UI_YELLOW, UI_BLACK)

    if outcome == "paid":
        title = "House Varro Collects"
        lines = [
            "Three men step from the shadows.",
            "One holds your ledger. One holds a club.",
            "The third already has your coin purse.",
            "",
            "They take what you owe, break what they",
            "please, and remind you the debt stands.",
        ]
    elif outcome == "seized":
        title = "Varro's Enforcers"
        lines = [
            "They come before dawn with a cart and",
            "a list. Every crate, every bolt, every",
            "seal vanishes into House Varro's books.",
            "",
            "Your cargo covers the interest. Not",
            "the debt. Never the debt.",
        ]
    else:
        title = "Varro Closes the Ledger"
        lines = [
            "There is nothing left to take.",
            "Varro's men look at you the way",
            "butchers look at an empty hook.",
            "",
            "The debt remains, but you don't.",
            "Rome moves on without you.",
        ]

    ui_begin_update()
    ui_fill_rect(6, 14, 53, 12, " ", fill_attr)
    ui_box(6, 14, 53, 12, border_attr, title)
    for idx, line in enumerate(lines):
        attr = danger_attr
        ui_write_padded(8 + idx, 16, 49, line, attr)
    ui_write_padded(16, 16, 49, "Press any key to continue", hint_attr)
    ui_end_update()
    ui_paint_region(14, 6, 66, 17)
    _wait_any_key()
    ui_puttext(block, 14, 6)
    ui_invalidate_region(14, 6, 66, 17)
    ui_paint_region(14, 6, 66, 17)


def show_game_over(state: GameState) -> None:
    clear_screen()
    divider()
    writeln("Smuggler of Rome - Reckoning")
    divider()
    writeln()
    if state.health <= 0:
        writeln("Rome finally caught up with you.")
        writeln("The colonnades forget your name before sunrise.")
    elif state.quit_requested:
        writeln("You fold the ledger shut and step back into the night.")
        writeln("Some smugglers call that wisdom. Others call it survival with better branding.")
    elif state.days_left_on_note <= 0 and state.debt_to_varro > 0:
        writeln("Varro's men took everything. There was nothing left to bargain with.")
        writeln("The debt outlived you. That is the only epitaph House Varro writes.")
    else:
        writeln("The road goes dark for reasons of its own.")
    writeln()
    writeln(f"Final day: {state.day_number}")
    writeln(f"Purse: {state.purse}")
    writeln(f"Vault: {state.vault_balance}")
    writeln(f"Debt: {state.debt_to_varro}")
    writeln(f"Net worth: {state.net_worth_text()}")
    writeln(f"Final district: {state.current_district_name()}")
    writeln()
    pause()
