from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from tools.repository_scan import Finding, main, scan_history, scan_text, scan_worktree


def _git(repository: Path, *arguments: str) -> None:
    subprocess.run(["git", *arguments], cwd=repository, check=True, capture_output=True)


def test_content_rules_find_private_paths_and_credentials_without_echoing_values() -> None:
    private_path = "C:" + "\\" + "Users" + "\\" + "person" + "\\" + "private.txt"
    credential = "ghp_" + "x" * 40
    findings = scan_text(
        private_path + "\n" + credential,
        source="worktree",
        location="fixture.txt",
    )
    assert {finding.rule for finding in findings} == {
        "github-token",
        "private-windows-user-path",
    }
    assert all(private_path not in finding.location for finding in findings)
    assert all(credential not in finding.location for finding in findings)


def test_worktree_scan_includes_untracked_nonignored_files_and_generated_residue(
    tmp_path: Path,
) -> None:
    _git(tmp_path, "init", "--initial-branch=main")
    (tmp_path / "clean.txt").write_text("public content", encoding="utf-8")
    generated = tmp_path / "__pycache__" / "module.pyc"
    generated.parent.mkdir()
    generated.write_bytes(b"\0binary")
    findings, count = scan_worktree(tmp_path)
    assert count == 2
    assert (
        Finding(
            rule="generated-release-residue",
            source="worktree",
            location="__pycache__/module.pyc",
        )
        in findings
    )


def test_history_scan_detects_removed_secret_but_does_not_return_it(tmp_path: Path) -> None:
    _git(tmp_path, "init", "--initial-branch=main")
    _git(tmp_path, "config", "user.name", "Fixture")
    _git(tmp_path, "config", "user.email", "fixture@example.invalid")
    path = tmp_path / "config.txt"
    credential = "sk-" + "z" * 32
    path.write_text("API_KEY=" + credential, encoding="utf-8")
    _git(tmp_path, "add", "config.txt")
    _git(tmp_path, "commit", "-m", "fixture")
    path.write_text("clean", encoding="utf-8")
    _git(tmp_path, "commit", "-am", "remove fixture")

    findings = scan_history(tmp_path)
    assert any(finding.rule in {"credential-assignment", "openai-token"} for finding in findings)
    assert all(credential not in finding.location for finding in findings)


def test_current_repository_worktree_and_history_pass_release_scan() -> None:
    repository = Path(__file__).resolve().parents[2]
    worktree_findings, _ = scan_worktree(repository)
    history_findings = scan_history(repository)
    assert not worktree_findings
    assert not history_findings


def test_json_report_is_sanitized(tmp_path: Path, capsys: Any) -> None:
    _git(tmp_path, "init", "--initial-branch=main")
    credential = "github_pat_" + "q" * 48
    (tmp_path / "credential.txt").write_text(credential, encoding="utf-8")
    assert main(["--repository", str(tmp_path), "--worktree-only", "--json"]) == 1
    output = capsys.readouterr().out
    assert credential not in output
    assert "github-token" in output
