from __future__ import annotations

import hashlib
from copy import deepcopy
from pathlib import Path
from typing import Any

from mentor_core.anchors import anchor_event_id, verify_anchors
from mentor_core.events import apply_event
from mentor_core.model import SCHEMA_VERSION


def _evidence(identifier: str, kind: str, locator: str) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "id": identifier,
        "class": "observed",
        "kind": kind,
        "locator": locator,
        "summary": "Synthetic anchor.",
    }


def test_verify_anchors_classifies_matches_changes_and_unavailable_kinds(
    tmp_path: Path, ledger: dict[str, Any], concept: dict[str, Any]
) -> None:
    source = tmp_path / "src" / "sample.py"
    source.parent.mkdir()
    source.write_text("def ready():\n    return True\n", encoding="utf-8")
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    concept["project_evidence"] = [
        _evidence("ev-digest-ok", "file_digest", f"src/sample.py#sha256={digest}"),
        _evidence("ev-symbol-ok", "file_symbol", "src/sample.py::ready"),
        _evidence("ev-key-stale", "config_key", "src/sample.py#missing_key"),
        _evidence("ev-command", "command", "python -m pytest"),
        _evidence("ev-unsafe", "file_symbol", "../outside.py::secret"),
    ]
    ledger["concepts"] = [concept]

    report, stale = verify_anchors(ledger, root=tmp_path)

    assert report["counts"] == {"valid": 2, "stale": 1, "unavailable": 2}
    assert [item["evidence_id"] for item in stale] == ["ev-key-stale"]
    assert all("locator" not in item for item in report["results"])
    assert all(len(item["locator_sha256"]) == 64 for item in report["results"])
    assert str(tmp_path) not in str(report)


def test_scoped_stale_event_supports_decisions_and_milestones(
    ledger: dict[str, Any], concept: dict[str, Any]
) -> None:
    evidence = _evidence("ev-decision-anchor", "config_key", "config.toml#missing")
    ledger["concepts"] = [concept]
    ledger["decisions"] = [
        {
            "id": "decision-one",
            "timestamp": "2026-08-01T00:01:00Z",
            "summary": "Use a value.",
            "alternatives": [],
            "rationale": "Synthetic test.",
            "concept_ids": [concept["id"]],
            "project_evidence": [evidence],
        }
    ]
    target = {
        "owner_type": "decision",
        "owner_id": "decision-one",
        "evidence_id": evidence["id"],
        "reason": "anchor no longer matched",
    }
    event = {
        "schema_version": SCHEMA_VERSION,
        "id": anchor_event_id(target, "2026-08-01T00:02:00Z"),
        "timestamp": "2026-08-01T00:02:00Z",
        "type": "evidence_marked_stale",
        "actor": "rule",
        "payload": target,
    }
    updated, changed = apply_event(ledger, event, expected_revision=0)
    assert changed is True
    stale = updated["decisions"][0]["project_evidence"][0]
    assert stale["class"] == "stale"
    assert stale["stale_from"] == "observed"


def test_rule_verified_evidence_retains_verification_when_marked_stale(
    ledger: dict[str, Any], concept: dict[str, Any], event_factory: Any
) -> None:
    evidence = _evidence("ev-rule-anchor", "file_digest", "a#sha256=" + "0" * 64)
    evidence.update({"class": "rule_verified", "verifier": "sha256", "result": "matched"})
    concept["project_evidence"] = [evidence]
    ledger["concepts"] = [concept]
    event = event_factory(
        "evidence_marked_stale",
        {"concept_id": concept["id"], "evidence_id": evidence["id"], "reason": "changed"},
    )
    updated, _ = apply_event(deepcopy(ledger), event, expected_revision=0)
    stale = updated["concepts"][0]["project_evidence"][0]
    assert stale["stale_from"] == "rule_verified"
    assert stale["verifier"] == "sha256"


def test_legacy_stale_rule_evidence_without_verification_fields_remains_valid(
    ledger: dict[str, Any], concept: dict[str, Any]
) -> None:
    from mentor_core.validate import validate_ledger

    evidence = _evidence("ev-legacy-stale", "file_digest", "a#sha256=" + "0" * 64)
    evidence.update(
        {
            "class": "stale",
            "stale_from": "rule_verified",
            "stale_reason": "Legacy V1 record.",
        }
    )
    concept["project_evidence"] = [evidence]
    ledger["concepts"] = [concept]
    validate_ledger(ledger)
