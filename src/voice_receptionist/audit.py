"""Compare configured receptionist behavior with mocked or live Retell state."""

from __future__ import annotations

import copy
import hashlib
import json
import os
from pathlib import Path

from .payloads import desired_snapshot
from .retell import RetellClient, RetellError

AGENT_FIELDS = (
    "agent_name",
    "voice_id",
    "language",
    "responsiveness",
    "interruption_sensitivity",
    "enable_backchannel",
)
LLM_FIELDS = ("model", "general_prompt", "begin_message", "start_speaker")


def _set_dotted(target: dict, dotted_key: str, value) -> None:
    parts = dotted_key.split(".")
    cursor = target
    for part in parts[:-1]:
        cursor = cursor.setdefault(part, {})
    cursor[parts[-1]] = value


def _mock_snapshots(path: str | Path, config: dict) -> dict[str, dict]:
    fixture = json.loads(Path(path).read_text(encoding="utf-8"))
    configured = {location["id"]: location for location in config["locations"]}
    snapshots: dict[str, dict] = {}
    for entry in fixture.get("agents", []):
        location_id = entry["location_id"]
        if entry.get("inherit_desired"):
            if location_id not in configured:
                snapshots[location_id] = {"fixture_error": "unknown location"}
                continue
            snapshot = copy.deepcopy(desired_snapshot(config, configured[location_id]))
            for dotted_key, value in entry.get("overrides", {}).items():
                _set_dotted(snapshot, dotted_key, value)
        else:
            snapshot = {"agent": entry.get("agent", {}), "llm": entry.get("llm", {})}
        snapshots[location_id] = snapshot
    return snapshots


def _select_live_fields(raw: dict) -> dict:
    agent_raw = raw.get("agent", {})
    llm_raw = raw.get("llm", {})
    agent = {field: agent_raw.get(field) for field in AGENT_FIELDS}
    agent["response_engine"] = {"type": agent_raw.get("response_engine", {}).get("type")}
    llm = {field: llm_raw.get(field) for field in LLM_FIELDS}
    return {"agent": agent, "llm": llm}


def _display(value) -> str:
    if isinstance(value, str) and len(value) > 160:
        digest = hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]
        return f"sha256:{digest} ({len(value)} chars)"
    return json.dumps(value, ensure_ascii=True, sort_keys=True)


def _compare(expected: dict, actual: dict, prefix: str = "") -> list[dict]:
    issues: list[dict] = []
    for key, expected_value in expected.items():
        field = f"{prefix}.{key}" if prefix else key
        if key not in actual:
            issues.append({"field": field, "expected": _display(expected_value), "actual": "<missing>"})
        elif isinstance(expected_value, dict):
            actual_value = actual[key] if isinstance(actual[key], dict) else {}
            issues.extend(_compare(expected_value, actual_value, field))
        elif actual[key] != expected_value:
            issues.append({"field": field, "expected": _display(expected_value), "actual": _display(actual[key])})
    return issues


def audit_snapshots(config: dict, snapshots: dict[str, dict]) -> dict:
    results: list[dict] = []
    configured_ids = {location["id"] for location in config["locations"]}
    for location in config["locations"]:
        location_id = location["id"]
        expected = desired_snapshot(config, location)
        raw = snapshots.get(location_id)
        if raw is None:
            issues = [{"field": "location", "expected": "configured", "actual": "<missing>"}]
        elif "fixture_error" in raw:
            issues = [{"field": "fixture", "expected": "valid", "actual": raw["fixture_error"]}]
        else:
            issues = _compare(expected, _select_live_fields(raw))
        results.append({"location_id": location_id, "status": "DRIFT" if issues else "MATCH", "issues": issues})

    for unknown in sorted(set(snapshots) - configured_ids):
        results.append({
            "location_id": unknown,
            "status": "DRIFT",
            "issues": [{"field": "location", "expected": "<not configured>", "actual": "present"}],
        })
    drift_count = sum(1 for result in results if result["status"] == "DRIFT")
    return {
        "locations_audited": len(results),
        "matching_locations": len(results) - drift_count,
        "drifted_locations": drift_count,
        "results": results,
    }


def audit_mock(config: dict, mock_path: str | Path) -> dict:
    return audit_snapshots(config, _mock_snapshots(mock_path, config))


def audit_live(config: dict, client: RetellClient | None = None) -> dict:
    client = client or RetellClient(os.environ.get("RETELL_API_KEY", ""))
    snapshots: dict[str, dict] = {}
    for location in config["locations"]:
        agent_id = os.environ.get(location["retell"]["agent_id_env"], "")
        llm_id = os.environ.get(location["retell"]["llm_id_env"], "")
        if not agent_id or not llm_id:
            missing = [name for name, value in ((location["retell"]["agent_id_env"], agent_id), (location["retell"]["llm_id_env"], llm_id)) if not value]
            snapshots[location["id"]] = {"fixture_error": f"missing environment variables: {', '.join(missing)}"}
            continue
        try:
            snapshots[location["id"]] = client.fetch_location(agent_id, llm_id)
        except RetellError as exc:
            snapshots[location["id"]] = {"fixture_error": str(exc)}
    return audit_snapshots(config, snapshots)


def format_report(report: dict) -> str:
    lines = [
        "RETELL CONFIGURATION AUDIT",
        f"Locations: {report['locations_audited']} | Match: {report['matching_locations']} | Drift: {report['drifted_locations']}",
    ]
    for result in report["results"]:
        lines.append(f"[{result['status']}] {result['location_id']}")
        for issue in result["issues"]:
            lines.append(f"  {issue['field']}: expected {issue['expected']}; actual {issue['actual']}")
    return "\n".join(lines)
