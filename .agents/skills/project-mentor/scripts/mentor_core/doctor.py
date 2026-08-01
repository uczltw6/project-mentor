"""Read-only environment diagnostics for the Project Mentor skill."""

from __future__ import annotations

import stat
import sys
from pathlib import Path
from typing import Any

from .errors import MentorError
from .io import read_json, read_text
from .model import SCHEMA_VERSION
from .validate import validate_ledger

REQUIRED_SKILL_FILES = (
    "SKILL.md",
    "agents/openai.yaml",
    "references/examples.md",
    "references/ledger-schema.md",
    "references/mentoring-policy.md",
    "scripts/project_mentor.py",
    "scripts/mentor_core/__main__.py",
    "scripts/mentor_core/anchors.py",
    "scripts/mentor_core/doctor.py",
)
FRONTMATTER_LIMIT = 65_536


def _check(identifier: str, ok: bool, detail: str) -> dict[str, str]:
    return {"id": identifier, "status": "ok" if ok else "error", "detail": detail}


def _frontmatter_name(skill_file: Path) -> str | None:
    try:
        lines = read_text(skill_file, limit=FRONTMATTER_LIMIT).splitlines()
    except (MentorError, OSError, UnicodeError):
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


def _is_link_or_reparse_point(path: Path) -> bool:
    try:
        metadata = path.lstat()
    except OSError:
        return True
    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    attributes = getattr(metadata, "st_file_attributes", 0)
    return stat.S_ISLNK(metadata.st_mode) or bool(attributes & reparse_flag)


def is_safe_skill_root(skill_root: Path, *, boundary: Path | None = None) -> bool:
    """Return whether a skill root is a real directory inside an optional boundary."""
    components: tuple[Path, ...]
    try:
        if boundary is None:
            components = (skill_root,)
            boundary_resolved = skill_root.parent.resolve(strict=True)
        else:
            relative = skill_root.relative_to(boundary)
            current = boundary
            components_list: list[Path] = []
            for part in relative.parts:
                current /= part
                components_list.append(current)
            components = tuple(components_list)
            if _is_link_or_reparse_point(boundary):
                return False
            boundary_resolved = boundary.resolve(strict=True)
        resolved = skill_root.resolve(strict=True)
    except (OSError, ValueError):
        return False
    return (
        skill_root.is_dir()
        and all(not _is_link_or_reparse_point(path) for path in components)
        and resolved.is_relative_to(boundary_resolved)
    )


def _is_safe_skill_file(skill_root: Path, relative: str) -> bool:
    try:
        root_resolved = skill_root.resolve(strict=True)
        current = skill_root
        for part in Path(relative).parts:
            current /= part
            if _is_link_or_reparse_point(current):
                return False
        resolved = current.resolve(strict=True)
    except OSError:
        return False
    return current.is_file() and resolved.is_relative_to(root_resolved)


def diagnose(
    *, skill_root: Path | None, project_root: Path, ledger_path: Path | None = None
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

    if skill_root is None:
        checks.append(
            {
                "id": "skill-root",
                "status": "skipped",
                "detail": "no Agent Skill directory was requested or discovered",
            }
        )
    else:
        skill_ok = is_safe_skill_root(skill_root)
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
            present = skill_ok and _is_safe_skill_file(skill_root, relative)
            checks.append(
                _check(
                    f"skill-file:{relative}",
                    present,
                    "present" if present else "required regular file is missing",
                )
            )

        skill_name = (
            _frontmatter_name(skill_root / "SKILL.md")
            if skill_ok and _is_safe_skill_file(skill_root, "SKILL.md")
            else None
        )
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
        "status": "ok" if all(item["status"] != "error" for item in checks) else "error",
        "checks": checks,
    }
