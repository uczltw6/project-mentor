# v0.1.0 security review

## Scope and method

An independent clean-context agent performed a read-only review of the v0.1.0
candidate, including the installable skill, Python helper, tests, workflows,
examples, threat model, current worktree, and reachable/dangling Git history.
The review made no filesystem or Git changes and contacted no external service.

The release gate also scans every tracked or non-ignored releasable file and the
full Git patch history for credential forms, private user paths, private-key
material, authenticated URLs, build residue, unsafe paths, and oversized files.
Findings are reported by rule and relative location without echoing matched
content.

## Resolved findings

The review found no critical or high-severity issue. Four medium or concrete
hardening findings were resolved before release:

| Finding | Resolution | Regression evidence |
| --- | --- | --- |
| Duplicate JSON object keys used last-value-wins parsing | Reject duplicate keys at every nesting level before schema validation, without echoing the key | `tests/unit/test_io.py` duplicate-key cases |
| Backticks in an untrusted evidence locator could leave a one-backtick code span | Delimit inline code with a fence longer than the longest contained backtick run | `tests/unit/test_render.py` link, image, and HTML locator case |
| `apply-event` hashed a ledger with an unbounded `read_bytes()` before its 1 MiB read | Bound both file input and streaming hashes, enforce the same cap during stat and read, and refuse symlink output paths before hashing | `tests/unit/test_io.py` oversized and symlink hash cases |
| Release sync resolved a skill root before checking whether it was a symlink | Refuse a symlink root before resolution | `tests/unit/test_dev_tools.py` root-symlink case |

The review also confirmed that event actors and ledgers are unsigned,
caller-supplied records rather than authenticated identity evidence. That is a
documented V1 boundary: the host must ground `user` or `shared` provenance in an
observable conversation event.

## No additional finding

- The repository and history scan found no live credential or private user path;
  security fixtures construct synthetic values and sanitized reports never echo
  them.
- Runtime code contains no network, telemetry, subprocess, recorded-command,
  shell-history, or environment-value collection path.
- Final-target symlinks are refused, expected content is rechecked before atomic
  replacement, and prior ledgers survive expected failures.
- Revision conflicts, identical replay, conflicting event-ID reuse, future
  schema rejection, and user-evidence actor rules are covered.
- GitHub Actions are commit-pinned, checkout credentials are disabled, and only
  CodeQL receives `security-events: write`.

## Residual risks

Redaction cannot recognize every possible secret format. Ledger validity does
not prove factual truth or authorship. Package indexes and GitHub Actions remain
external trust roots. Host-model interpretation of malicious repository prose
is nondeterministic. These limits are tracked in the main
[threat model](threat-model.md) and do not weaken the opt-in persistence or
delivery-first contracts.
