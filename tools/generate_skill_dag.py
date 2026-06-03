#!/usr/bin/env python3
"""Generate SKILL_DAG.yaml from SKILL.md frontmatter fields.

Reads all skills/<name>/SKILL.md files, extracts:
  - caller (leader/executor/any)
  - invokes (list of skill names this skill calls)
  - produces (list of artifact filenames)
  - consumes (list of artifact filenames)

Outputs docs/SKILL_DAG.yaml and validates the graph is acyclic.

Usage:
    python3 tools/generate_skill_dag.py [--check-only] [--mermaid] [--html]
"""

import argparse
import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

import yaml


SKILLS_DIR = Path(__file__).resolve().parent.parent / "skills"
OUTPUT_PATH = Path(__file__).resolve().parent.parent / "docs" / "SKILL_DAG.yaml"
MERMAID_PATH = Path(__file__).resolve().parent.parent / "docs" / "SKILL_DAG.mmd"
HTML_PATH = Path(__file__).resolve().parent.parent / "docs" / "skill-dag.html"
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


def compute_invoked_by(nodes: dict) -> dict:
    """Compute reverse dependency: for each skill, which skills invoke it."""
    invoked_by = defaultdict(list)
    for name, node in nodes.items():
        for target in node.get("invokes", []):
            if target in nodes:
                invoked_by[target].append(name)
    return {k: sorted(v) for k, v in invoked_by.items()}


def compute_impact(nodes: dict, skill_name: str) -> dict:
    """Compute transitive impact of modifying a skill.

    Returns dict with:
      - direct_upstream: skills this one directly invokes
      - direct_downstream: skills that directly invoke this one
      - transitive_upstream: all skills this one depends on
      - transitive_downstream: all skills affected by changes to this one
    """
    if skill_name not in nodes:
        return {"error": f"Skill '{skill_name}' not found"}

    # BFS downstream (who depends on this skill, transitively)
    visited_down = set()
    queue = [skill_name]
    while queue:
        current = queue.pop(0)
        # Find skills that invoke current
        for name, node in nodes.items():
            if current in node.get("invokes", []) and name not in visited_down:
                visited_down.add(name)
                queue.append(name)

    # BFS upstream (what does this skill depend on, transitively)
    visited_up = set()
    queue = [skill_name]
    while queue:
        current = queue.pop(0)
        for target in nodes.get(current, {}).get("invokes", []):
            if target not in visited_up:
                visited_up.add(target)
                queue.append(target)

    invoked_by = compute_invoked_by(nodes)

    return {
        "skill": skill_name,
        "direct_upstream": nodes[skill_name].get("invokes", []),
        "direct_downstream": invoked_by.get(skill_name, []),
        "transitive_upstream": sorted(visited_up),
        "transitive_downstream": sorted(visited_down),
        "transitive_upstream_count": len(visited_up),
        "transitive_downstream_count": len(visited_down),
    }


def generate_html(nodes: dict, dag_data: dict) -> str:
    """Generate self-contained HTML visualization page."""
    invoked_by = compute_invoked_by(nodes)
    # Build nodes with invoked_by for the HTML
    nodes_json = []
    for name in sorted(nodes.keys()):
        node = dict(nodes[name])
        node["invoked_by"] = invoked_by.get(name, [])
        nodes_json.append(node)
    nodes_json_str = json.dumps(nodes_json, ensure_ascii=False, indent=2)

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ARIS Skill DAG</title>
<script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #1a1a2e; color: #e0e0e0; }}
#header {{ padding: 16px 24px; background: #16213e; border-bottom: 1px solid #0f3460; display: flex; align-items: center; gap: 16px; }}
#header h1 {{ font-size: 20px; color: #e94560; }}
#stats {{ display: flex; gap: 24px; font-size: 13px; color: #a0a0a0; }}
#stats span {{ color: #e94560; font-weight: bold; }}
#toolbar {{ padding: 12px 24px; background: #16213e; border-bottom: 1px solid #0f3460; display: flex; gap: 12px; align-items: center; }}
#search {{ padding: 8px 12px; border-radius: 6px; border: 1px solid #0f3460; background: #1a1a2e; color: #e0e0e0; width: 300px; font-size: 14px; }}
#search:focus {{ outline: none; border-color: #e94560; }}
.filter-btn {{ padding: 6px 14px; border-radius: 6px; border: 1px solid #0f3460; background: transparent; color: #a0a0a0; cursor: pointer; font-size: 13px; }}
.filter-btn.active {{ background: #e94560; color: white; border-color: #e94560; }}
.filter-btn:hover {{ border-color: #e94560; }}
#container {{ display: flex; height: calc(100vh - 110px); }}
#graph {{ flex: 3; overflow: auto; padding: 24px; }}
#sidebar {{ width: 360px; background: #16213e; border-left: 1px solid #0f3460; overflow-y: auto; padding: 0; }}
#detail {{ padding: 20px; }}
#detail h2 {{ color: #e94560; font-size: 18px; margin-bottom: 12px; word-break: break-all; }}
#detail .caller-badge {{ display: inline-block; padding: 3px 10px; border-radius: 12px; font-size: 12px; font-weight: 600; margin-bottom: 12px; }}
.badge-leader {{ background: #ff9999; color: #660000; }}
.badge-executor {{ background: #99ccff; color: #003366; }}
.badge-any {{ background: #99ff99; color: #006600; }}
.badge-unknown {{ background: #cccccc; color: #333333; }}
.dep-section {{ margin-bottom: 16px; }}
.dep-section h3 {{ font-size: 14px; color: #a0a0a0; margin-bottom: 8px; border-bottom: 1px solid #0f3460; padding-bottom: 4px; }}
.dep-list {{ list-style: none; }}
.dep-list li {{ padding: 4px 8px; margin: 2px 0; border-radius: 4px; font-size: 13px; cursor: pointer; }}
.dep-list li:hover {{ background: #0f3460; }}
.dep-list .cnt {{ color: #e94560; font-weight: bold; }}
.impact-box {{ background: #1a1a2e; border: 1px solid #0f3460; border-radius: 8px; padding: 12px; margin: 12px 0; }}
.impact-box h4 {{ font-size: 13px; color: #e94560; margin-bottom: 8px; }}
.impact-stat {{ display: flex; justify-content: space-between; padding: 4px 0; font-size: 13px; }}
.impact-stat .num {{ color: #e94560; font-weight: bold; }}
#placeholder {{ text-align: center; padding: 60px 20px; color: #555; }}
#placeholder p {{ margin: 8px 0; font-size: 14px; }}
.mermaid {{ display: flex; justify-content: center; }}
#export-bar {{ padding: 8px 24px; background: #16213e; border-top: 1px solid #0f3460; display: flex; gap: 8px; }}
.export-btn {{ padding: 4px 12px; border-radius: 4px; border: 1px solid #0f3460; background: transparent; color: #a0a0a0; cursor: pointer; font-size: 12px; }}
.export-btn:hover {{ border-color: #e94560; color: #e94560; }}
</style>
</head>
<body>
<div id="header">
  <h1>ARIS Skill DAG</h1>
  <div id="stats">
    Skills: <span id="stat-total">{len(nodes)}</span> &nbsp;|&nbsp;
    Edges: <span id="stat-edges">{dag_data["stats"]["total_edges"]}</span> &nbsp;|&nbsp;
    Leader: <span id="stat-leader">{dag_data["stats"]["caller_distribution"].get("leader", 0)}</span> &nbsp;|&nbsp;
    Executor: <span id="stat-executor">{dag_data["stats"]["caller_distribution"].get("executor", 0)}</span> &nbsp;|&nbsp;
    Any: <span id="stat-any">{dag_data["stats"]["caller_distribution"].get("any", 0)}</span>
  </div>
</div>
<div id="toolbar">
  <input type="text" id="search" placeholder="Search skills..." />
  <button class="filter-btn active" data-filter="all">All</button>
  <button class="filter-btn" data-filter="leader">Leader</button>
  <button class="filter-btn" data-filter="executor">Executor</button>
  <button class="filter-btn" data-filter="any">Any</button>
  <button class="filter-btn" data-filter="impact">Impact Mode</button>
</div>
<div id="container">
  <div id="graph">
    <div class="mermaid" id="mermaid-graph"></div>
  </div>
  <div id="sidebar">
    <div id="placeholder">
      <p>Click a skill node to see details</p>
      <p style="font-size:12px">Impact Mode: click a node to see what it affects</p>
    </div>
    <div id="detail" style="display:none"></div>
  </div>
</div>
<div id="export-bar">
  <button class="export-btn" onclick="copyMermaid()">Copy Mermaid</button>
  <button class="export-btn" onclick="downloadSVG()">Download SVG</button>
</div>

<script>
const DAG_NODES = {nodes_json_str};

const nodeMap = {{}};
DAG_NODES.forEach(n => nodeMap[n.name] = n);

let currentFilter = 'all';
let impactMode = false;
let selectedSkill = null;

mermaid.initialize({{ startOnLoad: false, securityLevel: 'loose', theme: 'dark',
  flowchart: {{ htmlLabels: true, curve: 'basis' }} }});

function buildMermaidDef(filter, searchTerm, highlightSkill) {{
  const lines = ['graph TD'];
  const filtered = DAG_NODES.filter(n => {{
    if (filter && filter !== 'all' && filter !== 'impact' && n.caller !== filter) return false;
    if (searchTerm && !n.name.includes(searchTerm.toLowerCase())) return false;
    return true;
  }});
  const names = new Set(filtered.map(n => n.name));
  // Always include highlight skill and its deps
  if (highlightSkill) {{
    names.add(highlightSkill);
    (nodeMap[highlightSkill].invokes || []).forEach(n => names.add(n));
    (nodeMap[highlightSkill].invoked_by || []).forEach(n => names.add(n));
  }}

  const leaderN = [], executorN = [], anyN = [];
  filtered.forEach(n => {{
    const inv = (n.invokes || []).filter(t => names.has(t));
    inv.forEach(t => lines.push('    ' + n.name.replace(/-/g,'_') + ' --> ' + t.replace(/-/g,'_')));
    if (n.caller === 'leader') leaderN.push(n.name.replace(/-/g,'_'));
    else if (n.caller === 'executor') executorN.push(n.name.replace(/-/g,'_'));
    else anyN.push(n.name.replace(/-/g,'_'));
  }});

  lines.push('');
  if (leaderN.length) lines.push('    classDef leader fill:#ff9999,stroke:#cc0000,color:#660000');
  if (executorN.length) lines.push('    classDef executor fill:#99ccff,stroke:#0066cc,color:#003366');
  if (anyN.length) lines.push('    classDef any fill:#99ff99,stroke:#009900,color:#006600');
  // Batch classes (Mermaid has limits per class line)
  const batch = (arr, cls) => {{
    for (let i = 0; i < arr.length; i += 20)
      lines.push('    class ' + arr.slice(i, i+20).join(',') + ' ' + cls);
  }};
  if (leaderN.length) batch(leaderN, 'leader');
  if (executorN.length) batch(executorN, 'executor');
  if (anyN.length) batch(anyN, 'any');

  if (highlightSkill) {{
    lines.push('    classDef highlighted fill:#e94560,stroke:#fff,color:#fff');
    lines.push('    class ' + highlightSkill.replace(/-/g,'_') + ' highlighted');
  }}
  return lines.join('\\n');
}}

async function renderGraph(filter, search, highlight) {{
  const def = buildMermaidDef(filter, search, highlight);
  try {{
    const {{ svg }} = await mermaid.render('mermaid-svg', def);
    document.getElementById('mermaid-graph').innerHTML = svg;
    // Add click handlers to nodes
    document.querySelectorAll('.node').forEach(el => {{
      el.style.cursor = 'pointer';
      el.addEventListener('click', () => {{
        const id = el.id?.replace(/^flowchart-/, '').replace(/-\\d+$/, '') || '';
        const name = id.replace(/_/g, '-');
        if (nodeMap[name]) onNodeClick(name);
      }});
    }});
  }} catch(e) {{
    console.error('Mermaid render error:', e);
  }}
}}

function onNodeClick(name) {{
  selectedSkill = name;
  const n = nodeMap[name];
  const detail = document.getElementById('detail');
  const placeholder = document.getElementById('placeholder');
  placeholder.style.display = 'none';
  detail.style.display = 'block';

  const callerClass = 'badge-' + (n.caller || 'unknown');
  const upstream = n.invokes || [];
  const downstream = n.invoked_by || [];
  const produces = n.produces || [];
  const consumes = n.consumes || [];

  // Compute transitive impact
  let transDown = new Set(), transUp = new Set();
  function bfsDown(start) {{
    let q = [start], visited = new Set();
    while(q.length) {{
      let cur = q.shift();
      for (let dep of (nodeMap[cur]?.invoked_by || [])) {{
        if (!visited.has(dep)) {{ visited.add(dep); transDown.add(dep); q.push(dep); }}
      }}
    }}
  }}
  function bfsUp(start) {{
    let q = [start], visited = new Set();
    while(q.length) {{
      let cur = q.shift();
      for (let dep of (nodeMap[cur]?.invokes || [])) {{
        if (!visited.has(dep)) {{ visited.add(dep); transUp.add(dep); q.push(dep); }}
      }}
    }}
  }}
  bfsDown(name); bfsUp(name);

  detail.innerHTML = `
    <h2>${{name}}</h2>
    <span class="caller-badge ${{callerClass}}">${{n.caller || 'unknown'}}</span>
    <div class="impact-box">
      <h4>Impact Analysis</h4>
      <div class="impact-stat"><span>Direct downstream</span><span class="num">${{downstream.length}}</span></div>
      <div class="impact-stat"><span>Transitive downstream</span><span class="num">${{transDown.size}}</span></div>
      <div class="impact-stat"><span>Direct upstream</span><span class="num">${{upstream.length}}</span></div>
      <div class="impact-stat"><span>Transitive upstream</span><span class="num">${{transUp.size}}</span></div>
    </div>
    <div class="dep-section">
      <h3>Invokes (${{upstream.length}})</h3>
      <ul class="dep-list">${{upstream.map(s => '<li onclick="onNodeClick(\\''+s+'\\')">' + s + '</li>').join('')}}</ul>
    </div>
    <div class="dep-section">
      <h3>Invoked by (${{downstream.length}})</h3>
      <ul class="dep-list">${{downstream.map(s => '<li onclick="onNodeClick(\\''+s+'\\')">' + s + '</li>').join('')}}</ul>
    </div>
    ${{produces.length ? '<div class="dep-section"><h3>Produces</h3><ul class="dep-list">' + produces.map(s => '<li>' + s + '</li>').join('') + '</ul></div>' : ''}}
    ${{consumes.length ? '<div class="dep-section"><h3>Consumes</h3><ul class="dep-list">' + consumes.map(s => '<li>' + s + '</li>').join('') + '</ul></div>' : ''}}
    <div class="dep-section">
      <h3>Full Transitive Downstream (${{transDown.size}})</h3>
      <ul class="dep-list">${{[...transDown].sort().map(s => '<li onclick="onNodeClick(\\''+s+'\\')">' + s + '</li>').join('')}}</ul>
    </div>
  `;

  if (impactMode) renderGraph(currentFilter, document.getElementById('search').value, name);
}}

// Search
document.getElementById('search').addEventListener('input', e => {{
  renderGraph(currentFilter, e.target.value, impactMode ? selectedSkill : null);
}});

// Filter buttons
document.querySelectorAll('.filter-btn').forEach(btn => {{
  btn.addEventListener('click', () => {{
    document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    const f = btn.dataset.filter;
    impactMode = f === 'impact';
    currentFilter = impactMode ? 'all' : f;
    renderGraph(currentFilter, document.getElementById('search').value, impactMode ? selectedSkill : null);
  }});
}});

function copyMermaid() {{
  const def = buildMermaidDef(currentFilter, document.getElementById('search').value, impactMode ? selectedSkill : null);
  navigator.clipboard.writeText(def).then(() => alert('Mermaid copied!'));
}}

function downloadSVG() {{
  const svg = document.querySelector('#mermaid-graph svg');
  if (!svg) return;
  const data = new XMLSerializer().serializeToString(svg);
  const blob = new Blob([data], {{type: 'image/svg+xml'}});
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = 'skill-dag.svg'; a.click();
  URL.revokeObjectURL(url);
}}

// Initial render
renderGraph('all', '', null);
</script>
</body>
</html>'''

def main():
    parser = argparse.ArgumentParser(description="Generate SKILL_DAG.yaml")
    parser.add_argument("--check-only", action="store_true", help="Only validate, don't write")
    parser.add_argument("--mermaid", action="store_true", help="Also generate Mermaid diagram")
    parser.add_argument("--html", action="store_true", help="Also generate HTML visualization")
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

    if args.html:
        html = generate_html(nodes, dag)
        with open(HTML_PATH, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"Written: {HTML_PATH}")


if __name__ == "__main__":
    main()
