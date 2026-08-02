"""Deterministic contract validation and scoring for Project Mentor evals."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

GENERATED_PARTS = frozenset({"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"})
GENERATED_SUFFIXES = frozenset({".pyc", ".pyo"})
CASE_ID = re.compile(r"FT-(?:\d{2}|B\d+)")


class EvalContractError(ValueError):
    """Raised when an eval artifact violates the public data contract."""


@dataclass(frozen=True)
class CaseGrade:
    identifier: str
    passed: bool
    applicable_points: int
    earned_points: int
    percentage: float
    failures: tuple[str, ...]


@dataclass(frozen=True)
class RunGrade:
    passed: int
    failed: int
    applicable_points: int
    earned_points: int
    percentage: float
    release_gate: str
    cases: tuple[CaseGrade, ...]


def _object(value: Any, *, label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or not all(isinstance(key, str) for key in value):
        raise EvalContractError(f"{label} must be a JSON object with string keys")
    return value


def _string(value: Any, *, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise EvalContractError(f"{label} must be a non-empty string")
    return value


def _string_list(value: Any, *, label: str) -> list[str]:
    if not isinstance(value, list) or not value or not all(isinstance(item, str) for item in value):
        raise EvalContractError(f"{label} must be a non-empty string list")
    if len(value) != len(set(value)):
        raise EvalContractError(f"{label} must not contain duplicates")
    return value


def load_json(path: Path) -> dict[str, Any]:
    try:
        return _object(json.loads(path.read_text(encoding="utf-8")), label=path.name)
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise EvalContractError(f"cannot read valid JSON from {path.name}") from error


def load_cases(path: Path) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as error:
        raise EvalContractError(f"cannot read eval cases from {path.name}") from error
    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            case = _object(json.loads(line), label=f"case line {line_number}")
        except json.JSONDecodeError as error:
            raise EvalContractError(f"invalid JSON on case line {line_number}") from error
        cases.append(case)
    if not cases:
        raise EvalContractError("eval case inventory must not be empty")
    return cases


def validate_rubric(rubric: dict[str, Any]) -> tuple[list[str], set[str], dict[str, int]]:
    if rubric.get("schema_version") != 1:
        raise EvalContractError("rubric schema_version must be 1")
    raw_dimensions = rubric.get("dimensions")
    if not isinstance(raw_dimensions, list) or not raw_dimensions:
        raise EvalContractError("rubric dimensions must be a non-empty list")
    dimensions: list[str] = []
    critical: set[str] = set()
    for index, value in enumerate(raw_dimensions):
        dimension = _object(value, label=f"rubric dimension {index}")
        identifier = _string(dimension.get("id"), label=f"rubric dimension {index} id")
        _string(dimension.get("description"), label=f"rubric dimension {identifier} description")
        if not isinstance(dimension.get("critical"), bool):
            raise EvalContractError(f"rubric dimension {identifier} critical must be boolean")
        dimensions.append(identifier)
        if dimension["critical"]:
            critical.add(identifier)
    if len(dimensions) != len(set(dimensions)):
        raise EvalContractError("rubric dimension ids must be unique")

    rule = _object(rubric.get("pass_rule"), label="rubric pass_rule")
    critical_score = rule.get("critical_score")
    minimum_score = rule.get("minimum_score")
    percentage = rule.get("minimum_percentage")
    if critical_score != 2:
        raise EvalContractError("critical_score must be 2")
    if minimum_score != 1:
        raise EvalContractError("minimum_score must be 1")
    if not isinstance(percentage, int) or not 1 <= percentage <= 100:
        raise EvalContractError("minimum_percentage must be an integer from 1 to 100")
    return (
        dimensions,
        critical,
        {
            "critical_score": 2,
            "minimum_score": 1,
            "minimum_percentage": percentage,
        },
    )


def validate_cases(cases: list[dict[str, Any]], dimensions: list[str]) -> None:
    identifiers: list[str] = []
    dimension_set = set(dimensions)
    for index, case in enumerate(cases):
        if case.get("schema_version") != 1:
            raise EvalContractError(f"case {index} schema_version must be 1")
        identifier = _string(case.get("id"), label=f"case {index} id")
        if CASE_ID.fullmatch(identifier) is None:
            raise EvalContractError(f"case id has an unsupported format: {identifier}")
        identifiers.append(identifier)
        _string(case.get("fixture"), label=f"case {identifier} fixture")
        language = _string(case.get("language"), label=f"case {identifier} language")
        if language not in {"en", "zh"}:
            raise EvalContractError(f"case {identifier} language must be en or zh")
        if not isinstance(case.get("uses_skill"), bool):
            raise EvalContractError(f"case {identifier} uses_skill must be boolean")
        request = _string(case.get("request"), label=f"case {identifier} request")
        if len(request) > 2_000:
            raise EvalContractError(f"case {identifier} request exceeds 2000 characters")
        applicable = _string_list(
            case.get("applicable_dimensions"), label=f"case {identifier} applicable_dimensions"
        )
        if not set(applicable) <= dimension_set:
            raise EvalContractError(f"case {identifier} uses an unknown rubric dimension")
        _string_list(case.get("tags"), label=f"case {identifier} tags")
        interaction = case.get("interaction", "single_turn")
        if interaction not in {"single_turn", "user_follow_up"}:
            raise EvalContractError(f"case {identifier} interaction is unsupported")
    if len(identifiers) != len(set(identifiers)):
        raise EvalContractError("eval case ids must be unique")
    if {case["language"] for case in cases} != {"en", "zh"}:
        raise EvalContractError("eval inventory must cover English and Chinese")
    if not any(case["uses_skill"] for case in cases):
        raise EvalContractError("eval inventory must include skill-enabled cases")
    if not any(not case["uses_skill"] for case in cases):
        raise EvalContractError("eval inventory must include a no-skill control")


def _fixture_files(fixtures: Path) -> list[Path]:
    return sorted(
        path
        for path in fixtures.rglob("*")
        if path.is_file()
        and not GENERATED_PARTS.intersection(path.parts)
        and path.suffix not in GENERATED_SUFFIXES
    )


def dataset_digest(*, repository: Path, cases: Path, rubric: Path, fixtures: Path) -> str:
    repository = repository.resolve()
    inputs = [
        cases.resolve(),
        rubric.resolve(),
        *[path.resolve() for path in _fixture_files(fixtures)],
    ]
    for path in inputs:
        if path != repository and repository not in path.parents:
            raise EvalContractError("eval dataset path escapes the repository")
    digest = hashlib.sha256()
    for path in sorted(inputs, key=lambda item: item.relative_to(repository).as_posix()):
        relative = path.relative_to(repository).as_posix()
        try:
            data = path.read_bytes()
        except OSError as error:
            raise EvalContractError(f"cannot read eval dataset file: {relative}") from error
        digest.update(relative.encode("utf-8") + b"\0")
        digest.update(data + b"\0")
    return digest.hexdigest()


def _grade_case(
    *,
    case: dict[str, Any],
    result: dict[str, Any],
    critical: set[str],
    rule: dict[str, int],
) -> CaseGrade:
    identifier = case["id"]
    if result.get("id") != identifier:
        raise EvalContractError(f"result id does not match case {identifier}")
    scores = _object(result.get("scores"), label=f"result {identifier} scores")
    applicable = case["applicable_dimensions"]
    if set(scores) != set(applicable):
        raise EvalContractError(f"result {identifier} scores must match applicable dimensions")
    normalized: dict[str, int] = {}
    for dimension, value in scores.items():
        if not isinstance(value, int) or isinstance(value, bool) or value not in {0, 1, 2}:
            raise EvalContractError(f"result {identifier} score {dimension} must be 0, 1, or 2")
        normalized[dimension] = value
    verification = _object(result.get("verification"), label=f"result {identifier} verification")
    _string(verification.get("behavior"), label=f"result {identifier} behavior verification")
    _string(verification.get("technical"), label=f"result {identifier} technical verification")

    failures: list[str] = []
    for dimension, score in normalized.items():
        minimum = rule["critical_score"] if dimension in critical else rule["minimum_score"]
        if score < minimum:
            failures.append(f"{dimension} scored {score}, requires {minimum}")
    applicable_points = len(normalized) * 2
    earned_points = sum(normalized.values())
    percentage = round(earned_points / applicable_points * 100, 2)
    if percentage < rule["minimum_percentage"]:
        failures.append(f"percentage {percentage:.2f} is below {rule['minimum_percentage']}")
    passed = not failures
    expected_result = "pass" if passed else "fail"
    if result.get("result") != expected_result:
        raise EvalContractError(f"result {identifier} outcome does not match its scores")
    return CaseGrade(
        identifier=identifier,
        passed=passed,
        applicable_points=applicable_points,
        earned_points=earned_points,
        percentage=percentage,
        failures=tuple(failures),
    )


def grade_run(
    *,
    cases: list[dict[str, Any]],
    rubric: dict[str, Any],
    results: dict[str, Any],
    expected_digest: str,
) -> RunGrade:
    dimensions, critical, rule = validate_rubric(rubric)
    validate_cases(cases, dimensions)
    if results.get("schema_version") != 1:
        raise EvalContractError("results schema_version must be 1")
    _string(results.get("suite"), label="results suite")
    release = _string(results.get("release"), label="results release")
    if re.fullmatch(r"v\d+\.\d+\.\d+", release) is None:
        raise EvalContractError("results release must be a v-prefixed semantic version")
    if (
        re.fullmatch(r"\d{4}-\d{2}-\d{2}", _string(results.get("run_date"), label="run_date"))
        is None
    ):
        raise EvalContractError("run_date must use YYYY-MM-DD")
    provenance = _object(results.get("provenance"), label="results provenance")
    for key in ("host", "model", "evaluator", "skill_commit"):
        _string(provenance.get(key), label=f"provenance {key}")
    if re.fullmatch(r"[0-9a-f]{40}", provenance["skill_commit"]) is None:
        raise EvalContractError("provenance skill_commit must be a full Git commit")
    if provenance.get("dataset_sha256") != expected_digest:
        raise EvalContractError("results dataset_sha256 does not match cases, rubric, and fixtures")
    _string(results.get("isolation"), label="results isolation")

    raw_results = results.get("cases")
    if not isinstance(raw_results, list):
        raise EvalContractError("results cases must be a list")
    by_id: dict[str, dict[str, Any]] = {}
    for index, value in enumerate(raw_results):
        result = _object(value, label=f"result case {index}")
        identifier = _string(result.get("id"), label=f"result case {index} id")
        if identifier in by_id:
            raise EvalContractError(f"duplicate result id: {identifier}")
        by_id[identifier] = result
    if set(by_id) != {case["id"] for case in cases}:
        raise EvalContractError("results must cover every eval case exactly once")

    grades = tuple(
        _grade_case(case=case, result=by_id[case["id"]], critical=critical, rule=rule)
        for case in cases
    )
    passed = sum(grade.passed for grade in grades)
    failed = len(grades) - passed
    applicable_points = sum(grade.applicable_points for grade in grades)
    earned_points = sum(grade.earned_points for grade in grades)
    percentage = round(earned_points / applicable_points * 100, 2)
    release_gate = "pass" if failed == 0 else "fail"

    summary = _object(results.get("summary"), label="results summary")
    expected_summary = {
        "passed": passed,
        "failed": failed,
        "applicable_points": applicable_points,
        "earned_points": earned_points,
        "percentage": percentage,
        "release_gate": release_gate,
    }
    if summary != expected_summary:
        raise EvalContractError("results summary does not match recomputed scores")
    return RunGrade(
        passed=passed,
        failed=failed,
        applicable_points=applicable_points,
        earned_points=earned_points,
        percentage=percentage,
        release_gate=release_gate,
        cases=grades,
    )
