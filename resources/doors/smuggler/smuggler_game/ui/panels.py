"""Panel-oriented render helpers for Smuggler dashboard parity."""

from __future__ import annotations

from ..data import DISTRICTS, GOODS
from ..models import GameState
from ..systems import next_unlock_text, triumph_rank_text, triumph_status_text
from .common import draw_box, panel_colors
from .layout import ACTION_CONTENT_LEFT, ACTION_CONTENT_TOP, ACTION_CONTENT_WIDTH, ACTIONS_BOX, CARGO_BOX, EVENT_BOX, MARKET_BOX, STATUS_BOX, TRIUMPH_BOX
from .maxui import (
    UI_BLACK,
    UI_BLUE,
    UI_CYAN,
    UI_DKGRAY,
    UI_GRAY,
    UI_LCYAN,
    UI_LGREEN,
    UI_MAGENTA,
    UI_LRED,
    UI_WHITE,
    UI_YELLOW,
    ui_fill_rect,
    ui_make_attr,
    ui_write_padded,
)


def _clip(text: str, width: int) -> str:
    return text[:width].ljust(width)


def _money_line(label: str, value: str, width: int = 21) -> str:
    return _clip(f"{label:<10}{value:>10}", width)


def draw_shell(submenu_title: str | None = None, identity: str = "") -> None:
    fill_attr = ui_make_attr(UI_WHITE, UI_BLACK)
    ui_fill_rect(1, 1, 79, 24, " ", fill_attr)
    ui_fill_rect(1, 1, 79, 1, " ", ui_make_attr(UI_WHITE, UI_BLUE))
    draw_box(*MARKET_BOX, title="Market", border_attr=ui_make_attr(panel_colors("market"), UI_BLACK))
    # Status box title shows the player's full Roman identity when available.
    status_title = identity if identity else "Status"
    # Clip to fit within the box border (width - 4 for corners and padding).
    max_title = STATUS_BOX[2] - 4
    if len(status_title) > max_title:
        status_title = status_title[:max_title]
    draw_box(*STATUS_BOX, title=status_title, border_attr=ui_make_attr(panel_colors("status"), UI_BLACK))
    actions_title = "Actions"
    if submenu_title:
        actions_title = f"Actions ({submenu_title})"
    draw_box(*ACTIONS_BOX, title=actions_title, border_attr=ui_make_attr(UI_CYAN, UI_BLACK))
    draw_box(*CARGO_BOX, title="Cargo", border_attr=ui_make_attr(panel_colors("cargo"), UI_BLACK))
    draw_box(*TRIUMPH_BOX, title="Triumph", border_attr=ui_make_attr(panel_colors("triumph"), UI_BLACK))
    draw_box(*EVENT_BOX, title="Street Word", border_attr=ui_make_attr(UI_WHITE, UI_BLACK))


def draw_action_header(submenu: bool = False) -> None:
    title = "Actions"
    if submenu:
        title = "Actions (ESC: return to previous menu)"
    draw_box(*ACTIONS_BOX, title=title, border_attr=ui_make_attr(UI_CYAN, UI_BLACK))


def clear_action_area() -> None:
    ui_fill_rect(9, 32, 47, 3, " ", ui_make_attr(UI_WHITE, UI_BLACK))


def draw_header(state: GameState) -> None:
    bar_attr = ui_make_attr(UI_WHITE, UI_BLUE)
    title_attr = ui_make_attr(UI_YELLOW, UI_BLUE)
    note_attr = ui_make_attr(UI_LCYAN, UI_BLUE)
    ui_fill_rect(1, 1, 79, 1, " ", bar_attr)
    ui_write_padded(1, 3, 20, "Smuggler of Rome", title_attr)
    ui_write_padded(1, 24, 28, f"Day {state.day_number}  {state.current_district_name()}", bar_attr)
    ui_write_padded(1, 54, 25, f"Note due in {state.days_left_on_note} days", note_attr)


def draw_market(state: GameState) -> None:
    ui_fill_rect(3, 2, 28, 6, " ", ui_make_attr(UI_WHITE, UI_BLACK))
    for idx, good in enumerate(GOODS, start=0):
        row = 3 + idx
        ui_write_padded(row, 3, 18, _clip(f"{idx + 1}. {good.name}", 18), ui_make_attr(UI_WHITE, UI_BLACK))
        price = state.prices[good.key]
        attr = ui_make_attr(UI_WHITE, UI_BLACK)
        if price <= good.price_min + (good.price_span // 3):
            attr = ui_make_attr(UI_LGREEN, UI_BLACK)
        elif price >= good.price_min + ((good.price_span * 2) // 3):
            attr = ui_make_attr(UI_YELLOW, UI_BLACK)
        ui_write_padded(row, 22, 7, f"{price:>7}", attr)


def draw_status(state: GameState) -> None:
    left_attr = ui_make_attr(UI_WHITE, UI_BLACK)
    right_attr = ui_make_attr(UI_LCYAN, UI_BLACK)
    debt_attr = ui_make_attr(UI_LRED, UI_BLACK)
    worth_attr = ui_make_attr(UI_YELLOW, UI_BLACK)
    ui_fill_rect(3, 32, 47, 4, " ", left_attr)
    ui_write_padded(3, 33, 21, _money_line("Purse", str(state.purse)), left_attr)
    ui_write_padded(3, 57, 21, _money_line("Vault", str(state.vault_balance)), left_attr)
    ui_write_padded(4, 33, 21, _money_line("Debt", str(state.debt_to_varro)), debt_attr)
    ui_write_padded(4, 57, 21, _money_line("Net Worth", state.net_worth_text()), worth_attr)
    ui_write_padded(5, 33, 21, _money_line("Health", str(state.health)), right_attr)
    ui_write_padded(5, 57, 21, _money_line("Suspicion", str(state.suspicion)), right_attr)
    ui_write_padded(6, 33, 21, _money_line("Guards", str(state.guards)), right_attr)
    ui_write_padded(6, 57, 21, _money_line("Capacity", f"{state.free_capacity()}/{state.capacity_total}"), right_attr)


def draw_actions_hint() -> None:
    clear_action_area()
    ui_write_padded(11, 33, 45, "Trade directly or open a submenu.", ui_make_attr(UI_GRAY, UI_BLACK))


def draw_visit_actions_hint() -> None:
    clear_action_area()
    ui_write_padded(11, 33, 45, "Finance, storage, blades, and transport.", ui_make_attr(UI_GRAY, UI_BLACK))


def draw_options_actions_hint() -> None:
    clear_action_area()
    ui_write_padded(10, 33, 45, "Utilities, score table, and graceful exits", ui_make_attr(UI_YELLOW, UI_BLACK))
    ui_write_padded(11, 33, 45, "Nothing dramatic. Mostly bookkeeping.", ui_make_attr(UI_GRAY, UI_BLACK))


def draw_inventory(state: GameState) -> None:
    ui_fill_rect(11, 2, 28, 7, " ", ui_make_attr(UI_WHITE, UI_BLACK))
    ui_write_padded(11, 3, 24, "Good         Carry Cache", ui_make_attr(UI_GRAY, UI_BLACK))
    for idx, good in enumerate(GOODS, start=0):
        row = 12 + idx
        ui_write_padded(row, 3, 12, _clip(good.name[:12], 12), ui_make_attr(UI_WHITE, UI_BLACK))
        ui_write_padded(row, 16, 4, f"{state.carried[good.key]:>4}", ui_make_attr(UI_CYAN, UI_BLACK))
        ui_write_padded(row, 21, 5, f"{state.cached[good.key]:>5}", ui_make_attr(UI_MAGENTA, UI_BLACK))


def draw_triumph(state: GameState) -> None:
    label_attr = ui_make_attr(UI_GRAY, UI_BLACK)
    value_attr = ui_make_attr(UI_YELLOW, UI_BLACK)
    alert_attr = ui_make_attr(UI_LRED, UI_BLACK)
    ready_attr = ui_make_attr(UI_LGREEN, UI_BLACK)
    ui_fill_rect(20, 2, 28, 4, " ", ui_make_attr(UI_WHITE, UI_BLACK))

    debt_text = f"Owes {state.debt_to_varro}" if state.debt_to_varro > 0 else "Clear"
    forum_text = "Ready" if state.current_district == 1 else "Away"
    status_text = triumph_status_text(state)

    ui_write_padded(20, 3, 26, "Rank", label_attr)
    ui_write_padded(20, 10, 19, _clip(triumph_rank_text(state), 19), value_attr)
    ui_write_padded(21, 3, 26, "Next", label_attr)
    ui_write_padded(21, 10, 19, _clip(next_unlock_text(state), 19), value_attr)
    ui_write_padded(22, 3, 12, "Debt", label_attr)
    ui_write_padded(22, 10, 8, _clip(debt_text, 8), alert_attr if state.debt_to_varro > 0 else ready_attr)
    ui_write_padded(22, 19, 8, "Forum", label_attr)
    ui_write_padded(22, 25, 4, _clip(forum_text, 4), ready_attr if state.current_district == 1 else value_attr)
    ui_write_padded(23, 3, 26, _clip(status_text, 26), ready_attr if state.debt_to_varro <= 0 and state.current_district == 1 else value_attr)


def draw_event_log(state: GameState) -> None:
    import textwrap

    row = 14
    ui_fill_rect(14, 32, 47, 11, " ", ui_make_attr(UI_WHITE, UI_BLACK))
    lines: list[tuple[int, str]] = []
    if not state.event_log.entries:
        lines.append((ui_make_attr(UI_WHITE, UI_BLACK), "Nothing worth repeating just now."))
    else:
        for entry in state.event_log.entries[-10:]:
            attr = ui_make_attr(UI_WHITE, UI_BLACK)
            if entry.level == "gain":
                attr = ui_make_attr(UI_LGREEN, UI_BLACK)
            elif entry.level == "warning":
                attr = ui_make_attr(UI_YELLOW, UI_BLACK)
            elif entry.level in ("danger", "theft"):
                attr = ui_make_attr(UI_LRED, UI_BLACK)
            for part in textwrap.wrap(entry.message, width=47, break_long_words=False, break_on_hyphens=False) or [""]:
                lines.append((attr, part))
    for attr, message in lines[:11]:
        ui_write_padded(row, 32, 47, _clip(message, 47), attr)
        row += 1


def draw_district_tagline(state: GameState) -> None:
    ui_write_padded(24, 2, 28, _clip(DISTRICTS[state.current_district - 1].tagline, 28), ui_make_attr(UI_DKGRAY, UI_BLACK))
