#!/usr/bin/env python3
"""Validate Project Mentor eval data, stored grades, and deterministic fixtures."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

from graders import EvalContractError, dataset_digest, grade_run, load_cases, load_json

EVALS = Path(__file__).resolve().parent
REPOSITORY = EVALS.parent
DEFAULT_CASES = EVALS / "cases.jsonl"
DEFAULT_RUBRIC = EVALS / "rubric.json"
DEFAULT_FIXTURES = REPOSITORY / "tests" / "behavior" / "fixtures"
DEFAULT_RESULTS = EVALS / "results" / "v0.3.0.json"
FIXTURE_CONTRACTS: dict[str, tuple[int, str | None]] = {
    "python_setup": (0, None),
    "endpoint": (0, None),
    "posthoc": (0, None),
    "debug": (1, "test_average"),
}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    parser.add_argument("--rubric", type=Path, default=DEFAULT_RUBRIC)
    parser.add_argument("--fixtures", type=Path, default=DEFAULT_FIXTURES)
    parser.add_argument("--results", type=Path, default=DEFAULT_RESULTS)
    parser.add_argument("--skip-fixtures", action="store_true")
    parser.add_argument("--json", action="store_true", help="Emit a machine-readable summary")
    return parser.parse_args(argv)


def _fixture_check(root: Path, name: str) -> dict[str, object]:
    expected_exit, required_text = FIXTURE_CONTRACTS[name]
    fixture = root / name
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    completed = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests"],
        cwd=fixture,
        capture_output=True,
        check=False,
        text=True,
        encoding="utf-8",
        env=environment,
        timeout=30,
    )
    combined = completed.stdout + completed.stderr
    passed = completed.returncode == expected_exit and (
        required_text is None or required_text in combined
    )
    return {
        "fixture": name,
        "passed": passed,
        "actual_exit": completed.returncode,
        "expected_exit": expected_exit,
    }


def run(argv: list[str] | None = None) -> tuple[int, dict[str, object]]:
    args = parse_args(argv)
    try:
        cases = load_cases(args.cases)
        rubric = load_json(args.rubric)
        results = load_json(args.results)
        digest = dataset_digest(
            repository=REPOSITORY,
            cases=args.cases,
            rubric=args.rubric,
            fixtures=args.fixtures,
        )
        grade = grade_run(
            cases=cases,
            rubric=rubric,
            results=results,
            expected_digest=digest,
        )
        case_fixtures = {case["fixture"] for case in cases}
        if case_fixtures != set(FIXTURE_CONTRACTS):
            raise EvalContractError("eval cases must cover exactly the declared fixture contracts")
        fixture_checks = (
            []
            if args.skip_fixtures
            else [_fixture_check(args.fixtures, name) for name in FIXTURE_CONTRACTS]
        )
        fixtures_passed = all(check["passed"] is True for check in fixture_checks)
        fixture_check_count = len(fixture_checks)
        status = "pass" if grade.release_gate == "pass" and fixtures_passed else "fail"
        report: dict[str, object] = {
            "status": status,
            "suite": results["suite"],
            "release": results["release"],
            "dataset_sha256": digest,
            "case_count": len(cases),
            "passed": grade.passed,
            "failed": grade.failed,
            "applicable_points": grade.applicable_points,
            "earned_points": grade.earned_points,
            "percentage": grade.percentage,
            "fixture_checks": fixture_checks,
            "fixture_check_count": fixture_check_count,
        }
        return (0 if status == "pass" else 1), report
    except (EvalContractError, OSError, subprocess.SubprocessError) as error:
        return 2, {"status": "error", "error": str(error)}


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    exit_code, report = run(argv)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    elif exit_code == 0:
        print(
            "evals: PASS "
            f"({report['passed']}/{report['case_count']} cases; "
            f"{report['earned_points']}/{report['applicable_points']} points; "
            f"{report['fixture_check_count']} fixture checks)"
        )
    elif exit_code == 1:
        print("evals: FAIL (release gate or fixture contract failed)", file=sys.stderr)
    else:
        print(f"evals: ERROR ({report['error']})", file=sys.stderr)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
