"""Static data definitions for Smuggler."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GoodDef:
    key: str
    name: str
    price_min: int
    price_span: int


@dataclass(frozen=True)
class DistrictDef:
    index: int
    key: str
    name: str
    tagline: str
    arrival_text: str
    service_note: str
    travel_line: str
    watch_modifier: int


GOODS: tuple[GoodDef, ...] = (
    GoodDef("wine", "Falernian Wine", 12, 28),
    GoodDef("incense", "Syrian Incense", 35, 65),
    GoodDef("resin", "Poppy Resin", 24, 55),
    GoodDef("silk", "Silk Bolts", 90, 150),
    GoodDef("seals", "Forged Seals", 70, 170),
    GoodDef("steel", "Legion Steel", 120, 230),
)


DISTRICTS: tuple[DistrictDef, ...] = (
    DistrictDef(
        1,
        "forum",
        "Forum District",
        "Forum stone remembers every debt and every favor.",
        "The Forum pretends to sleep, but ledgers and whispers still trade hands.",
        "Forum services are close: coin, debt, cache, and hard men.",
        "You cut back through the colonnades and return under borrowed dignity.",
        0,
    ),
    DistrictDef(
        2,
        "subura",
        "Subura",
        "Subura chews through men, rumor, and cheap courage.",
        "Subura is all smoke, alleys, and profit measured in bruises.",
        "Subura respects force faster than etiquette.",
        "The alleys narrow, the knives multiply, and Subura opens around you.",
        3,
    ),
    DistrictDef(
        3,
        "ostia",
        "Ostia Docks",
        "Ostia smells like rope, salt, and unverifiable cargo.",
        "At Ostia, every manifest lies a little and every hull hides something.",
        "The docks reward volume, nerve, and fast hands.",
        "The docks groan around you as Ostia tallies profit by the tide.",
        2,
    ),
    DistrictDef(
        4,
        "aventine",
        "Aventine",
        "Aventine coin moves quietly behind painted doors.",
        "Servants, terraces, and discreet luxuries keep Aventine fed after dark.",
        "Aventine likes luxury, discretion, and polished lies.",
        "Terrace lamps and servant traffic draw you into the Aventine night.",
        0,
    ),
    DistrictDef(
        5,
        "campus",
        "Campus Martius",
        "Campus Martius pays in sweat, wagers, and sudden bad decisions.",
        "Crowds, fighters, and quartermasters make Campus Martius loud and profitable.",
        "The Campus values swagger, steel, and momentum.",
        "Dust, wagers, and shouted boasts announce your arrival at the Campus.",
        1,
    ),
    DistrictDef(
        6,
        "palatine",
        "Palatine Shadows",
        "The Palatine never speaks plainly, only profitably.",
        "Behind curtained litters and sealed courtyards, the Palatine buys silence.",
        "The Palatine rewards secrecy, access, and controlled prestige.",
        "Curtains stir and sealed notes move as you slip into Palatine shadows.",
        2,
    ),
)


PRETITLE_BUCKETS: dict[str, tuple[str, ...]] = {
    "debt": ("Debitor", "Cliens"),
    "freed": ("Liber", "Solutus"),
    "prestige": ("Notus", "Patronus", "Nobilis"),
    "influence": ("Index", "Arbiter", "Palatinus"),
    "might": ("Latro", "Lanista", "Praefectus"),
    "logistics": ("Vector", "Plaustrarius", "Magister Cursuum"),
    "wealth": ("Mercator", "Princeps Mercatorum"),
}

NICKNAME_BUCKETS: dict[str, tuple[str, ...]] = {
    "prestige": ("Forumensis", "Marble-Born", "Patricius"),
    "influence": ("Quiet Hand", "Silentii", "Invisibilis"),
    "might": ("Knife-Hand", "Sanguis", "Knife Prince"),
    "logistics": ("Cart-Born", "Axle-Hand", "Road Binder"),
    "wealth": ("Coin-Hand", "Black Ledger", "Golden Scale"),
}

TITLE_BUCKETS: dict[str, tuple[str, ...]] = {
    "guards_small": ("the Brigand", "Shadow Escort"),
    "guards_medium": ("Captain of Blades", "Street Captain"),
    "guards_large": ("Prefect of Blood", "Lord of the Night Knives"),
    "guards_empire": ("Dominus Sanguinis", "Lord of Iron Shadows"),
    "routes_small": ("the Carrier", "of the Handcart"),
    "routes_medium": ("Master of Wagons", "the Wagoner"),
    "routes_large": ("Master of the Routes", "Route Binder"),
    "routes_empire": ("Princeps Viae", "Lord of the Long Haul"),
    "traders_medium": ("Broker of Agents", "Master of Factors"),
    "traders_large": ("Factorum Princeps", "Lord of Quiet Ledgers"),
    "traders_empire": ("Princeps Mercatorum", "Lord of a Hundred Hands"),
}
