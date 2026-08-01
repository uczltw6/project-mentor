#!/usr/bin/env python3
"""Locate and run the official plugin-creator validator without shell interpolation."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


def validator_candidates(explicit: Path | None) -> list[Path]:
    candidates: list[Path] = []
    if explicit is not None:
        candidates.append(explicit)
    creator_dir = os.environ.get("PLUGIN_CREATOR_DIR")
    if creator_dir:
        candidates.append(Path(creator_dir) / "scripts" / "validate_plugin.py")
    codex_home = os.environ.get("CODEX_HOME")
    if codex_home:
        candidates.append(
            Path(codex_home)
            / "skills"
            / ".system"
            / "plugin-creator"
            / "scripts"
            / "validate_plugin.py"
        )
    candidates.append(
        Path.home()
        / ".codex"
        / "skills"
        / ".system"
        / "plugin-creator"
        / "scripts"
        / "validate_plugin.py"
    )
    return candidates


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plugin", required=True, type=Path)
    parser.add_argument("--validator", type=Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    plugin = args.plugin.resolve()
    if not plugin.is_dir():
        print("error: plugin directory does not exist", file=sys.stderr)
        return 2
    validator = next(
        (path.resolve() for path in validator_candidates(args.validator) if path.is_file()), None
    )
    if validator is None:
        print(
            "error: official validate_plugin.py was not found; set PLUGIN_CREATOR_DIR or "
            "pass --validator",
            file=sys.stderr,
        )
        return 2
    return subprocess.run([sys.executable, str(validator), str(plugin)], check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
