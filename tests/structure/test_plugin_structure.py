from __future__ import annotations

import json
import re
from pathlib import Path

from conftest import SKILL

from tools.sync_skill import differences

REPOSITORY = Path(__file__).resolve().parents[2]
PLUGIN_SKILL = REPOSITORY / "skills" / "project-mentor"


def test_plugin_manifest_is_skills_only_and_release_ready() -> None:
    manifest = json.loads(
        (REPOSITORY / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
    )
    assert manifest["name"] == "project-mentor"
    assert manifest["version"] == "0.2.0"
    assert manifest["skills"] == "./skills/"
    assert "apps" not in manifest and "mcpServers" not in manifest
    assert manifest["repository"] == "https://github.com/uczltw6/project-mentor"
    assert set(manifest) == {
        "name",
        "version",
        "description",
        "author",
        "homepage",
        "repository",
        "license",
        "keywords",
        "skills",
        "interface",
    }
    assert re.fullmatch(r"(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)", manifest["version"])
    assert manifest["license"] == "MIT"
    assert manifest["author"]["name"] and manifest["author"]["url"].startswith("https://")
    interface = manifest["interface"]
    required_interface = {
        "displayName",
        "shortDescription",
        "longDescription",
        "developerName",
        "category",
        "capabilities",
        "websiteURL",
        "defaultPrompt",
    }
    assert set(interface) == required_interface
    assert all(isinstance(item, str) and item for item in interface["capabilities"])
    assert 1 <= len(interface["defaultPrompt"]) <= 3
    assert all(0 < len(item) <= 128 for item in interface["defaultPrompt"])
    assert interface["websiteURL"].startswith("https://")


def test_public_and_plugin_skill_copies_are_identical() -> None:
    assert differences(SKILL, PLUGIN_SKILL) == []
