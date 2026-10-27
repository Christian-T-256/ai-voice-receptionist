from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_create_cli_defaults_to_dry_run_without_api_key() -> None:
    env = os.environ.copy()
    env.pop("RETELL_API_KEY", None)
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "create_agents.py")],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "DRY RUN: no network calls" in result.stdout
    assert "Generated 2 location payloads" in result.stdout


def test_audit_cli_returns_nonzero_when_drift_exists() -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "audit_agents.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 1
    assert "Drift: 1" in result.stdout
