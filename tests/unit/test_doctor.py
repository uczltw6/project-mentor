from __future__ import annotations

from pathlib import Path

from mentor_core.doctor import diagnose


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
