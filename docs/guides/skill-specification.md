<!-- DOC_META
lifecycle:  long-term
audience:   both
write_when: Skill 规范或最佳实践变更时更新
read_when:  创建或审查 Claude Code Skills 时读取
delete_when: 不删除
-->
# Skill 规范指南

> 基于 Claude Code 官方文档 + Agent Skills 标准（agentskills.io）+ 学术研究 + V2/V3 项目实践。
> 最后更新：2026-05-29

---

## 1. Skill 是什么

**一句话：** Skill 就是给 Claude 写的"操作手册"。

- CLAUDE.md = 公司规章制度（每次上班都要看）
- Skill = 具体操作手册（需要时才拿出来看）

解决的问题：每次粘贴同样 instructions、操作步骤太长、Claude 忘记规则。

## 2. 文件位置

| 范围 | 路径 | 适用 |
|------|------|------|
| 全局 | `~/.claude/skills/<skill名>/SKILL.md` | 所有项目 |
| 项目 | `.claude/skills/<skill名>/SKILL.md` | 当前项目 |

**原则：** 通用放全局，项目特定放项目里。

## 3. 最简结构

```
my-skill/
└── SKILL.md        ← 必须
```

## 4. 完整目录结构

```
my-skill/
├── SKILL.md           # 主指令（< 500 行）
├── reference.md       # 详细参考（按需加载）
├── examples/          # 示例输出
│   └── sample.md
└── scripts/           # 可执行脚本
    └── validate.sh
```

**原则：** SKILL.md 只放概览和导航，详细参考拆到 reference.md。

## 5. SKILL.md 格式

```markdown
---
description: Use when the user says "XXX" or asks to do YYY.
allowed-tools:
  - Bash
  - Read
  - Write
---

<!-- DOC_META
lifecycle:  long-term
audience:   agent
write_when: 功能变更时更新
read_when:  触发条件满足时
delete_when: 永不删除
-->

# Skill 名称

## Overview
核心原则，1-2 句话。

## When to Use
触发条件和症状。

## Steps
1. 第一步
2. 第二步
3. 第三步

## Common Mistakes
常见错误和修复。
```

## 6. Frontmatter 完整规范

```yaml
---
name: my-skill                    # 显示名（可选，默认取目录名）
description: >                    # 触发条件（推荐必填）
  Use when the user says "X" or asks to do Y.
when_to_use: >                    # 额外触发上下文（可选）
  Also triggers on keywords like "Z", "W".
allowed-tools:                    # 预授权工具（可选）
  - Bash
  - Read
  - Write
  - Grep
  - Glob
disallowed-tools:                 # 禁用工具（可选）
  - AskUserQuestion
disable-model-invocation: true    # 只能用户手动触发（可选）
user-invocable: false             # 只能 Claude 自动触发（可选）
model: opus                       # 模型覆盖（可选）
effort: high                      # 推理强度（可选）
context: fork                     # 在子 agent 中运行（可选）
agent: Explore                    # 子 agent 类型（可选）
paths:                            # 路径限制（可选）
  - "scripts/**"
argument-hint: "[issue-number]"   # 参数提示（可选）
arguments:                        # 命名参数（可选）
  - issue
  - branch
---
```

### 关键字段说明

**`description`** — 最重要的字段。
- 只写触发条件，不写流程摘要
- 格式："Use when..."
- 截断到 1,536 字符
- **写流程摘要会导致 Claude 跳过读完整文件**

**`allowed-tools`** — 预授权工具列表。
- 不限制可用工具，只是免确认
- 格式：`Bash(git add *)` 支持 glob 模式

**`disable-model-invocation`** — 控制谁可以触发。
- `true`：只有用户可以 `/name` 触发
- `false`（默认）：用户和 Claude 都可以触发
- 适用：部署、发消息等有副作用的操作

**`context: fork`** — 在子 agent 中运行。
- 隔离上下文，不影响主对话
- 搭配 `agent` 字段指定子 agent 类型

## 7. 动态上下文注入

加载时执行 shell 命令，将输出注入内容：

```markdown
## 当前状态

!`git diff HEAD`

## 数据统计

```!
wc -l data/*.csv
ls -la reports/
```
```

- `` !`command` `` 在 Claude 看到内容之前执行
- 输出替换占位符
- 禁用：设置 `"disableSkillShellExecution": true`

## 8. 参数替换

```yaml
---
name: fix-issue
arguments: [issue]
---

Fix GitHub issue $issue following our coding standards.
```

调用 `/fix-issue 123` → Claude 收到 "Fix GitHub issue 123..."

| 变量 | 说明 |
|------|------|
| `$ARGUMENTS` | 所有参数 |
| `$ARGUMENTS[N]` | 第 N 个参数（0-indexed） |
| `$N` | `$ARGUMENTS[N]` 的简写 |
| `$name` | 命名参数 |
| `${CLAUDE_SESSION_ID}` | 当前会话 ID |
| `${CLAUDE_SKILL_DIR}` | Skill 目录路径 |

## 9. Hooks vs Skills vs Rules

| 维度 | Rules | Skills | Hooks |
|------|-------|--------|-------|
| 加载时机 | 每次/按需 | 按需 | 事件触发 |
| 执行方式 | Claude 自愿遵守 | Claude 自愿遵守 | **强制执行** |
| 适用场景 | 约束、规范 | 流程、操作 | 安全、阻塞 |
| 可以绕过？ | 是 | 是 | **否** |

**必须用 hook 的场景：**
- 数据安全（append-only、禁止删除）
- 危险命令拦截（rm -rf、git reset --hard）
- 连续失败检测
- 文件清理检查

## 10. Invocation 控制矩阵

| Frontmatter | 用户可调用 | Claude 可调用 | 加载行为 |
|-------------|-----------|--------------|----------|
| （默认） | 是 | 是 | description 始终在 context，正文按需 |
| `disable-model-invocation: true` | 是 | 否 | description 不在 context，用户调用时加载 |
| `user-invocable: false` | 否 | 是 | description 始终在 context，正文按需 |

## 11. 生命周期

- Skill 内容加载后**在整个会话中保持**
- 自动压缩时保留最近调用的 skill 的前 5,000 token
- 所有保留的 skill 共享 25,000 token 预算
- 如果 skill 在后续回合"失效"，重新调用即可恢复

## 12. DOC_META 元数据

HTML 注释格式，零 token 成本：

```markdown
<!-- DOC_META
lifecycle:  long-term | temporary
audience:   agent | human | both
write_when: 触发条件
read_when:  读取条件
delete_when: 删除条件
-->
```

HTML 注释在注入 context 时被剥离，不消耗 token。

## 13. 学术依据

| 研究 | 年份 | 结论 | 对 Skill 的启示 |
|------|------|------|----------------|
| Lost in the Middle | TACL 2023 | 遵循指令呈 U 型曲线 | 关键规则放文件开头 |
| RULER Benchmark | COLM 2024 | 声称 32K 上下文的模型一半达不到 | 文件越短越好 |
| NoLiMa | ICML 2025 | 11/13 模型在 32K token 时性能下降 >50% | 控制 skill 总 token 数 |

## 14. 检查清单

创建或审查 skill 时，逐项检查：

- [ ] description 只写触发条件，不写流程摘要
- [ ] description < 1,536 字符
- [ ] SKILL.md < 500 行
- [ ] 关键指令在前 20 行
- [ ] 有 DOC_META 元数据
- [ ] 有 allowed-tools（如果需要免确认）
- [ ] 多步流程有明确的步骤编号
- [ ] 错误处理有具体指令（不是"处理错误"）
- [ ] 详细参考拆到 reference.md
- [ ] 用 `${CLAUDE_SKILL_DIR}` 引用同目录文件

## 15. V3 项目 Skill 清单

| Skill | 路径 | 触发方式 | 内容 |
|-------|------|---------|------|
| kp-discovery | `.claude/skills/kp-discovery/` | `/kp-discovery` | KP 管线三阶段 |
| keyword-discovery | `.claude/skills/keyword-discovery/` | `/keyword-discovery` | 关键词发现流程 |
| spec-checker | `~/.claude/skills/spec-checker/` | `/spec-checker` | 指令文件规范检查 |
| australia-lead-kp-research | `skills/australia-lead-kp-research/` | 自动匹配 | 旧 skill，保留兼容 |

---

## 参考资料

| 来源 | URL |
|------|-----|
| Claude Code Skills 文档 | https://code.claude.com/docs/en/skills |
| Agent Skills 标准 | https://agentskills.io |
| Lost in the Middle | https://arxiv.org/abs/2307.03172 |
| spec-checker | https://github.com/a331468564/spec-checker |
