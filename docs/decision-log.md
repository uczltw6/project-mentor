# Decision log

This log records release-relevant decisions without retaining private paths, credentials, or hidden reasoning.

## 2026-08-01 — Phase 0 baseline

- **Safe worktree:** Build from a uniquely named directory under the system temporary directory. The mounted OneDrive workspace passed creation, rename, overwrite, Git initialization, index update, lock creation, and commit checks, but recursive cleanup of Git objects was unreliable. Keep the mounted directory as an export and bundle-checkpoint location only.
- **Personal skill scope:** Author and install the personal skill under `$HOME/.agents/skills/project-mentor`, the current user-scope location documented by Codex. Do not use the older `$HOME/.codex/skills/remote-skills` fallback because current official guidance specifies `$HOME/.agents/skills`.
- **Publication boundary:** The authenticated GitHub account is `uczltw6`; `uczltw6/project-mentor` does not exist. Publication under that exact owner is available once all local gates pass.
- **Git identity:** Preserve the authenticated account's existing Git name and GitHub-provided no-reply email. Do not add co-authors.
- **Runtime baseline:** Python 3.11.5, Git 2.45.1, GitHub CLI 2.91.0, and Node.js 24.15.0 are available. The implementation target remains Python 3.10+ with standard-library-only runtime dependencies.
- **Distribution boundary:** Release a standalone skill and public source repository. Do not publish a plugin, package-registry artifact, or marketplace submission in V1.

## 2026-08-01 — Phase 1 product contract

- **Success ordering:** Judge delivery correctness first, mentoring usefulness second, and persistence convenience third. Teaching must never weaken the real task result.
- **Trust boundary:** Store project evidence and user demonstrations in separate fields. Agent work may establish project usage but can establish at most user exposure, never user capability.
- **Activation boundary:** Require explicit or clearly implied build-while-learning or post-hoc learning-audit intent. Ordinary delegated implementation and isolated explanations remain outside the skill.
- **Persistence boundary:** Keep state in conversation or temporary storage by default. Create `.project-mentor/` or any alternative learning artifact only after explicit user opt-in.
- **Mode contract:** Expose exactly `recap`, `guided`, and `hands_on`; make `guided` the activation default and honor mode changes immediately without restarting the delivery task.

## 2026-08-01 — Phase 2 initialization and scaffold

- **Official initialization:** Create `$HOME/.agents/skills/project-mentor` with the official `init_skill.py`, requesting only `scripts` and `references`, and generate the initial `agents/openai.yaml` through that command.
- **UI metadata:** Use “Project Mentor,” “Learn through evidence in real projects,” and a one-sentence `$project-mentor` default prompt. Keep implicit invocation at its documented default and add no icons, colors, MCP tools, or external dependencies.
- **Canonical editing flow:** Treat the personal skill as the authoring source through validation. Synchronize release files into `.agents/skills/project-mentor/` with `tools/sync_skill.py` and require byte-for-byte parity before release.
- **Template state:** The official initializer's placeholder `SKILL.md` is intentionally present at the Phase 2 boundary and fails validation because its description is not final. Replace every placeholder during Phase 4; do not interpret this expected intermediate result as release validation.
- **Repository boundary:** Keep development tools, tests, CI, contribution files, and public documentation outside the nested installable skill. Runtime behavior inside the skill remains standard-library-only.
