from __future__ import annotations

from pathlib import Path

from voice_receptionist.config import load_config
from voice_receptionist.site import build_site

ROOT = Path(__file__).resolve().parents[1]


def test_builds_index_and_page_per_location(tmp_path: Path) -> None:
    config = load_config(ROOT / "config" / "demo-clinics.json")
    written = build_site(config, ROOT / "fixtures" / "call-log.json", tmp_path / "out")
    assert len(written) == 4
    index = (tmp_path / "out" / "index.html").read_text(encoding="utf-8")
    dental = (tmp_path / "out" / "northwind-dental-riverside" / "index.html").read_text(encoding="utf-8")
    med_spa = (tmp_path / "out" / "harbor-glow-medical-spa" / "index.html").read_text(encoding="utf-8")
    assert "Northwind Dental Studio" in index
    assert "Harbor Glow Medical Spa" in index
    assert "Jamie Rivera" in dental
    assert "Casey Morgan" not in dental
    assert "Casey Morgan" in med_spa
    assert "No clinical advice" in med_spa


def test_generated_html_contains_no_long_dash_characters(tmp_path: Path) -> None:
    config = load_config(ROOT / "config" / "demo-clinics.json")
    written = build_site(config, ROOT / "fixtures" / "call-log.json", tmp_path / "out")
    html_files = [path for path in written if path.suffix == ".html"]
    for path in html_files:
        content = path.read_text(encoding="utf-8")
        assert "—" not in content
        assert "–" not in content
