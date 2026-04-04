"""Shared UI asset helpers."""

from __future__ import annotations

from pathlib import Path


def repo_resources_root() -> Path:
    return Path(__file__).resolve().parents[4]


def intro_base_path() -> Path:
    return repo_resources_root() / "scripts" / "smuggler" / "intro"
