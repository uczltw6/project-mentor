# Project Mentor

Turn real coding work into evidence-grounded, just-in-time learning without
slowing down delivery.

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB.svg)](https://www.python.org/)
[![CI](https://github.com/uczltw6/project-mentor/actions/workflows/ci.yml/badge.svg)](https://github.com/uczltw6/project-mentor/actions/workflows/ci.yml)
[![CodeQL](https://github.com/uczltw6/project-mentor/actions/workflows/codeql.yml/badge.svg)](https://github.com/uczltw6/project-mentor/actions/workflows/codeql.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/uczltw6/project-mentor/blob/v0.3.0/LICENSE)
[![Agent Skill](https://img.shields.io/badge/Agent%20Skill-open%20standard-5A67D8.svg)](https://agentskills.io/)

Project Mentor is a standalone Agent Skill for Codex and compatible hosts. It
keeps the user's real project goal first, explains only concepts that become
causally relevant, and separates evidence that a project uses a concept from
evidence that the user demonstrated it.

## Before and after

Without Project Mentor, a successful coding response may end at:

> Added the health endpoint. All focused tests pass.

With Project Mentor in `guided` mode, the implementation still comes first,
then the result becomes a compact evidence receipt:

> Added and verified the health endpoint. Request routing mattered because the
> method/path pair selects the handler; the anchor is
> `tests/test_app.py::test_health`. The agent demonstrated the implementation.
> Your understanding remains unassessed because you did not perform a step.

It is a receipt for observed work, not a certificate, grade, or mastery claim.

## What it does

- Completes real setup, implementation, debugging, and maintenance work using
  the same engineering standard as an ordinary task.
- Builds a small task-specific knowledge map with `blocking_now`,
  `explain_when_encountered`, and `deferred` concepts.
- Grounds explanations in files, symbols, configuration keys, diffs, commands,
  tests, runtime results, or explicit decisions.
- Supports live mentoring and conservative post-hoc audits.
- Produces milestone and final learning receipts in English or Chinese.
- Works in Git and non-Git directories and degrades cleanly when history,
  tests, Python, or other evidence is unavailable.
- Optionally validates and renders a local schema-versioned ledger with a
  standard-library-only Python helper.

It does not create courses, track learners across projects, call an external
model, collect telemetry, assign mastery scores, or write learning files unless
the user opts in.

## Modes

| Mode | Best for | Behavior |
| --- | --- | --- |
| `recap` | “Just finish, then summarize.” | Executes normally, interrupts only for safety or a material decision, and never quizzes proactively. |
| `guided` | “Build it with me.” | Default after activation; gives at most one short, timely micro-brief per milestone. |
| `hands_on` | “Let me try the important part.” | Offers a few high-value user actions with progressive hints, then resumes agent execution on request. |

Mode changes take effect immediately without restarting the task or losing the
working evidence map.

## Evidence, not inflated claims

Project Mentor keeps two claims separate:

1. **Project evidence** — the repository, command, test, runtime, or decision
   shows where a concept appeared.
2. **User evidence** — an observable user explanation, prediction, debugging
   choice, edit, or transfer attempt shows what the user did.

Agent-written code and passing tests can prove the project used a concept. They
cannot prove the user understands it. Missing evidence is labeled `unavailable`
or left `unassessed`; inferred and stale anchors are labeled explicitly.

## Install

Codex currently loads personal skills from `$HOME/.agents/skills` and
repository skills from `.agents/skills`. See the official
[Build skills documentation](https://developers.openai.com/codex/skills) for
the current loading and invocation model.

The repository also contains a skills-only Codex plugin manifest at
`.codex-plugin/plugin.json`; its installable copy under `skills/project-mentor`
is byte-for-byte identical to the repository-scoped skill. It adds no MCP
server, app connector, network access, or extra permission. The plugin bundle
is ready for a local or team marketplace, but is not represented as an official
or curated marketplace listing.

### Personal installation

Ask the built-in installer:

```text
$skill-installer install project-mentor from https://github.com/uczltw6/project-mentor/tree/v0.3.0/.agents/skills/project-mentor
```

Or install manually into an empty destination.

macOS/Linux:

```bash
git clone --depth 1 --branch v0.3.0 https://github.com/uczltw6/project-mentor.git
mkdir -p "$HOME/.agents/skills"
cp -R project-mentor/.agents/skills/project-mentor "$HOME/.agents/skills/project-mentor"
test -f "$HOME/.agents/skills/project-mentor/SKILL.md"
```

Windows PowerShell:

```powershell
git clone --depth 1 --branch v0.3.0 https://github.com/uczltw6/project-mentor.git
New-Item -ItemType Directory -Force "$HOME\.agents\skills" | Out-Null
Copy-Item -Recurse "project-mentor\.agents\skills\project-mentor" "$HOME\.agents\skills\project-mentor"
Test-Path "$HOME\.agents\skills\project-mentor\SKILL.md"
```

Codex normally detects the skill automatically. Restart Codex if it does not
appear. Back up or remove an older destination before a manual update so the
copies do not merge.

### Repository-scoped installation

Copy the release directory to `.agents/skills/project-mentor` in the target
repository. A checked-in copy is available to collaborators working in that
repository; the nested directory in this repository is itself the installable
artifact.

## Invoke it

Explicit invocation is predictable:

```text
$project-mentor Help me add this endpoint in guided mode. Finish the feature, teach only what becomes relevant, and give me an evidence receipt.
```

Implicit invocation is enabled and can match clear learning intent:

```text
Build this project with me and explain the architecture only when it matters.
```

Ordinary delegated coding, an isolated factual question, or course creation
should not activate the skill solely because code is involved.

## Two-minute quickstart

1. Install the skill at personal or repository scope.
2. Open a real project in Codex.
3. Ask: `$project-mentor Fix the current failing test in guided mode and help me
   understand the cause as we go.`
4. Let Codex inspect, reproduce, fix, and verify the task. Ask for `recap` or
   `hands_on` at any time; the change applies immediately.
5. Review the final receipt. Nothing is persisted by default. If you want a
   reusable record, explicitly ask to save the ledger and name the destination.

## Example receipt and ledger

The committed [example receipt](https://github.com/uczltw6/project-mentor/blob/v0.3.0/examples/learning-receipt.md) was generated
deterministically from the [example ledger](https://github.com/uczltw6/project-mentor/blob/v0.3.0/examples/project-mentor-ledger.json)
and [four input events](https://github.com/uczltw6/project-mentor/tree/v0.3.0/examples/events). It records:

- the verified health-endpoint milestone;
- request routing anchored to a named focused test;
- the minimal-response design decision and its tradeoff;
- agent evidence separately from unassessed user understanding; and
- one small next practice instead of an exhaustive curriculum.

## Privacy and persistence

- Working learning state stays in conversation or ephemeral storage by default.
- Persistent `.project-mentor/ledger.json` and
  `.project-mentor/learning-receipt.md` files require explicit opt-in, and the
  skill never commits them automatically.
- The helper has no runtime dependencies, telemetry, network client, account,
  database, shell-history ingestion, environment-value storage, or command
  execution facility.
- Recognized credentials are redacted before persistence and rendering. If
  redaction confidence is insufficient, evidence should be omitted.
- Repository instructions and source files are treated as untrusted data when
  they conflict with the user's request or higher-priority instructions.

See the [threat model](https://github.com/uczltw6/project-mentor/blob/v0.3.0/docs/threat-model.md) and [security policy](https://github.com/uczltw6/project-mentor/blob/v0.3.0/SECURITY.md)
for the complete boundary.

## Command-line interface

The mentoring workflow does not require the CLI. For deterministic validation,
redaction, event application, summaries, receipts, diagnostics, and anchor
verification, install the standard-library-only command from a trusted checkout:

```bash
pipx install project-mentor==0.3.0
project-mentor --version
project-mentor doctor --project-root .
```

For a project environment, use `python -m pip install project-mentor==0.3.0`.
Source-checkout installation remains available with `python -m pip install .`.

The installed executable and module entry point are equivalent:

```bash
project-mentor validate --kind ledger --input ledger.json
python -m project_mentor_cli render --ledger ledger.json --output learning-receipt.md
```

Without package installation, use the bundled fallback from the skill directory:

```bash
python scripts/project_mentor.py --version
python scripts/project_mentor.py verify-anchors --ledger ledger.json --root .
```

All entry points call the same implementation. The complete command, output,
compatibility, and exit-code contract is in [`docs/cli.md`](https://github.com/uczltw6/project-mentor/blob/v0.3.0/docs/cli.md).

## Develop and test

```bash
python -m venv .venv
python -m pip install -e ".[dev]"
python -m ruff check .
python -m ruff format --check .
python -m mypy --strict .agents/skills/project-mentor/scripts tools
python -m coverage run --branch -m pytest -q
python -m coverage report
python -m build --no-isolation --outdir <temporary-directory> .
python tools/validate_distribution.py --dist-dir <temporary-directory> --version 0.3.0
python tools/smoke_test_wheel.py --dist-dir <temporary-directory> --version 0.3.0 --skill-root .agents/skills/project-mentor
python tools/sync_skill.py --check
python tools/run_official_plugin_validation.py --plugin .
python tools/repository_scan.py --all
```

The test suite covers schema and event behavior, redaction, atomic writes,
rendering, the CLI lifecycle, public/personal parity tools, skill structure,
and behavioral fixtures. The v0.1.0 forward evaluation passed 14/14 isolated
cases with 260/260 applicable rubric points; read the exact, bounded claims in
[`docs/evaluation.md`](https://github.com/uczltw6/project-mentor/blob/v0.3.0/docs/evaluation.md).

## Limitations

- Semantic activation, concept selection, and teaching quality depend on the
  host model; the Python helper does not make pedagogical decisions.
- Redaction is defense in depth, not a guarantee that arbitrary secret formats
  will be recognized.
- Concurrent writers must reload after a revision conflict.
- Ledgers are not signed or tamper-evident. Validation proves structure and
  internal references, not the truth or authorship of supplied evidence.
- Event `actor` values are caller-supplied provenance labels, not authenticated
  identities; the host must ground `user` and `shared` labels in conversation.
- Post-hoc audits can only be as strong as the files, history, tests, and
  conversation evidence available to the host.
- English and Chinese are supported behavior targets, but v0.1.0 does not claim
  comprehensive localization.
- The skills-only plugin is not yet listed in an official or curated marketplace.
- PyPI publication uses GitHub OIDC Trusted Publishing; no long-lived PyPI
  credential is stored in the repository or release environment.

## Project links

- [Skill instructions](https://github.com/uczltw6/project-mentor/blob/v0.3.0/.agents/skills/project-mentor/SKILL.md)
- [Architecture](https://github.com/uczltw6/project-mentor/blob/v0.3.0/docs/architecture.md)
- [CLI contract](https://github.com/uczltw6/project-mentor/blob/v0.3.0/docs/cli.md)
- [Product contract](https://github.com/uczltw6/project-mentor/blob/v0.3.0/docs/product-contract.md)
- [Evaluation and reproduction](https://github.com/uczltw6/project-mentor/blob/v0.3.0/docs/evaluation.md)
- [v0.1.0 release readiness](https://github.com/uczltw6/project-mentor/blob/v0.3.0/docs/release-readiness-v0.1.0.md)
- [v0.2.0 release notes](https://github.com/uczltw6/project-mentor/blob/v0.3.0/docs/release-notes-v0.2.0.md)
- [v0.3.0 release notes](https://github.com/uczltw6/project-mentor/blob/v0.3.0/docs/release-notes-v0.3.0.md)
- [PyPI publishing](https://github.com/uczltw6/project-mentor/blob/main/docs/publishing.md)
- [Threat model](https://github.com/uczltw6/project-mentor/blob/v0.3.0/docs/threat-model.md)
- [v0.1.0 security review](https://github.com/uczltw6/project-mentor/blob/v0.3.0/docs/security-review-v0.1.0.md)
- [Contributing](https://github.com/uczltw6/project-mentor/blob/v0.3.0/CONTRIBUTING.md)
- [Security policy](https://github.com/uczltw6/project-mentor/blob/v0.3.0/SECURITY.md)
- [Changelog](https://github.com/uczltw6/project-mentor/blob/v0.3.0/CHANGELOG.md)
- [MIT license](https://github.com/uczltw6/project-mentor/blob/v0.3.0/LICENSE)
