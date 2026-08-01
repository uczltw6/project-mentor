"""Canonical constants and ledger construction."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

SCHEMA_VERSION = 1
MAX_INPUT_BYTES = 1_048_576
MAX_STRING_LENGTH = 16_384

MODES = frozenset({"recap", "guided", "hands_on"})
CLASSIFICATIONS = frozenset({"blocking_now", "explain_when_encountered", "deferred"})
EVIDENCE_CLASSES = frozenset(
    {
        "observed",
        "declared",
        "inferred",
        "rule_verified",
        "user_demonstrated",
        "unavailable",
        "stale",
    }
)
EVIDENCE_KINDS = frozenset(
    {
        "command",
        "commit",
        "config_key",
        "conversation",
        "decision",
        "diff",
        "file_digest",
        "file_symbol",
        "runtime_result",
        "test_result",
        "unavailable",
    }
)
EXPOSURES = frozenset({"not_seen", "encountered", "reinforced"})
DEMONSTRATION_CAPABILITIES = frozenset(
    {
        "recognized",
        "explained",
        "applied_with_guidance",
        "applied_independently",
        "transferred",
    }
)
ACTORS = frozenset({"user", "agent", "shared", "rule"})
VCS_TYPES = frozenset({"git", "none", "other", "unknown"})
EVENT_TYPES = frozenset(
    {
        "session_started",
        "mode_changed",
        "concept_identified",
        "project_evidence_added",
        "user_evidence_added",
        "decision_recorded",
        "milestone_completed",
        "concept_deferred",
        "evidence_marked_stale",
        "receipt_rendered",
    }
)


def utc_now() -> str:
    """Return the current UTC timestamp in the canonical second-resolution form."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def canonical_json(value: Any) -> str:
    """Serialize JSON deterministically for storage and replay comparison."""
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def new_ledger(
    *,
    goal: str,
    mode: str = "guided",
    session_id: str | None = None,
    created_at: str | None = None,
    root_label: str = "project",
    vcs: str = "unknown",
    baseline: str | None = None,
) -> dict[str, Any]:
    """Build and validate an empty V1 ledger."""
    from .redact import redact_text

    timestamp = created_at or utc_now()
    ledger: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "revision": 0,
        "session": {
            "id": session_id or f"pm-{uuid.uuid4().hex}",
            "goal": redact_text(goal),
            "mode": mode,
            "created_at": timestamp,
            "updated_at": timestamp,
        },
        "project": {
            "root_label": redact_text(root_label),
            "vcs": vcs,
            "baseline": redact_text(baseline) if baseline is not None else None,
        },
        "milestones": [],
        "concepts": [],
        "decisions": [],
        "events": [],
        "evidence_gaps": [],
        "deferred": [],
    }
    from .validate import validate_ledger

    validate_ledger(ledger)
    return ledger
