"""Dataclasses for Smuggler game state."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from .constants import (
    ARMOR_NONE,
    DISTRICT_COUNT,
    EVENT_CLASS_INFO,
    SWORD_NONE,
    TRADER_SLOTS,
)
from .data import DISTRICTS, GOODS


def default_goods_map() -> dict[str, int]:
    return {good.key: 0 for good in GOODS}


def default_prices_map() -> dict[str, int]:
    return {good.key: good.price_min for good in GOODS}


@dataclass
class EventEntry:
    level: str = EVENT_CLASS_INFO
    message: str = ""


@dataclass
class EventLog:
    headline: str = ""
    entries: list[EventEntry] = field(default_factory=list)

    def clear(self) -> None:
        self.headline = ""
        self.entries.clear()


@dataclass
class IdentityInventory:
    pretitles: dict[str, list[str]] = field(default_factory=dict)
    nicknames: dict[str, list[str]] = field(default_factory=dict)
    titles: dict[str, list[str]] = field(default_factory=dict)


@dataclass
class NotorietyState:
    kills: int = 0
    guard_fights: int = 0
    silencing_actions: int = 0
    rackets: int = 0


@dataclass
class BestowalNotice:
    component: str = ""
    category: str = ""
    text: str = ""
    value: str = ""
    forced: bool = False


@dataclass
class SpecialOffer:
    kind: str = ""
    title: str = ""
    prompt: str = ""
    price: int = 0
    good_key: str = ""
    lots: int = 0
    extra_capacity: int = 0
    guard_count: int = 0
    accept_msg: str = ""
    decline_msg: str = ""


@dataclass
class IdentityState:
    active_pretitle: str = ""
    active_nickname: str = ""
    active_title: str = ""
    dominant_axis: str = "prestige"
    inventory: IdentityInventory = field(default_factory=IdentityInventory)
    notoriety: NotorietyState = field(default_factory=NotorietyState)
    pending_bestowals: list[BestowalNotice] = field(default_factory=list)


@dataclass
class UnlockState:
    sellswords: bool = False
    cartwright: bool = False
    warehouse: bool = False
    property: bool = False
    traders: bool = False


@dataclass
class TraderState:
    active: bool = False
    route_from: int = 1
    route_to: int = 1
    goods_mask: int = 0
    cut_pct: int = 0
    guards: int = 0
    carts: int = 0
    oxen: int = 0
    sword_tier: int = SWORD_NONE
    armor_tier: int = ARMOR_NONE


@dataclass
class ScoreEntry:
    name: str
    value: int


@dataclass
class GameState:
    version: int = 1
    username: str = "Caller"
    current_district: int = 1
    previous_district: int = 1
    day_number: int = 1
    days_left_on_note: int = 30
    health: int = 100
    suspicion: int = 8
    guards: int = 0
    capacity_total: int = 30
    purse: int = 500
    vault_balance: int = 0
    debt_to_varro: int = 750
    last_trade_value: int = 0
    last_trade_volume: int = 0
    pending_resume_advance: bool = False
    resumed_game: bool = False
    quit_requested: bool = False
    retired: bool = False
    prestige_points: int = 0
    influence_points: int = 0
    might_points: int = 0
    self_cart_count: int = 0
    self_oxen_count: int = 0
    self_sword_tier: int = SWORD_NONE
    self_armor_tier: int = ARMOR_NONE
    trader_slots_unlocked: int = 1
    prices: dict[str, int] = field(default_factory=default_prices_map)
    carried: dict[str, int] = field(default_factory=default_goods_map)
    cached: dict[str, int] = field(default_factory=default_goods_map)
    unlocks: UnlockState = field(default_factory=UnlockState)
    traders: list[TraderState] = field(default_factory=lambda: [TraderState() for _ in range(TRADER_SLOTS)])
    event_log: EventLog = field(default_factory=EventLog)
    identity: IdentityState = field(default_factory=IdentityState)
    pending_offers: list[SpecialOffer] = field(default_factory=list)

    def carried_total(self) -> int:
        return sum(self.carried.values())

    def cached_total(self) -> int:
        return sum(self.cached.values())

    def free_capacity(self) -> int:
        return self.capacity_total - self.carried_total()

    def net_worth(self) -> int:
        return self.purse + self.vault_balance - self.debt_to_varro

    def net_worth_abs(self) -> int:
        worth = self.net_worth()
        return worth if worth >= 0 else -worth

    def net_worth_text(self) -> str:
        worth = self.net_worth()
        if worth < 0:
            return f"-{abs(worth)}"
        return str(worth)

    def current_district_name(self) -> str:
        return DISTRICTS[self.current_district - 1].name

    def identity_text(self) -> str:
        parts = [
            self.identity.active_pretitle,
            self.username,
            self.identity.active_nickname,
            self.identity.active_title,
        ]
        return " ".join(part for part in parts if part).strip()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GameState":
        unlocks = UnlockState(**data.get("unlocks", {}))
        event_dict = data.get("event_log", {})
        event_log = EventLog(
            headline=event_dict.get("headline", ""),
            entries=[EventEntry(**entry) for entry in event_dict.get("entries", [])],
        )
        inv_dict = data.get("identity", {}).get("inventory", {})
        inventory = IdentityInventory(
            pretitles=inv_dict.get("pretitles", {}),
            nicknames=inv_dict.get("nicknames", {}),
            titles=inv_dict.get("titles", {}),
        )
        notoriety = NotorietyState(**data.get("identity", {}).get("notoriety", {}))
        identity = IdentityState(
            active_pretitle=data.get("identity", {}).get("active_pretitle", ""),
            active_nickname=data.get("identity", {}).get("active_nickname", ""),
            active_title=data.get("identity", {}).get("active_title", ""),
            dominant_axis=data.get("identity", {}).get("dominant_axis", "prestige"),
            inventory=inventory,
            notoriety=notoriety,
            pending_bestowals=[BestowalNotice(**row) for row in data.get("identity", {}).get("pending_bestowals", [])],
        )
        pending_offers = [SpecialOffer(**row) for row in data.get("pending_offers", [])]
        traders = [TraderState(**entry) for entry in data.get("traders", [])]
        if len(traders) < TRADER_SLOTS:
            traders.extend(TraderState() for _ in range(TRADER_SLOTS - len(traders)))
        prices = default_prices_map()
        prices.update(data.get("prices", {}))
        carried = default_goods_map()
        carried.update(data.get("carried", {}))
        cached = default_goods_map()
        cached.update(data.get("cached", {}))
        return cls(
            version=data.get("version", 1),
            username=data.get("username", "Caller"),
            current_district=data.get("current_district", 1),
            previous_district=data.get("previous_district", 1),
            day_number=data.get("day_number", 1),
            days_left_on_note=data.get("days_left_on_note", 30),
            health=data.get("health", 100),
            suspicion=data.get("suspicion", 8),
            guards=data.get("guards", 0),
            capacity_total=data.get("capacity_total", 30),
            purse=data.get("purse", 500),
            vault_balance=data.get("vault_balance", 0),
            debt_to_varro=data.get("debt_to_varro", 750),
            last_trade_value=data.get("last_trade_value", 0),
            last_trade_volume=data.get("last_trade_volume", 0),
            pending_resume_advance=data.get("pending_resume_advance", False),
            resumed_game=data.get("resumed_game", False),
            quit_requested=data.get("quit_requested", False),
            retired=data.get("retired", False),
            prestige_points=data.get("prestige_points", 0),
            influence_points=data.get("influence_points", 0),
            might_points=data.get("might_points", 0),
            self_cart_count=data.get("self_cart_count", 0),
            self_oxen_count=data.get("self_oxen_count", 0),
            self_sword_tier=data.get("self_sword_tier", SWORD_NONE),
            self_armor_tier=data.get("self_armor_tier", ARMOR_NONE),
            trader_slots_unlocked=data.get("trader_slots_unlocked", 1),
            prices=prices,
            carried=carried,
            cached=cached,
            unlocks=unlocks,
            traders=traders[:TRADER_SLOTS],
            event_log=event_log,
            identity=identity,
            pending_offers=pending_offers,
        )
