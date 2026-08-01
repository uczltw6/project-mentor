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

## 2026-08-01 — Phase 6 forward evaluation

- **Clean contexts:** Run every semantic case in a fresh, non-Git fixture copy. Give acting agents only the natural request, the fixture, and the personal skill path for positive cases; do not disclose the rubric or expected failure.
- **Coverage:** Exercise guided setup and implementation, post-hoc audit, all three modes, debugging, synthetic-secret handling, non-Git operation, excessive-scope pressure, Chinese output, and a natural negative control.
- **Hands-on evidence:** Split the hands-on scenario across two turns so the user action and its failing-test evidence are independently observable before agent completion.
- **Baseline:** Compare the guided endpoint case with a no-skill endpoint run. Both complete the same task and pass the same three focused tests, so the teaching behavior does not reduce correctness or completion on this fixture.
- **Privacy:** Publish only sanitized prompts, numeric scores, and concise verification notes. Keep raw responses, local paths, and the synthetic secret outside the repository.
- **Release result:** All 14 cases pass their applicable gates, earning 260 of 260 applicable rubric points. Treat this as evidence for the committed fixtures, not a universal claim about every host, project, or learner.

## 2026-08-01 — Phase 7 public documentation

- **Installation guidance:** Document `$HOME/.agents/skills/project-mentor` for personal use and `.agents/skills/project-mentor` for repository use, matching the current official Codex loading locations. Cover both explicit `$project-mentor` invocation and intent-based implicit activation.
- **Public claim boundary:** Present v0.1.0 evaluation numbers with direct links to prompts, scoring, reproduction, and limitations. Avoid universal learning, security, or compatibility claims.
- **Example provenance:** Generate the example ledger and receipt with the released helper from four committed strict events and test byte-for-byte regeneration.
- **Architecture boundary:** Describe host-agent semantic reasoning separately from the standard-library helper's deterministic validation, redaction, event, persistence, and rendering responsibilities.
- **Community surface:** Add contribution, conduct, security, issue, and pull-request guidance with explicit secret and private-data hygiene.

## 2026-08-01 — Phase 8 continuous integration

- **Cross-platform contract:** Run the full suite on Linux for every supported Python minor from 3.10 through 3.14 and on Windows at both boundary versions.
- **Immutable actions:** Resolve current official releases and pin checkout v7.0.1, setup-python v7.0.0, and CodeQL v4.37.4 to full commit SHAs. Let Dependabot propose future reviewed updates.
- **Official structure gate:** Check out a pinned `openai/skills` snapshot, run its `quick_validate.py`, run repository structure tests, and compare a staged user-scope installation byte-for-byte with the public skill.
- **Coverage and static gates:** Keep lint, format, strict typing, and 90% branch coverage as independent required jobs so failures are attributable.
- **CodeQL decision:** Include Python CodeQL with extended security queries because the helper processes untrusted JSON, redacts sensitive strings, and performs persistent file replacement. The scan is useful despite the small, dependency-free runtime.
- **Least privilege:** Default workflows to read-only repository contents; grant `security-events: write` only to CodeQL. Disable checkout credential persistence.

## 2026-08-01 — Phase 9 adversarial security review

- **Independent audit:** Run a clean-context, read-only review across the skill, helper, tests, CI, documentation, worktree, and Git history. Resolve every high-confidence finding before release and publish a sanitized disposition.
- **Parser hardening:** Reject duplicate JSON keys recursively so a displayed field cannot differ from the last value used for validation.
- **Renderer hardening:** Treat evidence locators as untrusted Markdown and choose a code-span fence longer than every contained backtick run.
- **Bounded hashing:** Enforce the 1 MiB limit while streaming the pre-mutation ledger digest and refuse a symlink ledger before reading it.
- **Release-path hardening:** Check a skill root for symlinks before resolving it; retain nested-link rejection and destination confinement.
- **Authenticity boundary:** Define ledgers and event actors as unsigned caller-supplied provenance, not authenticated identity or proof of truth.
- **Repository gate:** Scan releasable worktree files and complete Git history without echoing matched content; run the same gate in full-history CI.

## 2026-08-01 — Phase 10 installation and release rehearsal

- **Installed discovery:** Locate the personal skill uniquely by frontmatter `name`, require the current `$HOME/.agents/skills/project-mentor` scope, a regular directory, no generated caches, official validation, and all documented helper commands.
- **Portable parity:** Require byte equality between the personal installation and a fresh Git checkout. Normalize the Windows-generated `agents/openai.yaml` to the repository's LF policy after the first clean clone exposed a line-ending-only mismatch.
- **Clean-clone gate:** Create a new clone and virtual environment, install documented development dependencies, and rerun lint, format, strict typing, tests, coverage, official validation, parity, and the repository/history scan.
- **Semantic rehearsal:** Reuse the Phase 6 clean-context explicit invocation evidence rather than creating a less controlled duplicate. Keep the negative no-skill baseline in the release record.
- **Tag boundary:** Do not tag from local success. Require the published final commit and hosted CI/CodeQL gates to pass first.

## 2026-08-01 — Phase 11 publication and hosted-CI correction

- **Publication:** Create only `uczltw6/project-mentor`, keep it public with `main` as default, enable issues, apply the authorized description and six relevant topics, and push without rewriting history.
- **Anonymous verification:** Confirm `refs/heads/main` over HTTPS with credential helpers disabled and require the remote SHA to match local `HEAD`.
- **First hosted result:** Do not accept the first CI run. Static quality and the full-history scanner passed, but test jobs generated bytecode inside source directories and then failed order-dependent assertions that inspected those ignored runtime caches.
- **Correction:** Disable bytecode writes in CI and make structure checks inspect Git-tracked release files. Keep fixture secret checks scoped to committed text source while fixture subprocesses inherit no-bytecode mode.
