#!/usr/bin/env python3
"""Print Retell payloads by default, or create agents with an explicit opt-in."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from voice_receptionist.config import ConfigError, load_config  # noqa: E402
from voice_receptionist.payloads import dry_run_bundle  # noqa: E402
from voice_receptionist.retell import RetellClient, RetellError  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=str(ROOT / "config" / "demo-clinics.json"))
    parser.add_argument("--apply", action="store_true", help="Make Retell API calls")
    parser.add_argument("--confirm", default="", help="Required with --apply. Must equal CREATE.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        config = load_config(args.config)
        if not args.apply:
            print("DRY RUN: no network calls will be made")
            for location in config["locations"]:
                print(json.dumps(dry_run_bundle(config, location), indent=2, ensure_ascii=True))
            print(f"Generated {len(config['locations'])} location payloads")
            return 0

        if args.confirm != "CREATE":
            print("Refusing live creation. Pass --apply --confirm CREATE.", file=sys.stderr)
            return 2
        client = RetellClient(os.environ.get("RETELL_API_KEY", ""))
        print("LIVE MODE: creating Retell resources")
        for location in config["locations"]:
            result = client.create_location(config, location)
            print(f"Created {result['location_id']}")
            print(f"export {location['retell']['agent_id_env']}={result['agent_id']}")
            print(f"export {location['retell']['llm_id_env']}={result['llm_id']}")
        print("Store these values outside the repository before closing this terminal.")
        return 0
    except (ConfigError, RetellError, OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
