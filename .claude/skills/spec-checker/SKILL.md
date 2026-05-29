---
name: spec-checker
description: Use when creating, editing, or reviewing CLAUDE.md, AGENTS.md, rules files, or skills. Triggers on keywords like "规范检查", "spec check", "指令文件", "CLAUDE.md 太长", "规则冲突", "instruction review", "检查规范".
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash
  - Agent
---

# Spec Checker（指令文件规范检查官）

## Overview

检查项目指令文件是否符合最佳实践规范。适用于所有项目，不限于特定代码库。

**核心原则：** 指令文件太长 = 规则被忽略。每次检查都按清单逐项验证。

**规范依据：** Claude Code 官方文档 + Cursor/Copilot/Continue 对标 + 学术研究（Lost in the Middle, TACL 2023）

## When to Use

- 创建或重构 CLAUDE.md / AGENTS.md
- 新建 `.claude/rules/` 文件
- 新建 `.claude/skills/` 文件
- agent 不遵循某条规则时（可能是文件结构问题）
- 用户说"检查规范"、"规范检查"、"spec check"

**不要用在：** 日常编码任务、数据处理、脚本调试

## 检查清单

### A. CLAUDE.md 检查

```bash
wc -l CLAUDE.md 2>/dev/null || echo "NOT FOUND"
```

| 检查项 | 标准 | 动作 |
|--------|------|------|
| 行数 | < 200 行 | 超标则拆分到 rules/skills |
| 关键规则位置 | 前 20 行 | 最常被违反的规则放最前面 |
| 多步流程 | 不在 CLAUDE.md | 移到 skills |
| 工具配置 | 不在 CLAUDE.md | 移到 rules |
| 文件结构 | 不在 CLAUDE.md | 删除（agent 可 ls） |
| 重复内容 | 无 | 与 AGENTS.md/rules 交叉检查 |
| DOC_META | `<!-- -->` 格式 | HTML 注释零 token |

### B. AGENTS.md 检查

| 检查项 | 标准 | 动作 |
|--------|------|------|
| 行数 | < 200 行 | 超标则拆分 |
| 阻塞处理流程 | 存在且在显眼位置 | 缺失则补充 |
| 数据安全规则 | 与 CLAUDE.md 一致 | 不一致则统一 |
| 任务分隔规则 | 有明确分隔（如 A区/B区） | 缺失则补充 |
| 文档生命周期 | 有 DOC_META 规则 | 缺失则补充 |

### C. `.claude/rules/` 检查

```bash
ls .claude/rules/*.md .claude/rules/**/*.md 2>/dev/null
```

| 检查项 | 标准 | 动作 |
|--------|------|------|
| `paths:` 前言 | 每个文件都有 | 无 paths 的每次启动加载 |
| 行数 | 每文件 < 200 行 | 超标则拆分 |
| 与 CLAUDE.md 重复 | 无 | 删除重复内容 |
| glob 模式正确 | 路径存在 | 验证匹配 |

### D. Skills 检查

```bash
ls .claude/skills/*/SKILL.md ~/.claude/skills/*/SKILL.md 2>/dev/null
```

| 检查项 | 标准 | 动作 |
|--------|------|------|
| description | 以 "Use when" 开头 | 不写流程摘要 |
| description < 500 字符 | 否则截断 | 精简 |
| SKILL.md < 500 行 | 否则拆分 | 详细参考放单独文件 |
| name 格式 | 只有字母、数字、连字符 | 不用特殊字符 |
| allowed-tools | 列出预授权工具 | 减少权限弹窗 |

### E. Hooks 检查

```bash
ls .claude/hooks/*.py ~/.claude/hooks/*.py 2>/dev/null
```

| 检查项 | 标准 | 动作 |
|--------|------|------|
| 必须执行的规则 | 用 hook 不靠 prompt | 阻塞检测、数据安全、清理检查 |
| settings.json 配置 | 与 hook 文件一一对应 | 缺失则补充 |
| 项目级 vs 全局 | 分清位置 | 项目迁移时需单独处理 |

### F. 交叉检查

| 检查项 | 标准 | 动作 |
|--------|------|------|
| CLAUDE.md vs AGENTS.md | 无重复规则 | 删除一边的重复 |
| CLAUDE.md vs rules | 无重复规则 | 从 CLAUDE.md 移除 |
| rules vs skills | rules 是约束，skills 是流程 | 混淆则重新分类 |
| 阻塞触发条件 | 全部文件统一 | 如 "2-3 次尝试无进展" |

### G. V2 优势模式检查（推荐采纳）

以下是经过 V2 项目验证的有效模式，检查当前项目是否具备：

| 模式 | 说明 | 检查方式 |
|------|------|----------|
| **Hook 强制执行** | 必须执行的规则用 hook，不靠 prompt | 检查 `.claude/hooks/` 和 `settings.json` |
| **阻塞处理流程** | classify → lookup → solve & record | 检查 AGENTS.md 是否有阻塞分类+查表流程 |
| **DOC_META 生命周期** | `lifecycle / audience / write_when / read_when / delete_when` | 检查 .md 文件是否有 DOC_META |
| **任务分隔** | 不同任务区域独立，不混写 | 检查是否有 A区/B区或类似分隔 |
| **进度快照** | `current-progress.md` 记录数据量和下一步 | 检查是否存在 |
| **运行报告** | 每轮任务跑完生成人类可读报告 | 检查是否有报告生成脚本 |
| **决策日志** | `request-solution-log.md` 记录重要决策 | 检查是否存在 |
| **交接文档** | handoff 文档用于跨会话/跨 agent 交接 | 检查是否有 handoff 机制 |
| **CODEx 标记** | `<!-- CODEx_START: xxx -->` 标记工作流区块 | 检查 workflow 文档是否有标记 |
| **数据只追加** | 主表 append-only，清理写 rejected 文件 | 检查数据安全规则 |

## 执行流程

```
1. Glob 扫描项目指令文件（CLAUDE.md / AGENTS.md / rules / skills / hooks）
  ↓
2. 逐项检查 A-G 清单
  ↓
3. 生成检查报告（通过/警告/失败）
  ↓
4. 对失败项给出具体修复建议
```

## 检查报告格式

```
## 规范检查报告 — YYYY-MM-DD

### A. CLAUDE.md
- [x] 行数: 180 行 (< 200) ✅
- [ ] 关键规则位置: 前 20 行只有入口说明 ⚠️ 建议把数据安全移到前 20 行
- [x] 无多步流程 ✅

### B. AGENTS.md
- [x] 行数: 150 行 (< 200) ✅
- [x] 阻塞处理流程存在 ✅

### C. .claude/rules/
- [x] 3 个文件都有 paths: 前言 ✅
- [ ] extraction-rules.md: 250 行 ⚠️ 超标，建议拆分

### D. Skills
- [x] description 以 "Use when" 开头 ✅
- [x] SKILL.md < 500 行 ✅

### E. Hooks
- [x] 阻塞检测 hook 存在 ✅
- [ ] 数据安全无 hook ⚠️ 建议加 PreToolUse hook

### F. 交叉检查
- [x] 无重复规则 ✅
- [ ] 阻塞触发条件不统一 ⚠️ CLAUDE.md 写 "5 分钟"，AGENTS.md 写 "2-3 次"

### G. V2 优势模式
- [x] Hook 强制执行 ✅
- [x] 阻塞处理流程 ✅
- [ ] 运行报告生成 ⚠️ 缺少报告脚本
- [ ] 决策日志 ⚠️ 缺少 request-solution-log

### 总结
- 通过: 12/16
- 警告: 3
- 失败: 1
```

## 常见问题

| 问题 | 根因 | 修复 |
|------|------|------|
| agent 不遵循某规则 | 规则埋在长文档中间 | 移到前 20 行或用 hook |
| 规则冲突 | CLAUDE.md 和 AGENTS.md 重复 | 删除一边 |
| skill 没被加载 | description 不匹配触发条件 | 优化 description |
| hook 没触发 | settings.json 配置错误 | 检查 matcher 和 event |
| rules 没按需加载 | 缺少 `paths:` 前言 | 添加 glob 模式 |
| 阻塞规则没执行 | 靠 prompt 不靠 hook | 加 PostToolUse hook |
| 跨会话丢失上下文 | 无 handoff / progress 文档 | 创建交接文档 |

## 参考

- Claude Code 官方: https://code.claude.com/docs/en/memory
- Agent Skills 标准: https://agentskills.io
- Lost in the Middle: https://arxiv.org/abs/2307.03172
