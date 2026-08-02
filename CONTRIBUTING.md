# Contributing

Thanks for helping make Project Mentor more useful, truthful, and safe.

## Before opening a change

- Use an issue for material behavior or schema changes so the activation and
  evidence implications can be discussed first.
- Keep the delivery-first promise: mentoring must not reduce correctness,
  completion, privacy, or user control.
- Never add real credentials, private project content, raw model reasoning, or
  unsanitized absolute paths to fixtures, commits, issues, or pull requests.
- Schema version 1 is strict. Propose a versioned migration instead of silently
  accepting new fields or changing existing semantics.

## Local setup

Python 3.10 or newer is required for development and the optional helper.

```bash
python -m venv .venv
python -m pip install ".[dev]"
```

Run the release checks before submitting:

```bash
python -m ruff check .
python -m ruff format --check .
python -m mypy --strict .agents/skills/project-mentor/scripts tools evals
python -m coverage run --branch -m pytest -q
python -m coverage report
python evals/run_local.py --results evals/results/v0.3.0.json
python tools/sync_skill.py --check
python tools/repository_scan.py --all
```

The official `quick_validate.py` from the current `skill-creator` should also
pass for `.agents/skills/project-mentor`. The wrapper in
`tools/run_official_skill_validation.py` locates a normal Codex installation or
accepts `--validator` explicitly.

## Canonical skill changes

Development uses the personal skill directory as the canonical source and the
repository directory as the public release copy. If you do not maintain a
personal installation, edit the public copy and validate it directly. Maintainer
release work synchronizes with:

```bash
python tools/sync_skill.py --source /path/to/project-mentor --destination .agents/skills/project-mentor --write
python tools/sync_skill.py --source /path/to/project-mentor --destination .agents/skills/project-mentor --check
```

Do not add repository-only tests, CI files, or contributor documentation inside
the installable skill directory.

## Tests and behavior changes

- Add focused unit tests for deterministic code paths and failure preservation.
- Add integration coverage for CLI contracts or persistent state changes.
- Update activation metadata fixtures for description-boundary changes, but do
  not treat those fixtures as semantic proof.
- Run clean-context forward cases for changes to activation, modes, interruption
  policy, evidence language, privacy, or receipts.
- Keep natural prompts in `evals/cases.jsonl`, score against `evals/rubric.json`
  only after the acting agent stops, and validate sanitized results with the
  local eval gate.
- Compare a representative learning case with a no-skill baseline when a change
  could affect ordinary task completion.
- Publish only sanitized prompts, numeric results, and concise conclusions.

## Pull requests

Keep commits reviewable and explain the user-visible behavior, tests, privacy
impact, and compatibility impact. A pull request should leave the public skill
copy internally clean and should not weaken the documented threat model.

By participating, you agree to follow the [Code of Conduct](CODE_OF_CONDUCT.md).
