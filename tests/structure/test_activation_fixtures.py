from __future__ import annotations

import json
from pathlib import Path


def test_activation_prompt_inventory_has_all_required_categories() -> None:
    fixture = Path(__file__).resolve().parents[1] / "fixtures" / "activation_prompts.json"
    prompts = json.loads(fixture.read_text(encoding="utf-8"))
    assert set(prompts) == {"positive", "indirect", "negative", "ambiguous"}
    assert all(len(values) >= 3 for values in prompts.values())
    flattened = [prompt for values in prompts.values() for prompt in values]
    assert len(flattened) == len(set(flattened))
    assert any(
        any("\u4e00" <= character <= "\u9fff" for character in prompt) for prompt in flattened
    )


def test_deterministic_fixture_does_not_claim_semantic_activation_results() -> None:
    fixture = Path(__file__).resolve().parents[1] / "fixtures" / "activation_prompts.json"
    text = fixture.read_text(encoding="utf-8").lower()
    for unsupported_claim in ("activated", "pass", "score", "expected_output"):
        assert unsupported_claim not in text
