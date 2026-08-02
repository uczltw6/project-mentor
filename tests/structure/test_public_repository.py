from __future__ import annotations

import re
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parents[2]


def test_public_repository_has_required_documentation_and_community_files() -> None:
    required = {
        "README.md",
        "LICENSE",
        "CHANGELOG.md",
        "CONTRIBUTING.md",
        "SECURITY.md",
        "CODE_OF_CONDUCT.md",
        "docs/architecture.md",
        "docs/product-contract.md",
        "docs/cli.md",
        "docs/evaluation.md",
        "docs/release-readiness-v0.1.0.md",
        "docs/release-notes-v0.2.0.md",
        "docs/release-notes-v0.3.0.md",
        "docs/security-review-v0.1.0.md",
        "docs/threat-model.md",
        "evals/README.md",
        "evals/cases.jsonl",
        "evals/rubric.json",
        "evals/graders.py",
        "evals/run_local.py",
        "evals/results/v0.3.0.json",
        "examples/project-mentor-ledger.json",
        "examples/learning-receipt.md",
        ".github/ISSUE_TEMPLATE/bug_report.yml",
        ".github/ISSUE_TEMPLATE/feature_request.yml",
        ".github/ISSUE_TEMPLATE/config.yml",
        ".github/pull_request_template.md",
    }
    assert all((REPOSITORY / relative).is_file() for relative in required)


def test_readme_covers_release_user_journey() -> None:
    readme = (REPOSITORY / "README.md").read_text(encoding="utf-8")
    headings = {
        "## Before and after",
        "## What it does",
        "## Modes",
        "## Evidence, not inflated claims",
        "## Install",
        "## Invoke it",
        "## Two-minute quickstart",
        "## Example receipt and ledger",
        "## Privacy and persistence",
        "## Command-line interface",
        "## Develop and test",
        "## Evals",
        "## Limitations",
        "## Project links",
    }
    assert headings <= set(readme.splitlines())
    assert "$HOME/.agents/skills" in readme
    assert ".agents/skills/project-mentor" in readme
    assert "$project-mentor" in readme


def test_relative_markdown_links_resolve() -> None:
    markdown_files = (
        list(REPOSITORY.glob("*.md"))
        + list((REPOSITORY / "docs").glob("*.md"))
        + list((REPOSITORY / "evals").glob("*.md"))
    )
    pattern = re.compile(r"\[[^]]*]\(([^)]+)\)")
    missing: list[str] = []
    for markdown in markdown_files:
        for target in pattern.findall(markdown.read_text(encoding="utf-8")):
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            relative = target.split("#", 1)[0]
            if relative and not (markdown.parent / relative).resolve().exists():
                missing.append(f"{markdown.relative_to(REPOSITORY)} -> {target}")
    assert not missing, "missing relative Markdown links: " + ", ".join(missing)
