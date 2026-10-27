from __future__ import annotations

import copy
from pathlib import Path

from voice_receptionist.audit import audit_mock, audit_snapshots
from voice_receptionist.config import load_config
from voice_receptionist.payloads import desired_snapshot

ROOT = Path(__file__).resolve().parents[1]


def test_mock_audit_finds_intentional_voice_and_greeting_drift() -> None:
    config = load_config(ROOT / "config" / "demo-clinics.json")
    report = audit_mock(config, ROOT / "fixtures" / "mock-live-agents.json")
    assert report["matching_locations"] == 1
    assert report["drifted_locations"] == 1
    issues = report["results"][1]["issues"]
    assert {issue["field"] for issue in issues} == {"agent.voice_id", "llm.begin_message"}


def test_exact_desired_snapshots_all_match() -> None:
    config = load_config(ROOT / "config" / "demo-clinics.json")
    snapshots = {
        location["id"]: copy.deepcopy(desired_snapshot(config, location))
        for location in config["locations"]
    }
    report = audit_snapshots(config, snapshots)
    assert report["matching_locations"] == 2
    assert report["drifted_locations"] == 0
