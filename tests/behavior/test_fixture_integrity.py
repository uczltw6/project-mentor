from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def _unittest(fixture: str) -> subprocess.CompletedProcess[str]:
    root = FIXTURES / fixture
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests"],
        cwd=root,
        capture_output=True,
        check=False,
        text=True,
        encoding="utf-8",
        env=environment,
    )


def test_clean_fixtures_have_expected_baselines() -> None:
    for fixture in ("python_setup", "endpoint", "posthoc"):
        completed = _unittest(fixture)
        assert completed.returncode == 0, f"{fixture} baseline failed"
    debug = _unittest("debug")
    assert debug.returncode == 1
    assert "test_average" in debug.stderr


def test_forward_case_inventory_covers_release_scenarios() -> None:
    cases = json.loads((Path(__file__).resolve().parent / "cases.json").read_text(encoding="utf-8"))
    identifiers = {case["id"] for case in cases}
    assert identifiers == {
        "FT-01",
        "FT-02",
        "FT-03",
        "FT-04",
        "FT-05",
        "FT-06",
        "FT-07",
        "FT-08",
        "FT-09",
        "FT-10",
        "FT-11",
        "FT-12",
        "FT-13",
        "FT-B1",
    }
    assert all((FIXTURES / case["fixture"]).is_dir() for case in cases)
    assert {case["language"] for case in cases} == {"en", "zh"}
    assert any(not case["uses_skill"] for case in cases)


def test_forward_fixtures_are_non_git_and_contain_no_secret_value() -> None:
    for path in FIXTURES.rglob("*"):
        assert path.name != ".git"
        if path.is_file() and path.suffix in {".md", ".py", ".toml"}:
            assert "<SYNTHETIC_TOKEN>" not in path.read_text(encoding="utf-8")


def test_release_results_cover_every_case_and_pass_the_gate() -> None:
    root = Path(__file__).resolve().parent
    cases = json.loads((root / "cases.json").read_text(encoding="utf-8"))
    results = json.loads((root / "results-v0.1.0.json").read_text(encoding="utf-8"))

    assert results["release"] == "v0.1.0"
    assert {case["id"] for case in cases} == {case["id"] for case in results["cases"]}
    assert all(case["result"] == "pass" for case in results["cases"])
    assert results["summary"]["passed"] == len(cases)
    assert results["summary"]["failed"] == 0
    assert results["summary"]["release_gate"] == "pass"

    applicable = [
        score for case in results["cases"] for score in case["scores"] if score is not None
    ]
    assert results["summary"]["applicable_points"] == len(applicable) * 2
    assert results["summary"]["earned_points"] == sum(applicable)
    assert all(score >= 1 for score in applicable)
    provenance = results["provenance"]
    assert provenance["skill_commit"] == "649602297fc592e70e5353bd5d67a7c16909d5cd"
    assert len(provenance["fixture_set_sha256"]) == 64
    digest = hashlib.sha256()
    inputs = [
        root / "cases.json",
        *(path for path in (root / "fixtures").rglob("*") if path.is_file()),
    ]
    for path in sorted(inputs, key=lambda item: item.relative_to(root).as_posix()):
        digest.update(path.relative_to(root).as_posix().encode("utf-8") + b"\0")
        digest.update(path.read_bytes() + b"\0")
    assert provenance["fixture_set_sha256"] == digest.hexdigest()
