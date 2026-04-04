"""Runnable Smuggler door app."""

from __future__ import annotations

import argparse
import random
import sys
import time
from typing import Sequence

_DBG = "/tmp/smuggler_debug.log"

def _dlog(msg: str) -> None:
    try:
        with open(_DBG, "a") as f:
            f.write(f"[{time.strftime('%H:%M:%S')}] APP: {msg}\n")
    except Exception:
        pass

from notorious_doorkit import Door

from .constants import (
    ACTION_BUY,
    ACTION_CACHE,
    ACTION_CARTWRIGHT,
    EVENT_CLASS_INFO,
    ACTION_LENDER,
    ACTION_QUIT,
    ACTION_REDRAW,
    ACTION_SCORES,
    ACTION_SELL,
    ACTION_SELLSWORDS,
    ACTION_TRAVEL,
    ACTION_VAULT,
)
from .models import GameState
from .persistence import delete_game, load_game, save_game
from .systems import (
    begin_watch_encounter,
    buy_goods,
    handle_resume,
    init_new_game,
    maybe_watch_encounter,
    move_goods_to_cache,
    pop_bestowals,
    resolve_bestowal_notice,
    resolve_special_offer,
    should_varro_enforce,
    show_scores as load_score_rows,
    set_event,
    travel_to_district,
    update_scores,
    varro_enforcement,
    visit_cartwright,
    visit_counting_house,
    visit_house_varro,
    visit_sellswords,
    watch_encounter,
)
from .ui import (
    choose_action,
    choose_cache_move_action,
    choose_cartwright_action,
    choose_district,
    choose_good,
    choose_menu,
    choose_options_action,
    choose_visit_action,
    choose_watch_action,
    confirm_identity_component,
    pause,
    prompt_special_offer,
    prompt_number,
    refresh_event_only,
    refresh_day_rollover,
    refresh_status_event,
    refresh_status_cargo_event,
    render_state,
    show_game_over,
    show_intro,
    show_scores,
    show_varro_enforcement,
    title_bestowal_notice,
)


class SmugglerApp:
    """First migrated Smuggler app loop."""

    def __init__(self, smoke_test: bool = False):
        self.door = Door()
        self.smoke_test = smoke_test
        self.rng = random.Random()
        self.state: GameState | None = None

    def start(self) -> None:
        if len(sys.argv) >= 3:
            self.door.start()
        else:
            self.door.start_local(username="Local Tester", node=1)

    def load_or_create_state(self) -> None:
        assert self.door.session.username
        state = load_game(self.door.session.username)
        if state is None:
            state = init_new_game(self.door.session.username, self.rng)
        else:
            handle_resume(state, self.rng)
        self.state = state

    def run(self) -> int:
        self.start()
        self.load_or_create_state()
        assert self.state is not None

        if self.smoke_test:
            render_state(self.state)
            return 0

        show_intro(self.state)
        self.process_bestowals()
        self.process_pending_offers()
        render_state(self.state)

        # Check for overdue Varro debt on entry (resume with days <= 0).
        if self._enforce_varro():
            return 0

        while True:
            _dlog("--- loop top ---")
            watchmen = maybe_watch_encounter(self.state, self.rng)
            _dlog(f"watchmen={watchmen}")
            if watchmen:
                begin_watch_encounter(self.state, watchmen)
                refresh_status_cargo_event(self.state)
                watch_choice = choose_watch_action(watchmen)
                watch_encounter(self.state, self.rng, watchmen, watch_choice)
                save_game(self.state)
                refresh_status_cargo_event(self.state)
                if self.state.health <= 0:
                    _dlog("GAME OVER from watch encounter (health)")
                    update_scores(self.state)
                    show_game_over(self.state)
                    return 0

            # Random Varro enforcement on day 0 or guaranteed when overdue.
            if self._enforce_varro():
                return 0

            choice = choose_action()
            _dlog(f"choose_action -> {choice!r}")
            if choice is None:
                refresh_event_only(self.state)
                continue
            refresh = refresh_event_only
            should_save = False
            if choice == 0:
                self.do_buy()
                refresh = refresh_status_cargo_event
                should_save = True
            elif choice == 1:
                self.do_sell()
                refresh = refresh_status_cargo_event
                should_save = True
            elif choice == 2:
                _dlog("entering do_travel")
                moved = self.do_travel()
                _dlog(f"do_travel returned moved={moved}")
                refresh = refresh_day_rollover if moved else refresh_event_only
                # Varro's men intercept at the gate when note is about to expire.
                if moved and self._enforce_varro(is_travel=True):
                    return 0
            elif choice == 3:
                refresh = self.do_visit()
                should_save = True
            elif choice == 4:
                _dlog("entering do_options")
                if self.do_options() == ACTION_QUIT:
                    _dlog("do_options returned ACTION_QUIT")
                    update_scores(self.state)
                    self.state.quit_requested = True
                    self.state.pending_resume_advance = True
                    save_game(self.state)
                    show_game_over(self.state)
                    return 0
                render_state(self.state)
                continue
            _dlog("pre-bestowals")
            self.process_bestowals()
            _dlog("pre-pending_offers")
            self.process_pending_offers()
            if should_save:
                save_game(self.state)
            _dlog(f"calling refresh={refresh.__name__}")
            refresh(self.state)
            _dlog(f"post-refresh health={self.state.health} days_left={self.state.days_left_on_note} debt={self.state.debt_to_varro}")
            if self.state.health <= 0:
                _dlog("GAME OVER triggered by health check")
                update_scores(self.state)
                show_game_over(self.state)
                return 0
            _dlog("loop iteration complete, back to top")

    def _enforce_varro(self, *, is_travel: bool = False) -> bool:
        """Run Varro enforcement if triggered. Returns True when game ends."""
        assert self.state is not None
        if not should_varro_enforce(self.state, self.rng, is_travel=is_travel):
            return False
        _dlog(f"Varro enforcement triggered (is_travel={is_travel})")
        outcome = varro_enforcement(self.state, self.rng)
        _dlog(f"Varro outcome={outcome!r}")
        show_varro_enforcement(outcome)
        if outcome == "ruined":
            update_scores(self.state)
            delete_game(self.state.username)
            show_game_over(self.state)
            return True
        # Survived — save the post-enforcement state (note timer reset, etc.)
        save_game(self.state)
        refresh_status_cargo_event(self.state)
        return False

    def do_buy(self) -> None:
        assert self.state is not None
        good_key = choose_good()
        if not good_key:
            set_event(self.state, EVENT_CLASS_INFO, "You let the offer pass. Not every whisper deserves coin.")
            return
        amount = prompt_number("How many? ", 5)
        buy_goods(self.state, good_key, amount)

    def do_sell(self) -> None:
        assert self.state is not None
        good_key = choose_good()
        if not good_key:
            set_event(self.state, EVENT_CLASS_INFO, "You keep your cargo close and wait for a better whisper.")
            return
        amount = prompt_number("How many? ", 5)
        from .systems import sell_goods

        sell_goods(self.state, good_key, amount)

    def do_travel(self) -> bool:
        assert self.state is not None
        district_idx = choose_district()
        _dlog(f"do_travel: choose_district -> {district_idx!r}")
        if district_idx is None:
            return False
        return travel_to_district(self.state, district_idx, self.rng)

    def do_visit(self):
        assert self.state is not None
        choice = choose_visit_action()
        if choice is None:
            return refresh_event_only
        if choice == 0:
            visit_counting_house(self.state, deposit=prompt_number("Deposit how much? ", 9))
            visit_counting_house(self.state, withdraw=prompt_number("Withdraw how much? ", 9))
            return refresh_status_event
        elif choice == 1:
            visit_house_varro(self.state, payment=prompt_number("Pay how much? ", 9))
            if self.state.debt_to_varro == 0:
                visit_house_varro(self.state, borrow=prompt_number("Borrow how much? ", 9))
            return refresh_status_event
        elif choice == 2:
            mode = choose_cache_move_action()
            good_key = choose_good()
            if not good_key:
                set_event(self.state, EVENT_CLASS_INFO, "You close the cache ledger and leave the stones undisturbed.")
                return refresh_status_cargo_event
            if mode == 0:
                move_goods_to_cache(self.state, good_key, prompt_number("How many? ", 5), True)
            elif mode == 1:
                move_goods_to_cache(self.state, good_key, prompt_number("How many? ", 5), False)
            else:
                set_event(self.state, EVENT_CLASS_INFO, "No goods move. The cache keeps its silence.")
            return refresh_status_cargo_event
        elif choice == 3:
            visit_sellswords(self.state)
            return refresh_status_event
        elif choice == 4:
            cart_cost = 140 + (self.state.self_cart_count * 90)
            ox_cost = 220 + (self.state.self_oxen_count * 120)
            sub = choose_cartwright_action(cart_cost, ox_cost)
            if sub == 0:
                visit_cartwright(self.state, buy_ox=False)
            elif sub == 1:
                visit_cartwright(self.state, buy_ox=True)
            else:
                set_event(self.state, EVENT_CLASS_INFO, "You leave the yard with the same wheels you came in with.")
            return refresh_status_event
        return refresh_event_only

    def do_options(self) -> int:
        assert self.state is not None
        choice = choose_options_action()
        _dlog(f"do_options: choose_options_action -> {choice!r}")
        if choice is None:
            return ACTION_REDRAW
        if choice == 0:
            show_scores(load_score_rows())
            return ACTION_SCORES
        if choice == 1:
            return ACTION_REDRAW
        if choice == 2:
            _dlog("do_options: returning ACTION_QUIT")
            return ACTION_QUIT
        return ACTION_REDRAW

    def process_bestowals(self) -> None:
        assert self.state is not None
        notices = pop_bestowals(self.state)
        for notice in notices:
            title_bestowal_notice(notice.text)
            if notice.forced:
                resolve_bestowal_notice(self.state, notice, accepted=True)
                continue
            accepted = confirm_identity_component(notice.component, notice.value)
            resolve_bestowal_notice(self.state, notice, accepted)

    def process_pending_offers(self) -> None:
        assert self.state is not None
        while self.state.pending_offers:
            offer = self.state.pending_offers.pop(0)
            accepted = prompt_special_offer(offer)
            resolve_special_offer(self.state, offer, accepted)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Smuggler of Rome (Python migration)")
    parser.add_argument("--smoke-test", action="store_true", help="Load the door and render once without entering the menu loop.")
    args, _unknown = parser.parse_known_args(list(argv) if argv is not None else None)
    app = SmugglerApp(smoke_test=args.smoke_test)
    return app.run()
