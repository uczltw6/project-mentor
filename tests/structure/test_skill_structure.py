from __future__ import annotations

import ast
import re

from conftest import SKILL

FRONTMATTER_PATTERN = re.compile(r"\A---\n(?P<body>.*?)\n---\n", re.DOTALL)
MARKDOWN_LINK_PATTERN = re.compile(r"\[[^]]+\]\(([^)]+)\)")


def _frontmatter() -> dict[str, str]:
    text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    match = FRONTMATTER_PATTERN.match(text)
    assert match is not None
    result: dict[str, str] = {}
    for line in match.group("body").splitlines():
        key, value = line.split(":", 1)
        result[key.strip()] = value.strip()
    return result


def test_frontmatter_has_exact_name_and_intent_bounded_description() -> None:
    metadata = _frontmatter()
    assert set(metadata) == {"name", "description"}
    assert metadata["name"] == "project-mentor"
    description = metadata["description"].lower()
    for positive in ("learn while building", "guided", "learning receipt", "completed task"):
        assert positive in description
    for boundary in ("do not use", "ordinary delegated coding", "isolated factual", "course"):
        assert boundary in description


def test_skill_is_concise_and_all_direct_references_exist() -> None:
    skill_text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    assert len(skill_text.splitlines()) < 500
    links = MARKDOWN_LINK_PATTERN.findall(skill_text)
    assert links == [
        "references/mentoring-policy.md",
        "references/ledger-schema.md",
        "references/examples.md",
    ]
    for link in links:
        assert (SKILL / link).is_file()


def test_skill_contains_no_placeholders_forbidden_docs_or_generated_files() -> None:
    forbidden_names = {"README.md", "INSTALLATION_GUIDE.md", "QUICK_REFERENCE.md", "CHANGELOG.md"}
    files = [path for path in SKILL.rglob("*") if path.is_file()]
    assert not forbidden_names & {path.name for path in files}
    assert not any("__pycache__" in path.parts or path.suffix in {".pyc", ".pyo"} for path in files)
    text_files = [path for path in files if path.suffix in {".md", ".py", ".yaml"}]
    combined = "\n".join(path.read_text(encoding="utf-8") for path in text_files)
    assert not re.search(r"\b(?:TODO|TBD)\b|\[TODO", combined)


def test_openai_yaml_matches_finished_skill() -> None:
    expected = (
        "interface:\n"
        '  display_name: "Project Mentor"\n'
        '  short_description: "Learn through evidence in real projects"\n'
        '  default_prompt: "Use $project-mentor to complete this real project while teaching '
        'the concepts that matter as we encounter them."\n'
    )
    assert (SKILL / "agents" / "openai.yaml").read_text(encoding="utf-8") == expected


def test_reference_tables_of_contents_cover_long_references() -> None:
    for path in (SKILL / "references").glob("*.md"):
        text = path.read_text(encoding="utf-8")
        if len(text.splitlines()) > 100:
            assert "## Contents" in text


def test_runtime_imports_only_standard_library_or_local_modules() -> None:
    standard = set(__import__("sys").stdlib_module_names)
    local = {"mentor_core"}
    for path in (SKILL / "scripts").rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                roots = {alias.name.split(".")[0] for alias in node.names}
            elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                roots = {node.module.split(".")[0]}
            else:
                continue
            assert roots <= standard | local


def test_required_helper_subcommands_are_documented() -> None:
    skill_text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    for command in ("init", "apply-event", "validate", "render", "summarize", "redact"):
        assert f"project_mentor.py {command}" in skill_text
