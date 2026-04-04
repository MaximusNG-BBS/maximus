"""Core game systems migrated from MEX."""

from __future__ import annotations

import random

from .constants import (
    ACTION_NONE,
    ACTION_QUIT,
    ACTION_REDRAW,
    ACTION_SCORES,
    EVENT_CLASS_DANGER,
    EVENT_CLASS_GAIN,
    EVENT_CLASS_INFO,
    EVENT_CLASS_THEFT,
    EVENT_CLASS_WARNING,
    TRIUMPH_TARGET,
)
from .data import DISTRICTS, GOODS, NICKNAME_BUCKETS, PRETITLE_BUCKETS, TITLE_BUCKETS
from .models import BestowalNotice, EventEntry, GameState, ScoreEntry, SpecialOffer
from .persistence import load_scores, save_game, save_scores


def append_event(state: GameState, level: str, message: str) -> None:
    if not message:
        return
    if not state.event_log.headline:
        state.event_log.headline = message
    state.event_log.entries.append(EventEntry(level=level, message=message))
    state.event_log.entries = state.event_log.entries[-12:]


def set_event(state: GameState, level: str, message: str) -> None:
    state.event_log.clear()
    append_event(state, level, message)


def init_new_game(username: str, rng: random.Random) -> GameState:
    state = GameState(username=username.upper())
    set_event(state, EVENT_CLASS_INFO, "You slip into the Forum after dark, hunting your first profitable whisper.")
    sync_progress_state(state)
    randomize_market_prices(state, rng)
    run_arrival_events(state, rng)
    save_game(state)
    return state


def sync_progress_state(state: GameState) -> None:
    if state.guards < 0:
        state.guards = 0
    if state.capacity_total < 1:
        state.capacity_total = 1
    state.unlocks.sellswords = state.net_worth() >= 600 or state.might_points >= 1 or state.guards > 0
    state.unlocks.cartwright = (
        state.debt_to_varro == 0
        or state.net_worth() >= 1200
        or state.prestige_points >= 2
        or state.self_cart_count > 0
    )
    state.unlocks.warehouse = state.debt_to_varro == 0 and state.net_worth() >= 3500 and state.influence_points >= 3
    state.unlocks.traders = state.debt_to_varro == 0 and state.net_worth() >= 5500 and state.influence_points >= 4
    state.unlocks.property = state.debt_to_varro == 0 and state.net_worth() >= 7000 and state.prestige_points >= 6
    state.trader_slots_unlocked = 1
    if state.unlocks.traders and state.influence_points >= 5:
        state.trader_slots_unlocked = 2
    if state.unlocks.traders and state.prestige_points >= 7:
        state.trader_slots_unlocked = 3
    if state.unlocks.traders and state.prestige_points >= 9 and state.influence_points >= 7:
        state.trader_slots_unlocked = 4
    assign_identity(state)


def dominant_axis(state: GameState) -> str:
    logistics_score = state.self_cart_count + state.self_oxen_count + sum(1 for trader in state.traders if trader.active)
    wealth_score = max(0, state.net_worth() // 1000)
    scores = {
        "prestige": state.prestige_points,
        "influence": state.influence_points,
        "might": state.might_points + (state.guards // 3),
        "logistics": logistics_score,
        "wealth": wealth_score,
    }
    return max(scores, key=lambda key: scores[key])


def assign_identity(state: GameState) -> None:
    axis = dominant_axis(state)
    state.identity.dominant_axis = axis
    if state.debt_to_varro > 0:
        pretitle = PRETITLE_BUCKETS["debt"][0]
    elif state.net_worth() > 0 and state.debt_to_varro == 0:
        pretitle = PRETITLE_BUCKETS["freed"][0]
    else:
        bucket = PRETITLE_BUCKETS.get(axis, PRETITLE_BUCKETS["prestige"])
        pretitle = bucket[min(len(bucket) - 1, 1)]
    nick_bucket = NICKNAME_BUCKETS.get(axis, NICKNAME_BUCKETS["prestige"])
    tier = 0
    axis_value = {
        "prestige": state.prestige_points,
        "influence": state.influence_points,
        "might": state.might_points + state.guards,
        "logistics": state.self_cart_count + state.self_oxen_count + state.trader_slots_unlocked,
        "wealth": max(0, state.net_worth() // 1000),
    }[axis]
    if axis_value >= 5:
        tier = 2
    elif axis_value >= 2:
        tier = 1
    nickname = nick_bucket[min(tier, len(nick_bucket) - 1)]
    active_traders = sum(1 for trader in state.traders if trader.active)
    if state.guards >= 50:
        title = TITLE_BUCKETS["guards_empire"][0]
    elif state.guards >= 25:
        title = TITLE_BUCKETS["guards_large"][0]
    elif state.guards >= 3:
        title = TITLE_BUCKETS["guards_medium"][0]
    elif state.guards >= 1:
        title = TITLE_BUCKETS["guards_small"][0]
    elif active_traders >= 16:
        title = TITLE_BUCKETS["traders_empire"][0]
    elif active_traders >= 9:
        title = TITLE_BUCKETS["traders_large"][0]
    elif active_traders >= 1:
        title = TITLE_BUCKETS["traders_medium"][0]
    elif state.self_cart_count + state.self_oxen_count >= 10:
        title = TITLE_BUCKETS["routes_empire"][0]
    elif state.self_cart_count + state.self_oxen_count >= 5:
        title = TITLE_BUCKETS["routes_large"][0]
    elif state.self_cart_count + state.self_oxen_count >= 2:
        title = TITLE_BUCKETS["routes_medium"][0]
    else:
        title = TITLE_BUCKETS["routes_small"][0]
    _register_bestowal(state, "pretitle", pretitle, axis)
    _register_bestowal(state, "nickname", nickname, axis)
    _register_bestowal(state, "title", title, axis)


def _remember_identity_value(bucket: dict[str, list[str]], category: str, value: str) -> None:
    if not value:
        return
    rows = bucket.setdefault(category, [])
    if value in rows:
        rows.remove(value)
    rows.insert(0, value)
    del rows[3:]


def _component_bucket(state: GameState, component: str) -> dict[str, list[str]]:
    if component == "pretitle":
        return state.identity.inventory.pretitles
    if component == "nickname":
        return state.identity.inventory.nicknames
    return state.identity.inventory.titles


def _active_identity_value(state: GameState, component: str) -> str:
    if component == "pretitle":
        return state.identity.active_pretitle
    if component == "nickname":
        return state.identity.active_nickname
    return state.identity.active_title


def _set_active_identity_value(state: GameState, component: str, value: str) -> None:
    if component == "pretitle":
        state.identity.active_pretitle = value
    elif component == "nickname":
        state.identity.active_nickname = value
    else:
        state.identity.active_title = value


def _register_bestowal(state: GameState, component: str, new_value: str, category: str) -> None:
    if not new_value:
        return
    old_value = _active_identity_value(state, component)
    bucket = _component_bucket(state, component)
    known_values = bucket.get(category, [])
    if not old_value:
        _remember_identity_value(bucket, category, new_value)
        _set_active_identity_value(state, component, new_value)
        return
    if not old_value or old_value == new_value:
        return
    if new_value in known_values:
        return
    _remember_identity_value(bucket, category, new_value)
    if component == "pretitle":
        text = f"The city adjusts the way it addresses you. Increasingly, you are styled {new_value}."
    elif component == "nickname":
        text = f"Word spreads through the alleys: they are calling you {new_value}."
    else:
        text = f"Your operation has grown teeth and weight. Men now speak of you as {new_value}."
    state.identity.pending_bestowals.append(
        BestowalNotice(component=component, category=category, text=text, value=new_value, forced=False)
    )
    state.identity.pending_bestowals = state.identity.pending_bestowals[-6:]


def resolve_bestowal_notice(state: GameState, notice: BestowalNotice, accepted: bool) -> None:
    bucket = _component_bucket(state, notice.component)
    _remember_identity_value(bucket, notice.category or state.identity.dominant_axis, notice.value)
    if notice.forced or accepted:
        _set_active_identity_value(state, notice.component, notice.value)
        append_event(
            state,
            EVENT_CLASS_GAIN,
            f"You encourage the name {notice.value}. Rome listens faster than it forgives.",
        )
        return
    append_event(
        state,
        EVENT_CLASS_INFO,
        f"You let the name {notice.value} circulate without claiming it as your own.",
    )


def triumph_rank_text(state: GameState) -> str:
    total = state.prestige_points + state.influence_points + state.might_points
    if total < 2:
        return "Street Runner"
    if total < 5:
        return "Shadow Broker"
    if total < 8:
        return "Forum Factor"
    if total < 12:
        return "House Operator"
    if total < 16:
        return "Night Magnate"
    if total < 21:
        return "Patrician"
    return "Imperial Power"


def next_unlock_text(state: GameState) -> str:
    if not state.unlocks.sellswords:
        return "Sellswords"
    if not state.unlocks.cartwright:
        return "Cartwright"
    if not state.unlocks.warehouse:
        return "Warehouse"
    if not state.unlocks.traders:
        return "Trade Routes"
    if not state.unlocks.property:
        return "Estate Paths"
    if triumph_ready(state):
        return "Retire in glory"
    return "Power paths"


def triumph_ready(state: GameState) -> bool:
    return state.health > 0 and state.debt_to_varro <= 0 and state.net_worth() >= TRIUMPH_TARGET and state.current_district == 1


def triumph_status_text(state: GameState) -> str:
    if state.health <= 0:
        return "The grave keeps no triumph."
    if state.debt_to_varro > 0:
        return "Clear Varro's note first."
    if state.net_worth() < TRIUMPH_TARGET:
        return f"Need {TRIUMPH_TARGET - state.net_worth()} more."
    if state.current_district != 1:
        return "Return to the Forum."
    return "Ready to retire in glory."


def note_daily_fee(state: GameState) -> int:
    if state.debt_to_varro <= 0:
        return 0
    return 6 + (state.debt_to_varro // 200)


def randomize_market_prices(state: GameState, rng: random.Random) -> None:
    for good in GOODS:
        state.prices[good.key] = good.price_min + rng.randrange(good.price_span)
    apply_district_market_bias(state)


def apply_district_market_bias(state: GameState) -> None:
    district = state.current_district
    if district == 1:
        state.prices["seals"] += 18
        state.prices["wine"] += 8
    elif district == 2:
        state.prices["resin"] += 12
        state.prices["wine"] += 6
    elif district == 3:
        state.prices["incense"] += 10
        state.prices["silk"] += 14
    elif district == 4:
        state.prices["wine"] += 10
        state.prices["incense"] += 10
    elif district == 5:
        state.prices["steel"] += 16
        state.prices["resin"] += 7
    elif district == 6:
        state.prices["seals"] += 12
        state.prices["silk"] += 10


def apply_market_event(state: GameState, rng: random.Random) -> None:
    roll = rng.randrange(100)
    good = GOODS[rng.randrange(len(GOODS))]
    if roll < 14:
        price = state.prices[good.key]
        state.prices[good.key] = price + ((price // 2) + rng.randrange(max(1, price)))
        surge_messages = {
            "wine": "A patrician banquet empties half the wine cellars. Falernian prices surge.",
            "incense": "Temple wardens seize incense shipments. Syrian incense turns scarce.",
            "resin": "Too many apothecaries lost their nerve. Poppy resin jumps.",
            "silk": "An eastern caravan vanished on the road. Silk bolts are suddenly dear.",
            "seals": "A magistrate purge hits the clerks. Forged seals become dangerous and expensive.",
            "steel": "Legion quartermasters start asking questions. Legion steel spikes.",
        }
        append_event(state, EVENT_CLASS_WARNING, surge_messages[good.key])
    elif roll < 28:
        state.prices[good.key] = max(good.price_min, state.prices[good.key] // 2)
        drop_messages = {
            "wine": "A river convoy arrives intact. Falernian wine floods the market.",
            "incense": "Smugglers dump fresh incense at the docks. Syrian incense softens.",
            "resin": "Back-alley brewers overcooked a batch. Poppy resin goes cheap.",
            "silk": "A Syrian broker panics and unloads silk. Prices crack.",
            "seals": "Half the district is selling forged papers. Seals bottom out.",
            "steel": "A crooked armorer unloads surplus blades. Legion steel turns common.",
        }
        append_event(state, EVENT_CLASS_GAIN, drop_messages[good.key])


def district_watch_modifier(state: GameState) -> int:
    return DISTRICTS[state.current_district - 1].watch_modifier


def apply_watch_event(state: GameState, rng: random.Random) -> None:
    roll = rng.randrange(100)
    if roll < 7 and state.suspicion > 15:
        state.suspicion = max(0, state.suspicion - 6)
        append_event(state, EVENT_CLASS_GAIN, "A magistrate's attention shifts to another fool for a few days. The heat eases.")
    elif roll < 13:
        state.suspicion = min(100, state.suspicion + 6 + district_watch_modifier(state))
        append_event(state, EVENT_CLASS_WARNING, "A clerk sells a name, a route, or a face. The vigiles seem a little too interested tonight.")
    elif roll < 17 and state.purse > 120:
        loss = min(state.purse, 20 + rng.randrange(31))
        state.purse -= loss
        append_event(state, EVENT_CLASS_DANGER, "A checkpoint tribute goes badly.")
        append_event(state, EVENT_CLASS_WARNING, f"Paid {loss} denarii.")


def apply_district_event(state: GameState, rng: random.Random) -> None:
    if rng.randrange(100) >= 18:
        return
    pick = rng.randrange(3)
    table = {
        1: (
            "A court clerk quietly needs forged seals before sunrise. Forum buyers pay like frightened senators.",
            "A steward from the basilica is buying Falernian by the quiet jug. Respectability is thirsty tonight.",
            "Temple accountants are arguing over incense levies again. Honest cargo suddenly looks less honest.",
        ),
        2: (
            "Subura's taverns burn through resin and wine faster than the watch can count cups.",
            "A knife-boy gang is leaning on stallholders for tribute. Everybody's costs feel heavier.",
            "A back-alley healer is desperate for poppy resin before dawn. Quiet buyers pay well in Subura.",
        ),
        3: (
            "Dock gossip says an eastern hull came in light. Silk and incense move strangely at Ostia tonight.",
            "A barge-master is unloading wine too fast to ask careful questions. The docks smell like margin.",
            "Harbor inspectors are sniffing around military cargo. Legion steel is suddenly a nervous trade.",
        ),
        4: (
            "Aventine households are buying luxury through servants again. Quiet buyers mean good margins.",
            "A terrace feast is stripping cellars and scent cabinets at the same time. Wine and incense both feel lively.",
            "A warehouse factor is fixing ledgers after dark. Forged seals suddenly matter more than charm.",
        ),
        5: (
            "Games and wagers pull crowds into Campus Martius. Quick coin follows noisy appetites.",
            "Drill yards are short on proper steel and asking impolite questions. Legion cargo is hotter than usual.",
            "Bruised bettors and fighters are paying for resin by the handful. Campus coin smells like sweat tonight.",
        ),
        6: (
            "Palatine doors stay shut, but sealed notes keep moving. Secrecy is buying secrecy tonight.",
            "Curtained litters keep stopping at the same side entrance. Silk and incense are moving under noble silence.",
            "A household purge is chewing through private ledgers. Forged seals are suddenly worth both more and less.",
        ),
    }
    message = table[state.current_district][pick]
    level = EVENT_CLASS_WARNING if "seals" in message.lower() or "questions" in message.lower() else EVENT_CLASS_GAIN
    append_event(state, level, message)


def apply_personal_event(state: GameState, rng: random.Random) -> None:
    roll = rng.randrange(100)
    good = GOODS[rng.randrange(len(GOODS))]
    amount = 1 + rng.randrange(4)
    if roll < 6 and state.purse > 80:
        state.purse -= 40
        append_event(state, EVENT_CLASS_THEFT, "A market ghost brushes past you in the crowd.")
        append_event(state, EVENT_CLASS_WARNING, "Lost 40 denarii.")
    elif roll < 12 and state.guards > 0:
        state.guards -= 1
        state.suspicion = min(100, state.suspicion + 5)
        append_event(state, EVENT_CLASS_THEFT, "One of your hired blades sells his loyalty for a cleaner purse.")
        append_event(state, EVENT_CLASS_WARNING, "Lost 1 hired blade.")
    elif roll < 18 and state.free_capacity() >= amount:
        state.carried[good.key] += amount
        append_event(state, EVENT_CLASS_GAIN, "A body in a side alley still grips a satchel strap. Rome has no use for the dead, but you do.")
        append_event(state, EVENT_CLASS_GAIN, f"[+{amount} lots of {good.name}]")
    elif roll < 22 and state.cached_total() > 10 and state.current_district != 1:
        for key in state.cached:
            state.cached[key] //= 2
        append_event(state, EVENT_CLASS_THEFT, "Someone reached your cache through the wrong priest, the right bribe, or both.")
        append_event(state, EVENT_CLASS_WARNING, "Half your reserve disappears.")


def run_arrival_events(state: GameState, rng: random.Random) -> None:
    district = DISTRICTS[state.current_district - 1]
    state.event_log.clear()
    append_event(state, EVENT_CLASS_INFO, district.arrival_text)
    apply_district_event(state, rng)
    apply_market_event(state, rng)
    apply_watch_event(state, rng)
    apply_personal_event(state, rng)
    run_special_offer_event(state, rng)
    sync_progress_state(state)


def queue_special_offer(state: GameState, offer: SpecialOffer) -> None:
    state.pending_offers.append(offer)
    state.pending_offers = state.pending_offers[-2:]


def offer_goods_bargain(
    state: GameState,
    good_key: str,
    lots: int,
    discount_pct: int,
    title: str,
    prompt: str,
    accept_msg: str,
    decline_msg: str,
) -> bool:
    if lots <= 0:
        return False
    good = next(good for good in GOODS if good.key == good_key)
    floor_price = (good.price_min * lots) // 2
    price = (state.prices[good_key] * lots * discount_pct) // 100
    price = max(price, floor_price, lots)
    if state.purse < price or state.free_capacity() < lots:
        return False
    queue_special_offer(
        state,
        SpecialOffer(
            kind="goods",
            title=title,
            prompt=prompt,
            price=price,
            good_key=good_key,
            lots=lots,
            accept_msg=accept_msg,
            decline_msg=decline_msg,
        ),
    )
    return True


def offer_guard_bargain(state: GameState, price: int, title: str, prompt: str, accept_msg: str, decline_msg: str) -> bool:
    if state.purse < price:
        return False
    queue_special_offer(
        state,
        SpecialOffer(
            kind="guards",
            title=title,
            prompt=prompt,
            price=price,
            guard_count=1,
            accept_msg=accept_msg,
            decline_msg=decline_msg,
        ),
    )
    return True


def offer_capacity_bargain(
    state: GameState,
    price: int,
    extra_capacity: int,
    title: str,
    prompt: str,
    accept_msg: str,
    decline_msg: str,
) -> bool:
    if state.purse < price:
        return False
    queue_special_offer(
        state,
        SpecialOffer(
            kind="capacity",
            title=title,
            prompt=prompt,
            price=price,
            extra_capacity=extra_capacity,
            accept_msg=accept_msg,
            decline_msg=decline_msg,
        ),
    )
    return True


def run_special_offer_event(state: GameState, rng: random.Random) -> None:
    if rng.randrange(100) >= 12:
        return
    if state.current_district == 1:
        amount = 1 + rng.randrange(2)
        offer_goods_bargain(
            state,
            "seals",
            amount,
            65,
            "Forum Packet",
            "A basilica clerk slips you a waxed packet of forged seals.",
            "A quiet exchange beneath the colonnades leaves you richer in seals and poorer in innocence.",
            "You leave the clerk with his packet and his panic.",
        )
        return
    if state.current_district == 2:
        price = 45 + rng.randrange(26)
        offer_guard_bargain(
            state,
            price,
            "Alley Steel",
            "A scarred broker offers another hired blade for the night.",
            "You add another hired blade to your shadow. He looks expensive because he is.",
            "You wave the broker off and keep your own shadow for company.",
        )
        return
    if state.current_district == 3:
        amount = 2 + rng.randrange(2)
        offer_goods_bargain(
            state,
            "incense",
            amount,
            60,
            "Dockside Lot",
            "A barge runner offers damp Syrian incense before customs counts the crates.",
            "You buy the dockside lot before the tally sticks catch up with the missing cargo.",
            "You leave the damp incense to somebody hungrier than you.",
        )
        return
    if state.current_district == 4:
        price = 55 + rng.randrange(31)
        offer_capacity_bargain(
            state,
            price,
            5,
            "Rigging Harness",
            "A leatherworker offers reinforced satchel rigging.",
            "A leatherworker toughens your rigging. You can carry five more lots now.",
            "You leave the extra straps and frame where they are.",
        )
        return
    if state.current_district == 5:
        amount = 1 + rng.randrange(2)
        offer_goods_bargain(
            state,
            "steel",
            amount,
            70,
            "Quartermaster Scrap",
            "A camp-follower offers dented legion steel from a wagon that never reached inventory.",
            "You take the army steel and pretend not to hear where it came from.",
            "You decide not to be the fool holding army metal at the wrong hour.",
        )
        return
    amount = 1 + rng.randrange(2)
    offer_goods_bargain(
        state,
        "silk",
        amount,
        68,
        "Quiet Delivery",
        "A curtained servant offers silk bolts with the household marks already cut away.",
        "You take the silk and leave the questions behind the curtain.",
        "You bow out of the noble household's quiet panic.",
    )


def resolve_special_offer(state: GameState, offer: SpecialOffer, accepted: bool) -> None:
    if not accepted:
        append_event(state, EVENT_CLASS_INFO, offer.decline_msg)
        return
    if offer.kind == "goods":
        state.purse -= offer.price
        state.carried[offer.good_key] += offer.lots
        good_name = next(good.name for good in GOODS if good.key == offer.good_key)
        append_event(state, EVENT_CLASS_GAIN, offer.accept_msg)
        append_event(state, EVENT_CLASS_GAIN, f"[+{offer.lots} lots of {good_name}]")
        return
    if offer.kind == "guards":
        state.purse -= offer.price
        state.guards += offer.guard_count
        state.might_points += 1
        sync_progress_state(state)
        append_event(state, EVENT_CLASS_GAIN, offer.accept_msg)
        append_event(state, EVENT_CLASS_GAIN, f"[+{offer.guard_count} hired blade]")
        return
    if offer.kind == "capacity":
        state.purse -= offer.price
        state.capacity_total += offer.extra_capacity
        state.prestige_points += 1
        sync_progress_state(state)
        append_event(state, EVENT_CLASS_GAIN, offer.accept_msg)
        append_event(state, EVENT_CLASS_GAIN, f"[+{offer.extra_capacity} capacity]")


def apply_turn_upkeep(state: GameState) -> None:
    state.day_number += 1
    if state.debt_to_varro > 0:
        state.days_left_on_note -= 1
        state.debt_to_varro += note_daily_fee(state)
    if state.vault_balance > 0:
        state.vault_balance += state.vault_balance // 50
    if state.health < 100:
        state.health += 1
    if state.day_number % 7 == 0:
        if state.purse >= 40:
            state.purse -= 40
            append_event(state, EVENT_CLASS_WARNING, "Stall fees, bribes, and bad wine eat forty denarii before you can argue with the ledger.")
        else:
            state.debt_to_varro += 50
            append_event(state, EVENT_CLASS_DANGER, "You cannot cover the week's expenses. House Varro notices faster than prayer.")


def handle_resume(state: GameState, rng: random.Random) -> str:
    if state.pending_resume_advance:
        state.event_log.clear()
        apply_turn_upkeep(state)
        if state.days_left_on_note > 0 or state.debt_to_varro <= 0:
            randomize_market_prices(state, rng)
            run_arrival_events(state, rng)
        state.pending_resume_advance = False
        state.resumed_game = True
        save_game(state)
        return "You reopen your ledger where you left it. Rome kept moving, but your operation survived the night."
    state.resumed_game = True
    set_event(state, EVENT_CLASS_GAIN, "You reopen your ledger where you left it.")
    return "You reopen your ledger where you left it."


def buy_goods(state: GameState, good_key: str, amount: int) -> bool:
    if amount <= 0:
        set_event(state, EVENT_CLASS_INFO, "No deal. The broker folds his hands and finds a less cautious fool.")
        return False
    if amount > state.free_capacity():
        set_event(state, EVENT_CLASS_WARNING, "Your satchel and cart space will not take that much weight.")
        return False
    price = state.prices[good_key] * amount
    if price > state.purse:
        set_event(state, EVENT_CLASS_DANGER, "You count your denarii twice and still come up short.")
        return False
    state.purse -= price
    state.carried[good_key] += amount
    state.last_trade_value = price
    state.last_trade_volume = amount
    if state.suspicion < 100:
        state.suspicion = min(100, state.suspicion + (amount // 4) + 1)
    good_name = next(good.name for good in GOODS if good.key == good_key)
    set_event(state, EVENT_CLASS_INFO, f"You take delivery of {amount} lots of {good_name} and keep moving before anyone grows curious.")
    return True


def sell_goods(state: GameState, good_key: str, amount: int) -> bool:
    if amount <= 0:
        set_event(state, EVENT_CLASS_INFO, "No sale. Better to wait than sell like a frightened amateur.")
        return False
    if amount > state.carried[good_key]:
        set_event(state, EVENT_CLASS_WARNING, "You cannot sell cargo that never made it into your satchel.")
        return False
    revenue = state.prices[good_key] * amount
    state.purse += revenue
    state.carried[good_key] -= amount
    state.last_trade_value = revenue
    state.last_trade_volume = amount
    if state.suspicion < 100:
        state.suspicion = min(100, state.suspicion + (amount // 5) + 1)
    set_event(state, EVENT_CLASS_GAIN, f"The buyer pays without haggling. {amount} lots move for {revenue} denarii.")
    return True


def visit_counting_house(state: GameState, deposit: int | None = None, withdraw: int | None = None) -> None:
    if deposit is not None:
        if deposit <= 0:
            set_event(state, EVENT_CLASS_INFO, "Nothing changes hands in the counting house.")
        elif deposit > state.purse:
            set_event(state, EVENT_CLASS_WARNING, "The counting-house clerks admire your confidence more than your arithmetic.")
        else:
            state.purse -= deposit
            state.vault_balance += deposit
            set_event(state, EVENT_CLASS_INFO, "The counting house swallows your deposit under wax, ledger dust, and selective memory.")
    elif withdraw is not None:
        if withdraw <= 0:
            set_event(state, EVENT_CLASS_INFO, "Nothing changes hands in the counting house.")
        elif withdraw > state.vault_balance:
            set_event(state, EVENT_CLASS_WARNING, "The counting house refuses to imagine money that is not on your line.")
        else:
            state.vault_balance -= withdraw
            state.purse += withdraw
            set_event(state, EVENT_CLASS_INFO, "A clerk slides a pouch across the counter and pretends not to know your trade.")


def visit_house_varro(state: GameState, payment: int | None = None, borrow: int | None = None) -> None:
    if state.current_district != 1:
        set_event(state, EVENT_CLASS_WARNING, "House Varro keeps its table in the Forum and does not travel for small operators.")
        return
    if payment is not None:
        if payment <= 0:
            set_event(state, EVENT_CLASS_INFO, "Varro's slate remains exactly as ugly as it was.")
        elif payment > state.purse:
            set_event(state, EVENT_CLASS_DANGER, "Varro's collector smiles like a butcher. Insolence is free; repayment is not.")
        else:
            applied = min(payment, state.debt_to_varro)
            state.purse -= applied
            state.debt_to_varro -= applied
            if state.debt_to_varro <= 0:
                state.debt_to_varro = 0
                set_event(state, EVENT_CLASS_GAIN, "House Varro marks your slate clean. In Rome, that kind of mercy is usually temporary.")
            else:
                set_event(state, EVENT_CLASS_INFO, "Varro takes your coin, updates the slate, and decides not to improve your face.")
    elif borrow is not None:
        if state.debt_to_varro > 0:
            return
        if borrow <= 0:
            set_event(state, EVENT_CLASS_INFO, "Varro sees no point in moving coin for your indecision.")
        else:
            state.purse += borrow
            state.debt_to_varro += borrow
            state.days_left_on_note = 30
            set_event(state, EVENT_CLASS_WARNING, "Varro extends fresh credit, which is just another word for a cleaner leash.")


def move_goods_to_cache(state: GameState, good_key: str, amount: int, to_cache: bool) -> bool:
    if state.current_district != 1:
        set_event(state, EVENT_CLASS_WARNING, "Your hidden cache sits under Forum stone, not out here in borrowed shadows.")
        return False
    if amount <= 0:
        set_event(state, EVENT_CLASS_INFO, "No goods move. The cache keeps its silence.")
        return False
    good_name = next(good.name for good in GOODS if good.key == good_key)
    if to_cache:
        if amount > state.carried[good_key]:
            set_event(state, EVENT_CLASS_WARNING, "You do not have that much on hand to hide.")
            return False
        state.carried[good_key] -= amount
        state.cached[good_key] += amount
        set_event(state, EVENT_CLASS_INFO, f"You bury {amount} lots of {good_name} in the hidden cache and trust stone more than men.")
        return True
    if amount > state.cached[good_key]:
        set_event(state, EVENT_CLASS_WARNING, "Your cache does not hold that much of this cargo, no matter what the ledger says.")
        return False
    if amount > state.free_capacity():
        set_event(state, EVENT_CLASS_WARNING, "Your satchel will not carry that much weight back into the street.")
        return False
    state.cached[good_key] -= amount
    state.carried[good_key] += amount
    set_event(state, EVENT_CLASS_GAIN, f"You recover {amount} lots of {good_name} from the cache and take them back into circulation.")
    return True


def apply_capture_penalty(state: GameState, rng: random.Random) -> None:
    lost_days = rng.randrange(2, 6)
    seized_goods = state.carried_total()
    seized_purse = state.purse // 2

    state.day_number += lost_days
    state.days_left_on_note -= lost_days
    for _ in range(lost_days):
        if state.debt_to_varro > 0:
            state.debt_to_varro += note_daily_fee(state)

    state.suspicion = min(100, state.suspicion + 8)
    state.purse = seized_purse
    state.guards = 0
    for key in state.carried:
        state.carried[key] = 0

    set_event(state, EVENT_CLASS_DANGER, "The prefect's men catch you and throw you back into the street.")
    append_event(
        state,
        EVENT_CLASS_WARNING,
        f"Lost {lost_days} days, {seized_purse} denarii, and {seized_goods} lots of cargo.",
    )


def _cargo_base_value(state: GameState) -> int:
    """Total value of carried + cached cargo at each good's price_min."""
    total = 0
    for good in GOODS:
        held = state.carried.get(good.key, 0) + state.cached.get(good.key, 0)
        total += held * good.price_min
    return total


def should_varro_enforce(state: GameState, rng: random.Random, *, is_travel: bool = False) -> bool:
    """Check whether Varro's enforcers arrive this action.

    Trigger rules:
    - Guaranteed when ``days_left_on_note <= 0`` (overdue).
    - Guaranteed on travel when ``days_left_on_note == 1``
      (enforcers intercept at the gate before the day ticks).
    - Random 35 % chance per action when ``days_left_on_note == 0``.
    """
    if state.debt_to_varro <= 0:
        return False
    if state.days_left_on_note < 0:
        return True
    if state.days_left_on_note == 0:
        return rng.random() < 0.35
    if is_travel and state.days_left_on_note == 1:
        return True
    return False


def varro_enforcement(state: GameState, rng: random.Random) -> str:
    """Apply Varro's enforcement and return an outcome key.

    Outcomes:
    - ``"paid"``:  Player had enough liquid coin (purse + vault).
                   Money extracted, HP -> 1, percentage of property stolen,
                   debt stays.
    - ``"seized"``: Not enough coin but cargo base value >= debt.
                    All cargo seized, HP -> 1, debt stays.
    - ``"ruined"``: Neither coin nor cargo covers the debt.
                    Everything taken, game over.

    In all cases an enforcement surcharge is added to the debt.
    """
    debt = state.debt_to_varro
    liquid = state.purse + state.vault_balance
    cargo_val = _cargo_base_value(state)

    # Enforcement surcharge — you pay for the privilege of being roughed up.
    surcharge = max(50, debt // 5)
    state.debt_to_varro += surcharge

    # --- Outcome: player has liquid funds ---
    if liquid >= debt:
        # Extract the owed amount from purse first, then vault.
        remaining = debt
        taken_purse = min(state.purse, remaining)
        state.purse -= taken_purse
        remaining -= taken_purse
        if remaining > 0:
            state.vault_balance -= remaining

        state.health = 1

        # Steal 25-50 % of property (guards, carts, oxen).
        steal_pct = rng.uniform(0.25, 0.50)
        lost_guards = int(state.guards * steal_pct)
        lost_carts = int(state.self_cart_count * steal_pct)
        lost_oxen = int(state.self_oxen_count * steal_pct)
        state.guards = max(0, state.guards - lost_guards)
        state.self_cart_count = max(0, state.self_cart_count - lost_carts)
        state.self_oxen_count = max(0, state.self_oxen_count - lost_oxen)
        # Recalculate capacity: base 30 + 5 per cart + 3 per ox.
        state.capacity_total = 30 + (state.self_cart_count * 5) + (state.self_oxen_count * 3)

        set_event(state, EVENT_CLASS_DANGER,
                  "Varro's men find you before the market opens. They take what you owe and most of what you don't.")
        parts = [f"{debt} denarii extracted"]
        if lost_guards:
            parts.append(f"{lost_guards} guards scattered")
        if lost_carts:
            parts.append(f"{lost_carts} carts smashed")
        if lost_oxen:
            parts.append(f"{lost_oxen} oxen taken")
        append_event(state, EVENT_CLASS_WARNING, ", ".join(parts) + ".")
        append_event(state, EVENT_CLASS_DANGER,
                     f"Surcharge of {surcharge} denarii added. The debt does not forgive.")
        # Varro resets the clock — shorter leash this time.
        state.days_left_on_note = 15
        return "paid"

    # --- Outcome: cargo covers the debt ---
    if cargo_val >= debt:
        # Seize everything carried and cached.
        for key in state.carried:
            state.carried[key] = 0
        for key in state.cached:
            state.cached[key] = 0
        state.health = 1

        set_event(state, EVENT_CLASS_DANGER,
                  "Varro's enforcers strip your warehouse and your cart down to splinters.")
        append_event(state, EVENT_CLASS_WARNING,
                     f"All cargo seized (valued at ~{cargo_val}). You owe every denarius still.")
        append_event(state, EVENT_CLASS_DANGER,
                     f"Surcharge of {surcharge} denarii added. The ledger remembers what you wish it wouldn't.")
        # Varro resets the clock — shorter leash this time.
        state.days_left_on_note = 15
        return "seized"

    # --- Outcome: nothing covers the debt — ruined ---
    state.purse = 0
    state.vault_balance = 0
    for key in state.carried:
        state.carried[key] = 0
    for key in state.cached:
        state.cached[key] = 0
    state.guards = 0
    state.self_cart_count = 0
    state.self_oxen_count = 0
    state.capacity_total = 30
    state.health = 1

    set_event(state, EVENT_CLASS_DANGER,
              "Varro's men take everything. The cart, the cache, the coin, the name.")
    append_event(state, EVENT_CLASS_DANGER,
                 "You have nothing left to cover the note. Rome forgets you by morning.")
    return "ruined"


def begin_watch_encounter(state: GameState, watchmen: int) -> None:
    set_event(
        state,
        EVENT_CLASS_WARNING,
        f"The vigiles close in near the colonnade. There are {watchmen} of them deciding whether you look expensive.",
    )


def watch_encounter(state: GameState, rng: random.Random, watchmen: int, choice: str) -> None:
    action = choice.upper()
    if action not in {"F", "R", "B"}:
        action = "R"

    if action == "B":
        bribe = (watchmen * 18) + (state.suspicion // 2) + rng.randrange(25)
        if state.purse < bribe:
            set_event(
                state,
                EVENT_CLASS_DANGER,
                f"You reach for a bribe pouch, but {bribe} denarii buys more silence than you can afford.",
            )
            action = "R"
        else:
            state.purse -= bribe
            if state.suspicion > 5:
                state.suspicion -= 5
            set_event(
                state,
                EVENT_CLASS_WARNING,
                f"A purse of {bribe} denarii changes hands. The vigiles rediscover their love of looking elsewhere.",
            )
            return

    if action == "R":
        player_roll = rng.randrange(1, 21) + state.guards + (state.health // 20)
        watch_roll = rng.randrange(1, 21) + watchmen + district_watch_modifier(state) + (state.suspicion // 15)
        if player_roll >= watch_roll:
            if state.suspicion > 3:
                state.suspicion -= 3
            set_event(
                state,
                EVENT_CLASS_GAIN,
                "You vanish into torchlight, steam, and curses. The watch loses you in the confusion and your suspicion eases a little.",
            )
        else:
            apply_capture_penalty(state, rng)
        return

    player_roll = rng.randrange(1, 21) + state.guards + (state.health // 18)
    watch_roll = rng.randrange(1, 21) + watchmen + 3 + district_watch_modifier(state)
    if player_roll >= watch_roll:
        state.suspicion = min(100, state.suspicion + (10 if watchmen > 1 else 6))
        set_event(state, EVENT_CLASS_GAIN, "Steel flashes, sandals scrape stone, and somehow you are the one still walking.")
        return

    state.health -= rng.randrange(8, 26)
    if state.health <= 0:
        state.health = 0
        set_event(
            state,
            EVENT_CLASS_DANGER,
            "The watch leaves you bleeding under a shrine wall. Rome keeps the profit and spends none of it on mercy.",
        )
        return
    apply_capture_penalty(state, rng)


def maybe_watch_encounter(state: GameState, rng: random.Random) -> int:
    trigger = (
        state.last_trade_value >= 700
        or state.last_trade_volume >= 10
        or state.purse >= 2500
        or state.carried_total() >= 40
        or state.suspicion >= 45
    )
    if not trigger:
        return 0

    threshold = min(60, 8 + district_watch_modifier(state) + (state.suspicion // 3))
    chance = rng.randrange(1, 101)
    if chance <= threshold:
        return rng.randrange(2, 6) + district_watch_modifier(state)

    state.last_trade_value = 0
    state.last_trade_volume = 0
    return 0


def visit_sellswords(state: GameState) -> bool:
    if state.current_district != 1:
        set_event(state, EVENT_CLASS_WARNING, "The better blades keep their benches in the Forum, not out here in borrowed districts.")
        return False
    sync_progress_state(state)
    if not state.unlocks.sellswords:
        set_event(state, EVENT_CLASS_WARNING, "The better sellsword houses still see you as a small operator. Build more standing first.")
        return False
    price = 80 + (state.guards * 20)
    if state.purse < price:
        set_event(state, EVENT_CLASS_DANGER, "The broker listens to your offer, then listens to the weight of your purse and loses interest.")
        return False
    state.purse -= price
    state.guards += 1
    state.might_points += 1
    sync_progress_state(state)
    set_event(state, EVENT_CLASS_GAIN, "A new hired blade falls in behind you and waits to be pointed at the next problem.")
    append_event(state, EVENT_CLASS_GAIN, "[+1 hired blade]")
    return True


def visit_cartwright(state: GameState, buy_ox: bool = False) -> bool:
    if state.current_district != 1:
        set_event(state, EVENT_CLASS_WARNING, "The cartwright keeps his yard in the Forum, where wheels and gossip both travel farther.")
        return False
    sync_progress_state(state)
    if not state.unlocks.cartwright:
        set_event(state, EVENT_CLASS_WARNING, "No cartwright will extend you serious credit or timber until your name weighs more than your debt.")
        return False
    cart_cost = 140 + (state.self_cart_count * 90)
    ox_cost = 220 + (state.self_oxen_count * 120)
    if not buy_ox:
        if state.purse < cart_cost:
            set_event(state, EVENT_CLASS_DANGER, "The cartwright taps the timber and waits for coin you do not quite have.")
            return False
        state.purse -= cart_cost
        state.self_cart_count += 1
        state.capacity_total += 5
        state.prestige_points += 1
        sync_progress_state(state)
        set_event(state, EVENT_CLASS_GAIN, "A new handcart joins your operation, and suddenly Rome feels a little smaller.")
        append_event(state, EVENT_CLASS_GAIN, "[+1 cart, +5 capacity]")
        return True
    if state.self_cart_count <= state.self_oxen_count:
        set_event(state, EVENT_CLASS_WARNING, "An ox team is pointless without another cart to yoke it to.")
        return False
    if state.purse < ox_cost:
        set_event(state, EVENT_CLASS_DANGER, "The drover smiles sadly. Feed, rope, and muscle all cost more than your purse allows.")
        return False
    state.purse -= ox_cost
    state.self_oxen_count += 1
    state.capacity_total += 3
    state.prestige_points += 1
    state.might_points += 1
    sync_progress_state(state)
    set_event(state, EVENT_CLASS_GAIN, "A fresh ox team takes the strain out of your next haul.")
    append_event(state, EVENT_CLASS_GAIN, "[+1 ox team, +3 capacity]")
    return True


def travel_to_district(state: GameState, district_idx: int, rng: random.Random) -> bool:
    if district_idx < 1 or district_idx > len(DISTRICTS):
        set_event(state, EVENT_CLASS_INFO, "You linger where you are and let the district keep talking around you.")
        return False
    if district_idx == state.current_district:
        set_event(state, EVENT_CLASS_WARNING, "You are already there, and Rome is not known for rewarding indecision.")
        return False
    state.previous_district = state.current_district
    state.current_district = district_idx
    state.purse = max(0, state.purse - 3)
    state.event_log.clear()
    append_event(state, EVENT_CLASS_WARNING, "Travel costs you 3 denarii in fares, palms, and inconvenience.")
    roll = rng.randrange(100)
    if roll < 8:
        loss = 2 + rng.randrange(6)
        state.health = max(1, state.health - loss)
        append_event(state, EVENT_CLASS_DANGER, "You arrive bruised after a street scuffle that should have stayed verbal.")
    elif roll < 14:
        gain = 18 + rng.randrange(18)
        state.purse += gain
        append_event(state, EVENT_CLASS_GAIN, "A courier pays well for silence and a quick handoff made between checkpoints.")
    else:
        append_event(state, EVENT_CLASS_INFO, DISTRICTS[district_idx - 1].travel_line)
    apply_turn_upkeep(state)
    randomize_market_prices(state, rng)
    run_arrival_events(state, rng)
    save_game(state)
    return True


def show_scores() -> list[ScoreEntry]:
    return load_scores()


def update_scores(state: GameState) -> None:
    rows = load_scores()
    rows.append(ScoreEntry(name=state.username, value=state.net_worth()))
    rows.sort(key=lambda row: row.value, reverse=True)
    save_scores(rows[:5])


def pop_bestowals(state: GameState) -> list[BestowalNotice]:
    notices = list(state.identity.pending_bestowals)
    state.identity.pending_bestowals.clear()
    return notices


def option_action_complete(action: int) -> bool:
    return action not in (ACTION_NONE, ACTION_SCORES, ACTION_REDRAW, ACTION_QUIT)
