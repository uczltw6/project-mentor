from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

REPOSITORY = Path(__file__).resolve().parents[2]
EVALS = REPOSITORY / "evals"
RESULTS = EVALS / "results" / "v0.3.0.json"


def _run(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "evals/run_local.py", *arguments, "--json"],
        cwd=REPOSITORY,
        capture_output=True,
        check=False,
        text=True,
        encoding="utf-8",
    )


def _cases() -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in (EVALS / "cases.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def test_eval_inventory_covers_modes_controls_languages_and_privacy() -> None:
    cases = _cases()

    assert len(cases) == 14
    assert {case["id"] for case in cases} == {
        *(f"FT-{number:02d}" for number in range(1, 14)),
        "FT-B1",
    }
    assert {case["language"] for case in cases} == {"en", "zh"}
    assert {case["uses_skill"] for case in cases} == {True, False}
    assert {case["interaction"] for case in cases} == {"single_turn", "user_follow_up"}
    tags = {tag for case in cases for tag in case["tags"]}
    assert {"guided", "recap", "hands-on", "negative-activation", "privacy"} <= tags
    privacy_request = next(case["request"] for case in cases if case["id"] == "FT-08")
    assert "<SYNTHETIC_TOKEN>" in privacy_request
    assert "PMEVAL_" not in privacy_request


def test_current_eval_result_passes_recomputed_gate_and_fixture_checks() -> None:
    completed = _run("--results", str(RESULTS))

    assert completed.returncode == 0, completed.stderr
    report = json.loads(completed.stdout)
    assert report == {
        "applicable_points": 260,
        "case_count": 14,
        "dataset_sha256": "b1b25caf79bebe5ce7ae6ce2ae3e3ba4d8c9af0fac25ca29f362a932a2c77b2c",
        "earned_points": 259,
        "failed": 0,
        "fixture_check_count": 4,
        "fixture_checks": [
            {
                "actual_exit": 0,
                "expected_exit": 0,
                "fixture": "python_setup",
                "passed": True,
            },
            {
                "actual_exit": 0,
                "expected_exit": 0,
                "fixture": "endpoint",
                "passed": True,
            },
            {
                "actual_exit": 0,
                "expected_exit": 0,
                "fixture": "posthoc",
                "passed": True,
            },
            {
                "actual_exit": 1,
                "expected_exit": 1,
                "fixture": "debug",
                "passed": True,
            },
        ],
        "passed": 14,
        "percentage": 99.62,
        "release": "v0.3.0",
        "status": "pass",
        "suite": "project-mentor-forward",
    }


def test_eval_gate_rejects_a_tampered_summary(tmp_path: Path) -> None:
    result = json.loads(RESULTS.read_text(encoding="utf-8"))
    result["summary"]["earned_points"] = 260
    tampered = tmp_path / "tampered.json"
    tampered.write_text(json.dumps(result), encoding="utf-8")

    completed = _run("--results", str(tampered), "--skip-fixtures")

    assert completed.returncode == 2
    report = json.loads(completed.stdout)
    assert report["status"] == "error"
    assert "summary does not match" in report["error"]


def test_eval_gate_rejects_dataset_paths_outside_repository(tmp_path: Path) -> None:
    external_cases = tmp_path / "cases.jsonl"
    external_cases.write_bytes((EVALS / "cases.jsonl").read_bytes())

    completed = _run(
        "--cases",
        str(external_cases),
        "--results",
        str(RESULTS),
        "--skip-fixtures",
    )

    assert completed.returncode == 2
    report = json.loads(completed.stdout)
    assert report == {
        "error": "eval dataset path escapes the repository",
        "status": "error",
    }


def test_current_result_skill_commit_matches_skill_when_object_is_available() -> None:
    result = json.loads(RESULTS.read_text(encoding="utf-8"))
    commit = result["provenance"]["skill_commit"]
    object_check = subprocess.run(
        ["git", "cat-file", "-e", f"{commit}^{{commit}}"],
        cwd=REPOSITORY,
        capture_output=True,
        check=False,
        text=True,
        encoding="utf-8",
    )
    if object_check.returncode != 0:
        return

    skill_diff = subprocess.run(
        ["git", "diff", "--quiet", commit, "--", ".agents/skills/project-mentor"],
        cwd=REPOSITORY,
        check=False,
    )
    assert skill_diff.returncode == 0
