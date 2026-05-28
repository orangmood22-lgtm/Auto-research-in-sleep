# Project: {project-name}

## 默认模式

- caveman 模式默认开启（精简回复，保留技术准确度）
- 代码修改遵循 TDD（仅限 Python/实验代码，文档/配置不要求）
- 新设计/架构决策落地前必须 /grill-me 或 /grill-with-docs
- 新用户首次使用建议跑 /git-guardrails

## Agent 约束

### 禁止 tail 轮询

**严禁**用 `Bash(tail -f ...)` 或重复 `Bash(tail ...)` 轮询实验进度。代价：800+ 次无意义 API 调用。

正确做法：
- 远程长时间实验 → `ssh server "screen -dmS exp_name bash -c 'cmd > log.txt 2>&1'"` 启动，用 `/monitor-experiment` 一次性收集结果
- 本地长时间实验 → `Bash(run_in_background: true)` 启动，等 task-notification 自动回调
- 需要等完成 → `Monitor` 工具（每行 stdout 一个事件），**不要循环 tail**
- 检查是否跑完 → 单次 `ssh server "tail -20 log.txt"` 或 `ssh server "screen -ls"`，**不要循环**

### Executor 阻塞协议

遵循 `skills/shared-references/executor-blocked-protocol.md`：
- Agent 遇阻塞自行尝试 2 种绕过
- 全失败写 `BLOCKED_REPORT.md`，不卡死不越权
- Leader 只转述报告给用户，不自己执行

## Pipeline Status

```yaml
stage: idle          # idle | idea-discovery | implementation | training | review | paper
idea: ""             # Current idea title (one line)
contract: ""         # Path to research_contract.md (e.g., idea-stage/docs/research_contract.md)
current_branch: ""   # Git branch for this idea
baseline: ""         # Baseline numbers for comparison
training_status: idle  # idle | running | complete | failed
language: en         # en | zh — controls skill output language (see shared-references/output-language.md)
active_tasks: []
next: ""             # Concrete next step
last_updated: ""     # YYYY-MM-DD HH:mm — auto-updated by skills on every output write
```

## Project Constraints

- {constraint 1}
- {constraint 2}

## Non-Goals

- {non-goal 1}

## Compute Budget

- {budget details, e.g., "8x A100 for 24h via vast.ai"}
