# Project Mentor evals

This directory is the public evaluation surface for Project Mentor. It keeps
semantic agent evaluation separate from deterministic software testing and does
not call a model API, require a credential, or add a runtime dependency.

## Contents

- `cases.jsonl` contains natural user requests and case metadata. Acting agents
  receive the request, fixture copy, and skill path only—not the rubric or a
  known failure.
- `rubric.json` defines ten task-specific dimensions and the release gate.
- `graders.py` validates and recomputes every case and aggregate score.
- `run_local.py` verifies the dataset digest, stored results, and clean fixture
  baselines.
- `results/` contains sanitized, versioned score records. Raw transcripts,
  hidden reasoning, secrets, and private paths are never committed.

The deterministic fixture sources remain under `tests/behavior/fixtures` so
they are also exercised by the normal test suite.

## Run the CI-safe gate

From the repository root:

```bash
python evals/run_local.py --results evals/results/v0.3.0.json
python evals/run_local.py --results evals/results/v0.3.0.json --json
```

This command proves that the case inventory, rubric, fixture bytes, score
accounting, and stored release record agree. It does not pretend to rerun or
prove nondeterministic model behavior.

## Run a semantic forward evaluation

For each case, start a fresh agent context and a fresh copy of the named fixture:

1. Give the acting agent only the natural `request`, fixture copy, and the
   `.agents/skills/project-mentor` path when `uses_skill` is true.
2. Do not provide the rubric, expected behavior, earlier results, or a suspected
   failure. Keep sibling result files inaccessible to the acting agent.
3. For `FT-05`, respond in a separate user turn to the action the agent actually
   requests; do not pre-seed an expected edit or failure.
4. For `FT-08`, replace `<SYNTHETIC_TOKEN>` in memory with a new synthetic value.
   Verify that the value is absent from the final answer, fixture, logs, and
   stored result, then discard it.
5. Run the fixture's focused tests independently after the agent stops. Score
   the observable outcome against `rubric.json` only afterward.
6. Record scores plus concise `behavior` and `technical` verification. Do not
   save chain-of-thought or an authenticated/private path.
7. Re-run `run_local.py` against the candidate result. A structural mismatch
   exits `2`; a valid but failing release gate exits `1`.

Compare `FT-02` with the no-skill `FT-B1` baseline. Mentoring fails the release
gate if it materially reduces correctness or completion even when its teaching
scores are otherwise strong.

## Interpretation

Eval results describe only the committed cases, fixtures, host, and run record.
They are regression evidence, not a certificate that every model, repository,
or learner interaction will behave identically. A successful agent run can show
project usage and user exposure; it cannot establish user mastery.
