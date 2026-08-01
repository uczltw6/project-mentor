#!/usr/bin/env python3
"""Scan releasable repository content and Git history without echoing matches."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

MAX_FILE_BYTES = 5 * 1024 * 1024
GENERATED_PARTS = frozenset({"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".venv"})
GENERATED_NAMES = frozenset({".coverage", ".DS_Store", ".env"})
GENERATED_SUFFIXES = frozenset({".pyc", ".pyo"})


@dataclass(frozen=True, order=True)
class Finding:
    rule: str
    source: str
    location: str


CONTENT_RULES: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "private-windows-user-path",
        re.compile(r"(?i)\b[A-Z]:[\\/]+Users[\\/]+[A-Za-z0-9._-]+"),
    ),
    (
        "private-posix-user-path",
        re.compile(r"(?<![$A-Za-z0-9_])/(?:Users|home)/[A-Za-z0-9._-]+/"),
    ),
    (
        "private-build-residue",
        re.compile(
            r"project-mentor-(?:build|forward|capability-probe)-[0-9a-f]{8,}", re.IGNORECASE
        ),
    ),
    (
        "private-key-material",
        re.compile(
            r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----\s+"
            r"[A-Za-z0-9+/=\r\n]{64,}\s+-----END (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"
        ),
    ),
    (
        "github-token",
        re.compile(r"\b(?:gh[oprsu]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,})\b"),
    ),
    ("openai-token", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b")),
    ("aws-access-key", re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b")),
    (
        "credential-assignment",
        re.compile(
            r"(?i)\b(?:api[_-]?key|access[_-]?token|auth[_-]?token|client[_-]?secret|"
            r"password|service[_-]?token)\s*[:=]\s*[\"']?[A-Za-z0-9_./+=:-]{16,}"
        ),
    ),
    (
        "bearer-credential",
        re.compile(r"(?i)\bAuthorization\s*:\s*Bearer\s+[A-Za-z0-9_./+=:-]{16,}"),
    ),
    (
        "authenticated-url",
        re.compile(r"https?://[^\s/:@]+:[A-Za-z0-9_./+=:-]{12,}@[^\s]+", re.IGNORECASE),
    ),
)


def _git(repository: Path, *arguments: str) -> bytes:
    completed = subprocess.run(
        ["git", "-c", "core.quotepath=false", *arguments],
        cwd=repository,
        capture_output=True,
        check=False,
        timeout=60,
    )
    if completed.returncode != 0:
        raise RuntimeError("Git command failed during repository scan")
    return completed.stdout


def releasable_paths(repository: Path) -> list[Path]:
    output = _git(repository, "ls-files", "-z", "--cached", "--others", "--exclude-standard")
    relative_paths = [Path(item.decode("utf-8")) for item in output.split(b"\0") if item]
    return sorted(relative_paths)


def scan_text(text: str, *, source: str, location: str) -> list[Finding]:
    return [
        Finding(rule=rule, source=source, location=location)
        for rule, pattern in CONTENT_RULES
        if pattern.search(text)
    ]


def _path_findings(relative: Path) -> list[Finding]:
    findings: list[Finding] = []
    if (
        GENERATED_PARTS.intersection(relative.parts)
        or relative.name in GENERATED_NAMES
        or relative.suffix in GENERATED_SUFFIXES
    ):
        findings.append(
            Finding(
                rule="generated-release-residue", source="worktree", location=relative.as_posix()
            )
        )
    return findings


def scan_worktree(repository: Path) -> tuple[list[Finding], int]:
    repository = repository.resolve()
    findings: list[Finding] = []
    paths = releasable_paths(repository)
    for relative in paths:
        findings.extend(_path_findings(relative))
        path = (repository / relative).resolve()
        if repository not in path.parents or not path.is_file():
            findings.append(
                Finding(
                    rule="unsafe-or-nonregular-release-path",
                    source="worktree",
                    location=relative.as_posix(),
                )
            )
            continue
        data = path.read_bytes()
        if len(data) > MAX_FILE_BYTES:
            findings.append(
                Finding(
                    rule="oversized-release-file",
                    source="worktree",
                    location=relative.as_posix(),
                )
            )
            continue
        if b"\0" in data:
            continue
        findings.extend(
            scan_text(
                data.decode("utf-8", errors="replace"),
                source="worktree",
                location=relative.as_posix(),
            )
        )
    return sorted(set(findings)), len(paths)


def scan_history(repository: Path) -> list[Finding]:
    text = _git(
        repository.resolve(),
        "log",
        "--all",
        "--full-history",
        "--no-color",
        "--format=fuller",
        "-p",
        "--",
        ".",
    ).decode("utf-8", errors="replace")
    return sorted(set(scan_text(text, source="history", location="<git-history>")))


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, default=Path.cwd())
    scope = parser.add_mutually_exclusive_group()
    scope.add_argument("--all", action="store_true", help="Scan worktree and history (default)")
    scope.add_argument("--worktree-only", action="store_true")
    scope.add_argument("--history-only", action="store_true")
    parser.add_argument("--json", action="store_true", help="Emit sanitized JSON")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    repository = args.repository.resolve()
    try:
        if _git(repository, "rev-parse", "--is-inside-work-tree").strip() != b"true":
            raise RuntimeError("target is not a Git worktree")
        findings: list[Finding] = []
        file_count = 0
        if not args.history_only:
            worktree_findings, file_count = scan_worktree(repository)
            findings.extend(worktree_findings)
        if not args.worktree_only:
            findings.extend(scan_history(repository))
        findings = sorted(set(findings))
    except (OSError, RuntimeError, subprocess.TimeoutExpired):
        print("repository scan: ERROR (unable to inspect requested scope)", file=sys.stderr)
        return 2

    if args.json:
        print(
            json.dumps(
                {
                    "status": "fail" if findings else "pass",
                    "file_count": file_count,
                    "findings": [asdict(finding) for finding in findings],
                },
                indent=2,
                sort_keys=True,
            )
        )
    elif findings:
        print(f"repository scan: FAIL ({len(findings)} sanitized finding(s))", file=sys.stderr)
        for finding in findings:
            print(f"- {finding.rule} in {finding.source}: {finding.location}", file=sys.stderr)
    else:
        print(f"repository scan: PASS ({file_count} releasable worktree files; history checked)")
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
