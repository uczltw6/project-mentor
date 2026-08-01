# Ledger schema and helper contract

Read this reference before persisting a ledger, constructing events, or interpreting helper failures.

## Contents

- [Privacy boundary](#privacy-boundary)
- [Ledger](#ledger)
- [Concepts and learning](#concepts-and-learning)
- [Project evidence](#project-evidence)
- [User demonstrations](#user-demonstrations)
- [Events](#events)
- [Receipt metadata](#receipt-metadata)
- [CLI](#cli)
- [Compatibility and safety](#compatibility-and-safety)

## Privacy boundary

Keep state ephemeral by default. Create a ledger only after explicit consent to save, track, export, or resume learning state. State the output paths before the first write and do not commit the files automatically.

Never store credentials, cookies, private keys, authorization headers, environment-variable values, authenticated URLs, source-file copies, shell history, or hidden reasoning. Store short conclusions and locators. The helper redacts recognized patterns before persistence and rendering; omit a field when confidence remains insufficient.

## Ledger

Schema version 1 uses this top-level shape:

```json
{
  "schema_version": 1,
  "revision": 0,
  "session": {
    "id": "pm-example-session",
    "goal": "Run the Python project",
    "mode": "guided",
    "created_at": "2026-08-01T00:00:00Z",
    "updated_at": "2026-08-01T00:00:00Z"
  },
  "project": {
    "root_label": "project",
    "vcs": "git",
    "baseline": null
  },
  "milestones": [],
  "concepts": [],
  "decisions": [],
  "events": [],
  "evidence_gaps": [],
  "deferred": []
}
```

Use `recap`, `guided`, or `hands_on` for `session.mode`. Use `git`, `none`, `other`, or `unknown` for `project.vcs`. Keep `root_label` descriptive rather than storing an unnecessary absolute path.

`revision` must equal the number of accepted events. Every successful new event increments it. An identical event replay does not. Timestamps must be valid UTC ISO-8601 values ending in `Z`.

## Concepts and learning

A concept contains:

```json
{
  "id": "dependency-isolation",
  "title": "Dependency isolation",
  "plain_language": "A project-specific environment keeps packages separate.",
  "classification": "explain_when_encountered",
  "why_now": "The project needs packages without changing system Python.",
  "prerequisites": [],
  "project_evidence": [],
  "user_learning": {
    "exposure": "not_seen",
    "demonstrations": []
  },
  "risks_if_changed": ["Packages could resolve from an incompatible environment."],
  "next_practice": "Create an isolated environment in a fresh sample."
}
```

Allowed classifications are `blocking_now`, `explain_when_encountered`, and `deferred`. Allowed exposure values are `not_seen`, `encountered`, and `reinforced`.

Keep `project_evidence` and `user_learning.demonstrations` separate. Adding observed project evidence may change exposure from `not_seen` to `encountered`; it never creates a demonstration. Add demonstrations only through `user_evidence_added` with a `user` or `shared` actor.

## Project evidence

Every project-evidence record is independently versioned:

```json
{
  "schema_version": 1,
  "id": "ev-project-001",
  "class": "observed",
  "kind": "config_key",
  "locator": "pyproject.toml#[project.dependencies]",
  "summary": "Project dependencies are declared here."
}
```

Evidence classes:

- `observed`: directly inspected artifact or result;
- `declared`: assertion from a user, agent, document, or configuration;
- `inferred`: plausible interpretation that may be wrong;
- `rule_verified`: a named deterministic rule passed for a named subject and result;
- `unavailable`: stronger evidence could not be accessed;
- `stale`: a prior anchor no longer matches the current task or artifact.

`user_demonstrated` is reserved for user evidence and is rejected in project evidence. Allowed kinds are `command`, `commit`, `config_key`, `conversation`, `decision`, `diff`, `file_digest`, `file_symbol`, `runtime_result`, `test_result`, and `unavailable`.

For `rule_verified`, include `verifier` and `result`. Include `exit_status` for commands or tests when available and `observed_at` when the observation time matters. The stale-event transition preserves the prior class in `stale_from` and records `stale_reason`.

Use globally unique project-evidence IDs across concepts, decisions, and milestones.

## User demonstrations

Every user demonstration is independently versioned:

```json
{
  "schema_version": 1,
  "id": "ev-user-001",
  "timestamp": "2026-08-01T00:05:00Z",
  "class": "user_demonstrated",
  "capability": "recognized",
  "observation": "The user selected the project-local interpreter.",
  "task_context": "Choose the interpreter used to launch the sample."
}
```

Allowed capabilities are `recognized`, `explained`, `applied_with_guidance`, `applied_independently`, and `transferred`. Store the observed action, not an interpretation of personality or a mastery score.

Use globally unique demonstration IDs and never reuse a project-evidence ID.

## Events

Every event uses:

```json
{
  "schema_version": 1,
  "id": "evt-mode-001",
  "timestamp": "2026-08-01T00:03:00Z",
  "type": "mode_changed",
  "actor": "user",
  "payload": {
    "mode": "recap",
    "reason": "The user asked to stop explanations and finish."
  }
}
```

Allowed actors are `user`, `agent`, `shared`, and `rule`. Event payloads are strict:

| Event type | Payload |
| --- | --- |
| `session_started` | `goal`, `mode`; both must match the initialized session |
| `mode_changed` | `mode`, `reason` |
| `concept_identified` | `concept`; demonstrations must start empty |
| `project_evidence_added` | `concept_id`, `evidence` |
| `user_evidence_added` | `concept_id`, `demonstration`; actor must be `user` or `shared` |
| `decision_recorded` | `decision` |
| `milestone_completed` | `milestone` |
| `concept_deferred` | `concept_id`, `reason` |
| `evidence_marked_stale` | `concept_id`, `evidence_id`, `reason` |
| `receipt_rendered` | `receipt` metadata |

Decisions contain `id`, `timestamp`, `summary`, `alternatives`, `rationale`, `concept_ids`, and `project_evidence`. Milestones contain `id`, `timestamp`, `title`, `result`, `concept_ids`, and `project_evidence`.

Supply a stable event ID. Replaying byte-equivalent redacted content with the same ID is idempotent. Reusing that ID with different content exits with an event conflict and does not modify the ledger.

## Receipt metadata

The versioned receipt contract records `schema_version`, `generated_at`, `session_id`, `language`, `goal`, `mode`, selected milestone/concept/decision/deferred IDs, and `output_locator`. It describes the rendered receipt without copying its Markdown into the ledger.

Use `en` or `zh` for language. Rendering selects up to five active concepts by default and lists the rest as deferred. The same ledger, timestamp, language, and selection limit must produce identical Markdown.

## CLI

Run from the skill directory:

```text
python scripts/project_mentor.py init --goal "Run the project" --session-id pm-example --created-at 2026-08-01T00:00:00Z --vcs git --output ledger.json
python scripts/project_mentor.py apply-event --ledger ledger.json --event event.json --expected-revision 0
python scripts/project_mentor.py validate --kind ledger --input ledger.json
python scripts/project_mentor.py render --ledger ledger.json --language en --rendered-at 2026-08-01T00:10:00Z --output learning-receipt.md
python scripts/project_mentor.py summarize --ledger ledger.json --output summary.json
python scripts/project_mentor.py redact --input command.txt
```

Use `-` for stdin or stdout where the command supports it. `apply-event` always requires an explicit ledger path and expected revision because it performs persistent atomic replacement.

Stable exit classes:

| Code | Meaning |
| --- | --- |
| 0 | Success, including identical event replay |
| 2 | Invalid JSON, schema, enum, ID, timestamp, or unsupported version |
| 3 | Expected revision or file-content conflict |
| 4 | I/O or path-safety failure |
| 5 | Conflicting event replay |

Expected failures print a concise error without a traceback. Use the global `--debug` flag only for unexpected implementation failures.

## Compatibility and safety

- Support schema version 1 only. Reject a future version without modifying the file.
- Reject unknown fields rather than silently losing them.
- Limit each input to 1 MiB and require UTF-8.
- Validate and redact before persistence.
- Write a same-directory temporary file, flush it, recheck expected content, and replace atomically.
- Refuse an existing symlink output target.
- Preserve the prior file after invalid input, revision conflict, unsafe path, or write failure.
- Never scan a repository, read shell history, contact a network service, or execute a recorded command.
- Use the host agent for semantic concept selection; the helper validates, redacts, stores, sorts, summarizes, and renders supplied conclusions.
