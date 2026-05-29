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

## 使用方式

### 自动模式（推荐）

在 `keyword_discovery.py` 或 `scheduler.py` 中，代理轮换自动生效：

```python
# keyword_discovery.py 内部调用链
search_google(query)
  → proxy_manager.ensure_running()    # 确保 mihomo 运行
  → cloak_fetcher.search_google()     # CloakBrowser 走 7898 代理
  → 如遇 429 → proxy_manager.rotate() # 自动切换节点
  → 重建浏览器 → 重试
```

### 手动模式

```python
from scripts.kp_pipeline.proxy_manager import ProxyManager

pm = ProxyManager()
pm.start()           # 启动 mihomo
pm.verify_ip()       # 验证代理 IP ≠ 本机 IP
pm.rotate()          # 手动切换到下一个节点
pm.get_current_ip()  # 获取当前代理 IP
pm.stop()            # 停止 mihomo
```

## 节点池

从用户 Clash 配置中复制的节点：

| 区域 | 节点数 | 协议 |
|------|--------|------|
| 日本 | 5 | SS/AnyTLS/Hysteria2 |
| 台湾 | 3 | Trojan/AnyTLS/Hysteria2 |
| 新加坡 | 2 | SS |
| 香港 | 4 | Trojan/AnyTLS/Hysteria2 |
| 美国 | 5 | SS/Hysteria2 |

## 安全说明

- 代理失败时浏览器自动关闭（不回退到直连）
- 独立 mihomo 使用 fake-ip DNS 模式
- 配置文件含代理凭证，已加入 .gitignore
- 每次启动前验证代理 IP ≠ 本机 IP

## 设计文档

详细设计见：`docs/superpowers/specs/2026-05-29-stealth-proxy-rotation-design.md`
