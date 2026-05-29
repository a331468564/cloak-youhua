<!-- DOC_META
lifecycle:  long-term
audience:   user
write_when: 功能变更时更新
read_when:  使用前阅读
delete_when: 仓库废弃后删除
-->
# CloakBrowser Proxy Rotation

CloakBrowser 多节点轮换 + 仿人浏览，用于绕过 Google 429 限流的大规模搜索采集。

## 核心功能

- **多 IP 轮换**：18 个代理节点（JP/TW/SG/HK/US），429 时自动切换
- **仿人浏览**：humanize 模式 + 随机搜索间隔（5-10s 高斯分布）
- **环境随机化**：UA/分辨率/语言/时区每次浏览器重建时随机
- **完全隔离**：独立 mihomo 进程（端口 7898），不影响用户日常代理

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 准备 mihomo 二进制
#    下载: https://github.com/MetaCubeX/mihomo/releases
#    放到任意目录，修改 proxy_manager.py 中的 MIHOMO_BIN 路径

# 3. 配置代理节点
cp config/cloak-clash.yaml.example config/cloak-clash.yaml
# 编辑 cloak-clash.yaml，填入你的代理节点信息

# 4. 复制 geodata 文件（mihomo 需要）
#    从你的 Clash 安装目录复制 Country.mmdb, geoip.dat, geosite.dat
#    到 config/ 目录
```

## 使用

```python
from proxy_manager import get_manager
from cloak_fetcher import search_google, close_browser

# 启动代理
pm = get_manager()
pm.start()

# Google 搜索（自动代理轮换 + 仿人行为）
results = search_google("australian restaurant supplier", max_results=5)
for url in results:
    print(url)

close_browser()
```

## 架构

```
search_google(query)
  │
  ├─ proxy_manager.py
  │    ├─ 确保 mihomo 运行（端口 7898 / API 9091）
  │    ├─ 429 检测 → Clash API 切换节点 → 冷却 10-15s
  │    └─ 3 次连续 429 → 暂停 5 分钟
  │
  ├─ cloak_fetcher.py
  │    ├─ CloakBrowser humanize=True, careful preset
  │    ├─ proxy=http://127.0.0.1:7898
  │    ├─ 搜索间隔 5-10s（高斯分布）
  │    └─ 30% 概率点击第一个结果（仿人行为）
  │
  └─ 返回结果 URL 列表
```

## 文件说明

| 文件 | 用途 |
|------|------|
| `proxy_manager.py` | mihomo 进程管理 + Clash API 节点轮换 + 429 处理 |
| `cloak_fetcher.py` | CloakBrowser 抓取 + Google 搜索 + humanize |
| `config/cloak-clash.yaml.example` | mihomo 配置模板（复制为 cloak-clash.yaml 后填入节点） |
| `SKILL.md` | 详细技术文档：参数调优、扩展方案、操作指南 |

## 配置要点

### proxy_manager.py

```python
MIHOMO_BIN = r"D:\Clash Verge\verge-mihomo.exe"  # 改为你的 mihomo 路径
CONFIG_PATH = Path(__file__).parent / "config" / "cloak-clash.yaml"

# 节点池（与 cloak-clash.yaml 中的 proxy-groups 对应）
REGIONS = {
    "JP": ["JP-01", "JP-02", "JP-03", "JP-04", "JP-05"],
    "TW": ["TW-01", "TW-02"],
    "SG": ["SG-01", "SG-02"],
    "HK": ["HK-01", "HK-02", "HK-03", "HK-04"],
    "US": ["US-01", "US-02", "US-03", "US-04", "US-05"],
}
```

### cloak_fetcher.py

```python
# 搜索间隔（秒，高斯分布）
_enforce_search_interval(min_seconds=5.0, max_seconds=10.0)

# UA 池（10+ 真实 Chrome/Edge UA）
_UA_POOL = [...]

# 语言/时区池
_LOCALE_PROFILES = [
    {"locale": "en-AU", "timezone": "Australia/Sydney"},
    {"locale": "en-US", "timezone": "America/New_York"},
    {"locale": "zh-CN", "timezone": "Asia/Shanghai"},
]
```

## 详细文档

见 [SKILL.md](SKILL.md)：设计思路、可配置参数、扩展技术、操作指南。
