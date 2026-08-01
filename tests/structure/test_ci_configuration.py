from __future__ import annotations

import re
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parents[2]
WORKFLOWS = REPOSITORY / ".github" / "workflows"


def test_workflows_pin_every_action_to_an_immutable_commit() -> None:
    use_pattern = re.compile(r"^\s*uses:\s*[^@\s]+@([^\s#]+)", re.MULTILINE)
    for workflow in WORKFLOWS.glob("*.yml"):
        text = workflow.read_text(encoding="utf-8")
        references = use_pattern.findall(text)
        assert references, f"no action references found in {workflow.name}"
        assert all(re.fullmatch(r"[0-9a-f]{40}", reference) for reference in references)
        assert "pull_request_target" not in text
        assert "permissions:" in text and "contents: read" in text


def test_ci_covers_supported_python_cross_platform_and_release_gates() -> None:
    ci = (WORKFLOWS / "ci.yml").read_text(encoding="utf-8")
    for version in ("3.10", "3.11", "3.12", "3.13", "3.14"):
        assert f'"{version}"' in ci
    for requirement in (
        "ubuntu-latest",
        "windows-latest",
        "ruff check",
        "project-mentor --version",
        "python -m project_mentor_cli --version",
        "python -m build --no-isolation",
        "validate_distribution.py",
        "smoke_test_wheel.py",
        "ruff format --check",
        "mypy --strict",
        "coverage report --fail-under=90",
        "repository_scan.py --all",
        "sync_skill.py --check",
        "run_official_skill_validation.py",
        "tests/structure",
        "CI Gate",
    ):
        assert requirement in ci


def test_codeql_and_dependabot_are_narrowly_configured() -> None:
    codeql = (WORKFLOWS / "codeql.yml").read_text(encoding="utf-8")
    dependabot = (REPOSITORY / ".github" / "dependabot.yml").read_text(encoding="utf-8")
    assert "languages: python" in codeql
    assert "security-events: write" in codeql
    assert "security-extended" in codeql
    assert "package-ecosystem: pip" in dependabot
    assert "package-ecosystem: github-actions" in dependabot
    assert "development-minor-and-patch" in dependabot
    assert "update-types:" in dependabot


def test_pypi_release_workflow_is_separated_and_minimally_privileged() -> None:
    release = (WORKFLOWS / "release.yml").read_text(encoding="utf-8")
    for contract in (
        "release:",
        "types: [published]",
        "needs: build",
        "name: pypi",
        "id-token: write",
        "python-distributions",
        "validate_distribution.py",
        "smoke_test_wheel.py",
        "pypa/gh-action-pypi-publish@",
        "packages-dir: dist/",
    ):
        assert contract in release
    assert "workflow_dispatch:" not in release
    assert release.count("id-token: write") == 1
    assert "password:" not in release
    assert "PYPI_TOKEN" not in release
    assert "skip-existing" not in release
