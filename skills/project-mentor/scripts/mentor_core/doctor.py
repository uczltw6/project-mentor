"""Read-only environment diagnostics for the Project Mentor skill."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from .io import read_json
from .model import SCHEMA_VERSION
from .validate import validate_ledger

REQUIRED_SKILL_FILES = (
    "SKILL.md",
    "agents/openai.yaml",
    "references/examples.md",
    "references/ledger-schema.md",
    "references/mentoring-policy.md",
    "scripts/project_mentor.py",
    "scripts/mentor_core/anchors.py",
    "scripts/mentor_core/doctor.py",
)


def _check(identifier: str, ok: bool, detail: str) -> dict[str, str]:
    return {"id": identifier, "status": "ok" if ok else "error", "detail": detail}


def _frontmatter_name(skill_file: Path) -> str | None:
    try:
        lines = skill_file.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError):
        return None
    if not lines or lines[0].strip() != "---":
        return None
    for line in lines[1:]:
        if line.strip() == "---":
            break
        key, separator, value = line.partition(":")
        if separator and key.strip() == "name":
            return value.strip().strip("\"'")
    return None


def diagnose(
    *, skill_root: Path, project_root: Path, ledger_path: Path | None = None
) -> dict[str, Any]:
    """Return a stable diagnostic report without mutating either root."""
    checks: list[dict[str, str]] = []
    python_ok = sys.version_info >= (3, 10)
    checks.append(
        _check(
            "python-version",
            python_ok,
            f"Python {sys.version_info.major}.{sys.version_info.minor}"
            if python_ok
            else "Python 3.10 or newer is required",
        )
    )

    skill_ok = skill_root.is_dir() and not skill_root.is_symlink()
    checks.append(
        _check(
            "skill-root",
            skill_ok,
            "skill directory is a regular directory"
            if skill_ok
            else "skill directory is missing or is a symlink",
        )
    )
    for relative in REQUIRED_SKILL_FILES:
        path = skill_root / relative
        present = path.is_file() and not path.is_symlink()
        checks.append(
            _check(
                f"skill-file:{relative}",
                present,
                "present" if present else "required regular file is missing",
            )
        )

    skill_name = _frontmatter_name(skill_root / "SKILL.md")
    checks.append(
        _check(
            "skill-name",
            skill_name == "project-mentor",
            "frontmatter name is project-mentor"
            if skill_name == "project-mentor"
            else "SKILL.md frontmatter name is missing or unexpected",
        )
    )

    project_ok = project_root.is_dir() and not project_root.is_symlink()
    checks.append(
        _check(
            "project-root",
            project_ok,
            "project directory is a regular directory"
            if project_ok
            else "project directory is missing or is a symlink",
        )
    )

    if ledger_path is not None:
        try:
            validate_ledger(read_json(ledger_path))
        except Exception:  # The report intentionally does not disclose file content or paths.
            checks.append(_check("ledger", False, "ledger is unreadable or invalid"))
        else:
            checks.append(_check("ledger", True, "ledger contract is valid"))

    return {
        "schema_version": SCHEMA_VERSION,
        "status": "ok" if all(item["status"] == "ok" for item in checks) else "error",
        "checks": checks,
    }
