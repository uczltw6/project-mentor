# Project Mentor v0.1.0

Project Mentor is a standalone Agent Skill for people who want to finish real
coding work while learning the few concepts that actually matter to that work.
It supports setup, implementation, debugging, maintenance, and evidence-based
review without turning the project into a course.

## What is included

- Three mentoring modes: `recap` finishes first and summarizes, `guided`
  provides short just-in-time explanations, and `hands_on` offers a few
  high-value steps for the user to try with progressive hints.
- Live mentoring during a task and conservative post-hoc audits of completed
  work.
- Small, project-grounded concept maps and learning receipts anchored to
  observable files, symbols, tests, commands, results, and decisions.
- A strict separation between evidence that the project used a concept and
  evidence that the user personally demonstrated understanding. Agent work is
  never counted as a user demonstration.
- English and Chinese behavior targets, immediate mode switching, Git and
  non-Git operation, and graceful degradation when tools or evidence are
  unavailable.
- An optional Python 3.10+ helper for schema-versioned ledger initialization,
  event application, validation, rendering, summaries, and redaction. It uses
  only the Python standard library at runtime.

The mentoring workflow itself does not require Python. Working learning state
stays in the conversation or ephemeral storage by default. Persistent ledgers
and receipts require explicit opt-in. The skill and helper are local-only: they
include no telemetry, hosted account, database, external model call, or network
client.

## Install and invoke

Install through the built-in skill installer:

```text
$skill-installer install project-mentor from https://github.com/uczltw6/project-mentor/tree/v0.1.0/.agents/skills/project-mentor
```

Or clone the tagged release and copy
`.agents/skills/project-mentor` to `$HOME/.agents/skills/project-mentor` for a
personal installation, or to the same relative path in another repository for
repository scope. The README contains complete macOS, Linux, and Windows
commands.

Start a real project task with an explicit invocation:

```text
$project-mentor Fix the current failing test in guided mode and help me understand the cause as we go.
```

## Validation and evaluation

The release candidate passed Ruff lint and formatting, strict mypy, the full
pytest suite on its supported platform paths, and 95% branch coverage against a
90% gate. Official skill validation passed for both the installed and public
copies, which contain 15 byte-for-byte identical release files. The repository
and complete Git history passed the credential and path scan. Independent
security review found no unresolved critical or high-severity issue.

Clean-context forward evaluation passed 14 of 14 cases and all 260 applicable
rubric points. The cases covered explicit and implicit activation, all three
modes, live and post-hoc work, mode changes, user-evidence boundaries, secret
handling, non-Git work, English and Chinese behavior, and a no-skill baseline.
These are bounded release-process results, not proof of universal teaching
quality or educational outcomes.

## V1 non-goals and known limitations

- V1 is not a curriculum, learning-management system, education platform, IDE
  extension, MCP server, plugin, marketplace package, or package-registry
  release.
- It provides no grades, mastery claims, certification, learner profiling,
  cross-project graph, spaced repetition, cloud sync, team analytics,
  telemetry, automatic shell-history ingestion, or arbitrary command runner.
- Activation, concept selection, and teaching quality depend on the host model;
  the deterministic helper does not make pedagogical decisions.
- Redaction is defense in depth and cannot guarantee recognition of every
  possible secret format.
- Post-hoc results are limited by the available project, history, test, runtime,
  and conversation evidence.
- Ledgers are not signed or tamper-evident, and actor labels are caller supplied;
  validation establishes structure and internal references, not authorship or
  truth.
- English and Chinese are supported behavior targets, not a claim of complete
  localization.

See the README, product contract, evaluation report, threat model, and security
review in the repository for the full boundaries and reproduction instructions.
