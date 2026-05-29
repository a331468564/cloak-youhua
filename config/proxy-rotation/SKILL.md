<!-- DOC_META
lifecycle:  long-term
audience:   agent, user
write_when: 代理轮换配置或技术变更时更新
read_when:  需要了解代理轮换设计思路、参数调优、或扩展功能时读取
delete_when: 功能废弃后删除
-->
# CloakBrowser 多节点轮换与仿人浏览

## Use when

需要对 CloakBrowser 的代理策略、仿人行为、节点轮换进行配置、调优或扩展时使用本指南。

---

## 设计思路

### 问题背景

大规模数据采集场景中，目标站点会通过以下方式限制自动化访问：
- **速率限制**（HTTP 429）：单 IP 短时间内请求过多
- **行为检测**：请求间隔固定、无鼠标/滚动行为
- **环境检测**：浏览器指纹异常、WebRTC/DNS 暴露真实地址

### 解决思路

```
单 IP + 无延迟 + 无行为 → 被限制
     ↓ 改进
多 IP 轮换 + 随机延迟 + 仿人行为 → 持续可用
```

**三层防护：**

| 层级 | 策略 | 效果 |
|------|------|------|
| 网络层 | 多节点轮换，429 时自动切换 | 分散请求，单节点被限不影响整体 |
| 行为层 | 仿人打字/鼠标/滚动/闲置 | 请求模式接近真人操作 |
| 环境层 | UA/分辨率/语言/时区随机化 | 每次访问呈现不同设备特征 |

### 隔离原则

代理轮换系统必须与用户日常网络环境隔离：
- 独立代理端口（7898），不走系统代理（7897）
- 独立进程（mihomo），不影响主代理软件
- 独立配置文件，凭证不提交到代码仓库

---

## 可配置参数

### 1. 代理节点配置

**配置文件：** `config/proxy-rotation/cloak-clash.yaml`

```yaml
# 节点选择策略
proxy-groups:
  - name: CLOAK-GOOGLE
    type: select          # select=手动选 / url-test=自动选最快 / fallback=故障转移
    proxies:
      - Japan-01
      - Taiwan-01
      - Singapore-01
      # 添加更多节点...
```

**可调参数：**

| 参数 | 说明 | 推荐值 |
|------|------|--------|
| `type` | 节点选择策略 | `select`（可控）或 `url-test`（自动） |
| `url` | 延迟测试地址 | `http://www.gstatic.com/generate_204` |
| `interval` | 自动测试间隔（秒） | `300`（5 分钟） |
| `tolerance` | 延迟容差（ms） | `50` |

### 2. 仿人行为参数

**配置位置：** `scripts/kp_pipeline/cloak_fetcher.py` 中的 `HumanConfig`

```python
from cloakbrowser.human import HumanConfig

config = HumanConfig(
    # 打字行为
    typing_delay=70,              # 平均按键间隔（ms）
    typing_delay_spread=40,       # 间隔随机范围（ms）
    typing_pause_chance=0.1,      # 打字暂停概率
    typing_pause_range=(400, 1000),  # 暂停时长范围（ms）
    mistype_chance=0.02,          # 打字错误概率

    # 鼠标行为
    mouse_steps_divisor=8,        # 移动步数除数（越大越慢）
    mouse_min_steps=25,           # 最少移动步数
    mouse_max_steps=80,           # 最多移动步数
    mouse_wobble_max=1.5,         # 鼠标抖动幅度（px）
    mouse_overshoot_chance=0.15,  # 鼠标过冲概率
    mouse_overshoot_px=(3, 6),    # 过冲距离范围（px）

    # 滚动行为
    scroll_delta_base=(80, 130),  # 基础滚动量
    scroll_overshoot_chance=0.1,  # 滚动过冲概率
    scroll_settle_delay=(300, 600),  # 滚动稳定延迟（ms）

    # 闲置行为
    idle_drift_px=3,              # 闲置时鼠标漂移距离（px）
    idle_pause_range=(300, 1000), # 闲置暂停范围（ms）
)
```

**调优建议：**

| 场景 | 调整方向 |
|------|----------|
| 需要更快响应 | 降低 `typing_delay`、`mouse_min_steps`、`scroll_settle_delay` |
| 需要更自然 | 提高 `mouse_overshoot_chance`、`mistype_chance`、`idle_drift_px` |
| 目标站点检测严格 | 使用 `careful` preset，增加所有延迟值 |

### 3. 设备环境随机化

```python
# UA 池（10+ 真实 Chrome/Edge 版本）
UA_POOL = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0",
    # 更多 UA...
]

# 屏幕分辨率池
RESOLUTION_POOL = [
    (1920, 1080), (2560, 1440), (1366, 768),
    (1440, 900), (1536, 864), (1280, 720),
]

# 语言/时区池
LOCALE_POOL = [
    {"locale": "en-AU", "timezone": "Australia/Sydney"},
    {"locale": "en-US", "timezone": "America/New_York"},
    {"locale": "en-GB", "timezone": "Europe/London"},
]
```

### 4. 节点轮换策略

**配置位置：** `scripts/kp_pipeline/proxy_manager.py`

```python
# 轮换触发条件
ROTATION_TRIGGERS = {
    "http_429": True,          # 遇到 429 立即轮换
    "consecutive_empty": 3,    # 连续 N 次空结果轮换
    "requests_per_node": 20,   # 每节点最多请求数
    "time_per_node": 300,      # 每节点最多使用时间（秒）
}

# 轮换冷却
ROTATION_COOLDOWN = {
    "switch_delay": (10, 15),  # 切换后等待时间（秒）
    "pause_after_3_fail": 300, # 连续 3 个节点失败后暂停（秒）
}
```

### 5. 搜索间隔策略

```python
import random

# 正态分布间隔（均值 6 秒，标准差 2 秒）
delay = max(2, random.gauss(6, 2))

# 均匀分布间隔（3-8 秒）
delay = random.uniform(3, 8)

# 递增间隔（越搜越慢）
delay = base_delay + (keyword_index * 0.5)
```

---

## 扩展技术

### 1. 代理协议支持

独立 mihomo 实例支持以下协议：

| 协议 | 特点 | 适用场景 |
|------|------|----------|
| SS (Shadowsocks) | 轻量、快速 | 低延迟需求 |
| Trojan | 伪装 HTTPS 流量 | 高隐蔽性需求 |
| Hysteria2 | UDP 加速、高吞吐 | 大量数据传输 |
| AnyTLS | TLS 伪装 | 高隐蔽性需求 |

### 2. DNS 隐私保护

```yaml
# cloak-clash.yaml 中的 DNS 配置
dns:
  enable: true
  enhanced-mode: fake-ip      # 使用假 IP，防止 DNS 暴露
  fake-ip-range: 198.18.0.0/16
  nameserver:
    - 8.8.8.8                 # Google DNS
    - 1.1.1.1                 # Cloudflare DNS
```

### 3. WebRTC 隐私保护

CloakBrowser 基于 Chromium stealth 模式，默认禁用 WebRTC。如需额外保护：

```python
# 启动参数中禁用 WebRTC
browser = launch(
    headless=True,
    proxy={"server": "http://127.0.0.1:7898"},
    args=["--disable-webrtc", "--disable-webrtc-multiple-routes"]
)
```

### 4. Cookie 隔离策略

```python
# 每个 IP 会话使用独立 context
context = browser.new_context(
    proxy={"server": "http://127.0.0.1:7898"},
    # 新 context = 新 cookies = 新会话
)
page = context.new_page()
```

### 5. 请求头随机化

```python
# Accept-Language 与 locale 一致
headers = {
    "Accept-Language": "en-AU,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}
```

---

## 操作指南

### 启动代理轮换系统

```python
from scripts.kp_pipeline.proxy_manager import ProxyManager

pm = ProxyManager()
pm.start()           # 启动独立 mihomo 实例
pm.verify_ip()       # 验证代理 IP ≠ 本机 IP
print(pm.get_current_ip())  # 查看当前出口 IP
```

### 手动切换节点

```python
pm.rotate()          # 切换到下一个随机节点
pm.rotate("Japan-01")  # 切换到指定节点
```

### 查看节点状态

```python
nodes = pm.list_nodes()      # 列出所有可用节点
current = pm.get_current_node()  # 当前使用的节点
latency = pm.test_latency()  # 测试各节点延迟
```

### 集成到搜索流程

```python
from scripts.kp_pipeline.cloak_fetcher import search_google, close_browser

# search_google 内部自动处理代理轮换
results = search_google("restaurant group Sydney", max_results=5)

# 用完关闭浏览器
close_browser()
```

---

## 设计文档

详细设计见：`docs/superpowers/specs/2026-05-29-stealth-proxy-rotation-design.md`
