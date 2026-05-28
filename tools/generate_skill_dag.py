#!/usr/bin/env python3
"""Generate SKILL_DAG.yaml from SKILL.md frontmatter fields.

Reads all skills/<name>/SKILL.md files, extracts:
  - caller (leader/executor/any)
  - invokes (list of skill names this skill calls)
  - produces (list of artifact filenames)
  - consumes (list of artifact filenames)

Outputs docs/SKILL_DAG.yaml and validates the graph is acyclic.

Usage:
    python3 tools/generate_skill_dag.py [--check-only] [--mermaid]
"""

import argparse
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

import yaml


SKILLS_DIR = Path(__file__).resolve().parent.parent / "skills"
OUTPUT_PATH = Path(__file__).resolve().parent.parent / "docs" / "SKILL_DAG.yaml"
MERMAID_PATH = Path(__file__).resolve().parent.parent / "docs" / "SKILL_DAG.mmd"
EXCLUDE = {"shared-references", "skills-codex", "skills-codex.bak"}


def parse_frontmatter(skill_path: Path) -> dict:
    """Extract YAML frontmatter from SKILL.md."""
    text = skill_path.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    if not match:
        return {}
    try:
        return yaml.safe_load(match.group(1)) or {}
    except yaml.YAMLError:
        return {}


def scan_invocations(skill_path: Path) -> list:
    """Scan SKILL.md body for /skill-name invocations (heuristic)."""
    text = skill_path.read_text(encoding="utf-8")
    # Remove frontmatter
    text = re.sub(r"^---\n.*?\n---\n?", "", text, count=1, flags=re.DOTALL)
    # Find /skill-name patterns (in code blocks or prose)
    matches = re.findall(r"(?<![`\w])/([a-z][a-z0-9-]+)", text)
    # Filter to known skill names
    return list(set(matches))


def build_graph(skills_dir: Path) -> dict:
    """Build the full skill graph."""
    nodes = {}
    all_skill_names = set()

    for d in sorted(skills_dir.iterdir()):
        if not d.is_dir() or d.name in EXCLUDE:
            continue
        skill_md = d / "SKILL.md"
        if not skill_md.exists():
            continue
        all_skill_names.add(d.name)

    for d in sorted(skills_dir.iterdir()):
        if not d.is_dir() or d.name in EXCLUDE:
            continue
        skill_md = d / "SKILL.md"
        if not skill_md.exists():
            continue

        fm = parse_frontmatter(skill_md)
        invoked = scan_invocations(skill_md)
        # Filter to only known skills
        invoked = [s for s in invoked if s in all_skill_names and s != d.name]

        node = {
            "name": d.name,
            "caller": fm.get("caller", "unknown"),
        }
        if invoked:
            node["invokes"] = sorted(set(invoked))
        if fm.get("produces"):
            node["produces"] = fm["produces"] if isinstance(fm["produces"], list) else [fm["produces"]]
        if fm.get("consumes"):
            node["consumes"] = fm["consumes"] if isinstance(fm["consumes"], list) else [fm["consumes"]]

        nodes[d.name] = node

    return nodes


def detect_cycles(nodes: dict) -> list:
    """Detect cycles using DFS. Returns list of cycles found."""
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {name: WHITE for name in nodes}
    cycles = []
    path = []

    def dfs(u):
        color[u] = GRAY
        path.append(u)
        for v in nodes[u].get("invokes", []):
            if v not in color:
                continue
            if color[v] == GRAY:
                cycle_start = path.index(v)
                cycles.append(path[cycle_start:] + [v])
            elif color[v] == WHITE:
                dfs(v)
        path.pop()
        color[u] = BLACK

    for name in nodes:
        if color[name] == WHITE:
            dfs(name)

    return cycles


def generate_mermaid(nodes: dict) -> str:
    """Generate Mermaid flowchart from DAG."""
    lines = ["graph TD"]
    # Style by caller
    leader_nodes = []
    executor_nodes = []
    any_nodes = []

    for name, node in sorted(nodes.items()):
        caller = node.get("caller", "unknown")
        if caller == "leader":
            leader_nodes.append(name)
        elif caller == "executor":
            executor_nodes.append(name)
        else:
            any_nodes.append(name)

        for target in node.get("invokes", []):
            lines.append(f"    {name} --> {target}")

    lines.append("")
    if leader_nodes:
        lines.append(f"    classDef leader fill:#ff9999,stroke:#cc0000")
        lines.append(f"    class {','.join(leader_nodes[:20])} leader")
    if executor_nodes:
        lines.append(f"    classDef executor fill:#99ccff,stroke:#0066cc")
        lines.append(f"    class {','.join(executor_nodes[:20])} executor")
    if any_nodes:
        lines.append(f"    classDef any fill:#99ff99,stroke:#009900")
        lines.append(f"    class {','.join(any_nodes[:20])} any")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Generate SKILL_DAG.yaml")
    parser.add_argument("--check-only", action="store_true", help="Only validate, don't write")
    parser.add_argument("--mermaid", action="store_true", help="Also generate Mermaid diagram")
    args = parser.parse_args()

    nodes = build_graph(SKILLS_DIR)
    print(f"Scanned {len(nodes)} skills")

    # Check for cycles
    cycles = detect_cycles(nodes)
    if cycles:
        print(f"WARNING: {len(cycles)} cycle(s) detected:")
        for c in cycles:
            print(f"  {' -> '.join(c)}")
    else:
        print("No cycles detected (DAG valid)")

    # Stats
    callers = defaultdict(int)
    for node in nodes.values():
        callers[node.get("caller", "unknown")] += 1
    print(f"Caller distribution: {dict(callers)}")

    edges = sum(len(n.get("invokes", [])) for n in nodes.values())
    print(f"Total invocation edges: {edges}")

    if args.check_only:
        sys.exit(1 if cycles else 0)

    # Write YAML
    dag = {
        "version": 1,
        "generated_by": "tools/generate_skill_dag.py",
        "stats": {
            "total_skills": len(nodes),
            "total_edges": edges,
            "caller_distribution": dict(callers),
            "has_cycles": bool(cycles),
        },
        "nodes": [nodes[k] for k in sorted(nodes.keys())],
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        yaml.dump(dag, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
    print(f"Written: {OUTPUT_PATH}")

    if args.mermaid:
        mermaid = generate_mermaid(nodes)
        with open(MERMAID_PATH, "w", encoding="utf-8") as f:
            f.write(mermaid)
        print(f"Written: {MERMAID_PATH}")


if __name__ == "__main__":
    main()
