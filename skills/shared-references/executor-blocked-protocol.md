# Executor Blocked Protocol

## Core Principle

**Executor 遇到阻塞时先自救，自救失败再上报。Leader 永远不替代执行。**

当 Executor Agent 在执行任务过程中遇到无法继续的阻塞（权限拦截、网络不通、资源不足、依赖缺失、文件不存在等），按本协议处理，而不是直接放弃或等 Leader 来救。

## 阻塞分类

| 类型 | 典型场景 |
|------|---------|
| `permission` | Bash 命令被 auto-mode classifier 拦截、文件写入被 sandbox 拒绝 |
| `network` | SSH 连不上 GPU 服务器、API timeout、DNS 解析失败 |
| `resource` | GPU OOM、磁盘满、内存不足 |
| `dependency` | pip 包装不上、模块 import 失败、conda env 不存在 |
| `missing_file` | 计划引用的路径不存在、数据集未下载、配置文件缺失 |

## 处理流程

```
遇到阻塞
  │
  ├─ 尝试绕过方案 1（换等价命令/工具/参数）
  │   ├─ 成功 → 继续任务，用户无感
  │   └─ 失败 ↓
  │
  ├─ 尝试绕过方案 2（降级执行/替代路径）
  │   ├─ 成功 → 继续任务
  │   └─ 失败 ↓
  │
  └─ 写 BLOCKED_REPORT.md → 停止当前阻塞点
      │
      ├─ 累计阻塞 < 3 → 跳过该步骤，继续任务中其他可做的部分
      └─ 累计阻塞 ≥ 3 → 整个任务停止，输出总报告
```

### 计数规则

- **每个阻塞事件独立计 2 次尝试**。SSH 被拦试 2 次、pip 又被拦再试 2 次——各自独立。
- **累计阻塞次数是任务级的**。同一个任务内累计 ≥ 3 个不同阻塞全失败 → 整个任务停止，不再继续。

### 绕过原则

- 优先用等价工具/命令替代（如 `Read` 替代 `cat`，`rsync` 替代 `scp`）
- 如果换命令能解决，直接继续，不需要报告
- 只有两种绕过都失败才降级为"写人工操作指令"
- 不要在绕过过程中做危险操作（`--force`、`rm -rf`、绕过安全检查等）

## BLOCKED_REPORT.md 格式

写到项目根目录 `BLOCKED_REPORT.md`（多次阻塞追加，不覆盖）：

```markdown
# Blocked Report

> 生成时间：YYYY-MM-DD HH:MM
> 任务来源：[Leader 派发的原始任务描述]

## 阻塞 1

**分类：** permission | network | resource | dependency | missing_file

**触发点：** [具体什么操作失败了]

**错误信息：**
\`\`\`
[原始错误输出，不要摘要]
\`\`\`

**尝试过的绕过：**
1. [方法] → [结果]
2. [方法] → [结果]

**需要人工操作：**
- [ ] \`具体命令或操作步骤\`
- [ ] \`具体命令或操作步骤\`

## 阻塞 2
...

## 恢复方式

[人工操作完成后如何继续：重新派发原任务 / 从某阶段继续 / 需要额外配置]
```

### 格式要求

- "需要人工操作"必须是**可复制粘贴的具体命令**，不是模糊描述
- "错误信息"贴原始输出，不要意译
- "恢复方式"要明确到 Leader 能直接执行的动作

## Leader 端行为

Leader 收到 Executor 的阻塞报告后：

1. **读 `BLOCKED_REPORT.md`**
2. **原样转述给用户** — 不自己解决、不自己绕过、不执行里面的命令
3. **等用户确认完成**
4. **重新派发 Agent 继续**

Leader 在整个过程中**不写代码、不跑命令、不修配置**。阻塞的诊断和降级方案已由 Executor 完成，Leader 只当传话人。

## Executor Agent Prompt 嵌入

Leader 派发 Executor Agent 时，prompt 中加入：

```
遵循 skills/shared-references/executor-blocked-protocol.md：
遇到阻塞先自行尝试 2 种绕过，全失败写 BLOCKED_REPORT.md 后停止。
```
