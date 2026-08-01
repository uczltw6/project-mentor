#!/usr/bin/env python3
"""Install the built wheel offline and exercise its public CLI in a fresh venv."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import venv
from pathlib import Path


class SmokeTestError(RuntimeError):
    """Raised when the isolated installed CLI violates its public contract."""


def _run(
    command: list[str], *, cwd: Path, expected_exit: int = 0
) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        check=False,
        text=True,
        encoding="utf-8",
    )
    if completed.returncode != expected_exit:
        raise SmokeTestError(
            f"command returned {completed.returncode}, expected {expected_exit}: {command[1]}"
        )
    return completed


def smoke_test(wheel: Path, *, version: str, skill_root: Path) -> None:
    with tempfile.TemporaryDirectory(prefix="project-mentor-wheel-smoke-") as temporary:
        root = Path(temporary)
        environment = root / "venv"
        work = root / "work"
        work.mkdir()
        venv.EnvBuilder(with_pip=True, clear=False).create(environment)
        scripts = environment / ("Scripts" if os.name == "nt" else "bin")
        python = scripts / ("python.exe" if os.name == "nt" else "python")
        command = scripts / ("project-mentor.exe" if os.name == "nt" else "project-mentor")

        _run(
            [
                str(python),
                "-m",
                "pip",
                "install",
                "--no-index",
                "--no-deps",
                str(wheel),
            ],
            cwd=work,
        )
        _run([str(python), "-m", "pip", "check"], cwd=work)
        expected_version = f"project-mentor {version}"
        if _run([str(command), "--version"], cwd=work).stdout.strip() != expected_version:
            raise SmokeTestError("console entry point returned an unexpected version")
        if (
            _run([str(python), "-m", "project_mentor_cli", "--version"], cwd=work).stdout.strip()
            != expected_version
        ):
            raise SmokeTestError("module entry point returned an unexpected version")

        ledger = work / "ledger.json"
        _run(
            [
                str(command),
                "init",
                "--goal",
                "Installed wheel smoke test",
                "--session-id",
                "pm-wheel-smoke",
                "--created-at",
                "2026-08-01T00:00:00Z",
                "--output",
                str(ledger),
            ],
            cwd=work,
        )
        validated = _run(
            [str(command), "validate", "--kind", "ledger", "--input", str(ledger)], cwd=work
        )
        if validated.stdout.strip() != "valid ledger schema_version=1":
            raise SmokeTestError("installed CLI did not validate its generated ledger")

        summary = work / "summary.json"
        _run(
            [str(command), "summarize", "--ledger", str(ledger), "--output", str(summary)],
            cwd=work,
        )
        summary_data = json.loads(summary.read_text(encoding="utf-8"))
        if summary_data.get("revision") != 0:
            raise SmokeTestError("installed CLI returned an unexpected ledger summary")

        doctor = work / "doctor.json"
        _run(
            [
                str(command),
                "doctor",
                "--project-root",
                str(work),
                "--skill-root",
                str(skill_root),
                "--output",
                str(doctor),
            ],
            cwd=work,
        )
        if json.loads(doctor.read_text(encoding="utf-8")).get("status") != "ok":
            raise SmokeTestError("installed CLI doctor reported an unexpected failure")

        missing = _run(
            [str(command), "validate", "--kind", "ledger", "--input", str(work / "missing")],
            cwd=work,
            expected_exit=4,
        )
        if "Traceback" in missing.stderr or not missing.stderr.startswith("error:"):
            raise SmokeTestError("expected installed CLI failures must be concise")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dist-dir", required=True, type=Path)
    parser.add_argument("--version", required=True)
    parser.add_argument("--skill-root", required=True, type=Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    wheels = sorted(args.dist_dir.glob(f"project_mentor-{args.version}-*.whl"))
    if len(wheels) != 1 or not args.skill_root.is_dir():
        print("error: expected one wheel and an existing skill root", file=sys.stderr)
        return 2
    try:
        smoke_test(wheels[0].resolve(), version=args.version, skill_root=args.skill_root.resolve())
    except (OSError, UnicodeError, ValueError, SmokeTestError, json.JSONDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    print(f"installed wheel smoke test passed for project-mentor {args.version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
