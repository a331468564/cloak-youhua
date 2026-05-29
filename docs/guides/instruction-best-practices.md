<!-- DOC_META
lifecycle:  long-term
audience:   agent, user
write_when: 指令文件规范或最佳实践变更时更新
read_when:  创建或重构 CLAUDE.md / AGENTS.md / rules / skills 时读取
delete_when: 不删除
-->
# 指令文件最佳实践规范

*Based on: Claude Code 官方文档 + Cursor/Copilot/Continue 对标 + 学术研究（2026-05-28）*

---

## 一、文件层级与加载时机

| 层级 | 机制 | 何时加载 | 放什么 | 大小限制 |
|------|------|----------|--------|----------|
| **核心规则** | `CLAUDE.md` | 每次启动 | 数据安全、阻塞流程、入口规则 | **< 200 行** |
| **操作规则** | `AGENTS.md` | 每次启动 | 数据操作规则、文档规范、安全边界 | < 200 行 |
| **路径规则** | `.claude/rules/*.md` | 匹配文件时 | 任务特定约束（提取阈值、工具配置） | 每文件 < 200 行 |
| **技能** | `.claude/skills/*/SKILL.md` | 按需调用 | 多步流程（KP 管线、关键词发现） | 每文件 < 500 行 |
| **工作流文档** | `docs/workflows/*.md` | agent 读取时 | CODEx 标记区块、详细流程 | 无硬限制 |
| **操作指南** | `docs/guides/*.md` | agent 读取时 | 命令参考、配置说明 | 无硬限制 |
| **记忆** | `MEMORY.md` | 每次启动 | 跨会话学习（前 200 行） | < 200 行 / 25KB |

**决策规则：**
- 每次会话都必须知道 → `CLAUDE.md`
- 只在特定目录工作时才需要 → `.claude/rules/`（带 `paths:` 前言）
- 多步流程，按需调用 → `.claude/skills/`
- 人类参考，agent 按需读取 → `docs/`

---

## 二、CLAUDE.md 写作规范

### 2.1 大小限制

**硬限制：200 行。** 超过则遵循率下降。

> 来源：Claude Code 官方 — "Target under 200 lines per CLAUDE.md file. Longer files consume more context and reduce adherence."

### 2.2 关键规则放前 20 行

> 来源：Lost in the Middle (Liu et al., TACL 2023) — LLM 对上下文中间的指令遵循率呈 U 型曲线，开头和结尾最强。

**前 20 行只放：** 最常被违反的规则（数据安全核心禁令 + 阻塞查表流程）

**不放：** 入口说明、项目概述、文件结构（放后面）

### 2.3 HTML 注释零成本

`<!-- DOC_META ... -->` 格式的注释在注入上下文前被剥离，零 token 成本。维护者笔记用 HTML 注释。

### 2.4 不放的内容

| 不要放 | 应该放 |
|--------|--------|
| 多步流程 | `.claude/skills/` |
| 工具配置细节 | `.claude/rules/tool-config.md` |
| 文件结构（可 ls 查看） | 不放任何地方 |
| 数据恢复步骤 | `.claude/rules/data-safety.md` |
| 脚本用法 | `docs/guides/` 或 `.claude/rules/` |
| 标准语言规范（agent 已知） | 不放 |

---

## 三、`.claude/rules/` 写作规范

### 3.1 路径作用域

```yaml
---
paths:
  - "scripts/extraction/**"
  - "reports/**"
---
```

- `paths:` 用 glob 模式
- 多个模式用 YAML 列表
- 无 `paths:` 的 rules 每次启动加载（同 CLAUDE.md）
- 有 `paths:` 的 rules 在 agent 读取匹配文件时加载

### 3.2 支持的模式

| 模式 | 匹配 |
|------|------|
| `scripts/extraction/**` | 该目录下所有文件 |
| `data/**` | data 目录下所有文件 |
| `**/*.py` | 所有 Python 文件 |
| `src/**/*.{ts,tsx}` | 多扩展名匹配 |

### 3.3 子目录支持

`.claude/rules/` 支持子目录，递归发现所有 `.md` 文件：

```
.claude/rules/
├── data-safety.md
├── extraction/
│   └── rules.md
└── kp-pipeline/
    └── rules.md
```

---

## 四、Skills 写作规范

### 4.1 什么时候用 Skill

- 多步流程（KP 管线、关键词发现、部署流程）
- 重复粘贴的指令
- CLAUDE.md 里长大的流程段落

### 4.2 SKILL.md 格式

```yaml
---
name: skill-name-with-hyphens
description: Use when [触发条件]. Triggers on keywords like [关键词].
allowed-tools:
  - Read
  - Bash
  - Grep
---
```

**关键字段：**

| 字段 | 必需 | 说明 |
|------|------|------|
| `name` | 推荐 | 目录名即命令名（`/skill-name`） |
| `description` | **必需** | **只写触发条件，不写流程摘要** |
| `allowed-tools` | 可选 | 预授权工具，减少权限弹窗 |
| `disable-model-invocation` | 可选 | `true` = 只能用户手动调用 |
| `context` | 可选 | `fork` = 在子 agent 中运行 |

### 4.3 Description 写法（CSO 优化）

> 来源：writing-skills 技能的测试发现 — description 写流程摘要会导致 agent 走捷径不读全文。

```yaml
# ❌ 错误：写了流程摘要
description: KP pipeline - stage 1 discover, stage 2 enrich, stage 3 validate

# ✅ 正确：只写触发条件
description: Use when discovering key persons for AU restaurant/hotel companies, enriching contact information, or running the KP pipeline.
```

**规则：** Description = 什么时候用，不是做什么。以 "Use when..." 开头。

### 4.4 大小限制

- SKILL.md < 500 行
- 详细参考放单独文件（`reference.md`、`examples/`）
- SKILL.md 内用 `[reference.md](reference.md)` 链接

### 4.5 动态上下文注入

```yaml
# 运行 shell 命令注入上下文
- Current leads: !`wc -l data/leads.csv`
- Git status: !`git status --short`
```

---

## 五、Hooks 写作规范

### 5.1 CLAUDE.md vs Hooks 的区别

| | CLAUDE.md | Hooks |
|---|---|---|
| 执行方式 | agent 自觉遵循 | **强制执行** |
| 可靠性 | 不保证 | 保证触发 |
| 适合放 | 建议、指导、流程 | 必须执行的规则 |

> 来源：Claude 官方 — "CLAUDE.md instructions shape Claude's behavior but are not a hard enforcement layer. To block an action regardless of what Claude decides, use a PreToolUse hook instead."

### 5.2 必须用 Hook 强制执行的规则

- 数据安全（append-only、不能删除）
- 危险命令拦截
- 阻塞检测（连续失败自动提醒）
- 文件清理检查

### 5.3 Hook 类型

| 类型 | 用途 | 复杂度 |
|------|------|--------|
| `command` | 运行 shell 脚本 | 低 |
| `prompt` | 发送到模型单轮评估 | 中 |
| `agent` | 启动子 agent 读取规则验证 | 高 |

### 5.4 additionalContext 注入

Hook 可以返回 `additionalContext` 注入 agent 上下文：

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PostToolUse",
    "additionalContext": "阻塞提醒：请查 docs/logs/changelog.md 历史阻塞索引"
  }
}
```

---

## 六、多源对标

| 来源 | 要点 | 本项目应用 |
|------|------|-----------|
| Claude Code 官方 | < 200 行、`paths:` 按需加载、hooks 强制执行 | CLAUDE.md 精简、rules 拆分 |
| Cursor | `globs:` 前言、< 500 行 | 同 `paths:` 机制 |
| GitHub Copilot | `applyTo:` 前言、< 2 页 | 同 `paths:` 机制 |
| Continue | `globs` + `regex` + `alwaysApply` | 同 `paths:` 机制 |
| Lost in the Middle (TACL 2023) | U 型遵循曲线 | 关键规则放前 20 行 |
| RULER Benchmark (COLM 2024) | 长上下文性能下降 | 控制指令文件大小 |
| NoLiMa Benchmark (ICML 2025) | 32K 时 50%+ 性能下降 | 按需加载减少上下文 |

---

## 七、文件组织检查清单

创建或重构指令文件时，逐项检查：

- [ ] CLAUDE.md < 200 行
- [ ] 关键规则在前 20 行
- [ ] 多步流程在 skills 里，不在 CLAUDE.md
- [ ] 工具配置在 rules 里，不在 CLAUDE.md
- [ ] rules 有 `paths:` 前言（按需加载）
- [ ] skills 的 description 只写触发条件
- [ ] 必须执行的规则用 hook，不靠 prompt
- [ ] DOC_META 用 `<!-- -->` HTML 注释
- [ ] 无重复内容（CLAUDE.md / AGENTS.md / rules 之间）
- [ ] 文件结构不放在 CLAUDE.md（agent 可以 ls 查看）
