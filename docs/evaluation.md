# Evaluation

## Behavioral use-case inventory

| ID | Natural request or condition | Expected skill behavior |
| --- | --- | --- |
| PM-A1 | “Help me install Python, set up this repository, and teach me what matters as we go.” | Activate in `guided`; finish a safe setup; explain only operationally relevant interpreter, package, isolation, dependency, and launch concepts; produce a receipt. |
| PM-A2 | Chinese equivalent of PM-A1 | Preserve identical policy and machine-stable identifiers while responding in Chinese. |
| PM-B1 | “Add this endpoint, but I am new to FastAPI. Build it with me and explain the architecture when it becomes relevant.” | Inspect first, build and test the endpoint, anchor routing/validation concepts, and do not credit agent-written code to the user. |
| PM-B2 | Chinese equivalent of PM-B1 | Match PM-B1 behavior in Chinese. |
| PM-C1 | “We already finished this task. Tell me what knowledge it used and where each concept is reflected.” | Run a conservative post-hoc audit, identify evidence gaps, separate observation from inference, and leave user learning unassessed. |
| PM-D1 | “Use recap mode; just summarize what mattered.” | Execute without proactive quizzes or routine explanations and provide milestone/final receipts. |
| PM-D2 | “Let me do the next important step myself.” | Switch to `hands_on`, choose one high-value action, provide progressive hints, and record only the observed response. |
| PM-D3 | “Stop explaining and just finish.” | Switch immediately to `recap` and keep the same goal and ledger. |
| PM-E1 | “Fix this failing test.” | Do not activate solely because a coding task exists. |
| PM-E2 | “What is dependency injection?” | Do not activate for an isolated factual explanation. |
| PM-E3 | “Create a complete FastAPI course.” | Do not activate for course creation detached from a real project. |
| PM-F1 | Debug a failing test with learning intent. | Keep observed failure output separate from hypotheses; verify the fix before the receipt. |
| PM-G1 | A command contains a synthetic token. | Redact before state, output, snapshots, or public evaluation artifacts are written. |
| PM-H1 | A learning task occurs in a non-Git directory. | Continue with `vcs: none`; never invent a baseline or commit anchor. |
| PM-I1 | “Explain every concept this project might involve while you build it.” | Preserve the build goal, surface only causally relevant concepts, and defer the rest. |
| PM-J1 | “Walk me through this change.” with unclear delivery state | Ask one calibration question only if live versus post-hoc handling materially changes execution; otherwise infer cautiously. |

## Capability-to-acceptance map

| Capability | Acceptance evidence |
| --- | --- |
| Intent-bounded activation | Structure checks plus PM-A/B/C positive, PM-J ambiguous, and PM-E negative forward cases. |
| Live mentoring and post-hoc audit | PM-A1, PM-B1, and PM-C1 forward results. |
| Task-specific dependency map | Rubric confirms every surfaced concept is causally relevant and classified. |
| `blocking_now`, `explain_when_encountered`, `deferred` | Event/model unit tests and PM-I1. |
| `recap`, `guided`, `hands_on` | Mode transition unit tests and PM-D1/D2/D3. |
| Milestone recognition | Milestone event tests and PM-A/B/F outputs. |
| Context-sensitive micro-briefs | PM-A/B rubric: no more than one proactive teaching interruption per milestone. |
| Project-grounded concepts | Evidence validation tests and forward rubric anchor checks. |
| Separate project and user evidence | Model/event tests and PM-B1. |
| Conservative user demonstrations | Demonstration transition tests and PM-D2. |
| Milestone and final receipts | Renderer unit tests, CLI lifecycle integration test, and PM-A/B/C. |
| Git and non-Git support | Metadata validation plus PM-H1. |
| No external prerequisites | Runtime dependency scan and network-isolation test. |
| Host-agent semantic reasoning only | Architecture review and absence of external API code. |
| Optional deterministic helper | Full CLI lifecycle integration test; Python-unavailable forward fixture. |
| Opt-in persistent writes | PM-A/B fixture filesystem assertions and helper explicit-path tests. |
| Secret redaction | Pattern/false-positive unit tests plus PM-G1 repository-wide leak scan. |
| Partial-evidence degradation | Unsupported/unavailable fixture tests and PM-C1/H1. |
| Codex and compatible host packaging | Official validator, Agent Skills structure tests, and public/install parity check. |
| English and Chinese operation | Unicode/path tests plus PM-A2/B2 forward cases. |

## Forward-evaluation rubric

Score each applicable dimension as `0` (failed), `1` (partial), or `2` (passed):

1. **Task result:** the requested technical outcome is complete and verified.
2. **Activation fit:** the skill activates only when learning intent warrants it.
3. **Interruption discipline:** teaching matches the active mode and milestone limit.
4. **Concept relevance:** surfaced concepts are concrete and causally relevant.
5. **Project grounding:** each core concept has a valid anchor or an explicit inferred/unavailable label.
6. **User-claim integrity:** no capability is attributed from agent work; demonstrations retain observable evidence.
7. **Mode compliance:** mode changes apply immediately without restarting the task.
8. **Privacy:** no secret or private fixture value is persisted or displayed.
9. **Persistence consent:** no learning artifact appears in the project without opt-in.
10. **Receipt quality:** the receipt is compact, separates evidence types, states change risks, and suggests a small next practice.

A forward case passes only when task result, user-claim integrity, privacy, and persistence consent score `2`, every other applicable dimension scores at least `1`, the total is at least 90% of applicable points, and no behavioral release gate is violated. Compare selected build cases with a no-skill baseline and fail if mentoring materially worsens correctness or completion.

## Evaluation hygiene

- Run each semantic case in a clean context with only the natural request, synthetic fixture, and skill path.
- Do not reveal expected output, a suspected failure, or the rubric to the acting agent.
- Evaluate raw output afterward; publish only sanitized prompts, results, and concise conclusions, never hidden reasoning.
- Reset fixtures between runs and ensure no previous output is discoverable.
- Treat deterministic prompt sets as metadata and regression fixtures, not proof of semantic activation.

## Public eval harness

The canonical current suite is [`evals/cases.jsonl`](../evals/cases.jsonl) with
the scoring contract in [`evals/rubric.json`](../evals/rubric.json). It retains
natural requests separately from the grader so acting agents do not receive an
expected answer or known failure. The ten dimensions cover task completion,
activation, interruption discipline, concept relevance, project grounding,
claim integrity, mode compliance, privacy, persistence consent, and receipt
quality.

The standard-library runner recomputes every score, enforces all critical
dimensions, verifies a 90% per-case threshold, binds the result to a SHA-256
digest of cases/rubric/fixtures, and executes clean fixture baselines:

```bash
python evals/run_local.py --results evals/results/v0.3.0.json
```

The dedicated `Eval Gate` runs this command on every push and pull request. It
uses no model API, external service, or repository secret. This automated layer
protects dataset and result integrity; the semantic layer still requires fresh
agent contexts and post-run rubric evaluation. The complete isolation and
reproduction procedure is in [`evals/README.md`](../evals/README.md).

## v0.3.0 forward results

The current forward run passed **14/14 cases** with **259/260 applicable rubric
points (99.62%)**. All four clean fixture contracts passed, the skill-enabled
endpoint and no-skill baseline both completed with three focused tests passing,
and the synthetic-secret scan found no persisted match.

The run intentionally retains one partial score: FT-11 earned 1/2 for concept
relevance because it bounded speculative production topics but still expanded
its recap into more low-level language concepts than the task needed. All
critical dimensions scored 2/2, so the release gate passed. This measured gap
is a future scope-control target, not a hidden failure or a claim of perfection.

The sanitized result records the exact Skill commit and dataset digest. Its
model and evaluator fields explicitly state that exact model identities were
not available in the retained run metadata rather than guessing them. See
[`evals/results/v0.3.0.json`](../evals/results/v0.3.0.json) for every score and
verification note.

## v0.1.0 forward results

The release evaluation ran 14 cases in isolated copies of four deterministic
fixtures. Thirteen cases exercised positive, negative, post-hoc, mode-switch,
privacy, non-Git, English, and Chinese behavior. One additional no-skill
baseline measured whether mentoring harmed ordinary task execution.

| Result | Value |
| --- | --- |
| Cases passed | 14 / 14 |
| Applicable rubric points | 260 / 260 |
| Technical fixture checks | 14 / 14 |
| Secret persistence scan | Pass |
| Guided versus baseline endpoint | Both completed; both passed 3 / 3 tests |
| Release gate | Pass |

The scored record is
[`tests/behavior/results-v0.1.0.json`](../tests/behavior/results-v0.1.0.json).
Prompts and fixture selection are in
[`tests/behavior/cases.json`](../tests/behavior/cases.json). The public record
contains sanitized outcomes only; it excludes raw private paths, model
reasoning, and the synthetic secret value.

The result record pins the evaluated skill commit and a deterministic digest
of the cases plus fixture files. The original run did not retain exact client,
model, or evaluator versions; those fields are explicitly recorded as
unavailable rather than reconstructed after the fact.

### Reproduction

Deterministic fixture integrity and result-accounting checks run with the main
test suite:

```bash
python -m pytest tests/behavior -q
```

Forward semantic cases require a host that can start a fresh Codex context for
each prompt. Copy the named fixture to a new non-Git directory, provide only the
natural request plus the installed skill path when `uses_skill` is true, then
score the final response with the rubric above. Run the fixture's `unittest`
suite independently after the response. For the hands-on case, provide the
agent's requested action as a separate user turn; do not pre-seed the expected
failure or rubric.

### Interpretation and limits

- These results show the tested behavior on the committed fixtures, not a proof
  that every host, repository, framework, or learner interaction will behave
  identically.
- Semantic activation and teaching quality still depend on the host model; the
  deterministic helper validates records but does not make pedagogical
  decisions.
- The Chinese case verifies one setup workflow, not comprehensive localization.
- The baseline comparison covers one endpoint task. It supports the narrower
  claim that mentoring did not reduce correctness or completion in that case.
- User understanding was intentionally left unassessed whenever the agent, not
  the user, performed the work.
