from __future__ import annotations

import io
import json
import subprocess
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest
from conftest import assert_no_secret
from mentor_core import cli


class StdinBytes:
    def __init__(self, value: bytes) -> None:
        self.buffer = io.BytesIO(value)


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")


def test_complete_cli_lifecycle_is_deterministic_and_atomic(
    tmp_path: Path,
    concept: dict[str, Any],
    evidence: dict[str, Any],
    demonstration: dict[str, Any],
    event_factory: Any,
    capsys: Any,
) -> None:
    directory = tmp_path / "path with spaces" / "项目"
    directory.mkdir(parents=True)
    ledger_path = directory / "ledger.json"
    assert (
        cli.main(
            [
                "init",
                "--goal",
                "运行示例",
                "--session-id",
                "pm-cli-session",
                "--created-at",
                "2026-08-01T00:00:00Z",
                "--vcs",
                "none",
                "--output",
                str(ledger_path),
            ]
        )
        == 0
    )
    capsys.readouterr()

    concept_event = event_factory(
        "concept_identified", {"concept": concept}, event_id="evt-concept-001"
    )
    event_path = directory / "event.json"
    _write_json(event_path, concept_event)
    assert (
        cli.main(
            [
                "apply-event",
                "--ledger",
                str(ledger_path),
                "--event",
                str(event_path),
                "--expected-revision",
                "0",
            ]
        )
        == 0
    )
    assert json.loads(capsys.readouterr().out)["replayed"] is False
    assert (
        cli.main(
            [
                "apply-event",
                "--ledger",
                str(ledger_path),
                "--event",
                str(event_path),
                "--expected-revision",
                "1",
            ]
        )
        == 0
    )
    assert json.loads(capsys.readouterr().out)["replayed"] is True

    synthetic = "test_" + "t" * 32
    evidence["kind"] = "command"
    evidence["locator"] = "API_KEY=" + synthetic + " python run.py"
    events = [
        event_factory(
            "project_evidence_added",
            {"concept_id": concept["id"], "evidence": evidence},
            event_id="evt-evidence-001",
            timestamp="2026-08-01T00:02:00Z",
        ),
        event_factory(
            "mode_changed",
            {"mode": "hands_on", "reason": "Let the user try."},
            event_id="evt-mode-001",
            timestamp="2026-08-01T00:03:00Z",
            actor="user",
        ),
        event_factory(
            "user_evidence_added",
            {"concept_id": concept["id"], "demonstration": demonstration},
            event_id="evt-user-001",
            timestamp="2026-08-01T00:04:00Z",
            actor="user",
        ),
    ]
    for revision, event in enumerate(events, start=1):
        _write_json(event_path, event)
        assert (
            cli.main(
                [
                    "apply-event",
                    "--ledger",
                    str(ledger_path),
                    "--event",
                    str(event_path),
                    "--expected-revision",
                    str(revision),
                ]
            )
            == 0
        )
        capsys.readouterr()

    assert cli.main(["validate", "--kind", "ledger", "--input", str(ledger_path)]) == 0
    assert "valid ledger" in capsys.readouterr().out
    first = directory / "receipt-en-1.md"
    second = directory / "receipt-en-2.md"
    chinese = directory / "receipt-zh.md"
    for output in (first, second):
        assert (
            cli.main(
                [
                    "render",
                    "--ledger",
                    str(ledger_path),
                    "--rendered-at",
                    "2026-08-01T00:10:00Z",
                    "--output",
                    str(output),
                ]
            )
            == 0
        )
    assert first.read_bytes() == second.read_bytes()
    assert (
        cli.main(
            [
                "render",
                "--ledger",
                str(ledger_path),
                "--language",
                "zh",
                "--rendered-at",
                "2026-08-01T00:10:00Z",
                "--output",
                str(chinese),
            ]
        )
        == 0
    )
    summary = directory / "summary.json"
    assert cli.main(["summarize", "--ledger", str(ledger_path), "--output", str(summary)]) == 0
    persisted = ledger_path.read_text(encoding="utf-8")
    combined = persisted + first.read_text(encoding="utf-8") + summary.read_text(encoding="utf-8")
    assert_no_secret(combined, synthetic)
    assert "REDACTED" in combined
    assert "已完成的工作" in chinese.read_text(encoding="utf-8")

    before = ledger_path.read_bytes()
    conflict = deepcopy(concept_event)
    conflict["payload"]["concept"]["title"] = "Conflicting title"
    _write_json(event_path, conflict)
    assert (
        cli.main(
            [
                "apply-event",
                "--ledger",
                str(ledger_path),
                "--event",
                str(event_path),
                "--expected-revision",
                "4",
            ]
        )
        == 5
    )
    assert ledger_path.read_bytes() == before
    assert "Traceback" not in capsys.readouterr().err


def test_cli_accepts_stdin_for_event_and_redaction(
    tmp_path: Path,
    concept: dict[str, Any],
    event_factory: Any,
    monkeypatch: pytest.MonkeyPatch,
    capsys: Any,
) -> None:
    ledger = tmp_path / "ledger.json"
    assert (
        cli.main(
            [
                "init",
                "--goal",
                "Run sample",
                "--session-id",
                "pm-stdin-session",
                "--created-at",
                "2026-08-01T00:00:00Z",
                "--output",
                str(ledger),
            ]
        )
        == 0
    )
    capsys.readouterr()
    event = event_factory("concept_identified", {"concept": concept})
    monkeypatch.setattr("sys.stdin", StdinBytes(json.dumps(event).encode()))
    assert (
        cli.main(
            [
                "apply-event",
                "--ledger",
                str(ledger),
                "--event",
                "-",
                "--expected-revision",
                "0",
            ]
        )
        == 0
    )
    capsys.readouterr()
    secret = "v" * 32
    monkeypatch.setattr("sys.stdin", StdinBytes(("PASSWORD=" + secret).encode()))
    assert cli.main(["redact", "--input", "-", "--output", "-"]) == 0
    output = capsys.readouterr().out
    assert_no_secret(output, secret)
    assert "[REDACTED]" in output


@pytest.mark.parametrize(
    ("arguments", "expected"),
    [
        (["validate", "--kind", "ledger", "--input", "missing.json"], 4),
        (["apply-event", "--ledger", "-", "--expected-revision", "0"], 2),
        (
            [
                "init",
                "--goal",
                "Run",
                "--session-id",
                "bad id",
                "--created-at",
                "2026-08-01T00:00:00Z",
            ],
            2,
        ),
    ],
)
def test_expected_cli_errors_have_stable_codes_without_tracebacks(
    arguments: list[str], expected: int, capsys: Any
) -> None:
    assert cli.main(arguments) == expected
    assert "Traceback" not in capsys.readouterr().err


def test_unexpected_cli_error_is_hidden_unless_debugged(
    monkeypatch: pytest.MonkeyPatch, capsys: Any
) -> None:
    def fail_new_ledger(**kwargs: Any) -> dict[str, Any]:
        raise RuntimeError("controlled")

    monkeypatch.setattr(cli, "new_ledger", fail_new_ledger)
    arguments = [
        "init",
        "--goal",
        "Run",
        "--session-id",
        "pm-debug-session",
        "--created-at",
        "2026-08-01T00:00:00Z",
    ]
    assert cli.main(arguments) == 1
    assert "unexpected failure" in capsys.readouterr().err
    with pytest.raises(RuntimeError, match="controlled"):
        cli.main(["--debug", *arguments])


def test_entry_script_help_runs_without_installing_package() -> None:
    entry = (
        Path(__file__).resolve().parents[2]
        / ".agents"
        / "skills"
        / "project-mentor"
        / "scripts"
        / "project_mentor.py"
    )
    completed = subprocess.run(
        [sys.executable, str(entry), "--help"],
        capture_output=True,
        check=False,
        text=True,
        encoding="utf-8",
    )
    assert completed.returncode == 0
    assert "apply-event" in completed.stdout and "render" in completed.stdout
