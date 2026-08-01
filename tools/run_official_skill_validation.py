#!/usr/bin/env python3
"""Locate and run the official skill-creator validator without shell interpolation."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


def validator_candidates(explicit: Path | None) -> list[Path]:
    """Return ordered validator candidates for supported local Codex layouts."""
    candidates: list[Path] = []
    if explicit is not None:
        candidates.append(explicit)
    creator_dir = os.environ.get("SKILL_CREATOR_DIR")
    if creator_dir:
        candidates.append(Path(creator_dir) / "scripts" / "quick_validate.py")
    codex_home = os.environ.get("CODEX_HOME")
    if codex_home:
        candidates.append(
            Path(codex_home) / "skills" / ".system" / "skill-creator" / "scripts" / "quick_validate.py"
        )
    candidates.append(
        Path.home()
        / ".codex"
        / "skills"
        / ".system"
        / "skill-creator"
        / "scripts"
        / "quick_validate.py"
    )
    return candidates


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skill", required=True, type=Path, help="Skill directory to validate")
    parser.add_argument("--validator", type=Path, help="Explicit quick_validate.py path")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    skill = args.skill.resolve()
    if not skill.is_dir():
        print(f"error: skill directory does not exist: {skill}", file=sys.stderr)
        return 2

    validator = next((path.resolve() for path in validator_candidates(args.validator) if path.is_file()), None)
    if validator is None:
        print(
            "error: official quick_validate.py was not found; set SKILL_CREATOR_DIR or pass --validator",
            file=sys.stderr,
        )
        return 2

    completed = subprocess.run([sys.executable, str(validator), str(skill)], check=False)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
