# Project Mentor v0.3.0

V0.3 defines and packages the deterministic helper as a real command-line
application while keeping the Agent Skill self-contained.

## Highlights

- Install the `project-mentor` Python distribution from source and run the
  `project-mentor` console command.
- Use `python -m project_mentor_cli` as an equivalent module entry point.
- Continue using `python scripts/project_mentor.py` inside a standalone skill;
  all three entry points call the same standard-library implementation.
- Inspect the installed CLI version with `project-mentor --version`.
- Build wheel and source distributions containing the actual runtime package
  rather than development metadata only.
- Validate distribution metadata, entry-point loading, module execution, wheel
  contents, and an installed ledger lifecycle in automated tests and CI.

## Compatibility

All eight v0.2 command names and ledger schema version 1 remain supported. CLI
versioning and ledger schema versioning are separate: adding a command or option
does not silently change the persisted contract.

## Publication boundary

This release makes the project package-ready. It does not claim a PyPI release
until the built artifacts are uploaded, downloaded from the public index, and
verified independently. The runtime remains local, offline, telemetry-free,
and dependency-free.
