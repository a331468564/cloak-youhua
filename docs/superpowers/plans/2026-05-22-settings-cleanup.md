# Settings.local.json 权限清理 Implementation Plan

> **For agentic workers:** Use the executing-plans skill to implement this plan task-by-task.

**Goal:** 将 198 条精确权限规则压缩到 ~30 条通配符规则，减少 95% 的审批弹窗

**Architecture:** 按工具类型分组通配，保留安全限制，清理一次性垃圾规则

**Tech Stack:** JSON, Claude Code permissions system

---

## 背景知识

### 权限规则格式

```
"Bash(python *)"          ← 通配符，匹配所有 python 开头的命令
"Bash(python -m scripts... --limit 40)"  ← 精确匹配，只匹配这一条
```

- `*` = 匹配任意字符
- `Bash(...)` = 终端命令权限
- `Read(...)` = 读文件权限
- `Write(...)` = 写文件权限
- `Edit(...)` = 编辑文件权限
- `Agent(...)` = 子任务权限
- `WebFetch(domain:...)` = 网页抓取权限
- `WebSearch` = 网页搜索权限
- `Skill(...)` = 技能调用权限

### 安全原则

- 危险命令（`rm`、`taskkill`、`git push --force`）**不通配**，保留 `pre_bash_safety.py` hook 拦截
- 写文件只对项目目录放开，不通配全局

---

## 当前状态分析

### 规则分布（198 条）

| 类别 | 数量 | 说明 |
|------|------|------|
| python 命令 | ~80 条 | 各种 python 脚本、-c 命令、.venv 路径 |
| powershell 命令 | ~15 条 | Token 查询、环境变量操作 |
| npm/npx 命令 | ~10 条 | 包管理、项目创建 |
| git/gh 命令 | ~5 条 | 版本控制 |
| curl 命令 | ~5 条 | HTTP 请求 |
| pip 命令 | ~3 条 | 包安装 |
| cp 命令 | ~10 条 | 一次性文件复制 |
| 其他 Bash | ~20 条 | find, mkdir, echo, xxd, tee 等 |
| Read 权限 | ~15 条 | 已有通配符，基本OK |
| WebFetch/Search | ~5 条 | 已OK |
| Skill | ~2 条 | 已OK |
| Write/Edit/Agent | 0 条 | **缺失，每次都要审批** |

### 可删除的一次性规则（~60 条）

以下规则只用过一次，永远不会再用：
- `cp ~/.claude/projects/.../*.jsonl` （session 文件复制，5 条）
- `cp /e/CC-test/.claude/projects/...` （跨项目复制，2 条）
- `cp /c/Users/Administrator/.codex/...` （codex 文件复制，2 条）
- `echo '{count: 0, ...}' > .rslog_counter.json` （hook 测试，6 条）
- `CLAUDE_PROJECT_DIR="/tmp/..." python ...` （hook 测试，3 条）
- `rm -r /tmp/test_hook_project` （测试清理，1 条）
- 各种 `python -c "import xxx; print(...)"` （库测试，~15 条）
- 各种 `powershell -NoProfile -Command ...` （Token 查询，~12 条）
- `cp "C:/Users/Administrator/.claude/plans/..." ...` （计划文件复制，2 条）
- `xxd "..."` （文件检查，2 条）
- `rm -r /d/antd-components` （已删除项目，1 条）

---

## 最终配置

### 新 settings.local.json 完整内容

```json
{
  "permissions": {
    "allow": [
      "Bash(python *)",
      "Bash(python3 *)",
      "Bash(.venv/Scripts/python *)",
      "Bash(.venv/Scripts/python.exe *)",
      "Bash(pip *)",
      "Bash(.venv/Scripts/pip *)",
      "Bash(.venv/Scripts/pip.exe *)",
      "Bash(git *)",
      "Bash(gh *)",
      "Bash(npm *)",
      "Bash(npx *)",
      "Bash(powershell *)",
      "Bash(curl *)",
      "Bash(find *)",
      "Bash(ls *)",
      "Bash(cat *)",
      "Bash(mkdir *)",
      "Bash(cp *)",
      "Bash(echo *)",
      "Bash(iconv *)",
      "Bash(grep *)",
      "Bash(xxd *)",
      "Bash(tee *)",
      "Bash(netstat *)",
      "Bash(sqlite3 *)",
      "Bash(wmic *)",
      "Read(//c/Users/Administrator/**)",
      "Read(//e/AI/**)",
      "Read(//d/**)",
      "Read(//proc/**)",
      "Read(//tmp/**)",
      "Write(E:/AI/TestProject-v2/**)",
      "Write(e:/AI/TestProject-v2/**)",
      "Edit(E:/AI/TestProject-v2/**)",
      "Edit(e:/AI/TestProject-v2/**)",
      "Agent(*)",
      "WebFetch(domain:google.com)",
      "WebFetch(domain:github.com)",
      "WebFetch(domain:raw.githubusercontent.com)",
      "WebFetch(domain:ui.shadcn.com)",
      "WebSearch",
      "Skill(*)"
    ],
    "additionalDirectories": [
      "D:\\antd-components\\public",
      "D:\\antd-components",
      "C:\\Users\\Administrator\\Desktop",
      "C:\\Users\\Administrator\\.claude",
      "C:\\Users\\Administrator\\.claude\\plans",
      "E:\\AI\\TestProject-v2\\.claude\\hooks",
      "E:\\AI\\TestProject-v2\\.claude"
    ]
  }
}
```

### 规则说明

| 规则 | 覆盖范围 | 替代了多少条 |
|------|----------|-------------|
| `Bash(python *)` | 所有 python 命令 | ~80 条 |
| `Bash(.venv/Scripts/python *)` | 虚拟环境 python | ~15 条 |
| `Bash(powershell *)` | 所有 powershell | ~15 条 |
| `Bash(npm *)` + `Bash(npx *)` | 包管理 | ~10 条 |
| `Bash(git *)` + `Bash(gh *)` | 版本控制 | ~5 条 |
| `Bash(curl *)` | HTTP 请求 | ~5 条 |
| `Write(E:/AI/TestProject-v2/**)` | 项目内写文件 | 0→全覆盖 |
| `Edit(E:/AI/TestProject-v2/**)` | 项目内编辑 | 0→全覆盖 |
| `Agent(*)` | 子任务 | 0→全覆盖 |

### 不通配的命令（需审批）

以下命令保持精确匹配或不通配，由 `pre_bash_safety.py` hook 拦截：
- `rm -rf` / `rm -r` — 危险删除
- `taskkill` — 杀进程
- `git push --force` — 强制推送
- `git reset --hard` — 硬重置
- `git clean -f` — 清理未跟踪文件

---

## 执行步骤

### Task 1: 备份当前配置

**Files:**
- Read: `.claude/settings.local.json`
- Create: `.claude/settings.local.json.bak`

- [ ] **Step 1: 备份**

```bash
cp .claude/settings.local.json .claude/settings.local.json.bak
```

- [ ] **Step 2: 验证备份**

```bash
diff .claude/settings.local.json .claude/settings.local.json.bak
```

Expected: 无输出（文件相同）

### Task 2: 替换配置文件

**Files:**
- Write: `.claude/settings.local.json`

- [ ] **Step 1: 写入新配置**

用上面"最终配置"部分的内容替换整个 `.claude/settings.local.json` 文件。

- [ ] **Step 2: 验证 JSON 格式**

```bash
python -c "import json; json.load(open('.claude/settings.local.json')); print('JSON valid')"
```

Expected: `JSON valid`

### Task 3: 测试验证

- [ ] **Step 1: 测试 python 命令免审批**

运行一个 python 命令，确认不弹审批：
```bash
python --version
```

Expected: 直接显示版本号，无审批弹窗

- [ ] **Step 2: 测试 git 命令免审批**

```bash
git status
```

Expected: 直接显示状态，无审批弹窗

- [ ] **Step 3: 测试写文件免审批**

创建一个测试文件：
```bash
echo "test" > /tmp/test_permission.txt
```

Expected: 直接执行，无审批弹窗

- [ ] **Step 4: 测试危险命令仍被拦截**

尝试一个危险命令（应该被 hook 拦截）：
```bash
rm -rf /tmp/test_nonexistent
```

Expected: 被 `pre_bash_safety.py` 拦截

- [ ] **Step 5: 清理测试文件**

```bash
rm /tmp/test_permission.txt
```

- [ ] **Step 6: 删除备份（可选）**

确认一切正常后：
```bash
rm .claude/settings.local.json.bak
```

---

## 回滚方案

如果新配置有问题，恢复备份：

```bash
cp .claude/settings.local.json.bak .claude/settings.local.json
```
