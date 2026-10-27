#!/usr/bin/env python3
"""Build the static call log dashboard and a page for each configured location."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from voice_receptionist.config import ConfigError, load_config  # noqa: E402
from voice_receptionist.site import build_site  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=str(ROOT / "config" / "demo-clinics.json"))
    parser.add_argument("--calls", default=str(ROOT / "fixtures" / "call-log.json"))
    parser.add_argument("--out", default=str(ROOT / "out"))
    args = parser.parse_args()
    try:
        config = load_config(args.config)
        written = build_site(config, args.calls, args.out)
        print(f"Built {len(written)} files in {Path(args.out)}")
        for path in written:
            print(f"  {path}")
        return 0
    except (ConfigError, OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
