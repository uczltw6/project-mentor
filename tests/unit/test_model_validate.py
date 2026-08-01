from __future__ import annotations

from copy import deepcopy
from typing import Any

import pytest
from conftest import assert_no_secret
from mentor_core.errors import DuplicateIdError, InvalidInputError, UnsupportedVersionError
from mentor_core.model import SCHEMA_VERSION, canonical_json, new_ledger
from mentor_core.validate import (
    validate_concept,
    validate_demonstration,
    validate_event,
    validate_evidence,
    validate_ledger,
    validate_receipt,
)


def test_new_ledger_is_valid_deterministic_and_redacted() -> None:
    secret = "s" * 32
    ledger = new_ledger(
        goal="API_KEY=" + secret + " run sample",
        session_id="pm-fixed-session",
        created_at="2026-08-01T12:00:00Z",
        root_label="sample",
        vcs="git",
        baseline="abc123",
    )
    validate_ledger(ledger)
    rendered = canonical_json(ledger)
    assert_no_secret(rendered, secret)
    assert "[REDACTED]" in rendered
    assert rendered == canonical_json(ledger)
    assert ledger["revision"] == 0


def test_new_ledger_generates_stable_storable_identifier() -> None:
    ledger = new_ledger(goal="Run it", created_at="2026-08-01T00:00:00Z")
    assert ledger["session"]["id"].startswith("pm-")
    validate_ledger(ledger)


@pytest.mark.parametrize(
    ("mutation", "error_type"),
    [
        (lambda item: item.update(schema_version=2), UnsupportedVersionError),
        (lambda item: item.update(revision=-1), InvalidInputError),
        (lambda item: item.update(extra=True), InvalidInputError),
        (lambda item: item.pop("project"), InvalidInputError),
        (lambda item: item["session"].update(mode="lecture"), InvalidInputError),
        (lambda item: item["session"].update(id="bad id"), InvalidInputError),
        (lambda item: item["session"].update(goal=""), InvalidInputError),
        (lambda item: item["session"].update(goal="bad\x00goal"), InvalidInputError),
        (lambda item: item["session"].update(created_at="yesterday"), InvalidInputError),
        (
            lambda item: item["session"].update(updated_at="2025-08-01T00:00:00Z"),
            InvalidInputError,
        ),
        (lambda item: item["project"].update(vcs="svn"), InvalidInputError),
        (lambda item: item["project"].update(baseline=3), InvalidInputError),
        (lambda item: item.update(revision=True), InvalidInputError),
    ],
)
def test_ledger_rejects_invalid_contract(
    ledger: dict[str, Any], mutation: Any, error_type: type[Exception]
) -> None:
    mutation(ledger)
    with pytest.raises(error_type):
        validate_ledger(ledger)


def test_ledger_revision_must_match_events(ledger: dict[str, Any], event_factory: Any) -> None:
    ledger["events"].append(
        event_factory(
            "session_started", {"goal": "Run the sample", "mode": "guided"}, actor="shared"
        )
    )
    with pytest.raises(InvalidInputError, match="revision"):
        validate_ledger(ledger)


def test_evidence_variants(evidence: dict[str, Any]) -> None:
    validate_evidence(evidence)

    verified = deepcopy(evidence)
    verified.update(
        id="ev-rule-001",
        **{"class": "rule_verified"},
        verifier="json-schema-v1",
        result="passed",
        exit_status=0,
        observed_at="2026-08-01T00:01:00Z",
    )
    validate_evidence(verified)

    missing_verifier = deepcopy(verified)
    missing_verifier.pop("verifier")
    with pytest.raises(InvalidInputError, match="requires verifier"):
        validate_evidence(missing_verifier)

    observed_with_verifier = deepcopy(evidence)
    observed_with_verifier["verifier"] = "unexpected"
    with pytest.raises(InvalidInputError, match="allowed only"):
        validate_evidence(observed_with_verifier)

    stale = deepcopy(evidence)
    stale.update(**{"class": "stale"}, stale_from="observed", stale_reason="The file changed.")
    validate_evidence(stale)

    stale["stale_from"] = "stale"
    with pytest.raises(InvalidInputError, match="previous non-stale"):
        validate_evidence(stale)


def test_project_evidence_rejects_user_class(evidence: dict[str, Any]) -> None:
    evidence["class"] = "user_demonstrated"
    with pytest.raises(InvalidInputError, match="project evidence"):
        validate_evidence(evidence)
    validate_evidence(evidence, project=False)


def test_demonstration_is_strict(demonstration: dict[str, Any]) -> None:
    validate_demonstration(demonstration)
    demonstration["class"] = "observed"
    with pytest.raises(InvalidInputError, match="user_demonstrated"):
        validate_demonstration(demonstration)


def test_concept_rejects_duplicate_and_inconsistent_learning(
    concept: dict[str, Any], demonstration: dict[str, Any], evidence: dict[str, Any]
) -> None:
    validate_concept(concept)
    concept["project_evidence"] = [evidence, deepcopy(evidence)]
    with pytest.raises(DuplicateIdError):
        validate_concept(concept)

    concept["project_evidence"] = []
    concept["user_learning"]["demonstrations"] = [demonstration]
    with pytest.raises(InvalidInputError, match="cannot be not_seen"):
        validate_concept(concept)


def test_ledger_validates_references_and_global_ids(
    ledger: dict[str, Any], concept: dict[str, Any], evidence: dict[str, Any]
) -> None:
    concept["project_evidence"] = [evidence]
    ledger["concepts"] = [concept]
    validate_ledger(ledger)

    concept["prerequisites"] = ["missing-concept"]
    with pytest.raises(InvalidInputError, match="missing prerequisite"):
        validate_ledger(ledger)

    concept["prerequisites"] = [concept["id"]]
    with pytest.raises(InvalidInputError, match="own prerequisite"):
        validate_ledger(ledger)


def test_ledger_rejects_missing_decision_and_milestone_concepts(
    ledger: dict[str, Any], concept: dict[str, Any]
) -> None:
    ledger["concepts"] = [concept]
    ledger["decisions"] = [
        {
            "id": "decision-001",
            "timestamp": "2026-08-01T00:01:00Z",
            "summary": "Choose isolation.",
            "alternatives": [],
            "rationale": "Avoid conflicts.",
            "concept_ids": ["missing-concept"],
            "project_evidence": [],
        }
    ]
    with pytest.raises(InvalidInputError, match="references missing concept"):
        validate_ledger(ledger)

    ledger["decisions"] = []
    ledger["milestones"] = [
        {
            "id": "milestone-001",
            "timestamp": "2026-08-01T00:02:00Z",
            "title": "Runs",
            "result": "Passed.",
            "concept_ids": ["missing-concept"],
            "project_evidence": [],
        }
    ]
    with pytest.raises(InvalidInputError, match="references missing concept"):
        validate_ledger(ledger)


def test_ledger_rejects_duplicate_project_and_user_evidence_ids(
    ledger: dict[str, Any],
    concept: dict[str, Any],
    evidence: dict[str, Any],
    demonstration: dict[str, Any],
) -> None:
    concept["project_evidence"] = [evidence]
    concept["user_learning"] = {"exposure": "reinforced", "demonstrations": [demonstration]}
    ledger["concepts"] = [concept]
    ledger["decisions"] = [
        {
            "id": "decision-001",
            "timestamp": "2026-08-01T00:01:00Z",
            "summary": "Choose isolation.",
            "alternatives": [],
            "rationale": "Avoid conflicts.",
            "concept_ids": [concept["id"]],
            "project_evidence": [deepcopy(evidence)],
        }
    ]
    with pytest.raises(DuplicateIdError, match="project evidence"):
        validate_ledger(ledger)

    ledger["decisions"] = []
    concept["user_learning"]["demonstrations"][0]["id"] = evidence["id"]
    with pytest.raises(DuplicateIdError, match="overlap"):
        validate_ledger(ledger)


def test_deferred_and_gap_contracts(ledger: dict[str, Any], concept: dict[str, Any]) -> None:
    ledger["concepts"] = [concept]
    ledger["evidence_gaps"] = [
        {
            "id": "gap-history-001",
            "class": "unavailable",
            "summary": "Commit history is unavailable.",
            "needed_for": "Establish the implementation baseline.",
        }
    ]
    ledger["deferred"] = [
        {
            "concept_id": concept["id"],
            "reason": "Background only.",
            "timestamp": "2026-08-01T00:02:00Z",
        }
    ]
    validate_ledger(ledger)
    ledger["evidence_gaps"][0]["class"] = "observed"
    with pytest.raises(InvalidInputError, match="must be unavailable"):
        validate_ledger(ledger)


def test_event_validation_protects_user_claims(
    concept: dict[str, Any], demonstration: dict[str, Any], event_factory: Any
) -> None:
    concept["user_learning"] = {"exposure": "reinforced", "demonstrations": [demonstration]}
    smuggled = event_factory("concept_identified", {"concept": concept})
    with pytest.raises(InvalidInputError, match="must start without"):
        validate_event(smuggled)

    user_event = event_factory(
        "user_evidence_added",
        {"concept_id": concept["id"], "demonstration": demonstration},
        actor="agent",
    )
    with pytest.raises(InvalidInputError, match="user or shared"):
        validate_event(user_event)


def test_receipt_contract_is_strict(ledger: dict[str, Any]) -> None:
    receipt = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": "2026-08-01T00:10:00Z",
        "session_id": ledger["session"]["id"],
        "language": "en",
        "goal": ledger["session"]["goal"],
        "mode": ledger["session"]["mode"],
        "milestone_ids": [],
        "concept_ids": [],
        "decision_ids": [],
        "deferred_concept_ids": [],
        "output_locator": "chat",
    }
    validate_receipt(receipt)
    receipt["language"] = "fr"
    with pytest.raises(InvalidInputError):
        validate_receipt(receipt)
