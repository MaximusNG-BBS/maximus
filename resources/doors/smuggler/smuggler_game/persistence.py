"""JSON persistence for Smuggler."""

from __future__ import annotations

import json
from pathlib import Path

from .constants import SAVE_PREFIX, SCORE_FILE, SCORE_ROWS
from .models import GameState, ScoreEntry


def resource_root() -> Path:
    return Path(__file__).resolve().parent.parent


def save_root() -> Path:
    path = resource_root() / "data" / "saves"
    path.mkdir(parents=True, exist_ok=True)
    return path


def sanitize_name(name: str) -> str:
    out = "".join(ch.lower() if ch.isalnum() else "_" for ch in name.strip())
    out = "_".join(part for part in out.split("_") if part)
    return out[:24] or "caller"


def state_path_for(username: str) -> Path:
    return save_root() / f"{SAVE_PREFIX}{sanitize_name(username)}.json"


def load_game(username: str) -> GameState | None:
    path = state_path_for(username)
    if not path.exists():
        return None
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, json.JSONDecodeError):
        return None
    return GameState.from_dict(data)


def save_game(state: GameState) -> Path:
    path = state_path_for(state.username)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(state.to_dict(), handle, indent=2, sort_keys=True)
    return path


def delete_game(username: str) -> bool:
    """Remove a player's save file. Returns True if a file was deleted."""
    path = state_path_for(username)
    try:
        path.unlink(missing_ok=True)
        return True
    except OSError:
        return False


def score_path() -> Path:
    return save_root() / SCORE_FILE


def load_scores() -> list[ScoreEntry]:
    path = score_path()
    if not path.exists():
        return []
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, json.JSONDecodeError):
        return []
    out: list[ScoreEntry] = []
    for row in data:
        try:
            out.append(ScoreEntry(name=str(row["name"]), value=int(row["value"])))
        except (KeyError, TypeError, ValueError):
            continue
    return out[:SCORE_ROWS]


def save_scores(entries: list[ScoreEntry]) -> None:
    rows = [{"name": entry.name, "value": entry.value} for entry in entries[:SCORE_ROWS]]
    with score_path().open("w", encoding="utf-8") as handle:
        json.dump(rows, handle, indent=2, sort_keys=True)
