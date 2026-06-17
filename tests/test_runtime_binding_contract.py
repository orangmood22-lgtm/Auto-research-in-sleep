from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (REPO_ROOT / rel).read_text(encoding="utf-8")


def test_user_runtime_binding_defaults_are_documented() -> None:
    expected = {
        "Leader": "gpt-5.5",
        "Planner": "gpt-5.4",
        "Reviewer": "gpt-5.4",
        "Writer": "gpt-5.4",
        "Coder": "gpt-5.4-mini",
        "Deployer": "gpt-5.4-mini",
    }
    docs = [
        read("docs/OPERATIONS_GUIDE.md"),
        read("docs/TRIPARTITE_ARCHITECTURE_GUIDE.md"),
        read("templates/AGENTS_MD_TEMPLATE.md"),
        read("skills/leader/SKILL.md"),
        read("skills/skills-codex/leader/SKILL.md"),
        read("skills/shared-references/agent-guide.md"),
        read("skills/shared-references/role-contracts.md"),
        read("skills/skills-codex/shared-references/role-contracts.md"),
    ]

    for content in docs:
        for role, model in expected.items():
            assert role in content
            assert model in content


def test_runtime_binding_does_not_use_legacy_sonnet_defaults() -> None:
    checked = [
        read("skills/leader/SKILL.md"),
        read("skills/skills-codex/leader/SKILL.md"),
        read("skills/shared-references/agent-guide.md"),
        read("skills/shared-references/executor-skill-routing.md"),
    ]

    for content in checked:
        assert 'model: "sonnet"' not in content
        assert "Opus" not in content
