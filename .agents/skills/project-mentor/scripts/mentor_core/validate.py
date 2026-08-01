"""Strict, fail-closed validation for V1 ledger contracts."""

from __future__ import annotations

import re
from collections.abc import Iterable
from datetime import datetime
from typing import Any

from .errors import DuplicateIdError, InvalidInputError, UnsupportedVersionError
from .model import (
    ACTORS,
    CLASSIFICATIONS,
    DEMONSTRATION_CAPABILITIES,
    EVENT_TYPES,
    EVIDENCE_CLASSES,
    EVIDENCE_KINDS,
    EXPOSURES,
    MAX_STRING_LENGTH,
    MODES,
    SCHEMA_VERSION,
    VCS_TYPES,
)

ID_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9._-]{2,127}$")
TIMESTAMP_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z$")


def _object(value: Any, path: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise InvalidInputError(f"{path} must be a JSON object")
    return value


def _exact_fields(
    value: dict[str, Any], path: str, required: Iterable[str], optional: Iterable[str] = ()
) -> None:
    required_set = set(required)
    optional_set = set(optional)
    missing = sorted(required_set - value.keys())
    unknown = sorted(value.keys() - required_set - optional_set)
    if missing:
        raise InvalidInputError(f"{path} is missing required field(s): {', '.join(missing)}")
    if unknown:
        raise InvalidInputError(f"{path} contains unsupported field(s): {', '.join(unknown)}")


def _string(value: Any, path: str, *, allow_empty: bool = False) -> str:
    if not isinstance(value, str):
        raise InvalidInputError(f"{path} must be a string")
    if "\x00" in value:
        raise InvalidInputError(f"{path} must not contain NUL characters")
    if len(value) > MAX_STRING_LENGTH:
        raise InvalidInputError(f"{path} exceeds the {MAX_STRING_LENGTH}-character limit")
    if not allow_empty and not value.strip():
        raise InvalidInputError(f"{path} must not be empty")
    return value


def _integer(value: Any, path: str, *, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise InvalidInputError(f"{path} must be an integer")
    if value < minimum:
        raise InvalidInputError(f"{path} must be at least {minimum}")
    return int(value)


def _enum(value: Any, path: str, allowed: frozenset[str]) -> str:
    result = _string(value, path)
    if result not in allowed:
        raise InvalidInputError(f"{path} must be one of: {', '.join(sorted(allowed))}")
    return result


def _id(value: Any, path: str) -> str:
    result = _string(value, path)
    if not ID_PATTERN.fullmatch(result):
        raise InvalidInputError(
            f"{path} must start with a letter and contain only letters, digits, dot, "
            "underscore, or hyphen"
        )
    return result


def _timestamp(value: Any, path: str) -> datetime:
    result = _string(value, path)
    if not TIMESTAMP_PATTERN.fullmatch(result):
        raise InvalidInputError(f"{path} must be a UTC ISO-8601 timestamp ending in Z")
    try:
        return datetime.fromisoformat(result.replace("Z", "+00:00"))
    except ValueError as error:
        raise InvalidInputError(f"{path} is not a valid calendar timestamp") from error


def _schema_version(value: Any, path: str) -> None:
    version = _integer(value, path, minimum=1)
    if version != SCHEMA_VERSION:
        raise UnsupportedVersionError(
            f"{path}={version} is unsupported; this helper supports schema_version={SCHEMA_VERSION}"
        )


def _list(value: Any, path: str) -> list[Any]:
    if not isinstance(value, list):
        raise InvalidInputError(f"{path} must be an array")
    return value


def _string_list(value: Any, path: str, *, identifiers: bool = False) -> list[str]:
    items = _list(value, path)
    result: list[str] = []
    for index, item in enumerate(items):
        checked = (
            _id(item, f"{path}[{index}]") if identifiers else _string(item, f"{path}[{index}]")
        )
        result.append(checked)
    if len(result) != len(set(result)):
        raise DuplicateIdError(f"{path} contains duplicate values")
    return result


def _unique_ids(items: list[dict[str, Any]], path: str) -> set[str]:
    seen: set[str] = set()
    for index, item in enumerate(items):
        identifier = _id(item.get("id"), f"{path}[{index}].id")
        if identifier in seen:
            raise DuplicateIdError(f"duplicate identifier in {path}: {identifier}")
        seen.add(identifier)
    return seen


def validate_evidence(value: Any, path: str = "evidence", *, project: bool = True) -> None:
    evidence = _object(value, path)
    _exact_fields(
        evidence,
        path,
        {"schema_version", "id", "class", "kind", "locator", "summary"},
        {"verifier", "result", "exit_status", "observed_at", "stale_from", "stale_reason"},
    )
    _schema_version(evidence["schema_version"], f"{path}.schema_version")
    _id(evidence["id"], f"{path}.id")
    evidence_class = _enum(evidence["class"], f"{path}.class", EVIDENCE_CLASSES)
    if project and evidence_class == "user_demonstrated":
        raise InvalidInputError(f"{path}.class cannot be user_demonstrated in project evidence")
    _enum(evidence["kind"], f"{path}.kind", EVIDENCE_KINDS)
    _string(evidence["locator"], f"{path}.locator")
    _string(evidence["summary"], f"{path}.summary")
    if "observed_at" in evidence:
        _timestamp(evidence["observed_at"], f"{path}.observed_at")
    if "exit_status" in evidence:
        _integer(evidence["exit_status"], f"{path}.exit_status", minimum=0)
    if evidence_class == "rule_verified":
        if "verifier" not in evidence or "result" not in evidence:
            raise InvalidInputError(f"{path} rule_verified evidence requires verifier and result")
        _string(evidence["verifier"], f"{path}.verifier")
        _string(evidence["result"], f"{path}.result")
    elif "verifier" in evidence or "result" in evidence:
        raise InvalidInputError(
            f"{path} verifier/result are allowed only for rule_verified evidence"
        )
    if evidence_class == "stale":
        stale_from = _enum(evidence.get("stale_from"), f"{path}.stale_from", EVIDENCE_CLASSES)
        if stale_from == "stale":
            raise InvalidInputError(f"{path}.stale_from must identify the previous non-stale class")
        _string(evidence.get("stale_reason"), f"{path}.stale_reason")
    elif "stale_from" in evidence or "stale_reason" in evidence:
        raise InvalidInputError(f"{path} stale metadata is allowed only when class is stale")


def validate_demonstration(value: Any, path: str = "demonstration") -> None:
    demonstration = _object(value, path)
    _exact_fields(
        demonstration,
        path,
        {"schema_version", "id", "timestamp", "class", "capability", "observation", "task_context"},
    )
    _schema_version(demonstration["schema_version"], f"{path}.schema_version")
    _id(demonstration["id"], f"{path}.id")
    _timestamp(demonstration["timestamp"], f"{path}.timestamp")
    if demonstration["class"] != "user_demonstrated":
        raise InvalidInputError(f"{path}.class must be user_demonstrated")
    _enum(demonstration["capability"], f"{path}.capability", DEMONSTRATION_CAPABILITIES)
    _string(demonstration["observation"], f"{path}.observation")
    _string(demonstration["task_context"], f"{path}.task_context")


def validate_concept(value: Any, path: str = "concept") -> None:
    concept = _object(value, path)
    _exact_fields(
        concept,
        path,
        {
            "id",
            "title",
            "plain_language",
            "classification",
            "why_now",
            "prerequisites",
            "project_evidence",
            "user_learning",
            "risks_if_changed",
            "next_practice",
        },
    )
    _id(concept["id"], f"{path}.id")
    _string(concept["title"], f"{path}.title")
    _string(concept["plain_language"], f"{path}.plain_language")
    _enum(concept["classification"], f"{path}.classification", CLASSIFICATIONS)
    _string(concept["why_now"], f"{path}.why_now")
    _string_list(concept["prerequisites"], f"{path}.prerequisites", identifiers=True)
    evidence_items = [
        _object(item, f"{path}.project_evidence[{index}]")
        for index, item in enumerate(_list(concept["project_evidence"], f"{path}.project_evidence"))
    ]
    for index, evidence in enumerate(evidence_items):
        validate_evidence(evidence, f"{path}.project_evidence[{index}]")
    _unique_ids(evidence_items, f"{path}.project_evidence")
    learning = _object(concept["user_learning"], f"{path}.user_learning")
    _exact_fields(learning, f"{path}.user_learning", {"exposure", "demonstrations"})
    exposure = _enum(learning["exposure"], f"{path}.user_learning.exposure", EXPOSURES)
    demonstrations = [
        _object(item, f"{path}.user_learning.demonstrations[{index}]")
        for index, item in enumerate(
            _list(learning["demonstrations"], f"{path}.user_learning.demonstrations")
        )
    ]
    for index, demonstration in enumerate(demonstrations):
        validate_demonstration(demonstration, f"{path}.user_learning.demonstrations[{index}]")
    _unique_ids(demonstrations, f"{path}.user_learning.demonstrations")
    if demonstrations and exposure == "not_seen":
        raise InvalidInputError(
            f"{path}.user_learning.exposure cannot be not_seen with demonstrations"
        )
    _string_list(concept["risks_if_changed"], f"{path}.risks_if_changed")
    _string(concept["next_practice"], f"{path}.next_practice")


def validate_decision(value: Any, path: str = "decision") -> None:
    decision = _object(value, path)
    _exact_fields(
        decision,
        path,
        {
            "id",
            "timestamp",
            "summary",
            "alternatives",
            "rationale",
            "concept_ids",
            "project_evidence",
        },
    )
    _id(decision["id"], f"{path}.id")
    _timestamp(decision["timestamp"], f"{path}.timestamp")
    _string(decision["summary"], f"{path}.summary")
    _string_list(decision["alternatives"], f"{path}.alternatives")
    _string(decision["rationale"], f"{path}.rationale")
    _string_list(decision["concept_ids"], f"{path}.concept_ids", identifiers=True)
    evidence = [
        _object(item, f"{path}.project_evidence[{index}]")
        for index, item in enumerate(
            _list(decision["project_evidence"], f"{path}.project_evidence")
        )
    ]
    for index, item in enumerate(evidence):
        validate_evidence(item, f"{path}.project_evidence[{index}]")
    _unique_ids(evidence, f"{path}.project_evidence")


def validate_milestone(value: Any, path: str = "milestone") -> None:
    milestone = _object(value, path)
    _exact_fields(
        milestone,
        path,
        {"id", "timestamp", "title", "result", "concept_ids", "project_evidence"},
    )
    _id(milestone["id"], f"{path}.id")
    _timestamp(milestone["timestamp"], f"{path}.timestamp")
    _string(milestone["title"], f"{path}.title")
    _string(milestone["result"], f"{path}.result")
    _string_list(milestone["concept_ids"], f"{path}.concept_ids", identifiers=True)
    evidence = [
        _object(item, f"{path}.project_evidence[{index}]")
        for index, item in enumerate(
            _list(milestone["project_evidence"], f"{path}.project_evidence")
        )
    ]
    for index, item in enumerate(evidence):
        validate_evidence(item, f"{path}.project_evidence[{index}]")
    _unique_ids(evidence, f"{path}.project_evidence")


def validate_receipt(value: Any, path: str = "receipt") -> None:
    receipt = _object(value, path)
    _exact_fields(
        receipt,
        path,
        {
            "schema_version",
            "generated_at",
            "session_id",
            "language",
            "goal",
            "mode",
            "milestone_ids",
            "concept_ids",
            "decision_ids",
            "deferred_concept_ids",
            "output_locator",
        },
    )
    _schema_version(receipt["schema_version"], f"{path}.schema_version")
    _timestamp(receipt["generated_at"], f"{path}.generated_at")
    _id(receipt["session_id"], f"{path}.session_id")
    _enum(receipt["language"], f"{path}.language", frozenset({"en", "zh"}))
    _string(receipt["goal"], f"{path}.goal")
    _enum(receipt["mode"], f"{path}.mode", MODES)
    for key in ("milestone_ids", "concept_ids", "decision_ids", "deferred_concept_ids"):
        _string_list(receipt[key], f"{path}.{key}", identifiers=True)
    _string(receipt["output_locator"], f"{path}.output_locator")


def validate_event(value: Any, path: str = "event") -> None:
    event = _object(value, path)
    _exact_fields(event, path, {"schema_version", "id", "timestamp", "type", "actor", "payload"})
    _schema_version(event["schema_version"], f"{path}.schema_version")
    _id(event["id"], f"{path}.id")
    _timestamp(event["timestamp"], f"{path}.timestamp")
    event_type = _enum(event["type"], f"{path}.type", EVENT_TYPES)
    actor = _enum(event["actor"], f"{path}.actor", ACTORS)
    payload = _object(event["payload"], f"{path}.payload")

    if event_type == "session_started":
        _exact_fields(payload, f"{path}.payload", {"goal", "mode"})
        _string(payload["goal"], f"{path}.payload.goal")
        _enum(payload["mode"], f"{path}.payload.mode", MODES)
    elif event_type == "mode_changed":
        _exact_fields(payload, f"{path}.payload", {"mode", "reason"})
        _enum(payload["mode"], f"{path}.payload.mode", MODES)
        _string(payload["reason"], f"{path}.payload.reason")
    elif event_type == "concept_identified":
        _exact_fields(payload, f"{path}.payload", {"concept"})
        validate_concept(payload["concept"], f"{path}.payload.concept")
        if payload["concept"]["user_learning"]["demonstrations"]:
            raise InvalidInputError(
                f"{path}.payload.concept must start without user demonstrations; "
                "use user_evidence_added"
            )
    elif event_type == "project_evidence_added":
        _exact_fields(payload, f"{path}.payload", {"concept_id", "evidence"})
        _id(payload["concept_id"], f"{path}.payload.concept_id")
        validate_evidence(payload["evidence"], f"{path}.payload.evidence")
    elif event_type == "user_evidence_added":
        _exact_fields(payload, f"{path}.payload", {"concept_id", "demonstration"})
        if actor not in {"user", "shared"}:
            raise InvalidInputError(
                f"{path}.actor must be user or shared when recording user evidence"
            )
        _id(payload["concept_id"], f"{path}.payload.concept_id")
        validate_demonstration(payload["demonstration"], f"{path}.payload.demonstration")
    elif event_type == "decision_recorded":
        _exact_fields(payload, f"{path}.payload", {"decision"})
        validate_decision(payload["decision"], f"{path}.payload.decision")
    elif event_type == "milestone_completed":
        _exact_fields(payload, f"{path}.payload", {"milestone"})
        validate_milestone(payload["milestone"], f"{path}.payload.milestone")
    elif event_type == "concept_deferred":
        _exact_fields(payload, f"{path}.payload", {"concept_id", "reason"})
        _id(payload["concept_id"], f"{path}.payload.concept_id")
        _string(payload["reason"], f"{path}.payload.reason")
    elif event_type == "evidence_marked_stale":
        _exact_fields(payload, f"{path}.payload", {"concept_id", "evidence_id", "reason"})
        _id(payload["concept_id"], f"{path}.payload.concept_id")
        _id(payload["evidence_id"], f"{path}.payload.evidence_id")
        _string(payload["reason"], f"{path}.payload.reason")
    elif event_type == "receipt_rendered":
        _exact_fields(payload, f"{path}.payload", {"receipt"})
        validate_receipt(payload["receipt"], f"{path}.payload.receipt")


def _validate_references(ledger: dict[str, Any]) -> None:
    concepts = {concept["id"] for concept in ledger["concepts"]}
    for concept in ledger["concepts"]:
        for prerequisite in concept["prerequisites"]:
            if prerequisite not in concepts:
                raise InvalidInputError(
                    f"concept {concept['id']} references missing prerequisite {prerequisite}"
                )
            if prerequisite == concept["id"]:
                raise InvalidInputError(f"concept {concept['id']} cannot be its own prerequisite")
    for collection_name in ("decisions", "milestones"):
        for item in ledger[collection_name]:
            for concept_id in item["concept_ids"]:
                if concept_id not in concepts:
                    raise InvalidInputError(
                        f"{collection_name[:-1]} {item['id']} references missing concept "
                        f"{concept_id}"
                    )
    for record in ledger["deferred"]:
        if record["concept_id"] not in concepts:
            raise InvalidInputError(
                f"deferred record references missing concept {record['concept_id']}"
            )


def _validate_global_evidence_ids(ledger: dict[str, Any]) -> None:
    seen_project: set[str] = set()
    seen_user: set[str] = set()
    evidence_groups = [concept["project_evidence"] for concept in ledger["concepts"]] + [
        item["project_evidence"] for item in ledger["decisions"] + ledger["milestones"]
    ]
    for evidence in (item for group in evidence_groups for item in group):
        if evidence["id"] in seen_project:
            raise DuplicateIdError(f"duplicate project evidence identifier: {evidence['id']}")
        seen_project.add(evidence["id"])
    for concept in ledger["concepts"]:
        for demonstration in concept["user_learning"]["demonstrations"]:
            if demonstration["id"] in seen_user:
                raise DuplicateIdError(f"duplicate user evidence identifier: {demonstration['id']}")
            seen_user.add(demonstration["id"])
    overlap = seen_project & seen_user
    if overlap:
        raise DuplicateIdError(
            f"project and user evidence identifiers overlap: {sorted(overlap)[0]}"
        )


def validate_ledger(value: Any, path: str = "ledger") -> None:
    ledger = _object(value, path)
    _exact_fields(
        ledger,
        path,
        {
            "schema_version",
            "revision",
            "session",
            "project",
            "milestones",
            "concepts",
            "decisions",
            "events",
            "evidence_gaps",
            "deferred",
        },
    )
    _schema_version(ledger["schema_version"], f"{path}.schema_version")
    revision = _integer(ledger["revision"], f"{path}.revision")
    session = _object(ledger["session"], f"{path}.session")
    _exact_fields(session, f"{path}.session", {"id", "goal", "mode", "created_at", "updated_at"})
    _id(session["id"], f"{path}.session.id")
    _string(session["goal"], f"{path}.session.goal")
    _enum(session["mode"], f"{path}.session.mode", MODES)
    created = _timestamp(session["created_at"], f"{path}.session.created_at")
    updated = _timestamp(session["updated_at"], f"{path}.session.updated_at")
    if updated < created:
        raise InvalidInputError(f"{path}.session.updated_at must not precede created_at")

    project = _object(ledger["project"], f"{path}.project")
    _exact_fields(project, f"{path}.project", {"root_label", "vcs", "baseline"})
    _string(project["root_label"], f"{path}.project.root_label")
    _enum(project["vcs"], f"{path}.project.vcs", VCS_TYPES)
    if project["baseline"] is not None:
        _string(project["baseline"], f"{path}.project.baseline")

    concepts = [
        _object(item, f"{path}.concepts[{index}]")
        for index, item in enumerate(_list(ledger["concepts"], f"{path}.concepts"))
    ]
    for index, concept in enumerate(concepts):
        validate_concept(concept, f"{path}.concepts[{index}]")
    _unique_ids(concepts, f"{path}.concepts")

    decisions = [
        _object(item, f"{path}.decisions[{index}]")
        for index, item in enumerate(_list(ledger["decisions"], f"{path}.decisions"))
    ]
    for index, decision in enumerate(decisions):
        validate_decision(decision, f"{path}.decisions[{index}]")
    _unique_ids(decisions, f"{path}.decisions")

    milestones = [
        _object(item, f"{path}.milestones[{index}]")
        for index, item in enumerate(_list(ledger["milestones"], f"{path}.milestones"))
    ]
    for index, milestone in enumerate(milestones):
        validate_milestone(milestone, f"{path}.milestones[{index}]")
    _unique_ids(milestones, f"{path}.milestones")

    events = [
        _object(item, f"{path}.events[{index}]")
        for index, item in enumerate(_list(ledger["events"], f"{path}.events"))
    ]
    for index, event in enumerate(events):
        validate_event(event, f"{path}.events[{index}]")
    _unique_ids(events, f"{path}.events")
    if revision != len(events):
        raise InvalidInputError(f"{path}.revision must equal the number of applied events")

    gaps = [
        _object(item, f"{path}.evidence_gaps[{index}]")
        for index, item in enumerate(_list(ledger["evidence_gaps"], f"{path}.evidence_gaps"))
    ]
    for index, gap in enumerate(gaps):
        gap_path = f"{path}.evidence_gaps[{index}]"
        _exact_fields(gap, gap_path, {"id", "class", "summary", "needed_for"})
        _id(gap["id"], f"{gap_path}.id")
        if gap["class"] != "unavailable":
            raise InvalidInputError(f"{gap_path}.class must be unavailable")
        _string(gap["summary"], f"{gap_path}.summary")
        _string(gap["needed_for"], f"{gap_path}.needed_for")
    _unique_ids(gaps, f"{path}.evidence_gaps")

    deferred = [
        _object(item, f"{path}.deferred[{index}]")
        for index, item in enumerate(_list(ledger["deferred"], f"{path}.deferred"))
    ]
    for index, item in enumerate(deferred):
        item_path = f"{path}.deferred[{index}]"
        _exact_fields(item, item_path, {"concept_id", "reason", "timestamp"})
        _id(item["concept_id"], f"{item_path}.concept_id")
        _string(item["reason"], f"{item_path}.reason")
        _timestamp(item["timestamp"], f"{item_path}.timestamp")
    concept_ids = [item["concept_id"] for item in deferred]
    if len(concept_ids) != len(set(concept_ids)):
        raise DuplicateIdError(f"{path}.deferred contains duplicate concept identifiers")

    _validate_references(ledger)
    _validate_global_evidence_ids(ledger)
