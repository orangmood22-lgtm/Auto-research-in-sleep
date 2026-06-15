from __future__ import annotations

import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def dag_nodes() -> set[str]:
    text = (REPO_ROOT / "docs" / "DOC_DAG.yaml").read_text(encoding="utf-8")
    node_block = text.split("nodes:", 1)[1].split("\nedges:", 1)[0]
    nodes = set()
    for line in node_block.splitlines():
        if line.startswith("  ") and not line.startswith("    ") and line.strip().endswith(":"):
            nodes.add(line.strip()[:-1])
    return nodes


def test_doc_dag_generator_check_passes():
    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "tools" / "generate_doc_dag.py"), "--check-only"],
        cwd=str(REPO_ROOT),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_all_docs_are_represented_in_doc_dag():
    nodes = dag_nodes()
    missing = []
    for path in sorted((REPO_ROOT / "docs").glob("**/*")):
        if path.is_file() and path.name != "aris_logo.svg":
            rel = str(path.relative_to(REPO_ROOT))
            if rel not in nodes:
                missing.append(rel)
    assert missing == []
