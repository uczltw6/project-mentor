from __future__ import annotations

import io
from pathlib import Path
from typing import Any

import pytest
from conftest import assert_no_secret
from mentor_core.errors import InvalidInputError, IOSafetyError, RevisionConflictError
from mentor_core.io import (
    atomic_write_json,
    atomic_write_text,
    parse_json,
    read_json,
    read_text,
    sha256_file,
    write_text,
)
from mentor_core.model import MAX_INPUT_BYTES


class StdinBytes:
    def __init__(self, value: bytes) -> None:
        self.buffer = io.BytesIO(value)


def test_read_utf8_file_and_json_with_spaces_and_unicode(tmp_path: Path) -> None:
    directory = tmp_path / "path with spaces" / "项目"
    directory.mkdir(parents=True)
    path = directory / "输入.json"
    path.write_text('{"message":"你好"}', encoding="utf-8")
    assert read_text(path) == '{"message":"你好"}'
    assert read_json(path) == {"message": "你好"}


def test_read_stdin_and_write_stdout(monkeypatch: pytest.MonkeyPatch, capsys: Any) -> None:
    monkeypatch.setattr("sys.stdin", StdinBytes("你好".encode()))
    assert read_text("-") == "你好"
    write_text("-", "done\n")
    assert capsys.readouterr().out == "done\n"


def test_rejects_oversized_file_and_stdin(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = tmp_path / "large.txt"
    path.write_bytes(b"x" * (MAX_INPUT_BYTES + 1))
    with pytest.raises(InvalidInputError, match="byte limit"):
        read_text(path)
    with pytest.raises(InvalidInputError, match="byte limit"):
        sha256_file(path)
    monkeypatch.setattr("sys.stdin", StdinBytes(b"x" * 12))
    with pytest.raises(InvalidInputError, match="byte limit"):
        read_text("-", limit=10)


def test_rejects_invalid_utf8_and_malformed_json(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "bad.bin"
    path.write_bytes(b"\xff")
    with pytest.raises(InvalidInputError, match="UTF-8"):
        read_text(path)
    with pytest.raises(InvalidInputError, match="line 1, column 16") as raised:
        parse_json('{"secret-value"}', label="fixture")
    assert "secret-value" not in str(raised.value)
    monkeypatch.setattr("sys.stdin", StdinBytes(b"\xff"))
    with pytest.raises(InvalidInputError, match="UTF-8"):
        read_text("-")


@pytest.mark.parametrize(
    "text",
    [
        '{"actor":"agent","actor":"user"}',
        '{"payload":{"mode":"guided","mode":"hands_on"}}',
    ],
)
def test_rejects_duplicate_json_keys_at_every_depth(text: str) -> None:
    with pytest.raises(InvalidInputError, match="duplicate JSON object key") as raised:
        parse_json(text, label="event")
    assert "actor" not in str(raised.value)
    assert "mode" not in str(raised.value)


def test_atomic_write_and_expected_digest(tmp_path: Path) -> None:
    path = tmp_path / "nested" / "ledger.json"
    atomic_write_text(path, "first\n")
    first_digest = sha256_file(path)
    atomic_write_json(path, {"safe": "value"}, expected_sha256=first_digest)
    assert path.read_text(encoding="utf-8") == '{\n  "safe": "value"\n}\n'
    with pytest.raises(RevisionConflictError):
        atomic_write_text(path, "stale\n", expected_sha256=first_digest)
    assert '"safe": "value"' in path.read_text(encoding="utf-8")


def test_atomic_json_redacts_at_persistence_boundary(tmp_path: Path) -> None:
    path = tmp_path / "ledger.json"
    secret = "m" * 32
    atomic_write_json(path, {"command": "API_KEY=" + secret})
    result = path.read_text(encoding="utf-8")
    assert_no_secret(result, secret)
    assert "[REDACTED]" in result


def test_atomic_write_failure_preserves_previous_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "output.txt"
    path.write_text("previous", encoding="utf-8")

    def fail_replace(source: Path, destination: Path) -> None:
        raise OSError("controlled failure")

    monkeypatch.setattr("mentor_core.io.os.replace", fail_replace)
    with pytest.raises(IOSafetyError, match="atomic write failed"):
        atomic_write_text(path, "new")
    assert path.read_text(encoding="utf-8") == "previous"
    assert not list(tmp_path.glob(".output.txt.*.tmp"))


def test_atomic_write_detects_change_before_replace(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "output.txt"
    path.write_text("previous", encoding="utf-8")
    digest = sha256_file(path)
    calls = 0

    def changing_digest(target: Path) -> str:
        nonlocal calls
        calls += 1
        return digest if calls == 1 else "different"

    monkeypatch.setattr("mentor_core.io.sha256_file", changing_digest)
    with pytest.raises(RevisionConflictError, match="before atomic replacement"):
        atomic_write_text(path, "new", expected_sha256=digest)
    assert path.read_text(encoding="utf-8") == "previous"


def test_rejects_directory_and_symlink_targets(tmp_path: Path) -> None:
    with pytest.raises(IOSafetyError, match="not a regular file"):
        atomic_write_text(tmp_path, "content")
    target = tmp_path / "real.txt"
    target.write_text("safe", encoding="utf-8")
    link = tmp_path / "link.txt"
    try:
        link.symlink_to(target)
    except OSError:
        pytest.skip("symlink creation is unavailable")
    with pytest.raises(IOSafetyError, match="symlink"):
        atomic_write_text(link, "unsafe")
    with pytest.raises(IOSafetyError, match="symlink"):
        sha256_file(link)
    assert target.read_text(encoding="utf-8") == "safe"


def test_missing_input_and_digest_are_io_errors(tmp_path: Path) -> None:
    missing = tmp_path / "missing.json"
    with pytest.raises(IOSafetyError, match="cannot read input"):
        read_json(missing)
    with pytest.raises(IOSafetyError, match="revision check"):
        sha256_file(missing)
