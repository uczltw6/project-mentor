"""Conservative, local verification of project evidence anchors."""

from __future__ import annotations

import hashlib
import os
import re
import stat
from collections.abc import Iterator
from pathlib import Path, PurePosixPath
from typing import Any, BinaryIO

from .errors import InvalidInputError, IOSafetyError
from .model import MAX_INPUT_BYTES, SCHEMA_VERSION

DIGEST_LOCATOR = re.compile(r"^(?P<path>[^#]+)#sha256=(?P<digest>[0-9a-fA-F]{64})$")
VERIFIABLE_KINDS = frozenset({"file_digest", "file_symbol", "config_key", "test_result"})
MAX_DIGEST_BYTES = 16 * MAX_INPUT_BYTES


def _anchors(
    ledger: dict[str, Any],
) -> Iterator[tuple[str, str, dict[str, Any]]]:
    for concept in ledger["concepts"]:
        for evidence in concept["project_evidence"]:
            yield "concept", concept["id"], evidence
    for decision in ledger["decisions"]:
        for evidence in decision["project_evidence"]:
            yield "decision", decision["id"], evidence
    for milestone in ledger["milestones"]:
        for evidence in milestone["project_evidence"]:
            yield "milestone", milestone["id"], evidence


def _safe_candidate(root: Path, relative_text: str) -> tuple[Path | None, str | None]:
    if "\\" in relative_text or re.match(r"^[A-Za-z]:", relative_text):
        return None, "locator path must use a relative POSIX path"
    relative = PurePosixPath(relative_text)
    if (
        relative.is_absolute()
        or not relative.parts
        or any(part in {"", ".", ".."} for part in relative.parts)
    ):
        return None, "locator path must stay within the project root"
    candidate = root.joinpath(*relative.parts)
    cursor = root
    for part in relative.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            return None, "locator path contains a symlink"
    try:
        candidate.resolve(strict=False).relative_to(root)
    except (OSError, ValueError):
        return None, "locator path escapes the project root"
    return candidate, None


def _split_locator(kind: str, locator: str) -> tuple[str | None, str | None, str | None]:
    if kind == "file_digest":
        match = DIGEST_LOCATOR.fullmatch(locator)
        if not match:
            return None, None, "expected <path>#sha256=<64-hex-digest>"
        return match.group("path"), match.group("digest").lower(), None
    separator = "#" if kind == "config_key" else "::"
    path, found, token = locator.partition(separator)
    if not found or not path or not token.strip():
        return None, None, f"expected <path>{separator}<anchor>"
    return path, token.strip(), None


def _open_regular(root: Path, candidate: Path) -> BinaryIO:
    """Open a stable regular-file handle and recheck containment before any read."""
    descriptor = -1
    try:
        before = os.lstat(candidate)
        if not stat.S_ISREG(before.st_mode):
            raise IOSafetyError("anchor target is not a regular file")
        flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
        descriptor = os.open(candidate, flags)
        opened = os.fstat(descriptor)
        candidate.resolve(strict=True).relative_to(root)
        current = os.lstat(candidate)
        identities = {
            (before.st_dev, before.st_ino),
            (opened.st_dev, opened.st_ino),
            (current.st_dev, current.st_ino),
        }
        if len(identities) != 1 or not stat.S_ISREG(opened.st_mode):
            raise IOSafetyError("anchor target changed while it was being opened")
        handle = os.fdopen(descriptor, "rb")
        descriptor = -1
        return handle
    except ValueError as error:
        raise IOSafetyError("anchor target escaped the project root") from error
    finally:
        if descriptor >= 0:
            os.close(descriptor)


def _hash_file(handle: BinaryIO) -> str:
    size = os.fstat(handle.fileno()).st_size
    if size > MAX_DIGEST_BYTES:
        raise IOSafetyError("anchor file exceeds the safe digest-verification limit")
    digest = hashlib.sha256()
    total = 0
    while chunk := handle.read(65_536):
        total += len(chunk)
        if total > MAX_DIGEST_BYTES:
            raise IOSafetyError("anchor file exceeds the safe digest-verification limit")
        digest.update(chunk)
    return digest.hexdigest()


def _read_anchor_text(handle: BinaryIO) -> str:
    if os.fstat(handle.fileno()).st_size > MAX_INPUT_BYTES:
        raise IOSafetyError("anchor file exceeds the safe text-verification limit")
    try:
        raw = handle.read(MAX_INPUT_BYTES + 1)
        if len(raw) > MAX_INPUT_BYTES:
            raise IOSafetyError("anchor file exceeds the safe text-verification limit")
        return raw.decode("utf-8")
    except UnicodeError as error:
        raise IOSafetyError("anchor file is not valid UTF-8 text") from error


def _verify_one(root: Path, evidence: dict[str, Any]) -> tuple[str, str]:
    if evidence["class"] == "stale":
        return "stale", "evidence was already marked stale"
    kind = evidence["kind"]
    if kind not in VERIFIABLE_KINDS:
        return "unavailable", "evidence kind has no safe local verifier"
    relative, expected, parse_error = _split_locator(kind, evidence["locator"])
    if parse_error is not None or relative is None or expected is None:
        return "unavailable", parse_error or "locator cannot be parsed safely"
    candidate, safety_error = _safe_candidate(root, relative)
    if safety_error is not None or candidate is None:
        return "unavailable", safety_error or "locator path is unsafe"
    try:
        with _open_regular(root, candidate) as handle:
            if kind == "file_digest":
                matches = _hash_file(handle) == expected
            else:
                matches = expected in _read_anchor_text(handle)
    except FileNotFoundError:
        return "stale", "anchored file no longer exists"
    except OSError:
        return "unavailable", "anchor target could not be read"
    except IOSafetyError as error:
        return "unavailable", str(error)
    return ("valid", "anchor matched") if matches else ("stale", "anchor no longer matched")


def verify_anchors(
    ledger: dict[str, Any], *, root: Path
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    """Return a redaction-safe report and non-stale targets that should be marked stale."""
    if root.is_symlink() or not root.is_dir():
        raise InvalidInputError("--root must be an existing regular directory, not a symlink")
    resolved_root = root.resolve()
    results: list[dict[str, str]] = []
    stale_targets: list[dict[str, str]] = []
    for owner_type, owner_id, evidence in _anchors(ledger):
        status, reason = _verify_one(resolved_root, evidence)
        result = {
            "owner_type": owner_type,
            "owner_id": owner_id,
            "evidence_id": evidence["id"],
            "kind": evidence["kind"],
            "locator_sha256": hashlib.sha256(evidence["locator"].encode("utf-8")).hexdigest(),
            "status": status,
            "reason": reason,
        }
        results.append(result)
        if status == "stale" and evidence["class"] != "stale":
            stale_targets.append(
                {
                    "owner_type": owner_type,
                    "owner_id": owner_id,
                    "evidence_id": evidence["id"],
                    "reason": reason,
                }
            )
    results.sort(key=lambda item: (item["owner_type"], item["owner_id"], item["evidence_id"]))
    counts = {
        status: sum(item["status"] == status for item in results)
        for status in ("valid", "stale", "unavailable")
    }
    return (
        {
            "schema_version": SCHEMA_VERSION,
            "root_label": ledger["project"]["root_label"],
            "counts": counts,
            "results": results,
        },
        stale_targets,
    )


def anchor_event_id(target: dict[str, str], checked_at: str) -> str:
    material = "\0".join(
        (target["owner_type"], target["owner_id"], target["evidence_id"], checked_at)
    ).encode("utf-8")
    return "evt-anchor-" + hashlib.sha256(material).hexdigest()[:20]
