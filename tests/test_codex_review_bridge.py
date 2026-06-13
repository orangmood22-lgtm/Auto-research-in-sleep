from __future__ import annotations

import importlib.util
from pathlib import Path


def load_bridge_module():
    repo = Path(__file__).resolve().parents[1]
    path = repo / "mcp-servers" / "codex-review" / "bridge.py"
    spec = importlib.util.spec_from_file_location("codex_review_bridge", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module, path


def test_bridge_server_script_defaults_to_sibling_server() -> None:
    module, bridge_path = load_bridge_module()
    assert Path(module.SERVER_SCRIPT) == bridge_path.with_name("server.py")
