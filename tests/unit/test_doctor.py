from __future__ import annotations

from pathlib import Path

import pytest
from mentor_core.doctor import (
    FRONTMATTER_LIMIT,
    REQUIRED_SKILL_FILES,
    _frontmatter_name,
    diagnose,
    is_safe_skill_root,
)


def _make_skill(root: Path, *, skill_text: str = "---\nname: project-mentor\n---\n") -> Path:
    for relative in REQUIRED_SKILL_FILES:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(skill_text if relative == "SKILL.md" else "fixture\n", encoding="utf-8")
    return root


def test_doctor_accepts_the_installed_skill_and_valid_ledger(
    tmp_path: Path, ledger: dict[str, object]
) -> None:
    skill = Path(__file__).resolve().parents[2] / ".agents" / "skills" / "project-mentor"
    ledger_path = tmp_path / "ledger.json"
    from mentor_core.model import canonical_json

    ledger_path.write_text(canonical_json(ledger), encoding="utf-8")
    report = diagnose(skill_root=skill, project_root=tmp_path, ledger_path=ledger_path)
    assert report["status"] == "ok"
    assert all(item["status"] == "ok" for item in report["checks"])
    assert str(tmp_path) not in str(report)


def test_doctor_reports_missing_skill_without_disclosing_paths(tmp_path: Path) -> None:
    missing = tmp_path / "private-location"
    report = diagnose(skill_root=missing, project_root=tmp_path)
    assert report["status"] == "error"
    assert any(
        item["id"] == "skill-root" and item["status"] == "error" for item in report["checks"]
    )
    assert str(missing) not in str(report)


def test_doctor_allows_a_standalone_cli_without_an_agent_skill(tmp_path: Path) -> None:
    report = diagnose(skill_root=None, project_root=tmp_path)
    assert report["status"] == "ok"
    assert any(
        item["id"] == "skill-root" and item["status"] == "skipped" for item in report["checks"]
    )


def test_doctor_bounds_skill_frontmatter_reads(tmp_path: Path) -> None:
    skill = _make_skill(
        tmp_path / "skill",
        skill_text="---\nname: project-mentor\n" + ("x" * FRONTMATTER_LIMIT),
    )
    report = diagnose(skill_root=skill, project_root=tmp_path)
    assert report["status"] == "error"
    assert any(
        item["id"] == "skill-name" and item["status"] == "error" for item in report["checks"]
    )


def test_doctor_rejects_symlinked_skill_components_when_supported(tmp_path: Path) -> None:
    skill = _make_skill(tmp_path / "skill")
    external = tmp_path / "external-references"
    external.mkdir()
    for name in ("examples.md", "ledger-schema.md", "mentoring-policy.md"):
        (external / name).write_text("fixture\n", encoding="utf-8")
    for path in (skill / "references").iterdir():
        path.unlink()
    (skill / "references").rmdir()
    try:
        (skill / "references").symlink_to(external, target_is_directory=True)
    except OSError:
        pytest.skip("symlink creation is unavailable")

    report = diagnose(skill_root=skill, project_root=tmp_path)
    assert report["status"] == "error"
    assert any(
        item["id"] == "skill-file:references/examples.md" and item["status"] == "error"
        for item in report["checks"]
    )


def test_skill_root_boundary_and_missing_file_checks(tmp_path: Path) -> None:
    skill = _make_skill(tmp_path / "nested" / "skill")
    assert is_safe_skill_root(skill, boundary=tmp_path)
    assert not is_safe_skill_root(skill, boundary=tmp_path / "different")
    assert not is_safe_skill_root(tmp_path / "missing", boundary=tmp_path)

    (skill / "scripts" / "mentor_core" / "doctor.py").unlink()
    report = diagnose(skill_root=skill, project_root=tmp_path)
    assert report["status"] == "error"
    assert any(
        item["id"] == "skill-file:scripts/mentor_core/doctor.py" and item["status"] == "error"
        for item in report["checks"]
    )


@pytest.mark.parametrize("content", ("", "name: project-mentor\n", "---\ntitle: fixture\n---\n"))
def test_frontmatter_parser_fails_closed(tmp_path: Path, content: str) -> None:
    skill_file = tmp_path / "SKILL.md"
    skill_file.write_text(content, encoding="utf-8")
    assert _frontmatter_name(skill_file) is None


def test_doctor_reports_an_invalid_optional_ledger_without_disclosing_it(tmp_path: Path) -> None:
    ledger = tmp_path / "private-ledger.json"
    ledger.write_text("{}", encoding="utf-8")
    report = diagnose(skill_root=None, project_root=tmp_path, ledger_path=ledger)
    assert report["status"] == "error"
    assert any(item["id"] == "ledger" and item["status"] == "error" for item in report["checks"])
    assert str(ledger) not in str(report)
