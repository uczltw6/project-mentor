from __future__ import annotations

from copy import deepcopy
from typing import Any

import pytest
from conftest import assert_no_secret
from mentor_core.events import apply_event
from mentor_core.model import SCHEMA_VERSION
from mentor_core.render import build_receipt_contract, render_receipt, summarize


def _rich_ledger(
    ledger: dict[str, Any],
    concept: dict[str, Any],
    evidence: dict[str, Any],
    demonstration: dict[str, Any],
    event_factory: Any,
) -> dict[str, Any]:
    concept["project_evidence"] = [evidence]
    concept_event = event_factory(
        "concept_identified", {"concept": concept}, event_id="evt-concept-001"
    )
    current, _ = apply_event(ledger, concept_event, expected_revision=0)
    user_event = event_factory(
        "user_evidence_added",
        {"concept_id": concept["id"], "demonstration": demonstration},
        event_id="evt-user-001",
        timestamp="2026-08-01T00:03:00Z",
        actor="user",
    )
    current, _ = apply_event(current, user_event, expected_revision=1)
    decision = {
        "id": "decision-isolate",
        "timestamp": "2026-08-01T00:04:00Z",
        "summary": "Use a project-local environment.",
        "alternatives": ["Use system Python."],
        "rationale": "Avoid package conflicts.",
        "concept_ids": [concept["id"]],
        "project_evidence": [],
    }
    current, _ = apply_event(
        current,
        event_factory(
            "decision_recorded",
            {"decision": decision},
            event_id="evt-decision-001",
            timestamp="2026-08-01T00:04:00Z",
            actor="shared",
        ),
        expected_revision=2,
    )
    milestone = {
        "id": "milestone-runs",
        "timestamp": "2026-08-01T00:05:00Z",
        "title": "Environment runs",
        "result": "The launch command passed.",
        "concept_ids": [concept["id"]],
        "project_evidence": [],
    }
    current, _ = apply_event(
        current,
        event_factory(
            "milestone_completed",
            {"milestone": milestone},
            event_id="evt-milestone-001",
            timestamp="2026-08-01T00:05:00Z",
            actor="shared",
        ),
        expected_revision=3,
    )
    return current


def test_english_and_chinese_receipts_are_deterministic_and_separate_claims(
    ledger: dict[str, Any],
    concept: dict[str, Any],
    evidence: dict[str, Any],
    demonstration: dict[str, Any],
    event_factory: Any,
) -> None:
    current = _rich_ledger(ledger, concept, evidence, demonstration, event_factory)
    english_contract = build_receipt_contract(
        current,
        language="en",
        generated_at="2026-08-01T00:10:00Z",
        output_locator="chat",
    )
    first = render_receipt(current, english_contract)
    second = render_receipt(current, deepcopy(english_contract))
    assert first == second
    assert "## What we completed" in first
    assert "Agent demonstrated:" in first and "You demonstrated:" in first
    assert "recognized" in first
    assert "pyproject.toml#[project.dependencies]" in first

    chinese_contract = build_receipt_contract(
        current,
        language="zh",
        generated_at="2026-08-01T00:10:00Z",
        output_locator="chat",
    )
    chinese = render_receipt(current, chinese_contract)
    assert "## 已完成的工作" in chinese
    assert "Agent 展示" in chinese and "你展示的内容" in chinese


def test_receipt_marks_unavailable_and_unassessed(
    ledger: dict[str, Any], concept: dict[str, Any], event_factory: Any
) -> None:
    event = event_factory("concept_identified", {"concept": concept})
    current, _ = apply_event(ledger, event, expected_revision=0)
    contract = build_receipt_contract(
        current,
        language="en",
        generated_at="2026-08-01T00:02:00Z",
        output_locator="chat",
    )
    receipt = render_receipt(current, contract)
    assert "Project evidence: unavailable" in receipt
    assert "understanding not yet verified" in receipt
    assert "## Understanding not yet demonstrated" in receipt


def test_receipt_escapes_markdown_and_redacts_sensitive_output(
    ledger: dict[str, Any], concept: dict[str, Any], event_factory: Any
) -> None:
    secret = "p" * 32
    concept["title"] = "# Heading [link]"
    concept["why_now"] = "API_KEY=" + secret
    event = event_factory("concept_identified", {"concept": concept})
    current, _ = apply_event(ledger, event, expected_revision=0)
    contract = build_receipt_contract(
        current,
        language="en",
        generated_at="2026-08-01T00:02:00Z",
        output_locator="chat",
    )
    receipt = render_receipt(current, contract)
    assert "### \\# Heading \\[link\\]" in receipt
    assert_no_secret(receipt, secret)
    assert "REDACTED" in receipt


def test_selection_prioritizes_blocking_and_defers_overflow(
    ledger: dict[str, Any], concept: dict[str, Any], event_factory: Any
) -> None:
    current = ledger
    for index, classification in enumerate(
        ["deferred", "explain_when_encountered", "blocking_now", "explain_when_encountered"]
    ):
        item = deepcopy(concept)
        item["id"] = f"concept-{index}"
        item["title"] = f"Concept {index}"
        item["classification"] = classification
        event = event_factory(
            "concept_identified",
            {"concept": item},
            event_id=f"evt-concept-{index}",
            timestamp=f"2026-08-01T00:0{index + 1}:00Z",
        )
        current, _ = apply_event(current, event, expected_revision=index)
    contract = build_receipt_contract(
        current,
        language="en",
        generated_at="2026-08-01T00:10:00Z",
        output_locator="chat",
        max_concepts=2,
    )
    assert contract["concept_ids"][0] == "concept-2"
    assert "concept-0" in contract["deferred_concept_ids"]
    assert len(contract["concept_ids"]) == 2


@pytest.mark.parametrize("maximum", [0, 11])
def test_selection_limit_is_bounded(ledger: dict[str, Any], maximum: int) -> None:
    with pytest.raises(ValueError, match="between 1 and 10"):
        build_receipt_contract(
            ledger,
            language="en",
            generated_at="2026-08-01T00:01:00Z",
            output_locator="chat",
            max_concepts=maximum,
        )


def test_summary_reports_strongest_demonstration(
    ledger: dict[str, Any],
    concept: dict[str, Any],
    evidence: dict[str, Any],
    demonstration: dict[str, Any],
    event_factory: Any,
) -> None:
    current = _rich_ledger(ledger, concept, evidence, demonstration, event_factory)
    second = deepcopy(demonstration)
    second.update(
        id="ev-user-002",
        timestamp="2026-08-01T00:06:00Z",
        capability="applied_independently",
        observation="The user recreated the environment.",
    )
    current, _ = apply_event(
        current,
        event_factory(
            "user_evidence_added",
            {"concept_id": concept["id"], "demonstration": second},
            event_id="evt-user-002",
            timestamp="2026-08-01T00:06:00Z",
            actor="user",
        ),
        expected_revision=4,
    )
    result = summarize(current)
    assert result["schema_version"] == SCHEMA_VERSION
    assert result["concepts"][0]["strongest_demonstration"] == "applied_independently"
    assert result["milestone_count"] == 1 and result["decision_count"] == 1
