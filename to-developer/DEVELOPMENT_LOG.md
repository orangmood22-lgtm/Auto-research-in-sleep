# ARIS Development Log

Maintainer-facing module log for ARIS framework development. This file is more detailed than `CHANGELOG.md` and is used to prepare user-facing release notes.

## [Unreleased]

### skills
- Normalized skill DAG governance so formal edges come only from frontmatter `invokes`.
- Added `platform`, `status`, and dependency metadata to key Codex/Claude dual-client skills.
- Added Codex mirrors for the newly added skill set.
- Enhanced `skills-codex-claude-review` overlays with reviewer bias guard, edit whitelist, reviewer memory, debate protocol, and broader venue support.

### tools
- Added guarded release tooling under `tools/release/`.
- Made `mcp-servers/codex-review/bridge.py` resolve its sibling `server.py` by default instead of using a hard-coded developer path.
- Added Python 3.8 compatibility fixes to selected tools and tests.
- Updated catalog generation/translation coverage for newer role and DAG-check skills.

### templates
- Reworked `templates/README.md` into a structured template index.
- Generalized `project.yaml.tmpl` server examples and framework metadata.
- Updated idea candidate template paths to the current project file layout.

### docs
- Added `docs/LANGGRAPH_EVALUATION.md`.
- Added `docs/README.md` and `mcp-servers/README.md` indexes.
- Updated repository paths and removed obsolete ARIS-Code/Matt Pocock/image assets.
- Added `CONTEXT.md` language for framework version governance.
- Added `to-developer/plans/VERSION_MANAGEMENT.md`.

### deploy
- Hardened GPU server deployment flow, including 3090x2 deployment assumptions and Docker guidance.

### mcp-servers
- Documented MCP bridge inventory and provider requirements.
- Made Codex review bridge portable across local paths.

### tests
- Added skill DAG contract tests.
- Added Codex review bridge path resolution test.
- Added release tooling tests.
- Ran catalog, DAG, mirror, bridge, and py_compile checks during stabilization.

### compatibility / migration
- Set `main` as stable, `dev` as integration, and `upstream-base` as old baseline backup.
- Switched Git remote push path to HTTPS after GitHub SSH transport failed in this environment.
- Restored `to-developer/` developer material into the dev worktree and ignored private settings/SSH notes.

### breaking / requires user action
- Projects should pin formal release tags after `v0.1.0`; prerelease tags are for deliberate testing only.
