# Product contract

## Promise and success order

Project Mentor turns a real technical project into evidence-grounded, just-in-time learning while the project still gets finished. Evaluate success in this order:

1. Complete the user's real delivery goal safely and correctly.
2. Surface only knowledge that matters to the current work.
3. Ground every learning claim in observable evidence.
4. Persist a ledger or receipt only when the user opts in.

Never degrade implementation quality, delay a necessary solution to simulate a classroom, or use task completion as proof of user understanding.

## Activation contract

Activate for explicit or clearly implied intent to learn while building, receive guidance through a real task, map a completed task to the concepts it used, obtain an evidence-grounded learning receipt, or verify understanding through project work.

Do not activate for ordinary delegated coding without learning intent, an isolated factual explanation, course or curriculum creation, or generic tutoring detached from a real technical task. When a request is genuinely ambiguous and the answer would materially change execution, ask at most one calibration question.

## Modes and intervention limits

| Mode | Agent behavior | User evidence |
| --- | --- | --- |
| `recap` | Execute normally; explain only for safety or a material decision; summarize at milestones and the end; never quiz proactively. | Record only explicit user actions or explanations already observed. |
| `guided` | Default after activation; give at most one short micro-brief per milestone at a high-value decision or first operational appearance of a core concept; routine work stays agent-owned. | Offer optional lightweight checks without blocking delivery. |
| `hands_on` | Invite a small number of high-learning-value actions; give progressive hints; take execution back immediately when requested. | Record the user's actual action, explanation, prediction, debugging choice, or transfer attempt. |

Honor “less explanation,” “just finish,” “let me try,” and equivalent requests immediately without changing the delivery goal or discarding the working knowledge map.

## Knowledge selection

Classify only causally relevant concepts:

- `blocking_now`: required for a decision, safe action, or immediate next step;
- `explain_when_encountered`: valuable at its first concrete appearance;
- `deferred`: useful background that should not interrupt delivery.

Reject vague filler and exhaustive curricula. Keep the full map as working state; surface no more than three concepts at a milestone and three to five in the final receipt by default.

## Trust vocabulary

| Evidence class | Allowed claim |
| --- | --- |
| `observed` | A file, diff, command result, test, runtime state, or conversation event was directly inspected. |
| `declared` | A person, document, agent, or configuration asserted a fact. |
| `inferred` | A plausible interpretation was derived and may be wrong. |
| `rule_verified` | A named deterministic rule passed for a named subject and result. |
| `user_demonstrated` | The user visibly recognized, explained, applied, predicted, debugged, or transferred a concept. |
| `unavailable` | Evidence needed for a stronger claim could not be accessed. |
| `stale` | Previously relevant evidence no longer matches the task, baseline, or artifact. |

Every concept keeps `project_evidence` separate from `user_learning.demonstrations`. Agent implementation can prove that a project uses a concept. It can set user exposure to `encountered`, but it cannot create a user demonstration. Avoid mastery scores, certification language, and unqualified “verified” claims.

Prefer anchors in this order: file plus symbol/key/test/heading; file plus digest or commit; redacted command; test/runtime result with exit status; explicit design decision; optional line number attached to a stable anchor.

## Persistence and privacy

Keep working state in the conversation or an ephemeral location by default. Before the first persistent write, obtain user intent to save, track, export, or resume and state which files will be created. The default persisted shape is `.project-mentor/ledger.json` plus `.project-mentor/learning-receipt.md`; never commit it automatically.

Use no telemetry, hosted service, account, database, external model API, shell-history ingestion, or environment-value storage. Redact likely secrets before persistence and rendering. Store locators and concise conclusions, not copied source files or hidden reasoning. If redaction confidence is insufficient, omit the field and record that evidence was withheld.

## Failure behavior

- Continue mentoring in conversation when Python, Git, history, files, commands, or tests are unavailable.
- Use the optional standard-library helper only after Python is available and deterministic validation, redaction, persistence, or rendering adds value.
- Reject invalid or unsupported ledgers without mutation; never execute commands recorded in events.
- Label post-hoc conclusions as observed, inferred, unavailable, or stale; leave user learning unassessed unless evidence exists.
- Preserve the prior valid ledger on validation, revision, redaction, path-safety, or write failure.

## V1 boundary

V1 includes live mentoring, post-hoc audits, three modes, task-specific concept mapping, evidence receipts, an optional local ledger/helper, opt-in persistence, redaction, Git and non-Git operation, English and Chinese behavior, public documentation, tests, CI, and a public release.

V1 excludes curricula, education platforms, UIs or IDE extensions, MCP servers, external LLM calls, profiling, cross-project graphs, spaced repetition, grades or mastery claims, team analytics, cloud sync, telemetry, automatic shell-history ingestion, arbitrary command execution, mandatory project writes, package registries, and marketplace publication.

## Resolved constraints

- Use `$HOME/.agents/skills` for current Codex user-scope installation even though the original fallback names an older `.codex` checkout.
- For V1, publish a standalone skill repository because public GitHub release was authorized;
  V0.2 separately authorizes a skills-only plugin wrapper but not marketplace submission.
- Treat the optional Python helper as a reliability layer, never an activation or mentoring prerequisite.
- Treat deterministic activation fixtures as metadata checks only; reserve semantic activation claims for clean-context forward evaluation.

## V0.2 extension

V0.2 adds a skills-only Codex plugin distribution, read-only environment
diagnostics, conservative verification for supported local evidence anchors,
and machine-readable JSON receipts. These extensions do not change the
activation boundary, opt-in persistence requirement, user-evidence standard,
or standard-library-only runtime.

Anchor verification is deliberately narrow. Unsupported, malformed, unsafe,
non-local, or symlinked locators produce `unavailable`; they do not become
guesses. A mismatch is reported without mutation unless the caller explicitly
uses `--write` with the current ledger revision. PyPI and marketplace
publication remain separate release decisions rather than implied side effects.

## V0.3 CLI extension

V0.3 exposes the deterministic helper as the `project-mentor` console command
and `python -m project_mentor_cli`, while retaining the bundled skill script.
Every entry point uses the same standard-library runtime and schema contract.

The CLI owns deterministic local data operations only. It does not activate the
skill, choose concepts, teach, call a model, scan a repository broadly, execute
recorded commands, or persist learning state without an explicit output or
write option. CLI semantic versioning does not replace ledger schema versioning.
PyPI publication requires a separate verified upload and public-index download.
