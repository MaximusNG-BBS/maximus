#!/usr/bin/env python3
"""Smuggler of Rome door entrypoint."""

from __future__ import annotations

import os
import sys


HERE = os.path.dirname(os.path.abspath(__file__))
LOCAL_DOORKIT_PYZ = os.path.join(HERE, "notorious_doorkit.pyz")

if not os.path.exists(LOCAL_DOORKIT_PYZ):
    raise SystemExit(f"Missing bundled DoorKit archive: {LOCAL_DOORKIT_PYZ}")

for entry in reversed((LOCAL_DOORKIT_PYZ, HERE)):
    if entry in sys.path:
        sys.path.remove(entry)
    sys.path.insert(0, entry)

from smuggler_game.app import main


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
