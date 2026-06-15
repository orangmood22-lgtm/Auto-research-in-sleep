from __future__ import annotations

import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_developer_doc_update_check_passes():
    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "tools" / "update_developer_docs.py"), "--check-only"],
        cwd=str(REPO_ROOT),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_developer_doc_dag_mermaid_is_current():
    before = (REPO_ROOT / "to-developer" / "DOC_DAG.mmd").read_text(encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "tools" / "update_developer_docs.py")],
        cwd=str(REPO_ROOT),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    after = (REPO_ROOT / "to-developer" / "DOC_DAG.mmd").read_text(encoding="utf-8")
    assert after == before
