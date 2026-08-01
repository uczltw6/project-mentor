from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from tools.run_official_skill_validation import validator_candidates
from tools.sync_skill import (
    SyncError,
    differences,
    release_files,
    synchronize,
    validate_destination,
)


def _skill(directory: Path, content: str = "source") -> Path:
    root = directory / ".agents" / "skills" / "project-mentor"
    root.mkdir(parents=True)
    (root / "SKILL.md").write_text(content, encoding="utf-8")
    return root


def test_sync_tool_detects_and_repairs_content_missing_and_extra_files(tmp_path: Path) -> None:
    source = _skill(tmp_path / "source", "source")
    destination = _skill(tmp_path / "destination", "different")
    (source / "references").mkdir()
    (source / "references" / "example.md").write_text("example", encoding="utf-8")
    (destination / "extra.md").write_text("extra", encoding="utf-8")
    mismatch = differences(source, destination)
    assert any("content differs" in item for item in mismatch)
    assert any("missing from destination" in item for item in mismatch)
    assert any("extra in destination" in item for item in mismatch)
    assert synchronize(source, destination) == 2
    assert differences(source, destination) == []


def test_sync_tool_ignores_generated_caches(tmp_path: Path) -> None:
    source = _skill(tmp_path / "source")
    cache = source / "__pycache__"
    cache.mkdir()
    (cache / "module.pyc").write_bytes(b"generated")
    files = release_files(source)
    assert list(files) == [Path("SKILL.md")]


def test_sync_tool_rejects_missing_unsafe_or_same_paths(tmp_path: Path) -> None:
    source = _skill(tmp_path / "source")
    with pytest.raises(SyncError, match="does not exist"):
        release_files(tmp_path / "missing")
    with pytest.raises(SyncError, match="must end"):
        validate_destination(tmp_path / "wrong")
    with pytest.raises(SyncError, match="different"):
        synchronize(source, source)


def test_sync_tool_rejects_symlinks_when_supported(tmp_path: Path) -> None:
    source = _skill(tmp_path / "source")
    external = tmp_path / "external.txt"
    external.write_text("external", encoding="utf-8")
    link = source / "link.txt"
    try:
        link.symlink_to(external)
    except OSError:
        pytest.skip("symlink creation is unavailable")
    with pytest.raises(SyncError, match="symlinks"):
        release_files(source)


def test_sync_tool_rejects_symlink_skill_root_when_supported(tmp_path: Path) -> None:
    real = _skill(tmp_path / "real")
    linked = tmp_path / "linked" / ".agents" / "skills" / "project-mentor"
    linked.parent.mkdir(parents=True)
    try:
        linked.symlink_to(real, target_is_directory=True)
    except OSError:
        pytest.skip("symlink creation is unavailable")
    with pytest.raises(SyncError, match="must not be a symlink"):
        release_files(linked)


def test_validator_candidates_preserve_explicit_precedence(tmp_path: Path) -> None:
    explicit = tmp_path / "quick_validate.py"
    candidates = validator_candidates(explicit)
    assert candidates[0] == explicit
    assert candidates[-1].name == "quick_validate.py"


def test_sync_preserves_source_and_removes_empty_destination_directories(tmp_path: Path) -> None:
    source = _skill(tmp_path / "source", "canonical")
    destination = _skill(tmp_path / "destination", "old")
    stale = destination / "stale" / "nested"
    stale.mkdir(parents=True)
    (stale / "old.md").write_text("old", encoding="utf-8")
    snapshot = shutil.copytree(source, tmp_path / "snapshot")
    synchronize(source, destination)
    assert differences(source, destination) == []
    assert differences(source, snapshot) == []
    assert not (destination / "stale").exists()
