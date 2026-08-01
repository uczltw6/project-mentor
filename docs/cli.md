# Command-line interface

Project Mentor provides one local, standard-library runtime through three
equivalent entry points:

```text
project-mentor ...
python -m project_mentor_cli ...
python scripts/project_mentor.py ...
```

The first two are available after installing the Python distribution. The last
is the self-contained fallback bundled with the Agent Skill. All three call the
same implementation and use the same ledger schema.

## Contents

- [Install from source](#install-from-source)
- [Global contract](#global-contract)
- [Commands](#commands)
- [Output contract](#output-contract)
- [Exit codes](#exit-codes)
- [Compatibility](#compatibility)

## Install from source

Until a PyPI release is explicitly published, install from a trusted checkout:

```bash
python -m pip install .
project-mentor --version
project-mentor doctor --project-root .
```

For an isolated application install, `pipx install .` is also suitable. The
runtime has no third-party dependencies and performs no network access,
telemetry, shell-history ingestion, or command execution.

## Global contract

```text
project-mentor [--help] [--version] [--debug] <command> ...
```

- `--help` prints command help and exits successfully.
- `--version` prints `project-mentor <semantic-version>` and exits successfully.
- `--debug` exposes a traceback only for unexpected implementation failures.
  Expected input, revision, conflict, and I/O failures never print a traceback.

## Commands

| Command | Purpose | Persistent by default |
| --- | --- | --- |
| `init` | Create a schema-versioned empty ledger | Only with explicit `--output` |
| `apply-event` | Validate, redact, and atomically apply one event | Yes; requires an explicit ledger and expected revision |
| `validate` | Validate a ledger, event, evidence item, demonstration, or receipt | No |
| `render` | Render a deterministic Markdown or JSON learning receipt | Only with explicit `--output` |
| `summarize` | Emit a compact deterministic JSON summary | Only with explicit `--output` |
| `redact` | Redact likely secrets from bounded UTF-8 text | Only with explicit `--output` |
| `doctor` | Diagnose Python, skill files, project root, and an optional ledger | No |
| `verify-anchors` | Verify supported local evidence anchors | No; mutation additionally requires `--write` and `--expected-revision` |

Run `project-mentor <command> --help` for the complete option list. The ledger
contract, locator grammars, and command examples are documented in the
[ledger reference](../.agents/skills/project-mentor/references/ledger-schema.md).

`doctor` checks an Agent Skill when `--skill-root` is provided or when it finds
one under the project root, the user's `.agents/skills` directory, or the
bundled runtime. A standalone CLI installation without a skill is valid: the
skill check is reported as `skipped`, while Python, project, and optional ledger
checks still run.

## Output contract

- Command results go to stdout; expected diagnostics go to stderr.
- `-` means stdin or stdout only on options that explicitly support it.
- JSON uses UTF-8, sorted keys, two-space indentation, and a trailing newline.
- Markdown rendering is deterministic for the same ledger, timestamp,
  language, selection limit, and output locator.
- A command that reads a file refuses to use that same path as its output.
- Persistent replacement is same-directory, revision-checked, symlink-safe,
  flushed, and atomic.

## Exit codes

| Code | Meaning |
| --- | --- |
| `0` | Success, including an identical event replay |
| `1` | A `doctor` check failed, or an unexpected failure was hidden |
| `2` | Invalid arguments (including identical input/output paths), JSON, schema, enum, ID, timestamp, or version |
| `3` | Expected revision or file-content conflict |
| `4` | I/O or path-safety failure |
| `5` | An event ID was replayed with different content |

## Compatibility

The CLI version and ledger `schema_version` are separate contracts. A CLI minor
release may add commands or options while continuing to read schema version 1.
Existing command names, meanings, output fields, and exit-code classes are
treated as stable within a major CLI version. A future incompatible ledger
shape must use a new schema version and fail closed in older clients.
