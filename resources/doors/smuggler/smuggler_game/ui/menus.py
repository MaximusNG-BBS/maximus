"""Menu helpers."""

from __future__ import annotations

from notorious_doorkit import AdvancedLightbarMenu, LightbarItem, LightbarMenu, clear_keybuffer
from notorious_doorkit.text import sgr_from_pc_attr

from ..data import DISTRICTS, GOODS
from .layout import ACTIONS_BOX
from .maxui import (
    UI_BLACK,
    UI_CYAN,
    UI_GRAY,
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
from .panels import (
    clear_action_area,
    draw_action_header,
    draw_actions_hint,
    draw_options_actions_hint,
    draw_visit_actions_hint,
)


def _run_positioned_menu(items: list[LightbarItem], *, hotkey_format: str = "none") -> int | None:
    menu = AdvancedLightbarMenu(
        items=items,
        selected_color=sgr_from_pc_attr(ui_make_attr(UI_BLACK, UI_CYAN)),
        normal_color=sgr_from_pc_attr(ui_make_attr(UI_WHITE, UI_BLACK)),
        hotkey_color=sgr_from_pc_attr(ui_make_attr(UI_YELLOW, UI_BLACK)),
        hotkey_highlight_color=sgr_from_pc_attr(ui_make_attr(UI_YELLOW, UI_CYAN)),
        hotkey_format=hotkey_format,
        wrap=True,
    )
    return menu.run()


def _paint_actions(submenu: bool, hint: str) -> None:
    ui_begin_update()
    draw_action_header(submenu)
    if hint == "visit":
        draw_visit_actions_hint()
    elif hint == "options":
        draw_options_actions_hint()
    else:
        draw_actions_hint()
    ui_end_update()
    left, top, width, height = ACTIONS_BOX
    ui_paint_region(left, top, left + width - 1, top + height - 1)


def _restore_actions() -> None:
    left, top, width, height = ACTIONS_BOX
    ui_invalidate_region(left, top, left + width - 1, top + height - 1)
    _paint_actions(False, "main")


def choose_action() -> int | None:
    _paint_actions(False, "main")
    choice = _run_positioned_menu(
        [
            LightbarItem("Buy", x=34, y=9, width=12, justify="left"),
            LightbarItem("Sell", x=47, y=9, width=12, justify="left"),
            LightbarItem("Travel", x=60, y=9, width=14, justify="left"),
            LightbarItem("Visit", x=37, y=10, width=16, justify="left"),
            LightbarItem("Options", x=56, y=10, width=16, justify="left"),
        ],
        hotkey_format="[X]",
    )
    _restore_actions()
    return choice


def choose_visit_action() -> int | None:
    _paint_actions(True, "visit")
    choice = _run_positioned_menu(
        [
            LightbarItem("Mensa", x=34, y=9, width=12, justify="left"),
            LightbarItem("Varro", x=47, y=9, width=12, justify="left"),
            LightbarItem("Cache", x=60, y=9, width=14, justify="left"),
            LightbarItem("Sellswords", x=37, y=10, width=16, justify="left"),
            LightbarItem("Cartwright", x=56, y=10, width=16, justify="left"),
        ],
        hotkey_format="[X]",
    )
    _restore_actions()
    return choice


def choose_options_action() -> int | None:
    _paint_actions(True, "options")
    choice = _run_positioned_menu(
        [
            LightbarItem("High Scores", x=34, y=9, width=15, justify="left"),
            LightbarItem("Redraw", x=50, y=9, width=14, justify="left"),
            LightbarItem("Quit", x=65, y=9, width=9, justify="left"),
        ],
        hotkey_format="[X]",
    )
    _restore_actions()
    return choice


def choose_cache_move_action() -> int | None:
    block = ui_gettext("smuggle_move_mode", 32, 9, 78, 11)
    items = [
        LightbarItem("1. Store goods", x=34, y=9, width=18, justify="left"),
        LightbarItem("2. Retrieve goods", x=55, y=9, width=20, justify="left"),
    ]

    ui_begin_update()
    clear_action_area()
    ui_write_padded(10, 33, 45, "Move goods in or out of cache", ui_make_attr(UI_YELLOW, UI_BLACK))
    ui_end_update()
    ui_paint_region(32, 9, 78, 11)
    choice = _run_positioned_menu(items, hotkey_format="none")
    ui_puttext(block, 32, 9)
    ui_invalidate_region(32, 9, 78, 11)
    ui_paint_region(32, 9, 78, 11)
    return choice


def choose_cartwright_action(cart_cost: int, ox_cost: int) -> int | None:
    block = ui_gettext("smuggle_cartwright", 32, 9, 78, 11)
    items = [
        LightbarItem(f"1. Handcart  {cart_cost}", x=34, y=9, width=20, justify="left"),
        LightbarItem(f"2. Ox team   {ox_cost}", x=55, y=9, width=20, justify="left"),
        LightbarItem("3. Leave", x=44, y=10, width=14, justify="left"),
    ]

    ui_begin_update()
    clear_action_area()
    ui_write_padded(9, 33, 45, "Handcarts and ox teams make weight move.", ui_make_attr(UI_YELLOW, UI_BLACK))
    ui_write_padded(11, 33, 45, "Cart +5 capacity, ox team +3 capacity.", ui_make_attr(UI_GRAY, UI_BLACK))
    ui_end_update()
    ui_paint_region(32, 9, 78, 11)
    choice = _run_positioned_menu(items, hotkey_format="none")
    ui_puttext(block, 32, 9)
    ui_invalidate_region(32, 9, 78, 11)
    ui_paint_region(32, 9, 78, 11)
    return choice


def choose_menu(title: str, items: list[str], submenu: str | None = None, *, restore_actions: bool = False) -> int | None:
    del title
    del submenu
    if restore_actions:
        clear_action_area()
        left, top, width, height = ACTIONS_BOX
        ui_paint_region(left, top, left + width - 1, top + height - 1)
        positions = [(34, 9, 18), (55, 9, 18), (34, 10, 18), (55, 10, 18), (34, 11, 18), (55, 11, 18)]
        lb_items = [
            LightbarItem(text=items[idx], x=positions[idx][0], y=positions[idx][1], width=positions[idx][2], justify="left")
            for idx in range(min(len(items), len(positions)))
        ]
        choice = _run_positioned_menu(lb_items)
        _restore_actions()
        if choice is None or choice >= len(items):
            return None
        return choice

    menu = LightbarMenu(
        items=items,
        x=4,
        y=8,
        width="auto",
        justify="left",
        selected_color=sgr_from_pc_attr(ui_make_attr(UI_BLACK, UI_CYAN)),
        normal_color=sgr_from_pc_attr(ui_make_attr(UI_WHITE, UI_BLACK)),
        hotkey_color=sgr_from_pc_attr(ui_make_attr(UI_YELLOW, UI_BLACK)),
        hotkey_highlight_color=sgr_from_pc_attr(ui_make_attr(UI_YELLOW, UI_CYAN)),
        hotkey_format="none",
        wrap=True,
    )
    return menu.run()


def choose_good() -> str | None:
    block = ui_gettext("smuggle_goods", 32, 9, 78, 11)
    items: list[LightbarItem] = []
    for idx, good in enumerate(GOODS, start=0):
        x = 33 if idx % 2 == 0 else 56
        y = 9 + (idx // 2)
        items.append(LightbarItem(text=f"{idx + 1}. {good.name}", x=x, y=y, width=20, justify="left"))

    ui_begin_update()
    clear_action_area()
    ui_end_update()
    ui_paint_region(32, 9, 78, 11)
    choice = _run_positioned_menu(items, hotkey_format="none")
    ui_puttext(block, 32, 9)
    ui_invalidate_region(32, 9, 78, 11)
    ui_paint_region(32, 9, 78, 11)

    if choice is None or choice >= len(GOODS):
        return None
    return GOODS[choice].key


def choose_district() -> int | None:
    block = ui_gettext("smuggle_travel", 31, 8, 79, 12)
    items: list[LightbarItem] = []
    for idx, district in enumerate(DISTRICTS, start=0):
        x = 33 if idx % 2 == 0 else 56
        y = 9 + (idx // 2)
        items.append(LightbarItem(text=f"{idx + 1}. {district.name}", x=x, y=y, width=20, justify="left"))

    ui_begin_update()
    ui_fill_rect(8, 31, 49, 5, " ", ui_make_attr(UI_WHITE, UI_BLACK))
    ui_box(8, 31, 49, 5, ui_make_attr(UI_BLACK, UI_CYAN), "Travel")
    ui_end_update()
    ui_paint_region(31, 8, 79, 12)
    choice = _run_positioned_menu(items, hotkey_format="none")
    ui_puttext(block, 31, 8)
    ui_invalidate_region(31, 8, 79, 12)
    ui_paint_region(31, 8, 79, 12)

    if choice is None or choice >= len(DISTRICTS):
        clear_keybuffer()
        return None
    return DISTRICTS[choice].index


def choose_watch_action(watchmen: int) -> str:
    del watchmen
    block = ui_gettext("smuggle_watch", 32, 9, 78, 11)

    ui_begin_update()
    clear_action_area()
    ui_write_padded(9, 33, 45, "Fight, run, or bribe?", ui_make_attr(UI_YELLOW, UI_BLACK))
    ui_end_update()
    ui_paint_region(32, 9, 78, 11)

    choice = _run_positioned_menu(
        [
            LightbarItem("Fight", x=38, y=10, width=10, justify="left"),
            LightbarItem("Run", x=50, y=10, width=10, justify="left"),
            LightbarItem("Bribe", x=62, y=10, width=10, justify="left"),
        ],
        hotkey_format="[X]",
    )

    ui_puttext(block, 32, 9)
    ui_invalidate_region(32, 9, 78, 11)
    ui_paint_region(32, 9, 78, 11)

    if choice == 0:
        return "F"
    if choice == 2:
        return "B"
    return "R"
