from __future__ import annotations

import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

REPOSITORY = Path(__file__).resolve().parents[1]
SKILL = REPOSITORY / ".agents" / "skills" / "project-mentor"
SCRIPTS = SKILL / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from mentor_core.model import SCHEMA_VERSION, new_ledger  # noqa: E402


def assert_no_secret(text: str, *secrets: str) -> None:
    if any(secret in text for secret in secrets):
        pytest.fail("a synthetic secret appeared in output", pytrace=False)


@pytest.fixture
def ledger() -> dict[str, Any]:
    return new_ledger(
        goal="Run the sample",
        mode="guided",
        session_id="pm-test-session",
        created_at="2026-08-01T00:00:00Z",
        root_label="sample",
        vcs="none",
    )


@pytest.fixture
def concept() -> dict[str, Any]:
    return {
        "id": "dependency-isolation",
        "title": "Dependency isolation",
        "plain_language": "A project-specific environment keeps packages separate.",
        "classification": "explain_when_encountered",
        "why_now": "The sample needs a separate dependency set.",
        "prerequisites": [],
        "project_evidence": [],
        "user_learning": {"exposure": "not_seen", "demonstrations": []},
        "risks_if_changed": ["Packages could resolve from another environment."],
        "next_practice": "Create an isolated environment in a fresh sample.",
    }


@pytest.fixture
def evidence() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "id": "ev-project-001",
        "class": "observed",
        "kind": "config_key",
        "locator": "pyproject.toml#[project.dependencies]",
        "summary": "Dependencies are declared here.",
    }


@pytest.fixture
def demonstration() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "id": "ev-user-001",
        "timestamp": "2026-08-01T00:03:00Z",
        "class": "user_demonstrated",
        "capability": "recognized",
        "observation": "The user selected the project-local interpreter.",
        "task_context": "Choose an interpreter for the sample.",
    }


@pytest.fixture
def event_factory() -> Callable[..., dict[str, Any]]:
    def make_event(
        event_type: str,
        payload: dict[str, Any],
        *,
        event_id: str | None = None,
        timestamp: str = "2026-08-01T00:01:00Z",
        actor: str = "agent",
    ) -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "id": event_id or f"evt-{event_type.replace('_', '-')}",
            "timestamp": timestamp,
            "type": event_type,
            "actor": actor,
            "payload": payload,
        }

    return make_event
