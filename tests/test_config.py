from __future__ import annotations

import copy
from pathlib import Path

import pytest

from voice_receptionist.config import ConfigError, load_config

ROOT = Path(__file__).resolve().parents[1]


def test_demo_config_has_two_valid_locations() -> None:
    config = load_config(ROOT / "config" / "demo-clinics.json")
    assert [location["practice_type"] for location in config["locations"]] == ["dental", "med_spa"]


def test_rejects_overlapping_hours(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    import json

    config = load_config(ROOT / "config" / "demo-clinics.json")
    broken = copy.deepcopy(config)
    broken["locations"][0]["hours"]["monday"] = [["08:00", "12:00"], ["11:00", "15:00"]]
    path = tmp_path / "broken.json"
    path.write_text(json.dumps(broken), encoding="utf-8")
    with pytest.raises(ConfigError, match="overlap"):
        load_config(path)


def test_rejects_unrecognized_booking_mode(tmp_path: Path) -> None:
    import json

    config = load_config(ROOT / "config" / "demo-clinics.json")
    config["locations"][0]["booking"]["mode"] = "pretend_confirmed"
    path = tmp_path / "broken.json"
    path.write_text(json.dumps(config), encoding="utf-8")
    with pytest.raises(ConfigError, match="booking.mode"):
        load_config(path)
