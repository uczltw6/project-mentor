from __future__ import annotations

import json
from pathlib import Path

from mentor_core import __version__

REPOSITORY = Path(__file__).resolve().parents[2]
VERSION = "0.3.0"


def test_distribution_name_version_and_entry_points_are_explicit() -> None:
    pyproject = (REPOSITORY / "pyproject.toml").read_text(encoding="utf-8")
    for contract in (
        'name = "project-mentor"',
        f'version = "{VERSION}"',
        'requires-python = ">=3.10"',
        'license = "MIT"',
        'license-files = ["LICENSE"]',
        'project-mentor = "project_mentor_cli.cli:main"',
        'packages = ["project_mentor_cli"]',
        'project_mentor_cli = ".agents/skills/project-mentor/scripts/mentor_core"',
    ):
        assert contract in pyproject


def test_runtime_plugin_and_release_versions_are_coherent() -> None:
    manifest = json.loads((REPOSITORY / ".codex-plugin" / "plugin.json").read_text("utf-8"))
    assert __version__ == manifest["version"] == VERSION
    assert f"## [{VERSION}]" in (REPOSITORY / "CHANGELOG.md").read_text(encoding="utf-8")

    public_runtime = (
        REPOSITORY / "skills" / "project-mentor" / "scripts" / "mentor_core" / "__init__.py"
    ).read_text(encoding="utf-8")
    assert f'__version__ = "{VERSION}"' in public_runtime
