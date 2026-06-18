from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (REPO_ROOT / rel).read_text(encoding="utf-8")


def test_experiment_transparency_ledger_is_indexed_and_declares_records() -> None:
    ledger = read("docs/EXPERIMENT_TRANSPARENCY_LEDGER.md")
    docs_index = read("docs/README.md")

    assert "EXPERIMENT_TRANSPARENCY_LEDGER.md" in docs_index
    assert "Experiment Integrity is a workflow module, not a single skill." in ledger
    assert "does not require LangGraph" in ledger

    for record_type in [
        "`dataset`",
        "`split`",
        "`metric`",
        "`run`",
        "`deviation`",
        "`artifact`",
        "`claim`",
        "`checkpoint`",
    ]:
        assert record_type in ledger


def test_experiment_integrity_shared_refs_point_to_ledger_contract() -> None:
    for rel in [
        "skills/shared-references/experiment-integrity.md",
        "skills/skills-codex/shared-references/experiment-integrity.md",
    ]:
        content = read(rel)
        assert "Experiment Integrity is a workflow module, not a single skill." in content
        assert "docs/EXPERIMENT_TRANSPARENCY_LEDGER.md" in content
        assert "refine-logs/EXPERIMENT_TRANSPARENCY_LEDGER.md" in content
        assert "refine-logs/checkpoints/" in content
