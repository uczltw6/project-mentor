"""Pure, validated, idempotent event application."""

from __future__ import annotations

import copy
from datetime import datetime
from typing import Any

from .errors import DuplicateIdError, EventConflictError, InvalidInputError, RevisionConflictError
from .model import canonical_json
from .redact import redact_data
from .validate import validate_event, validate_ledger


def _by_id(items: list[dict[str, Any]], identifier: str, kind: str) -> dict[str, Any]:
    match = next((item for item in items if item["id"] == identifier), None)
    if match is None:
        raise InvalidInputError(f"{kind} does not exist: {identifier}")
    return match


def _ensure_new_id(items: list[dict[str, Any]], identifier: str, kind: str) -> None:
    if any(item["id"] == identifier for item in items):
        raise DuplicateIdError(f"duplicate {kind} identifier: {identifier}")


def _later_timestamp(left: str, right: str) -> str:
    left_value = datetime.fromisoformat(left.replace("Z", "+00:00"))
    right_value = datetime.fromisoformat(right.replace("Z", "+00:00"))
    return right if right_value > left_value else left


def _sort_ledger(ledger: dict[str, Any]) -> None:
    ledger["concepts"].sort(key=lambda item: item["id"])
    for concept in ledger["concepts"]:
        concept["project_evidence"].sort(key=lambda item: item["id"])
        concept["user_learning"]["demonstrations"].sort(
            key=lambda item: (item["timestamp"], item["id"])
        )
    ledger["decisions"].sort(key=lambda item: (item["timestamp"], item["id"]))
    ledger["milestones"].sort(key=lambda item: (item["timestamp"], item["id"]))
    ledger["events"].sort(key=lambda item: (item["timestamp"], item["id"]))
    ledger["evidence_gaps"].sort(key=lambda item: item["id"])
    ledger["deferred"].sort(key=lambda item: item["concept_id"])


def _apply_transition(ledger: dict[str, Any], event: dict[str, Any]) -> None:
    event_type = event["type"]
    payload = event["payload"]
    if event_type == "session_started":
        if payload["goal"] != ledger["session"]["goal"] or payload["mode"] != ledger["session"]["mode"]:
            raise EventConflictError("session_started payload does not match the initialized session")
    elif event_type == "mode_changed":
        ledger["session"]["mode"] = payload["mode"]
    elif event_type == "concept_identified":
        concept = copy.deepcopy(payload["concept"])
        _ensure_new_id(ledger["concepts"], concept["id"], "concept")
        ledger["concepts"].append(concept)
    elif event_type == "project_evidence_added":
        concept = _by_id(ledger["concepts"], payload["concept_id"], "concept")
        evidence = copy.deepcopy(payload["evidence"])
        _ensure_new_id(concept["project_evidence"], evidence["id"], "project evidence")
        concept["project_evidence"].append(evidence)
        if concept["user_learning"]["exposure"] == "not_seen":
            concept["user_learning"]["exposure"] = "encountered"
    elif event_type == "user_evidence_added":
        concept = _by_id(ledger["concepts"], payload["concept_id"], "concept")
        demonstration = copy.deepcopy(payload["demonstration"])
        _ensure_new_id(
            concept["user_learning"]["demonstrations"], demonstration["id"], "user evidence"
        )
        concept["user_learning"]["demonstrations"].append(demonstration)
        concept["user_learning"]["exposure"] = "reinforced"
    elif event_type == "decision_recorded":
        decision = copy.deepcopy(payload["decision"])
        _ensure_new_id(ledger["decisions"], decision["id"], "decision")
        ledger["decisions"].append(decision)
    elif event_type == "milestone_completed":
        milestone = copy.deepcopy(payload["milestone"])
        _ensure_new_id(ledger["milestones"], milestone["id"], "milestone")
        ledger["milestones"].append(milestone)
    elif event_type == "concept_deferred":
        concept = _by_id(ledger["concepts"], payload["concept_id"], "concept")
        if any(item["concept_id"] == concept["id"] for item in ledger["deferred"]):
            raise DuplicateIdError(f"concept is already deferred: {concept['id']}")
        concept["classification"] = "deferred"
        ledger["deferred"].append(
            {
                "concept_id": concept["id"],
                "reason": payload["reason"],
                "timestamp": event["timestamp"],
            }
        )
    elif event_type == "evidence_marked_stale":
        concept = _by_id(ledger["concepts"], payload["concept_id"], "concept")
        evidence = _by_id(concept["project_evidence"], payload["evidence_id"], "evidence")
        if evidence["class"] == "stale":
            raise InvalidInputError(f"evidence is already stale: {evidence['id']}")
        evidence["stale_from"] = evidence["class"]
        evidence["class"] = "stale"
        evidence["stale_reason"] = payload["reason"]
    elif event_type == "receipt_rendered":
        receipt = payload["receipt"]
        if receipt["session_id"] != ledger["session"]["id"]:
            raise InvalidInputError("receipt session_id does not match the ledger session")
        known = {
            "concept_ids": {item["id"] for item in ledger["concepts"]},
            "decision_ids": {item["id"] for item in ledger["decisions"]},
            "milestone_ids": {item["id"] for item in ledger["milestones"]},
            "deferred_concept_ids": {item["concept_id"] for item in ledger["deferred"]},
        }
        for key, valid_ids in known.items():
            missing = set(receipt[key]) - valid_ids
            if missing:
                raise InvalidInputError(f"receipt {key} references missing identifier: {sorted(missing)[0]}")


def apply_event(
    ledger: dict[str, Any], event: dict[str, Any], *, expected_revision: int
) -> tuple[dict[str, Any], bool]:
    """Return a new ledger and whether the event changed it."""
    validate_ledger(ledger)
    if ledger["revision"] != expected_revision:
        raise RevisionConflictError(
            f"expected revision {expected_revision}, found {ledger['revision']}; reload and retry"
        )

    redacted_event = redact_data(copy.deepcopy(event))
    validate_event(redacted_event)
    if datetime.fromisoformat(redacted_event["timestamp"].replace("Z", "+00:00")) < datetime.fromisoformat(
        ledger["session"]["created_at"].replace("Z", "+00:00")
    ):
        raise InvalidInputError("event timestamp must not precede the session creation time")
    existing = next(
        (item for item in ledger["events"] if item["id"] == redacted_event["id"]), None
    )
    if existing is not None:
        if canonical_json(existing) == canonical_json(redacted_event):
            return copy.deepcopy(ledger), False
        raise EventConflictError(
            f"event identifier {redacted_event['id']} was already used with different content"
        )

    updated = copy.deepcopy(ledger)
    _apply_transition(updated, redacted_event)
    updated["events"].append(redacted_event)
    updated["revision"] += 1
    updated["session"]["updated_at"] = _later_timestamp(
        updated["session"]["updated_at"], redacted_event["timestamp"]
    )
    _sort_ledger(updated)
    validate_ledger(updated)
    return updated, True
