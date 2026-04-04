"""Screen rendering and intro flows."""

from __future__ import annotations

from pathlib import Path

from notorious_doorkit import clear_screen, display_file, display_file_best_match, writeln

from ..models import GameState
from .assets import intro_base_path
from .common import divider
from .maxui import reset_screen, ui_begin_update, ui_end_update, ui_paint_region
from .panels import draw_actions_hint, draw_event_log, draw_header, draw_inventory, draw_market, draw_shell, draw_status, draw_triumph
from .prompts import pause


_SCREEN_LOADED = False


def show_intro(state: GameState) -> None:
    intro_path = intro_base_path()
    intro_drawn = Path(f"{intro_path}.ans").exists()
    if intro_drawn:
        try:
            display_file_best_match(str(intro_path), clear=True)
        except RuntimeError:
            display_file(f"{intro_path}.ans", clear=True)
    else:
        clear_screen()
        divider()
        writeln("Smuggler of Rome")
        divider()
    writeln()
    if state.resumed_game:
        writeln("Your ledger opens where you left it.")
    else:
        writeln("You are a small-time broker in the shadow markets of the Maximus Imperium.")
        writeln("Move contraband between districts, work the price swings, keep House Varro")
        writeln("satisfied, and try not to end up as a cautionary tale.")
        writeln()
        writeln("Forum District is home. Your cache and House Varro both live there.")
        writeln("Travel advances the day. The note grows. The vigiles grow curious.")
    writeln()
    pause()


def render_state(state: GameState) -> None:
    global _SCREEN_LOADED
    clear_screen()
    reset_screen()
    ui_begin_update()
    draw_shell(identity=state.identity_text())
    draw_header(state)
    draw_market(state)
    draw_status(state)
    draw_actions_hint()
    draw_inventory(state)
    draw_triumph(state)
    draw_event_log(state)
    ui_end_update()
    ui_paint_region(1, 1, 79, 24)
    _SCREEN_LOADED = True


def refresh_event_only(state: GameState) -> None:
    if not _SCREEN_LOADED:
        render_state(state)
        return
    ui_begin_update()
    draw_event_log(state)
    ui_end_update()
    ui_paint_region(32, 14, 78, 24)


def refresh_status_event(state: GameState) -> None:
    if not _SCREEN_LOADED:
        render_state(state)
        return
    ui_begin_update()
    draw_status(state)
    draw_triumph(state)
    draw_event_log(state)
    ui_end_update()
    ui_paint_region(32, 3, 78, 6)
    ui_paint_region(2, 20, 29, 23)
    ui_paint_region(32, 14, 78, 24)


def refresh_status_cargo_event(state: GameState) -> None:
    if not _SCREEN_LOADED:
        render_state(state)
        return
    ui_begin_update()
    draw_status(state)
    draw_inventory(state)
    draw_triumph(state)
    draw_event_log(state)
    ui_end_update()
    ui_paint_region(32, 3, 78, 6)
    ui_paint_region(2, 11, 29, 17)
    ui_paint_region(2, 20, 29, 23)
    ui_paint_region(32, 14, 78, 24)


def refresh_day_rollover(state: GameState) -> None:
    if not _SCREEN_LOADED:
        render_state(state)
        return
    ui_begin_update()
    draw_header(state)
    draw_market(state)
    draw_status(state)
    draw_inventory(state)
    draw_triumph(state)
    draw_event_log(state)
    ui_end_update()
    ui_paint_region(1, 1, 79, 1)
    ui_paint_region(2, 3, 29, 8)
    ui_paint_region(32, 3, 78, 6)
    ui_paint_region(2, 11, 29, 17)
    ui_paint_region(2, 20, 29, 24)
    ui_paint_region(32, 14, 78, 24)
