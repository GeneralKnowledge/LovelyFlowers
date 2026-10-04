#!/usr/bin/env python3
"""Render a standalone Sine Farm morph preview gallery (does not change gameplay).

Usage:
  SDL_VIDEODRIVER=dummy python3 scripts/morph_preview.py
  python3 scripts/morph_preview.py --out data/previews/sine_farm_morph.png
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

# Prefer headless-friendly defaults for CI / cloud agents
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from procgen.morph import demo_catalog  # noqa: E402
from procgen.preview import save_gallery  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Sine Farm morph visual preview")
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT / "data" / "previews" / "sine_farm_morph.png",
        help="Output PNG path",
    )
    parser.add_argument("--cols", type=int, default=4)
    args = parser.parse_args()

    morphs = demo_catalog()
    path = save_gallery(args.out, morphs=morphs, cols=args.cols)
    print(f"Wrote {path} ({len(morphs)} plants)")


if __name__ == "__main__":
    main()
