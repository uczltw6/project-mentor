# Behavior examples

Use these compact cases to calibrate workflow output. Keep real responses proportional to the user's task rather than copying the examples mechanically.

## Contents

- [Positive and negative boundaries](#positive-and-negative-boundaries)
- [Live Python setup](#live-python-setup)
- [Feature in an unfamiliar stack](#feature-in-an-unfamiliar-stack)
- [Post-hoc audit](#post-hoc-audit)
- [Mode changes](#mode-changes)
- [User-evidence boundary](#user-evidence-boundary)
- [Debugging](#debugging)
- [Privacy and non-Git operation](#privacy-and-non-git-operation)
- [Chinese behavior](#chinese-behavior)

## Positive and negative boundaries

Activate:

- “Build this endpoint with me and explain the architecture when it becomes relevant.”
- “Help me set up Python and teach me what matters as we go.”
- “We finished this migration. Show which concepts it used and where they appear.”
- “Let me do the next important step so I understand it.”
- “Give me a learning receipt grounded in the files and tests.”

Do not activate:

- “Fix this failing test.”
- “What is dependency injection?”
- “Write a full beginner FastAPI course.”
- “Refactor this function and open a pull request.”

Ambiguous:

- “Walk me through this change.” Inspect conversation and repository state. Ask one question only if live mentoring versus post-hoc explanation would materially change execution.

## Live Python setup

User:

> Help me install Python, set up this repository, and teach me what matters as we go.

Good `guided` behavior:

1. Inspect the operating system, repository instructions, existing version/dependency files, and installed commands.
2. Explain a consequential installer or PATH choice before changing it.
3. Introduce interpreter, package manager, virtual environment, dependency declaration, and launch command only when each becomes operational.
4. Anchor claims only to files and commands actually observed, such as `.python-version`, `.venv`, `pyproject.toml`, or a launch command.
5. Verify that the environment runs.
6. Produce a compact receipt.

Micro-brief:

> **What we are doing:** Creating a project-local virtual environment.  
> **Why now:** The next command installs this project's packages, and isolation prevents changing other Python projects.  
> **Where:** `.venv/` and the interpreter used by the launch command.  
> **Risk:** Installing into system Python can create version conflicts.

Do not claim that the user can recreate the environment when the agent ran every command. Record project evidence and set exposure to `encountered`; leave demonstrations empty.

## Feature in an unfamiliar stack

User:

> Add this endpoint, but I am new to FastAPI. Build it with me and explain the architecture when it becomes relevant.

Good behavior:

- inspect routing, models, dependencies, tests, and repository instructions first;
- keep endpoint behavior and tests primary;
- brief routing when the route is placed, validation when the request model is defined, and async behavior only if it affects this implementation;
- anchor to symbols such as `create_item`, `CreateItemRequest`, and `test_create_item_rejects_invalid_input`;
- run focused tests and distinguish their assertions from broader application correctness;
- attribute agent-written code to the agent, not the user.

Bad behavior:

- front-load a full FastAPI curriculum;
- explain every decorator and syntax token;
- stop delivery until the user passes a quiz;
- state “you learned request validation” without a demonstration.

## Post-hoc audit

User:

> We already finished this task. Tell me what knowledge it used and where each concept is reflected.

Good audit language:

> Observed: `api/routes.py#create_item` registers the route and `tests/test_items.py#test_invalid_payload` checks a rejected payload.  
> Inferred: the request model is intended to keep validation at the API boundary. Commit history was unavailable, so I cannot establish when or why that choice was introduced.  
> User evidence: none in the available conversation; understanding remains unassessed.

Do not invent a baseline, author, command, or test run. A current file proves current structure, not the history that produced it.

## Mode changes

User:

> Stop explaining for now and just finish it.

Response behavior:

> Switching to `recap`. I’ll keep the same goal and finish the implementation, then summarize the important project evidence at the next milestone.

Do not ask for confirmation or discard the ledger.

User:

> Let me do the next important step myself.

Response behavior:

> Switching to `hands_on`. The highest-value next step is adding the invalid-input case to the focused test because it makes the validation boundary observable. I’ll give you the existing test pattern and review your change.

Do not assign dependency installation, file copying, or repetitive formatting merely to create manual work.

In `recap`, never add a proactive quiz. In `guided`, limit proactive teaching to once per milestone. In `hands_on`, prefer one applied action with progressive hints.

## User-evidence boundary

Agent implements everything:

```text
Project evidence: observed `pyproject.toml#[project.dependencies]`
Agent demonstrated: declared and installed the dependency in an isolated environment
User exposure: encountered
User demonstrations: []
```

User selects the correct interpreter and explains why:

```text
Project evidence: observed `.venv` interpreter in the successful launch command
Agent demonstrated: showed how the launch command resolves the interpreter
User exposure: reinforced
User demonstration: explained — identified the project-local interpreter and explained that it prevents system-package conflicts
```

Agreement, gratitude, reading an explanation, or saying “I understand” alone is not a demonstrated capability.

## Debugging

User:

> Help me understand and fix this failing test.

Keep observations and hypotheses separate:

```text
Observed: `test_retries_timeout` failed with two calls instead of three.
Hypothesis: the retry counter may be incremented before the first attempt.
Next verification: inspect the counter update and run only `test_retries_timeout`.
```

After the fix, state exactly which test passed and what it asserts. Do not claim the entire suite or application is correct unless those checks ran.

## Privacy and non-Git operation

If an observed command contains a credential-like assignment, persist only a redacted locator:

```text
SERVICE_TOKEN=[REDACTED] python run_demo.py
```

Never include the original value in an error, receipt, snapshot, or evaluation artifact.

In a non-Git directory:

```json
{
  "root_label": "sample",
  "vcs": "none",
  "baseline": null
}
```

Use file, command, test, runtime, and decision anchors. Do not fabricate a commit or diff.

If the user asks to explain every possible concept, say that the build remains the syllabus: surface the next causally relevant concept and put background topics under deferred learning.

## Chinese behavior

User:

> 帮我搭好这个 Python 项目，边做边讲真正需要懂的东西。

Good behavior:

> 我会用 `guided` 模式继续完成环境搭建，只在关键决策或概念第一次真正出现时做简短说明。项目能运行仍是首要目标。

Receipt fragment:

```markdown
### 依赖隔离

- 概念说明：为当前项目使用独立的包环境，避免影响系统 Python 或其他项目。
- 为什么此时重要：项目需要安装特定版本的依赖。
- 项目证据：`pyproject.toml#[project.dependencies]` 与已验证的 `.venv` 启动命令。
- Agent 展示：创建环境并验证项目启动；这不代表用户能力。
- 你展示的内容：接触过；理解尚未验证。
- 下一步小练习：在新的示例目录中创建并选择一个独立环境。
```

Keep identifiers such as `dependency-isolation`, enum values, paths, symbols, and commands stable even when labels and explanations are Chinese.
