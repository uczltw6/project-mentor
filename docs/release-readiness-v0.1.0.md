# v0.1.0 release readiness

## Candidate status

The local v0.1.0 candidate passed every pre-release gate on 2026-08-01. The
public repository is available, but hosted CI and CodeQL must pass on the final
commit before tagging and the GitHub release.

| Gate | Result |
| --- | --- |
| Ruff lint and format | Pass |
| Strict mypy | Pass |
| Pytest | 119 passed, 3 skipped locally |
| Branch coverage | 95% (90% required) |
| Official skill validation | Pass for installed and public copies |
| Personal/public release files | 15 files, byte-for-byte identical |
| Repository and full-history scan | Pass |
| Clean-context forward evaluation | 14 / 14 pass; 260 / 260 applicable points |
| Independent security review | No critical/high issue; all medium findings resolved |
| Clean-clone rehearsal | Pass |

The three local skips are symlink branches unavailable to the current Windows
account. CI runs those branches on Linux and also repeats the suite on Windows.

## Installed skill verification

The personal installation was located uniquely by `name: project-mentor` under
the current user-scope skill directory. It is a regular directory, contains no
`__pycache__`, `.pyc`, or `.pyo` residue, passes the official validator, exposes
all six documented helper subcommands, and exactly matches the nested public
skill.

The metadata file is LF-normalized to match `.gitattributes`. An initial clean
clone correctly exposed a CRLF/LF byte mismatch from the Windows-generated
canonical file; normalization fixed it, and the clean clone parity check then
passed.

## Clean-clone rehearsal

A new local clone with its own virtual environment ran the documented
development installation and these release gates:

```text
python -m ruff check .
python -m ruff format --check .
python -m mypy --strict .agents/skills/project-mentor/scripts tools
python -m coverage run --branch -m pytest -q
python -m coverage report --fail-under=90
python tools/sync_skill.py --check
python tools/run_official_skill_validation.py --skill .agents/skills/project-mentor
python tools/repository_scan.py --all
```

The clone retained no tracked changes after verification. Fresh explicit skill
invocation, non-Git operation, mode changes, Chinese output, and the no-skill
baseline were already exercised in the isolated forward evaluation.

## Claim boundary

This checklist demonstrates release-process results for the committed candidate.
It does not establish universal host behavior, perfect secret recognition,
authenticated ledger authorship, or user mastery. Hosted GitHub Actions and the
public anonymous-install path remain mandatory release gates for v0.1.0.
