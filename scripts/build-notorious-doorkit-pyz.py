#!/usr/bin/env python3
"""Build an importable .pyz bundle for notorious_doorkit."""

from __future__ import annotations

import shutil
import tempfile
import zipapp
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "notorious_doorkit"
OUTPUT_DIR = ROOT / "build" / "doors"
OUTPUT_FILE = OUTPUT_DIR / "notorious_doorkit.pyz"

MAIN_STUB = """\
from __future__ import annotations

import sys


def main() -> int:
    sys.stdout.write(
        "notorious_doorkit.pyz is an importable library bundle. "
        "Add it to PYTHONPATH or sys.path to use it.\\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
"""


def main() -> int:
    if not SOURCE_DIR.is_dir():
        raise SystemExit(f"missing source package: {SOURCE_DIR}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="ndk-pyz-") as tmp:
        staging = Path(tmp)
        shutil.copytree(SOURCE_DIR, staging / "notorious_doorkit")
        (staging / "__main__.py").write_text(MAIN_STUB, encoding="ascii")
        zipapp.create_archive(staging, target=OUTPUT_FILE, compressed=True)

    print(OUTPUT_FILE)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
