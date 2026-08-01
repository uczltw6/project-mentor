"""Bounded UTF-8 input and atomic, symlink-safe output."""

from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile
from contextlib import suppress
from pathlib import Path
from typing import Any

from .errors import InvalidInputError, IOSafetyError, RevisionConflictError
from .model import MAX_INPUT_BYTES, canonical_json
from .redact import redact_data


def _decode_utf8(raw: bytes, label: str) -> str:
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError as error:
        raise InvalidInputError(f"{label} must be valid UTF-8") from error


def read_text(source: str | Path, *, limit: int = MAX_INPUT_BYTES) -> str:
    """Read a bounded UTF-8 file or stdin when source is '-' ."""
    if str(source) == "-":
        raw = sys.stdin.buffer.read(limit + 1)
        label = "stdin"
    else:
        path = Path(source)
        try:
            if path.stat().st_size > limit:
                raise InvalidInputError(f"input exceeds the {limit}-byte limit")
            raw = path.read_bytes()
        except InvalidInputError:
            raise
        except OSError as error:
            raise IOSafetyError(f"cannot read input path: {path}") from error
        label = str(path)
    if len(raw) > limit:
        raise InvalidInputError(f"input exceeds the {limit}-byte limit")
    return _decode_utf8(raw, label)


def parse_json(text: str, *, label: str = "input") -> Any:
    """Parse JSON while reporting location but never echoing its content."""
    try:
        return json.loads(text)
    except json.JSONDecodeError as error:
        raise InvalidInputError(
            f"{label} is malformed JSON at line {error.lineno}, column {error.colno}"
        ) from error


def read_json(source: str | Path, *, limit: int = MAX_INPUT_BYTES) -> Any:
    return parse_json(read_text(source, limit=limit), label=str(source))


def sha256_file(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as error:
        raise IOSafetyError(f"cannot read output path for revision check: {path}") from error


def atomic_write_text(path: str | Path, text: str, *, expected_sha256: str | None = None) -> None:
    """Atomically replace an explicit path while refusing an existing symlink."""
    target = Path(path)
    if target.is_symlink():
        raise IOSafetyError(f"refusing to overwrite symlink: {target}")
    if target.exists() and not target.is_file():
        raise IOSafetyError(f"output path is not a regular file: {target}")
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
    except OSError as error:
        raise IOSafetyError(f"cannot create output directory: {target.parent}") from error

    if expected_sha256 is not None and (
        not target.exists() or sha256_file(target) != expected_sha256
    ):
        raise RevisionConflictError("ledger changed after it was read; reload and retry")

    descriptor = -1
    temporary: Path | None = None
    try:
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{target.name}.", suffix=".tmp", dir=target.parent
        )
        temporary = Path(temporary_name)
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            descriptor = -1
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        if expected_sha256 is not None and sha256_file(target) != expected_sha256:
            raise RevisionConflictError(
                "ledger changed before atomic replacement; reload and retry"
            )
        if target.is_symlink():
            raise IOSafetyError(f"refusing to replace path that became a symlink: {target}")
        os.replace(temporary, target)
        temporary = None
    except (IOSafetyError, RevisionConflictError):
        raise
    except OSError as error:
        raise IOSafetyError(f"atomic write failed for output path: {target}") from error
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        if temporary is not None:
            with suppress(OSError):
                temporary.unlink(missing_ok=True)


def atomic_write_json(path: str | Path, value: Any, *, expected_sha256: str | None = None) -> None:
    atomic_write_text(path, canonical_json(redact_data(value)), expected_sha256=expected_sha256)


def write_text(destination: str | Path, text: str) -> None:
    """Write to stdout for '-' or atomically to an explicit file."""
    if str(destination) == "-":
        sys.stdout.write(text)
        return
    atomic_write_text(destination, text)
