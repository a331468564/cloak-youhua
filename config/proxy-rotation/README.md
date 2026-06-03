<!-- DOC_META
lifecycle:  long-term
audience:   agent, user
write_when: 代理轮换配置变更时更新
read_when:  使用 CloakBrowser 进行 Google 搜索时读取
delete_when: 功能废弃后删除
-->
# Proxy Rotation for CloakBrowser

## 概述

独立的代理轮换系统，专为 CloakBrowser（指纹浏览器）设计。通过独立 mihomo 实例提供代理，实现多 IP 自动轮换 + 仿人浏览行为。

**关键隔离：** 本系统使用独立端口（7898），不影响系统其他软件的代理流量。

## 文件说明

| 文件 | 用途 |
|------|------|
| `cloak-clash.yaml` | mihomo 配置（节点池 + 端口 7898 + API 9091） |
| `README.md` | 本文件，使用说明 |

## 与主 Clash 的隔离

| 项目 | 主 Clash Verge Rev | 独立实例 |
|------|-------------------|---------|
| 端口 | 7897 | 7898 |
| API | 9090 | 9091 |
| 配置 | Clash Verge GUI | cloak-clash.yaml |
| 用途 | 用户日常上网 | CloakBrowser 专用 |

**互不影响。**

## 使用方式

### 自动模式（推荐）

`search_google()` 内置代理管理 + 429 自动轮换：

```python
from scripts.kp_pipeline.cloak_fetcher import search_google

results = search_google("australian restaurant supplier", max_results=5)
# 内部自动：确保 mihomo 运行 → 走 7898 代理 → humanize → 429 自动轮换
```

### 手动模式

```python
from scripts.kp_pipeline.proxy_manager import get_manager

pm = get_manager()
pm.start()                # 启动 mihomo
pm.verify_proxy_ip()      # 获取代理出口 IP
pm.verify_ip_is_proxy()   # 验证代理 IP ≠ 本机 IP
pm.switch_node("JP-03")   # 手动切换到指定节点
pm.switch_node()          # 切换到随机未用节点
pm.get_status()           # 查看状态
pm.stop()                 # 停止 mihomo
```

## 429 自动轮换流程

```
1. search_google() 执行搜索
2. 检测到 429 → 关闭浏览器
3. proxy_manager 切换到新随机节点（Clash API PUT）
4. 等待 10-15 秒冷却
5. 验证新代理 IP
6. 重建浏览器（新 UA/分辨率/语言/时区）
7. 重试搜索

3 次连续 429 → 暂停 5 分钟 → 继续
```

## 节点池

18 个节点，选自用户的高级专线节点（SS 协议）：

| 区域 | 节点数 | 节点名 |
|------|--------|--------|
| 日本 | 5 | JP-01 ~ JP-05 |
| 台湾 | 2 | TW-01 ~ TW-02 |
| 新加坡 | 2 | SG-01 ~ SG-02 |
| 香港 | 4 | HK-01 ~ HK-04 |
| 美国 | 5 | US-01 ~ US-05 |

## 安全说明

- 代理失败时浏览器自动关闭（不回退到直连）
- 独立 mihomo 使用 fake-ip DNS 模式
- 配置文件含代理凭证，已加入 .gitignore
- 每次启动前验证代理 IP ≠ 本机 IP

## 设计文档

详细设计见：`docs/superpowers/specs/2026-05-29-stealth-proxy-rotation-design.md`
