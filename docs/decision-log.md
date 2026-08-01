# Decision log

This log records release-relevant decisions without retaining private paths, credentials, or hidden reasoning.

## 2026-08-01 — Phase 0 baseline

- **Safe worktree:** Build from a uniquely named directory under the system temporary directory. The mounted OneDrive workspace passed creation, rename, overwrite, Git initialization, index update, lock creation, and commit checks, but recursive cleanup of Git objects was unreliable. Keep the mounted directory as an export and bundle-checkpoint location only.
- **Personal skill scope:** Author and install the personal skill under `$HOME/.agents/skills/project-mentor`, the current user-scope location documented by Codex. Do not use the older `$HOME/.codex/skills/remote-skills` fallback because current official guidance specifies `$HOME/.agents/skills`.
- **Publication boundary:** The authenticated GitHub account is `uczltw6`; `uczltw6/project-mentor` does not exist. Publication under that exact owner is available once all local gates pass.
- **Git identity:** Preserve the authenticated account's existing Git name and GitHub-provided no-reply email. Do not add co-authors.
- **Runtime baseline:** Python 3.11.5, Git 2.45.1, GitHub CLI 2.91.0, and Node.js 24.15.0 are available. The implementation target remains Python 3.10+ with standard-library-only runtime dependencies.
- **Distribution boundary:** Release a standalone skill and public source repository. Do not publish a plugin, package-registry artifact, or marketplace submission in V1.

## 2026-08-01 — Phase 1 product contract

- **Success ordering:** Judge delivery correctness first, mentoring usefulness second, and persistence convenience third. Teaching must never weaken the real task result.
- **Trust boundary:** Store project evidence and user demonstrations in separate fields. Agent work may establish project usage but can establish at most user exposure, never user capability.
- **Activation boundary:** Require explicit or clearly implied build-while-learning or post-hoc learning-audit intent. Ordinary delegated implementation and isolated explanations remain outside the skill.
- **Persistence boundary:** Keep state in conversation or temporary storage by default. Create `.project-mentor/` or any alternative learning artifact only after explicit user opt-in.
- **Mode contract:** Expose exactly `recap`, `guided`, and `hands_on`; make `guided` the activation default and honor mode changes immediately without restarting the delivery task.

## 2026-08-01 — Phase 2 initialization and scaffold

- **Official initialization:** Create `$HOME/.agents/skills/project-mentor` with the official `init_skill.py`, requesting only `scripts` and `references`, and generate the initial `agents/openai.yaml` through that command.
- **UI metadata:** Use “Project Mentor,” “Learn through evidence in real projects,” and a one-sentence `$project-mentor` default prompt. Keep implicit invocation at its documented default and add no icons, colors, MCP tools, or external dependencies.
- **Canonical editing flow:** Treat the personal skill as the authoring source through validation. Synchronize release files into `.agents/skills/project-mentor/` with `tools/sync_skill.py` and require byte-for-byte parity before release.
- **Template state:** The official initializer's placeholder `SKILL.md` is intentionally present at the Phase 2 boundary and fails validation because its description is not final. Replace every placeholder during Phase 4; do not interpret this expected intermediate result as release validation.
- **Repository boundary:** Keep development tools, tests, CI, contribution files, and public documentation outside the nested installable skill. Runtime behavior inside the skill remains standard-library-only.

## 2026-08-01 — Phase 3 deterministic core

- **Versioned contracts:** Use schema version 1 for ledgers, events, project evidence, user demonstrations, and receipt metadata. Reject unknown fields and unsupported versions before mutation.
- **Event integrity:** Require caller-supplied stable event IDs, strict typed payloads, optimistic expected revisions, idempotent identical replay, and fail-closed conflicting replay. Keep `revision` equal to applied event count.
- **User-claim safeguard:** Accept `user_evidence_added` only from `user` or `shared` actors, and forbid user demonstrations inside `concept_identified`. Agent-authored project evidence can move exposure from `not_seen` to `encountered`, never create a demonstration.
- **Persistence safety:** Bound input at 1 MiB, decode UTF-8 explicitly, validate before writing, reject existing symlink targets, recheck file content before replacement, and use same-directory temporary files plus atomic replace.
- **Redaction boundary:** Redact recognized credentials recursively before JSON persistence and again before rendered or summarized output. Prefer omission or a marker over retaining uncertain sensitive material.
- **Stable CLI exits:** Use 0 for success, 2 for invalid input/schema, 3 for revision conflict, 4 for I/O or path safety, and 5 for conflicting event replay. Expected failures do not emit tracebacks unless `--debug` is requested.
- **Rendering:** Select up to five active concepts by classification and evidence weight, render deterministic English or Chinese receipts, and state unverified user understanding explicitly when demonstrations are absent.

## 2026-08-01 — Phase 4 skill workflow

- **Progressive disclosure:** Keep `SKILL.md` at 162 lines with the operating workflow and direct links only. Place intervention detail in `mentoring-policy.md`, schema/CLI detail in `ledger-schema.md`, and calibration cases in `examples.md`.
- **Activation metadata:** Retain the proposed intent-bounded description after reviewing positive and negative cases. Keep implicit invocation enabled at its documented default because ordinary delegated coding, isolated explanations, and course creation are explicit negative boundaries.
- **Helper boundary:** Direct the host agent to perform semantic concept selection and evidence judgment. Use the Python helper only for deterministic validation, redaction, persistence, ordering, summaries, and rendering.
- **Python-unavailable fallback:** Continue mentoring with conversation or ephemeral state and avoid repeated helper retries during the same known-unavailable phase.
- **Official metadata generation:** Regenerate `agents/openai.yaml` with the official generator after reading the completed skill. Enable Python UTF-8 mode to avoid the generator's Windows locale-dependent read failure.
- **Validation:** The official validator passes against both the canonical personal skill and public copy; all 15 release files are byte-for-byte identical, with no placeholders, auxiliary documents, or generated caches.

## 2026-08-01 — Phase 5 deterministic verification

- **Test layers:** Cover schema/model validation, all event transitions, redaction true/false positives, atomic I/O, deterministic English/Chinese rendering, CLI lifecycle, developer sync tools, skill structure, and activation metadata fixtures.
- **Secret-safe failures:** Route synthetic-secret assertions through a helper that reports only that a leak occurred, never the tested value, so a regression does not expose fixture credentials in test logs.
- **Activation evidence boundary:** Store positive, indirect, negative, and ambiguous prompt sets as deterministic metadata fixtures. Do not treat those fixtures as proof of semantic model activation.
- **Local results:** Collect 100 tests; pass 98 and skip two symlink cases because the current Windows account cannot create test symlinks. Defer those platform branches to Linux CI rather than weakening the tests.
- **Coverage:** Measure the deterministic runtime helper with branch coverage and reach 95%, above the 90% release threshold without adding meaningless assertions.
- **Static quality:** Ruff lint and format checks pass; strict mypy passes across the runtime helper and repository development tools.
