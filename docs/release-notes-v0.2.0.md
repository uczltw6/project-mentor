# Project Mentor v0.2.0

V0.2 turns the original standalone skill into a more complete, maintainable
distribution without widening its privacy or trust boundary.

## Highlights

- Install as the existing standalone skill or package it as a skills-only
  Codex plugin. Both copies are checked byte-for-byte in CI.
- Run `doctor` to check Python, required skill files, a project root, and an
  optional ledger without changing project state or disclosing absolute paths.
- Run `verify-anchors` to classify supported digest, symbol, configuration, and
  test anchors as `valid`, `stale`, or `unavailable`. It is read-only unless
  `--write` is combined with an expected ledger revision.
  Reports hash rather than repeat raw locators, reject symlink/file-swap races,
  and bound text and digest reads.
- Emit the complete deterministic receipt contract with `render --format json`
  while retaining Markdown as the default.
- Protect releases with a single aggregate `CI Gate`; compatible Dependabot
  updates stay grouped while major updates remain individually reviewable.

## Compatibility

Ledger schema version 1 and existing concept-scoped `evidence_marked_stale`
events remain valid. V0.2 adds an owner-scoped form for evidence attached to a
concept, decision, or milestone. The runtime remains Python 3.10+, standard
library only, local, non-networked, and free of telemetry.

## Packaging boundary

The repository plugin is a distribution wrapper around the same skill; it adds
no MCP server or app. This release is not a PyPI runtime package and does not
claim an official or curated marketplace listing.
