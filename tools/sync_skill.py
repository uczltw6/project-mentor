#!/usr/bin/env python3
"""Synchronize or compare the installed and public Project Mentor skill copies."""

from __future__ import annotations

import argparse
import hashlib
import shutil
import sys
from pathlib import Path

IGNORED_DIRS = {"__pycache__"}
IGNORED_SUFFIXES = {".pyc", ".pyo"}


class SyncError(ValueError):
    """Raised when parity cannot be checked safely."""


def release_files(root: Path) -> dict[Path, str]:
    """Return content hashes for non-generated regular files below root."""
    root = root.resolve()
    if not root.is_dir():
        raise SyncError(f"skill directory does not exist: {root}")
    if root.is_symlink():
        raise SyncError(f"skill directory must not be a symlink: {root}")

    files: dict[Path, str] = {}
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if any(part in IGNORED_DIRS for part in relative.parts) or path.suffix in IGNORED_SUFFIXES:
            continue
        if path.is_symlink():
            raise SyncError(f"release content must not contain symlinks: {relative.as_posix()}")
        if path.is_file():
            files[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
    return files


def validate_destination(destination: Path) -> Path:
    """Confine writes to a directory with the expected skill boundary."""
    if destination.is_symlink():
        raise SyncError(f"destination must not be a symlink: {destination}")
    resolved = destination.resolve()
    if resolved.name != "project-mentor" or resolved.parent.name != "skills":
        raise SyncError("destination must end in skills/project-mentor")
    return resolved


def differences(source: Path, destination: Path) -> list[str]:
    source_files = release_files(source)
    destination_files = release_files(destination)
    messages: list[str] = []
    for relative in sorted(source_files.keys() - destination_files.keys()):
        messages.append(f"missing from destination: {relative.as_posix()}")
    for relative in sorted(destination_files.keys() - source_files.keys()):
        messages.append(f"extra in destination: {relative.as_posix()}")
    for relative in sorted(source_files.keys() & destination_files.keys()):
        if source_files[relative] != destination_files[relative]:
            messages.append(f"content differs: {relative.as_posix()}")
    return messages


def synchronize(source: Path, destination: Path) -> int:
    source = source.resolve()
    destination = validate_destination(destination)
    if source == destination:
        raise SyncError("source and destination must be different directories")

    source_files = release_files(source)
    destination.mkdir(parents=True, exist_ok=True)
    current_files = release_files(destination)

    for relative in sorted(current_files.keys() - source_files.keys(), reverse=True):
        (destination / relative).unlink()
    for directory in sorted(
        (path for path in destination.rglob("*") if path.is_dir()),
        key=lambda path: len(path.parts),
        reverse=True,
    ):
        if directory != destination and not any(directory.iterdir()):
            directory.rmdir()
    for relative in sorted(source_files):
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source / relative, target)
    return len(source_files)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    repository = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source",
        type=Path,
        default=Path.home() / ".agents" / "skills" / "project-mentor",
        help="Validated personal skill directory",
    )
    parser.add_argument(
        "--destination",
        type=Path,
        default=repository / ".agents" / "skills" / "project-mentor",
        help="Public repository skill directory",
    )
    action = parser.add_mutually_exclusive_group()
    action.add_argument(
        "--check", action="store_true", help="Check parity without writing (default)"
    )
    action.add_argument("--write", action="store_true", help="Synchronize source into destination")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        if args.write:
            count = synchronize(args.source, args.destination)
            print(f"Synchronized {count} release files.")
        mismatches = differences(args.source.resolve(), args.destination.resolve())
    except (OSError, SyncError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    if mismatches:
        for mismatch in mismatches:
            print(mismatch, file=sys.stderr)
        return 1
    print("Skill release files are byte-for-byte identical.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
