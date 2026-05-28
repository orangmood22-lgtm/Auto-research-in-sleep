# Executor Skill Routing

> Leader 派发 Executor 任务时，根据任务类型从本表选择推荐 skills 写入 prompt。
> Executor 收到推荐后**必须使用**标记为"必用"的 skill。

## 任务→Skill 映射

| 任务类型 | 必用 | 可选 | caveman |
|----------|------|------|---------|
| **写 Python/实验代码** | `/tdd` | `/diagnose`（出 bug 时） | ✅ 开启 |
| **诊断 bug/性能问题** | `/diagnose` | `/zoom-out`（需要全局视角时） | ✅ 开启 |
| **部署运行实验** | `/run-experiment`, `/monitor-experiment` | `/experiment-queue`（批量时）, `/training-check`（WandB） | ✅ 开启 |
| **实现实验计划** | `/experiment-bridge`, `/tdd` | `/diagnose` | ✅ 开启 |
| **分析实验结果** | `/analyze-results` | `/ablation-planner`（需要消融时） | ✅ 开启 |
| **写论文** | `/paper-write` | `/paper-compile`, `/formula-derivation` | ❌ 关闭 |
| **生成论文图表** | `/paper-figure` | `/figure-spec`, `/mermaid-diagram`, `/paper-illustration` | ✅ 开启 |
| **生成幻灯片/海报** | `/paper-slides` 或 `/paper-poster` | `/slides-polish` | ❌ 关闭 |
| **文献调研** | `/research-lit` | `/semantic-scholar`, `/arxiv`, `/novelty-check` | ✅ 开启 |
| **代码同步/部署** | `/sync` | `/overleaf-sync`（论文时） | ✅ 开启 |
| **写数学证明** | `/proof-writer` | `/proof-checker`（验证时） | ❌ 关闭 |
| **专利撰写** | 按阶段选用 | 见下方专利子表 | ❌ 关闭 |
| **基金申请** | `/grant-proposal` | — | ❌ 关闭 |

### 专利任务细分

| 子任务 | 必用 |
|--------|------|
| 发明构建 | `/invention-structuring` |
| 查新 | `/patent-novelty-check`, `/prior-art-search` |
| 权利要求 | `/claims-drafting` |
| 说明书 | `/specification-writing` |
| 实施例 | `/embodiment-description` |
| 附图 | `/figure-description` |
| 格式化 | `/jurisdiction-format` |
| 审查 | `/patent-review` |

## Leader 派发模板

Leader 派发 Executor 时，prompt 应包含以下结构：

```
Agent:
  model: "sonnet"
  description: "[任务简述]"
  prompt: |
    你是 Executor。
    
    ## 首先
    Read .claude/skills/shared-references/agent-guide.md 了解可用 skills 和约束。
    
    ## 你的任务
    [具体任务描述]
    
    ## 推荐 Skills
    本任务必用：/tdd（写代码）、/diagnose（遇 bug 时）
    本任务可选：[根据映射表]
    
    ## 约束
    - caveman 模式 [开启/关闭]
    - 遵循 executor-blocked-protocol
    - 不做自审，写完交 Reviewer
    - 完成后列出所有产出文件路径
```

## 更新本文件

新增任务类型时：
1. 在映射表中添加一行
2. 如果涉及新 skill，确认该 skill 的 `caller` frontmatter 包含 `executor`
3. 更新 `agent-guide.md` 的执行层表格（如果是新 skill）
