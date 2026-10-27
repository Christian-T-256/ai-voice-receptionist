from __future__ import annotations

from pathlib import Path

from voice_receptionist.config import load_config
from voice_receptionist.payloads import dry_run_bundle
from voice_receptionist.prompt import render_prompt

ROOT = Path(__file__).resolve().parents[1]


def test_prompt_contains_required_safety_boundaries() -> None:
    config = load_config(ROOT / "config" / "demo-clinics.json")
    prompt = render_prompt(config["locations"][0], config["retell"]["model"])
    assert "Do not diagnose" in prompt
    assert "call 911" in prompt
    assert "Never say an appointment is confirmed" in prompt
    assert "Do not request a medical history" in prompt
    assert "Monday: 08:00 to 17:00" in prompt


def test_services_do_not_cross_between_practice_types() -> None:
    config = load_config(ROOT / "config" / "demo-clinics.json")
    dental = render_prompt(config["locations"][0], config["retell"]["model"])
    med_spa = render_prompt(config["locations"][1], config["retell"]["model"])
    assert "routine cleaning" in dental
    assert "facial treatment" not in dental
    assert "facial treatment" in med_spa
    assert "toothache evaluation" not in med_spa


def test_dry_run_bundle_has_no_real_resource_ids() -> None:
    config = load_config(ROOT / "config" / "demo-clinics.json")
    bundle = dry_run_bundle(config, config["locations"][0])
    assert bundle["create_agent"]["body"]["response_engine"]["llm_id"] == "<created_llm_id>"
    assert bundle["create_llm"]["path"] == "/create-retell-llm"
