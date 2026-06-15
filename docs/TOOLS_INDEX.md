# ARIS Tools 索引

本索引说明 `tools/` 下脚本的用途、调用场景和相关文档。开发者和 Codex 在修改、promote、发布或排查问题前应优先查这里。

## 使用原则

- 优先通过对应 skill 使用工具；只有排查、维护、发布时才直接调用脚本。
- 先 dry-run，再 apply。带 `--apply`、`--push-tag`、`rsync --delete`、远端部署语义的命令要谨慎。
- 不提交 `tools/__pycache__/`、`tools/release/__pycache__/` 或任何运行输出。
- 新增工具时，同步更新本文件、`README.md` 的工具表，以及必要的 skill 文档。

## 安装、更新、同步、发布

| 工具 | 用途 | 主要入口 | 备注 |
|------|------|----------|------|
| `tools/install_aris.sh` | Claude/通用 ARIS 项目安装器；创建 per-skill symlink、维护 manifest、支持 `--reconcile` | 用户项目初始化、framework 更新后重建链接 | symlink install 的主入口 |
| `tools/install_aris_codex.sh` | Codex-only 安装器；更新项目 `AGENTS.md` managed block | Codex 项目初始化或 reconcile | Codex 项目优先用这个 |
| `tools/install_aris.ps1` | Windows PowerShell 安装器 | Windows 用户 | 文件头注明旧 junction 行为有已知限制，优先 WSL bash 版 |
| `tools/smart_update.sh` | copied install 的安全更新分析和应用 | `bash tools/smart_update.sh --project <project>` | 默认 dry-run；symlink install 不用它 |
| `tools/smart_update_codex.sh` | Codex copied install 的安全更新 | `bash tools/smart_update_codex.sh --project <project>` | 支持 reviewer overlay；默认 dry-run |
| `tools/smart_update.ps1` | Windows copied install 更新工具 | PowerShell 项目更新 | 默认 dry-run |
| `tools/sync.sh` | 项目级 git add/commit/push/pull 和远端 rsync deploy | `/sync` skill 或直接调用 | 读取项目 `project.yaml` |
| `tools/release/check_release_ready.py` | stable release gate 检查 | promote/release 前 | 检查 main、clean worktree、tag、CHANGELOG、catalog/DAG |
| `tools/release/tag_release.sh` | release tag dry-run / create / push | 维护者明确要求打 tag 时 | 默认 dry-run；`--apply --push-tag` 才推送 tag |

相关文档：

- [PROMOTE_FLOW.md](PROMOTE_FLOW.md)
- [FRAMEWORK_STRUCTURE.md](FRAMEWORK_STRUCTURE.md)

## Feishu 控制

| 工具 | 用途 | 主要入口 | 备注 |
|------|------|----------|------|
| `tools/feishu_control.py` | Feishu 控制状态机：session 注册、inbox/outbox、lease、approval、`/interrupt`、`/btw` | bridge `/control/*` 或手动排查 | 不执行 shell/tool，只管理控制状态 |
| `tools/aris_feishu_session.py` | Feishu inbox 驱动的 Codex runner；支持 `codex exec`、live tmux 注入、状态卡更新 | `feishu-session` skill 或文档命令 | 运行态写入 `.aris/feishu-control/` |

相关文档：

- [FEISHU_INTEGRATION.md](FEISHU_INTEGRATION.md)
- `skills/feishu-session/SKILL.md`

## Agent 状态和长任务可观测性

| 工具 | 用途 | 主要入口 | 备注 |
|------|------|----------|------|
| `tools/agent_status.py` | 读写 `.aris/status/` agent status snapshot | Leader/Executor/Reviewer 角色规则 | 只记录状态，不调度任务 |
| `tools/watchdog.py` | 远端训练/实验 watchdog；注册任务、输出状态、告警 | `/run-experiment`、人工远端监控 | 适合长时间训练监控 |

相关文档：

- [WATCHDOG_GUIDE.md](WATCHDOG_GUIDE.md)
- [WATCHDOG_GUIDE_CN.md](WATCHDOG_GUIDE_CN.md)
- `skills/shared-references/agent-status-stream.md`

## 实验队列

| 工具 | 用途 | 主要入口 | 备注 |
|------|------|----------|------|
| `tools/experiment_queue/build_manifest.py` | 把 grid spec 展开成显式 job manifest | `/experiment-queue` | 支持 YAML/JSON；可手动调试 |
| `tools/experiment_queue/queue_manager.py` | 远端 GPU job scheduler；分配空闲 GPU、screen 启动、OOM retry、状态持久化 | `/experiment-queue` 自动上传到远端 | `queue_state.json` 是恢复依据 |

相关文档：

- `tools/experiment_queue/README.md`

## 文献、网页和知识库

| 工具 | 用途 | 主要入口 | 备注 |
|------|------|----------|------|
| `tools/arxiv_fetch.py` | arXiv 搜索和 PDF 下载 | `arxiv`、`research-lit` | 标准库实现 |
| `tools/semantic_scholar_fetch.py` | Semantic Scholar 搜索 | `semantic-scholar`、`research-lit` | venue/citation/TLDR 信息 |
| `tools/openalex_fetch.py` | OpenAlex 搜索 | `openalex`、`research-lit` | 需要 `requests`；可用 email/polite pool |
| `tools/deepxiv_fetch.py` | DeepXiv CLI 适配 | `deepxiv`、`research-lit` | 需要安装 `deepxiv` CLI |
| `tools/exa_search.py` | Exa web/search/content extraction 适配 | `exa-search`、`research-lit` | 需要 `exa-py` 和 API 配置 |
| `tools/research_wiki.py` | ARIS research wiki ingest/query/sync/lint/stats | `research-wiki` 和多个研究 skill | 多个检索/claim skill 的知识库后端 |
| `tools/verify_wiki_coverage.sh` | 比对 session 产物中出现的 arXiv ID 和 wiki ingest 覆盖 | 诊断工具 | 非 gate，覆盖不足也 exit 0 |

相关 skill：

- `research-lit`
- `arxiv`
- `semantic-scholar`
- `openalex`
- `deepxiv`
- `exa-search`
- `research-wiki`

## 论文、图表和视觉辅助

| 工具 | 用途 | 主要入口 | 备注 |
|------|------|----------|------|
| `tools/figure_renderer.py` | FigureSpec JSON 渲染成 deterministic SVG | `figure-spec` | 支持 validate/schema/render |
| `tools/extract_paper_style.py` | 从参考论文提取结构风格 profile | `paper-plan`、`paper-write`、`auto-paper-improvement-loop` 等 | 只做结构风格，不复制内容 |
| `tools/paper_illustration_image2.py` | AI 插图 workflow 的 preflight/finalize/verify | `paper-illustration-image2` | 校验 PNG 和生成规范产物 |
| `tools/verify_paper_audits.sh` | 论文 mandatory audit 外部 verifier | `paper-writing` Phase 6、审计 hook | submission 级别会阻塞缺失/失败 audit |
| `tools/save_trace.sh` | 保存 reviewer/agent 调用 trace | 多个 review/audit skill | 写入 `.aris/traces/...` |

相关 skill：

- `figure-spec`
- `paper-illustration-image2`
- `paper-writing`
- `paper-plan`
- `paper-write`
- `citation-audit`
- `paper-claim-audit`
- `proof-checker`
- `kill-argument`

## Overleaf

| 工具 | 用途 | 主要入口 | 备注 |
|------|------|----------|------|
| `tools/overleaf_setup.sh` | Overleaf Git bridge 初始化/配置辅助 | `overleaf-sync` | 涉及 token/remote，注意不要提交凭据 |
| `tools/overleaf_audit.sh` | Overleaf 同步前后审计 | `overleaf-sync` | 用于检查敏感 token 和同步状态 |

## Skill 生成、目录和迁移

| 工具 | 用途 | 主要入口 | 备注 |
|------|------|----------|------|
| `tools/generate_skill_catalog.py` | 生成 `docs/SKILL_CATALOG.md` | 新增/删除/改 skill 后 | 需要同步中文目录 |
| `tools/translate_skill_catalog.py` | 生成 `docs/SKILL_CATALOG_CN.md` | catalog 更新后 | 维护中文描述映射 |
| `tools/generate_skill_dag.py` | 生成 `docs/SKILL_DAG.yaml`、`.mmd`、`.html` | skill DAG 变化后 | formal edge 来自 frontmatter `invokes` |
| `tools/generate_doc_dag.py` | 校验 `docs/DOC_DAG.yaml` 并生成 `docs/DOC_DAG.mmd` | 新增/删除/重命名文档后 | 无 PyYAML 时使用内置轻量解析器 |
| `tools/generate_codex_claude_review_overrides.py` | 生成 Codex skill 的 Claude reviewer overlay | 维护 reviewer overlay 时 | 输出到 `skills/skills-codex-claude-review/` |
| `tools/convert_skills_to_llm_chat.py` | 将 Codex-native skill 转换成 llm-chat MCP 版本 | 迁移/兼容实验 | 会替换 Codex MCP 调用文本 |

相关文档：

- [DOC_DEPENDENCIES.md](DOC_DEPENDENCIES.md)
- [SKILL_CATALOG.md](SKILL_CATALOG.md)
- [SKILL_CATALOG_CN.md](SKILL_CATALOG_CN.md)
- [SKILL_DAG.yaml](SKILL_DAG.yaml)

## Meta Optimization

| 工具 | 用途 | 主要入口 | 备注 |
|------|------|----------|------|
| `tools/meta_opt/log_event.sh` | Claude hook 事件记录到 `.aris/meta/` 和 `~/.aris/meta/` | Claude Code hook | 记录 skill/tool 使用趋势 |
| `tools/meta_opt/check_ready.sh` | SessionEnd 时检查是否该运行 `/meta-optimize` | Claude Code hook | 达到阈值时输出提醒 |

## 维护建议

- 新工具如果只服务某个 skill，应在对应 `SKILL.md` 中注明 canonical helper。
- 新工具如果是维护/发布流程的一部分，应同步更新 [PROMOTE_FLOW.md](PROMOTE_FLOW.md)。
- 新工具如果面向用户，应在 `README.md` 和本文件中出现。
- 脚本应提供 `--help` 或文件头 usage；复杂工具应有独立 README。
