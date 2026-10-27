#!/usr/bin/env python3
"""Run the offline payload, drift, and dashboard demo end to end."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from voice_receptionist.audit import audit_mock, format_report  # noqa: E402
from voice_receptionist.config import load_config  # noqa: E402
from voice_receptionist.payloads import dry_run_bundle  # noqa: E402
from voice_receptionist.site import build_site  # noqa: E402


def main() -> int:
    config = load_config(ROOT / "config" / "demo-clinics.json")
    print("\n1. RETELL PAYLOAD DRY RUN")
    print("No network calls will be made.\n")
    for location in config["locations"]:
        print(json.dumps(dry_run_bundle(config, location), indent=2, ensure_ascii=True))

    print("\n2. MOCK LIVE DRIFT AUDIT")
    report = audit_mock(config, ROOT / "fixtures" / "mock-live-agents.json")
    print(format_report(report))
    if report["drifted_locations"] != 1:
        print("Demo expected exactly one intentionally drifted location.", file=sys.stderr)
        return 1

    print("\n3. STATIC DASHBOARD BUILD")
    written = build_site(config, ROOT / "fixtures" / "call-log.json", ROOT / "out")
    print(f"Built {len(written)} files in {ROOT / 'out'}")
    print("\nDemo complete. Open out/index.html in a browser.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
