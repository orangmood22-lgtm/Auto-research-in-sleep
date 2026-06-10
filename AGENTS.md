# ARIS Project: Few-Shot Class-Incremental Object Detection (FSCIOD)

## 默认模式

- caveman 模式默认开启（精简回复，保留技术准确度）
- 代码修改遵循 TDD（仅限 Python/实验代码，文档/配置不要求）
- 新设计/架构决策落地前必须 `$grill-me` 或 `$grill-with-docs`
- 新用户首次使用建议跑 `$git-guardrails`

## Agent 约束

**完整约束和 skill 用法见 `.agents/skills/shared-references/agent-guide.md`。**

- 禁止 `tail -f` 或循环 `tail` 轮询实验 → 用 `$monitor-experiment` 或 background tasks
- Executor 遇阻塞遵循 `executor-blocked-protocol.md`：自救 2 次，失败写 `BLOCKED_REPORT.md`
- Leader 不写代码/不跑命令，Executor 不自审，Reviewer 只看原始文件
- Skill 分层：编排层(leader) / 执行层(executor) / 工具层(any) / 检索层(any)，不要越层调用

## Research Direction

小样本增量目标检测（Few-Shot Class-Incremental Object Detection），以**频域特征 + 原型学习**为核心出发点。

参考论文：Jiang et al., 2025 — "Revisiting Pool-based Prompt Learning for Few-shot Class-incremental Learning"

## Pipeline Status

| Stage             | Status      | Artifact |
| ----------------- | ----------- | -------- |
| Idea Discovery    | NOT STARTED | —        |
| Experiment Plan   | NOT STARTED | —        |
| Experiment Bridge | NOT STARTED | —        |
| Experiment Audit  | NOT STARTED | —        |
| Result-to-Claim   | NOT STARTED | —        |
| Paper Writing     | NOT STARTED | —        |

## Three-Party Architecture

本项目采用三边架构，三个独立 codex exec 会话分别承担不同角色：

| Role         | Profile               | Responsibility                          |
| ------------ | --------------------- | --------------------------------------- |
| **Leader**   | `codex exec -p leader`   | 研究规划、gate 决策、止损判断、分发任务 |
| **Executor** | `codex exec -p executor` | 代码实现、实验部署、论文撰写            |
| **Reviewer** | `codex exec -p reviewer` | 独立代码审查、实验审计、claim 判定      |

### 角色边界（严格遵守）

**Leader 不写代码、不跑实验。** 只读文件、做判断、分发任务。
**Executor 不做自审。** 代码写完交给 Reviewer，不自己判断质量。
**Reviewer 只看原始文件。** 遵守 `skills/shared-references/reviewer-independence.md`，不看 Executor 的总结。

### 协作流程

1. **Leader** 通过 `$experiment-plan` 制定计划 → 产出 `refine-logs/EXPERIMENT_PLAN.md`
2. **Executor** 通过 `$experiment-bridge` 实现代码 → Reviewer 做代码审查 → 部署运行
3. **Reviewer** 通过 `$experiment-audit` 独立审计实验诚实度
4. **Leader** 通过 `$result-to-claim` 判定结果支持什么 claim

### Skill 调用方式

Codex 中 skill 使用 `$skill-name` 语法（非 `/skill-name`）。Skills 自动从 `.agents/skills/` 发现。

## Compute Resources

### Server 1: V100 x4
- SSH: `ssh 4090x4--ai`
- Experiment dir: `/home/ai_worker/exps/exp0516`
- Env: `conda activate aris`
- Python 3.10, PyTorch 2.6.0+cu118
- GPU 0 available (~23GB free), GPU 1-3 occupied

### Server 2: 4090 x8 (首选)
- SSH: `ssh 4090x8-root`
- Experiment dir: `/workspace/orangmood/aris/exp0516`
- Env: `conda activate yolo11`
- Python 3.11, PyTorch 2.6.0, CUDA 12.2
- GPU 2 available (24GB free), `CUDA_VISIBLE_DEVICES=2`

## Key Directories

```
idea-stage/          ← $idea-discovery output
refine-logs/         ← $experiment-plan, $experiment-bridge output
paper/               ← $paper-writing output
discussions/         ← progress logs, analysis reports
templates/           ← experiment plan template (含完整 contract 段落)
skills/              ← ARIS skill definitions
tools/               ← queue manager, watchdog, fetch utilities
tests/               ← regression tests
```

## Experiment Chain Contract

所有实验链 skill 共享统一词汇（详见 `skills/shared-references/integration-contract.md`）：

- **Expectation Declaration**: split、GT 来源、baseline 假设
- **Execution Spec**: 每个 block 的 variants / metrics / seeds / constraints
- **Data Flow Summary**: 数据如何流经 eval pipeline
- **Delta Assertion**: control vs modified 之间应有的具体差异，以及无效果检测器
- **Evidence Mapping**: 哪些 artifact 支撑哪些 claim
- **Implementation Deviations**: `IMPLEMENTATION_DEVIATIONS.json` 记录计划偏移

## Recovery Contract

长时间运行的工具遵循 `skills/shared-references/recovery-state-contract.md`：
- 原子写入保证状态持久化
- 失败分类：transient_network / retryable_http / retryable_parse / validation_error / environment_error / logic_error
- 阶段检查点支持断点续跑

## Integrity Rules

- 遵守 `skills/shared-references/experiment-integrity.md`：禁止 fake GT、score normalization fraud、phantom results、insufficient scope
- 遵守 `skills/shared-references/reviewer-independence.md`：Reviewer 必须读原始文件，不看 Executor 转述
- 评估类型（real_gt / synthetic_proxy / self_supervised_proxy / simulation_only / human_eval）必须在 plan 中声明，audit/claim 阶段不得悄悄升级
