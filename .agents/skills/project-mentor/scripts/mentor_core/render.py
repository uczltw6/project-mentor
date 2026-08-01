"""Deterministic Markdown receipts and machine-readable summaries."""

from __future__ import annotations

from typing import Any

from .model import SCHEMA_VERSION
from .validate import validate_ledger, validate_receipt

CLASSIFICATION_ORDER = {"blocking_now": 0, "explain_when_encountered": 1, "deferred": 2}
CAPABILITY_ORDER = {
    "recognized": 0,
    "explained": 1,
    "applied_with_guidance": 2,
    "applied_independently": 3,
    "transferred": 4,
}


def _plain(value: Any) -> str:
    text = str(value).replace("\r", " ").replace("\n", " ").strip()
    for character in "\\`*_{}[]<>#":
        text = text.replace(character, f"\\{character}")
    return text


def _code(value: Any) -> str:
    return str(value).replace("\r", " ").replace("\n", " ").replace("`", "\\`").strip()


def _selected_concepts(ledger: dict[str, Any], maximum: int) -> list[dict[str, Any]]:
    active = [item for item in ledger["concepts"] if item["classification"] != "deferred"]
    return sorted(
        active,
        key=lambda item: (
            CLASSIFICATION_ORDER[item["classification"]],
            -len(item["project_evidence"]),
            item["id"],
        ),
    )[:maximum]


def build_receipt_contract(
    ledger: dict[str, Any],
    *,
    language: str,
    generated_at: str,
    output_locator: str,
    max_concepts: int = 5,
) -> dict[str, Any]:
    validate_ledger(ledger)
    if not 1 <= max_concepts <= 10:
        raise ValueError("max_concepts must be between 1 and 10")
    selected = _selected_concepts(ledger, max_concepts)
    receipt = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at,
        "session_id": ledger["session"]["id"],
        "language": language,
        "goal": ledger["session"]["goal"],
        "mode": ledger["session"]["mode"],
        "milestone_ids": [item["id"] for item in ledger["milestones"]],
        "concept_ids": [item["id"] for item in selected],
        "decision_ids": [item["id"] for item in ledger["decisions"]],
        "deferred_concept_ids": sorted(
            {item["concept_id"] for item in ledger["deferred"]}
            | {item["id"] for item in ledger["concepts"] if item not in selected}
        ),
        "output_locator": output_locator,
    }
    validate_receipt(receipt)
    return receipt


def _user_demonstration(concept: dict[str, Any], language: str) -> str:
    demonstrations = concept["user_learning"]["demonstrations"]
    if not demonstrations:
        if language == "zh":
            return f"接触状态：{_plain(concept['user_learning']['exposure'])}；理解尚未验证"
        return f"Exposure: {_plain(concept['user_learning']['exposure'])}; understanding not yet verified"
    strongest = max(
        demonstrations,
        key=lambda item: (CAPABILITY_ORDER[item["capability"]], item["timestamp"], item["id"]),
    )
    if language == "zh":
        return (
            f"{_plain(strongest['capability'])} — {_plain(strongest['observation'])} "
            f"（任务背景：{_plain(strongest['task_context'])}）"
        )
    return (
        f"{_plain(strongest['capability'])} — {_plain(strongest['observation'])} "
        f"(task context: {_plain(strongest['task_context'])})"
    )


def _evidence_lines(concept: dict[str, Any], language: str) -> list[str]:
    evidence = concept["project_evidence"]
    if not evidence:
        label = "项目证据：不可用；未提出更强结论" if language == "zh" else "Project evidence: unavailable; no stronger claim made"
        return [f"- {label}"]
    title = "项目证据" if language == "zh" else "Project evidence"
    lines = [f"- {title}:"]
    for item in sorted(evidence, key=lambda entry: entry["id"]):
        lines.append(
            f"  - `{_code(item['locator'])}` — {_plain(item['summary'])} "
            f"({_plain(item['class'])})"
        )
    return lines


def render_receipt(ledger: dict[str, Any], receipt: dict[str, Any]) -> str:
    """Render a validated English or Chinese receipt with stable ordering."""
    validate_ledger(ledger)
    validate_receipt(receipt)
    language = receipt["language"]
    selected_ids = set(receipt["concept_ids"])
    selected = [item for item in _selected_concepts(ledger, 10) if item["id"] in selected_ids]
    decisions_by_concept: dict[str, list[dict[str, Any]]] = {}
    for decision in ledger["decisions"]:
        for concept_id in decision["concept_ids"]:
            decisions_by_concept.setdefault(concept_id, []).append(decision)

    if language == "zh":
        lines = [
            "# Project Mentor 学习回执",
            "",
            f"_生成时间：{_plain(receipt['generated_at'])}_",
            "",
            "## 已完成的工作",
            "",
            f"- 目标：{_plain(ledger['session']['goal'])}",
            f"- 当前模式：`{_code(ledger['session']['mode'])}`",
        ]
        if ledger["milestones"]:
            lines.extend(
                f"- 里程碑：{_plain(item['title'])} — {_plain(item['result'])}"
                for item in ledger["milestones"]
            )
        else:
            lines.append("- 里程碑：尚无已验证的里程碑记录")
        lines.extend(["", "## 本项目实际用到的知识", ""])
    else:
        lines = [
            "# Project Mentor learning receipt",
            "",
            f"_Generated: {_plain(receipt['generated_at'])}_",
            "",
            "## What we completed",
            "",
            f"- Goal: {_plain(ledger['session']['goal'])}",
            f"- Current mode: `{_code(ledger['session']['mode'])}`",
        ]
        if ledger["milestones"]:
            lines.extend(
                f"- Milestone: {_plain(item['title'])} — {_plain(item['result'])}"
                for item in ledger["milestones"]
            )
        else:
            lines.append("- Milestones: no verified milestone recorded")
        lines.extend(["", "## Knowledge actually used in this project", ""])

    for concept in selected:
        decisions = decisions_by_concept.get(concept["id"], [])
        risk = "; ".join(_plain(item) for item in concept["risks_if_changed"])
        if language == "zh":
            lines.extend(
                [
                    f"### {_plain(concept['title'])}",
                    "",
                    f"- 概念说明：{_plain(concept['plain_language'])}",
                    f"- 为什么此时重要：{_plain(concept['why_now'])}",
                ]
            )
            lines.extend(_evidence_lines(concept, language))
            decision_text = (
                "; ".join(_plain(item["summary"]) for item in decisions) if decisions else "未记录单独决策"
            )
            lines.extend(
                [
                    f"- 关键决策：{decision_text}",
                    "- Agent 展示：已展示上列项目证据所支持的项目用法；这不代表用户能力",
                    f"- 你展示的内容：{_user_demonstration(concept, language)}",
                    f"- 如果发生变化：{risk or '未记录具体风险'}",
                    f"- 下一步小练习：{_plain(concept['next_practice'])}",
                    "",
                ]
            )
        else:
            lines.extend(
                [
                    f"### {_plain(concept['title'])}",
                    "",
                    f"- What it is: {_plain(concept['plain_language'])}",
                    f"- Why it mattered here: {_plain(concept['why_now'])}",
                ]
            )
            lines.extend(_evidence_lines(concept, language))
            decision_text = (
                "; ".join(_plain(item["summary"]) for item in decisions)
                if decisions
                else "No separate decision recorded"
            )
            lines.extend(
                [
                    f"- Decision made: {decision_text}",
                    "- Agent demonstrated: project use supported by the evidence above; this does not imply user capability",
                    f"- You demonstrated: {_user_demonstration(concept, language)}",
                    f"- If this changes: {risk or 'No specific risk recorded'}",
                    f"- Small next practice: {_plain(concept['next_practice'])}",
                    "",
                ]
            )

    if language == "zh":
        lines.extend(["## 关键设计决策", ""])
        lines.extend(
            [f"- {_plain(item['summary'])} — {_plain(item['rationale'])}" for item in ledger["decisions"]]
            or ["- 未记录单独的设计决策"]
        )
        lines.extend(["", "## 尚未展示的理解", ""])
        unassessed = [item for item in selected if not item["user_learning"]["demonstrations"]]
        lines.extend([f"- {_plain(item['title'])}" for item in unassessed] or ["- 无"])
        lines.extend(["", "## 延后 / 稍后学习", ""])
    else:
        lines.extend(["## Key design decisions", ""])
        lines.extend(
            [f"- {_plain(item['summary'])} — {_plain(item['rationale'])}" for item in ledger["decisions"]]
            or ["- No separate design decision recorded"]
        )
        lines.extend(["", "## Understanding not yet demonstrated", ""])
        unassessed = [item for item in selected if not item["user_learning"]["demonstrations"]]
        lines.extend([f"- {_plain(item['title'])}" for item in unassessed] or ["- None"])
        lines.extend(["", "## Deferred / learn later", ""])

    deferred_reason = {item["concept_id"]: item["reason"] for item in ledger["deferred"]}
    deferred = [item for item in ledger["concepts"] if item["id"] in receipt["deferred_concept_ids"]]
    if deferred:
        for concept in sorted(deferred, key=lambda item: item["id"]):
            reason = deferred_reason.get(concept["id"], concept["why_now"])
            lines.append(f"- {_plain(concept['title'])} — {_plain(reason)}")
    else:
        lines.append("- 无" if language == "zh" else "- None")
    return "\n".join(lines).rstrip() + "\n"


def summarize(ledger: dict[str, Any]) -> dict[str, Any]:
    """Return a compact deterministic ledger summary."""
    validate_ledger(ledger)
    concepts = []
    for concept in sorted(ledger["concepts"], key=lambda item: item["id"]):
        demonstrations = concept["user_learning"]["demonstrations"]
        strongest = (
            max(demonstrations, key=lambda item: CAPABILITY_ORDER[item["capability"]])["capability"]
            if demonstrations
            else None
        )
        concepts.append(
            {
                "id": concept["id"],
                "classification": concept["classification"],
                "project_evidence_count": len(concept["project_evidence"]),
                "exposure": concept["user_learning"]["exposure"],
                "demonstration_count": len(demonstrations),
                "strongest_demonstration": strongest,
            }
        )
    return {
        "schema_version": SCHEMA_VERSION,
        "session_id": ledger["session"]["id"],
        "goal": ledger["session"]["goal"],
        "mode": ledger["session"]["mode"],
        "revision": ledger["revision"],
        "milestone_count": len(ledger["milestones"]),
        "decision_count": len(ledger["decisions"]),
        "evidence_gap_count": len(ledger["evidence_gaps"]),
        "concepts": concepts,
    }
