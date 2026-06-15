#!/usr/bin/env python3
"""校验并生成 ARIS 文档 DAG。

输入：docs/DOC_DAG.yaml
输出：docs/DOC_DAG.mmd

边方向为“源文档/源资产 -> 受影响的派生文档、索引或摘要”。
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = REPO_ROOT / "docs" / "DOC_DAG.yaml"
DEFAULT_MERMAID = REPO_ROOT / "docs" / "DOC_DAG.mmd"


def load_yaml(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore

        return yaml.safe_load(text) or {}
    except ModuleNotFoundError:
        return load_doc_dag_subset(text)


def parse_scalar(value: str) -> Any:
    value = value.strip()
    if not value:
        return ""
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        return value[1:-1]
    if value.isdigit():
        return int(value)
    return value


def load_doc_dag_subset(text: str) -> dict[str, Any]:
    """Parse the small YAML subset used by docs/DOC_DAG.yaml.

    This keeps the generator dependency-free in minimal Python environments.
    It intentionally supports only top-level scalars, `nodes` mappings with
    scalar metadata, and `edges` lists of scalar mappings.
    """
    data: dict[str, Any] = {}
    section: str | None = None
    current_node: str | None = None
    current_edge: dict[str, Any] | None = None

    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        if not line.startswith(" "):
            key, _, value = stripped.partition(":")
            if value.strip():
                data[key] = parse_scalar(value)
                section = None
            else:
                section = key
                data.setdefault(key, {} if key == "nodes" else [])
            current_node = None
            current_edge = None
            continue

        if section == "nodes":
            if line.startswith("  ") and not line.startswith("    "):
                key = stripped[:-1] if stripped.endswith(":") else stripped.partition(":")[0]
                current_node = key
                data["nodes"].setdefault(current_node, {})
                continue
            if current_node and line.startswith("    "):
                key, _, value = stripped.partition(":")
                data["nodes"][current_node][key] = parse_scalar(value)
                continue

        if section == "edges":
            if line.startswith("  - "):
                current_edge = {}
                data["edges"].append(current_edge)
                body = stripped[2:].strip()
                if body:
                    key, _, value = body.partition(":")
                    current_edge[key] = parse_scalar(value)
                continue
            if current_edge is not None and line.startswith("    "):
                key, _, value = stripped.partition(":")
                current_edge[key] = parse_scalar(value)
                continue

        raise ValueError(f"unsupported DOC_DAG yaml line: {raw_line}")

    return data


def node_id(name: str) -> str:
    value = re.sub(r"[^A-Za-z0-9_]", "_", name)
    if not re.match(r"^[A-Za-z_]", value):
        value = "n_" + value
    return value


def mermaid_label(name: str, meta: dict[str, Any]) -> str:
    title = str(meta.get("title") or name)
    layer = str(meta.get("layer") or "")
    if layer:
        return f"{name}<br/><small>{title} · {layer}</small>"
    return f"{name}<br/><small>{title}</small>"


def path_exists(repo: Path, name: str) -> bool:
    if "*" in name:
        return bool(list(repo.glob(name)))
    return (repo / name).exists()


def validate(data: dict[str, Any], repo: Path) -> list[str]:
    errors: list[str] = []
    nodes = data.get("nodes") or {}
    edges = data.get("edges") or []
    if not isinstance(nodes, dict):
        errors.append("nodes must be a mapping")
        return errors
    if not isinstance(edges, list):
        errors.append("edges must be a list")
        return errors

    for name, meta in nodes.items():
        if not isinstance(meta, dict):
            errors.append(f"node {name}: metadata must be a mapping")
            continue
        if meta.get("kind") == "generated":
            continue
        if not path_exists(repo, name):
            errors.append(f"node {name}: path/glob does not exist")

    for idx, edge in enumerate(edges):
        if not isinstance(edge, dict):
            errors.append(f"edge[{idx}] must be a mapping")
            continue
        src = edge.get("from")
        dst = edge.get("to")
        if src not in nodes:
            errors.append(f"edge[{idx}]: unknown from node {src!r}")
        if dst not in nodes:
            errors.append(f"edge[{idx}]: unknown to node {dst!r}")
        if not edge.get("type"):
            errors.append(f"edge[{idx}]: missing type")

    cycles = detect_cycles(nodes, edges)
    for cycle in cycles:
        errors.append("cycle detected: " + " -> ".join(cycle))
    return errors


def detect_cycles(nodes: dict[str, Any], edges: list[dict[str, Any]]) -> list[list[str]]:
    graph: dict[str, list[str]] = defaultdict(list)
    for edge in edges:
        src = edge.get("from")
        dst = edge.get("to")
        if src in nodes and dst in nodes:
            graph[src].append(dst)

    WHITE, GRAY, BLACK = 0, 1, 2
    color = {name: WHITE for name in nodes}
    stack: list[str] = []
    cycles: list[list[str]] = []

    def visit(name: str) -> None:
        color[name] = GRAY
        stack.append(name)
        for nxt in graph.get(name, []):
            if color[nxt] == WHITE:
                visit(nxt)
            elif color[nxt] == GRAY:
                start = stack.index(nxt)
                cycles.append(stack[start:] + [nxt])
        stack.pop()
        color[name] = BLACK

    for name in nodes:
        if color[name] == WHITE:
            visit(name)
    return cycles


def generate_mermaid(data: dict[str, Any]) -> str:
    nodes: dict[str, dict[str, Any]] = data["nodes"]
    edges: list[dict[str, Any]] = data.get("edges") or []

    lines = [
        "graph LR",
        "    %% Generated from docs/DOC_DAG.yaml by tools/generate_doc_dag.py",
    ]

    for name, meta in sorted(nodes.items()):
        label = mermaid_label(name, meta).replace('"', "'")
        lines.append(f'    {node_id(name)}["{label}"]')

    lines.append("")
    for edge in edges:
        src = node_id(str(edge["from"]))
        dst = node_id(str(edge["to"]))
        typ = str(edge.get("type") or "relates_to").replace('"', "'")
        lines.append(f'    {src} -- "{typ}" --> {dst}')

    layers = defaultdict(list)
    for name, meta in nodes.items():
        layers[str(meta.get("layer") or "other")].append(node_id(name))

    class_defs = {
        "entry": "fill:#e0f2fe,stroke:#0369a1",
        "governance": "fill:#ede9fe,stroke:#6d28d9",
        "release": "fill:#fef3c7,stroke:#b45309",
        "index": "fill:#dcfce7,stroke:#15803d",
        "generated": "fill:#f3f4f6,stroke:#4b5563",
        "source": "fill:#fee2e2,stroke:#b91c1c",
        "integration": "fill:#fae8ff,stroke:#a21caf",
        "client": "fill:#dbeafe,stroke:#1d4ed8",
        "provider": "fill:#ccfbf1,stroke:#0f766e",
        "architecture": "fill:#fce7f3,stroke:#be185d",
        "project": "fill:#ecfccb,stroke:#4d7c0f",
        "experiment": "fill:#ffedd5,stroke:#c2410c",
        "deploy": "fill:#e5e7eb,stroke:#374151",
        "adr": "fill:#f5f3ff,stroke:#7c3aed",
        "user": "fill:#eef2ff,stroke:#4338ca",
    }
    lines.append("")
    for layer, style in class_defs.items():
        lines.append(f"    classDef {layer} {style}")
    for layer, ids in sorted(layers.items()):
        if layer in class_defs and ids:
            lines.append(f"    class {','.join(sorted(ids))} {layer}")

    return "\n".join(lines) + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", default=str(DEFAULT_SOURCE))
    parser.add_argument("--mermaid", default=str(DEFAULT_MERMAID))
    parser.add_argument("--check-only", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    source = Path(args.source)
    mermaid = Path(args.mermaid)
    data = load_yaml(source)
    errors = validate(data, REPO_ROOT)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    if not args.check_only:
        mermaid.write_text(generate_mermaid(data), encoding="utf-8")
        print(f"wrote {mermaid}")
    print(f"doc dag ok: {len(data.get('nodes', {}))} nodes, {len(data.get('edges', []))} edges")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
