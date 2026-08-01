from __future__ import annotations

import json
import subprocess
import sys
from importlib import metadata
from pathlib import Path

import project_mentor_cli


def test_distribution_metadata_and_console_entry_point_are_coherent() -> None:
    assert metadata.version("project-mentor") == project_mentor_cli.__version__ == "0.3.0"
    entry = next(
        item
        for item in metadata.entry_points(group="console_scripts")
        if item.name == "project-mentor" and item.dist.name == "project-mentor"
    )
    assert entry.value == "project_mentor_cli.cli:main"
    assert entry.load().__name__ == "main"


def test_module_entry_point_reports_public_cli_name_and_version() -> None:
    completed = subprocess.run(
        [sys.executable, "-m", "project_mentor_cli", "--version"],
        capture_output=True,
        check=False,
        text=True,
        encoding="utf-8",
    )
    assert completed.returncode == 0
    assert completed.stdout.strip() == "project-mentor 0.3.0"
    assert completed.stderr == ""


def test_installed_module_entry_point_can_create_and_validate_a_ledger(tmp_path: Path) -> None:
    ledger = tmp_path / "ledger.json"
    initialized = subprocess.run(
        [
            sys.executable,
            "-m",
            "project_mentor_cli",
            "init",
            "--goal",
            "Package smoke test",
            "--session-id",
            "pm-package-smoke",
            "--created-at",
            "2026-08-01T00:00:00Z",
            "--output",
            str(ledger),
        ],
        capture_output=True,
        check=False,
        text=True,
        encoding="utf-8",
    )
    assert initialized.returncode == 0
    assert json.loads(ledger.read_text(encoding="utf-8"))["session"]["id"] == "pm-package-smoke"
    validated = subprocess.run(
        [
            sys.executable,
            "-m",
            "project_mentor_cli",
            "validate",
            "--kind",
            "ledger",
            "--input",
            str(ledger),
        ],
        capture_output=True,
        check=False,
        text=True,
        encoding="utf-8",
    )
    assert validated.returncode == 0
    assert validated.stdout.strip() == "valid ledger schema_version=1"
