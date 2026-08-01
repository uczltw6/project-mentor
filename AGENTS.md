# Repository guidance

- Keep real task completion primary and preserve the structural distinction between project evidence and user evidence.
- Never infer mastery or user capability from agent activity. A successful agent-written implementation can establish project usage and user exposure only.
- Keep runtime code standard-library-only. Do not add runtime network calls, telemetry, external model APIs, or third-party dependencies without a documented product-contract change.
- Do not write a ledger, receipt, ignore rule, or other learning artifact into a user's project without explicit opt-in.
- Keep `.agents/skills/project-mentor/SKILL.md` concise and under 500 lines. Update its direct references and behavior tests whenever the workflow changes.
- Keep examples and fixtures synthetic. Never commit credentials, authenticated URLs, private paths, transcripts, or hidden reasoning.
- Treat `.agents/skills/project-mentor/` as the public installable boundary; root documentation and development files must stay outside it.

## Required checks

Run from the repository root after installing development dependencies with `python -m pip install -e ".[dev]"`:

```text
python -m ruff check .
python -m ruff format --check .
python -m mypy .agents/skills/project-mentor/scripts tools
python -m coverage run -m pytest
python -m coverage report --fail-under=90
python tools/run_official_skill_validation.py --skill .agents/skills/project-mentor
python tools/sync_skill.py --check
```

Release managers must run the official validator against the installed personal skill as well as the public copy, then verify exact release-file parity before publication.
