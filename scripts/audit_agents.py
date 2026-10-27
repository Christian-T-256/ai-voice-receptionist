#!/usr/bin/env python3
"""Audit mocked or live Retell agent state against the source configuration."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from voice_receptionist.audit import audit_live, audit_mock, format_report  # noqa: E402
from voice_receptionist.config import ConfigError, load_config  # noqa: E402
from voice_receptionist.retell import RetellError  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=str(ROOT / "config" / "demo-clinics.json"))
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--mock", default=str(ROOT / "fixtures" / "mock-live-agents.json"))
    source.add_argument("--live", action="store_true")
    parser.add_argument("--json", action="store_true", help="Print machine-readable results")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        config = load_config(args.config)
        report = audit_live(config) if args.live else audit_mock(config, args.mock)
        print(json.dumps(report, indent=2) if args.json else format_report(report))
        return 1 if report["drifted_locations"] else 0
    except (ConfigError, RetellError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
