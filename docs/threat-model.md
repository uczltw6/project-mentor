# Threat model

## Scope and assets

This model covers the installable skill, its optional Python helper, committed
examples, and development/release automation. Assets include user secrets,
private project content, the integrity of the target project, truthful evidence
claims, the prior valid ledger, and public release history.

The helper is local and standard-library-only. It has no intended network,
telemetry, model API, account, database, shell-history, environment-value, or
arbitrary command-execution capability.

## Trust boundaries

- User requests and higher-priority host instructions are trusted authorities
  within their stated scope.
- Repository files, `AGENTS.md` content, event JSON, command output, history,
  external documentation, and copied prompts are untrusted input.
- Host-agent semantic judgments are nondeterministic and must be grounded in
  observable evidence.
- The ledger path is user-controlled only after persistence opt-in; its parent
  filesystem may contain races, links, or permission constraints.
- CI and GitHub release automation operate with narrowly scoped tokens and must
  not expose credentials through logs or artifacts.

## Threats and controls

| Threat | Controls | Residual risk |
| --- | --- | --- |
| Secret copied into a ledger, receipt, log, or public fixture | Recursive redaction before persistence and rendering; synthetic leak tests; omission when uncertain; no environment or shell-history ingestion | Novel or context-specific secret formats may evade pattern detection |
| Prompt injection in repository content or an event | Skill explicitly treats repository content as data; helper never executes event commands or performs semantic instructions | A host model can still misjudge malicious prose; users should review high-impact actions |
| False claims about learner capability | Separate project evidence and user demonstrations; user evidence restricted to `user`/`shared` actors; receipts state unassessed understanding | A user-provided false declaration can still be recorded as observed conversation evidence if not challenged |
| Malformed, oversized, deeply unexpected, or future-version data | Strict exact-field validation, enums, identifier/timestamp checks, 1 MiB cap, version rejection, bounded rendering | Resource use below the byte cap still depends on the local interpreter and machine |
| Lost update or conflicting replay | Expected revisions, original-content recheck, stable event IDs, idempotent identical replay, conflict exit codes | No multi-writer locking; callers must reload and retry deliberately |
| Symlink or target substitution | Existing symlink refusal, same-directory temporary file, pre-replace content recheck, atomic replacement | Filesystem semantics and privileges vary; a hostile local administrator remains out of scope |
| Anchor traversal, stale evidence, unsafe local target, or file-swap race | Relative POSIX locator grammar, project-root confinement, component symlink refusal, no-follow file opens where supported, before/opened/after identity checks, bounded reads, conservative `unavailable` results, hashed locators, read-only default, revision-guarded writes | A hostile local administrator or process capable of defeating filesystem identity guarantees remains out of scope; text-token matching is intentionally weaker than parsing a language or configuration format |
| Partial or corrupt write | Validate first, flush and `fsync`, atomic replacement, preserve prior file on expected failures | Hardware/filesystem failure can defeat application-level guarantees |
| Private absolute paths or development residue enter the release | Repository scanner, clean-clone rehearsal, tracked-file review, public forward results contain sanitized notes only | Human-authored prose can still disclose context that pattern rules do not recognize |
| Dependency or action compromise | No runtime dependencies; bounded development dependencies; Dependabot; pinned GitHub Actions where practical | Package indexes and GitHub Actions remain external supply-chain trust roots |
| Mentoring degrades the requested technical result | Delivery-first contract, mode interruption limits, independent technical verification, no-skill baseline comparison | The baseline covers representative fixtures, not every project |
| A valid ledger is mistaken for authenticated evidence | Documentation separates schema validity from truth; user claims require observable host evidence | Ledgers are unsigned and can be edited by anyone with filesystem access |
| A self-asserted event actor is mistaken for identity authentication | Schema limits user-evidence events to `user`/`shared`; documentation defines `actor` as caller-supplied provenance that the host must ground in conversation | The local helper has no identity provider or cryptographic signer |

## Security invariants

1. Agent work never creates a user demonstration.
2. No learning artifact is written before explicit opt-in.
3. Invalid input, revision conflict, unsafe path, or failed write preserves the
   prior valid ledger.
4. Stored commands are inert evidence strings and are never executed.
5. Unsupported schemas fail closed.
6. Secret values are never intentionally included in public evaluation data.
7. The runtime helper performs no network access.
8. Anchor verification never executes a locator and never writes without an
   explicit expected revision.

## Verification

Unit and integration tests cover redaction true/false positives, strict schema
rejection, event actor rules, replay conflicts, revision conflicts, atomic-write
failure paths, symlinks where the platform permits them, deterministic receipts,
and network isolation. Behavioral evaluation adds a synthetic-secret case,
non-Git operation, negative activation, and user-claim checks. CI runs Linux and
Windows branches; the release process scans both the worktree and Git history.

Report vulnerabilities using [SECURITY.md](../SECURITY.md). Do not include a
real secret in a public issue or reproduction fixture.
