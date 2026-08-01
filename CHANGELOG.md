# Changelog

All notable changes to Project Mentor are documented here. The project follows
[Semantic Versioning](https://semver.org/).

## [0.2.0] — 2026-08-01

### Added

- A skills-only Codex plugin manifest and byte-for-byte synchronized plugin skill.
- Read-only `doctor` diagnostics for Python, skill structure, project roots, and ledgers.
- Conservative `verify-anchors` checks for digest, symbol, configuration, and test anchors,
  with bounded stable-file reads, hashed report locators, and an explicit
  revision-guarded `--write` mode for stale evidence.
- Deterministic JSON learning receipts through `render --format json`.
- A single `CI Gate` status suitable for main-branch protection.

### Changed

- Dependabot groups only compatible minor and patch development updates; majors remain
  individually reviewable.
- Stale-evidence events can address evidence owned by concepts, decisions, or milestones
  while retaining compatibility with V1 concept events.

## [0.1.0] — 2026-08-01

### Added

- Intent-bounded live mentoring and post-hoc learning audits.
- `recap`, `guided`, and `hands_on` modes with immediate switching.
- Project-grounded concept maps, conservative user evidence, milestones, and
  English/Chinese receipts.
- Optional schema-versioned, standard-library-only Python helper with strict
  validation, redaction, idempotent events, revision checks, and atomic writes.
- Git and non-Git behavior, opt-in persistence, public examples, evaluation
  fixtures, and cross-platform verification.

[0.1.0]: https://github.com/uczltw6/project-mentor/releases/tag/v0.1.0
[0.2.0]: https://github.com/uczltw6/project-mentor/releases/tag/v0.2.0
