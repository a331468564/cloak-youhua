<!-- DOC_META
lifecycle:  long-term
audience:   agent, user
write_when: 设计方案变更时更新
read_when:  实现代理轮换功能时读取
delete_when: 功能废弃后删除
-->
# Multi-IP Proxy Rotation with Humanized Browsing

**Date:** 2026-05-29
**Status:** Draft
**Scope:** CloakBrowser 仿人多IP轮换方案，用于关键词发现的 Google 搜索

## Problem

Google 429 rate limit blocks keyword discovery. Current setup uses a single proxy IP (via Clash Verge Rev port 7897). After ~75 searches in Run 20, the IP was rate-limited. Running 107 keywords in the scheduler all returned 0 results.

**Root cause:** Single IP, no human-like browsing behavior, no delays between searches.

**User constraints:**
- IP rotation must NOT affect other software using Google (Clash SDK DNS group is shared)
- Real IP must be protected at all times
- Balanced mode: 5-10s per search, key human behaviors enabled

## Architecture

```
CloakBrowser (humanize=True, careful preset)
  │ proxy={"server": "http://127.0.0.1:7898"}
  ▼
Independent mihomo instance (verge-mihomo.exe)
  Port: 7898 (HTTP) / API: 9091
  Config: config/cloak-clash.yaml
  Nodes: copied from user's Clash config (JP/TW/SG/HK/US)
  ▼
Proxy node pool (trojan/ss/hysteria2)
  Rotation: 429 detect → API switch node → rebuild browser
```

**Key isolation:** CloakBrowser uses port 7898 (not the user's main 7897). Independent mihomo process + config. User's main Clash Verge Rev is untouched.

## Components

### 1. Independent Clash Instance (`config/cloak-clash.yaml`)

Standalone mihomo config with (binary: `D:\Clash Verge\verge-mihomo.exe`):
- `mixed-port: 7898` (HTTP proxy for CloakBrowser)
- `external-controller: 127.0.0.1:9091` (API for node rotation)
- Proxy nodes copied from user's Clash config (JP/TW/SG/HK/US)
- `mode: select` proxy group for manual control
- `dns.enable: true` with `fake-ip` mode (DNS privacy)
- `log-level: warning` (no search content in logs)

### 2. Proxy Manager (`scripts/kp_pipeline/proxy_manager.py`)

New module responsible for:
- Starting/stopping the independent mihomo subprocess
- Clash API calls to switch nodes (`PUT /proxies/:name`)
- 429 detection and automatic node rotation
- IP verification before each session

**API interaction:**
```
GET  http://127.0.0.1:9091/proxies          → list available nodes
GET  http://127.0.0.1:9091/proxies/:name     → get current selection
PUT  http://127.0.0.1:9091/proxies/:name     → switch node {"name": "..."}
GET  http://127.0.0.1:9091/providers/proxies → get proxy provider info
```

### 3. Humanized Browsing Layer (in `cloak_fetcher.py`)

**Balanced mode settings:**

| Dimension | Setting |
|-----------|---------|
| Browser privacy | CloakBrowser built-in (canvas/webgl/font randomization) |
| Humanize | `humanize=True`, `human_preset='careful'` |
| Typing | 70±40ms/key, 10% pause, 2% mistype |
| Mouse | Bezier curve + overshoot + wobble |
| Scroll | Acceleration/deceleration + 10% overshoot |
| Idle | 3-8s random between searches |
| Search interval | `random.gauss(6, 2)` seconds (normal distribution) |

**Additional dimensions:**

| Dimension | Strategy |
|-----------|----------|
| UA rotation | Random from 10+ real Chrome/Edge UA pool, changes per browser restart |
| Screen resolution | Random from [1920x1080, 2560x1440, 1366x768, 1440x900] |
| Language/timezone | Random from [en-AU/Australia/Sydney, en-US/America/New_York, zh-CN/Asia/Shanghai] |
| Search behavior | 30% chance to visit first result URL (via `cloak_fetch`), wait 3-5s, then continue. Simulates reading a result before refining the search. |
| Cookie isolation | Independent browser context per IP session (new context = new cookies) |
| Accept-Language | Matches locale setting (set via Chromium `--lang` flag) |

### 4. Rotation Logic

```
1. Start → select random node → verify IP ≠ local IP → begin search
2. During search → detect HTTP 429 from Google
3. On 429:
   a. Close browser
   b. Switch to next random node via Clash API
   c. Wait 10-15s (cool-down)
   d. Verify new IP ≠ previous IP
   e. Rebuild browser with new profile (UA/resolution/locale)
   f. Resume search
4. After 3 consecutive 429s across different nodes:
   a. Pause 5 minutes
   b. Retry with random node
5. All nodes exhausted → report remaining keywords, stop
```

### 5. IP Protection

| Risk | Mitigation |
|------|------------|
| Proxy drops, real IP exposed | Browser closes immediately on proxy failure (no fallback to direct) |
| WebRTC exposure | CloakBrowser Chromium privacy mode disables WebRTC |
| DNS exposure | Independent mihomo uses fake-ip DNS mode |
| Process residue | Script exits: force `close_browser()` + terminate mihomo subprocess |
| Config file exposure | `config/cloak-clash.yaml` in .gitignore (contains proxy credentials) |
| Log exposure | mihomo log-level: warning (no search content) |
| IP verification | Before each session: fetch httpbin.org/ip via proxy, confirm ≠ local IP |

## File Changes

| File | Type | Description |
|------|------|-------------|
| `config/cloak-clash.yaml` | New | Independent mihomo config (nodes + port 7898 + API 9091) |
| `scripts/kp_pipeline/proxy_manager.py` | New | mihomo process management + Clash API rotation + 429 handling |
| `scripts/kp_pipeline/cloak_fetcher.py` | Modify | Proxy → 7898 + humanize + UA/resolution/locale rotation + IP verification |
| `scripts/keyword_scheduler/scheduler.py` | Keep | Existing pre-flight + 5s delay + 3-empty-exit (already done) |
| `.gitignore` | Modify | Add `config/cloak-clash.yaml` |

## Node Pool

Selected from user's Clash config:

| Region | Nodes | Protocol |
|--------|-------|----------|
| Japan | 日本-01~05 | SS/AnyTLS/Hysteria2 |
| Taiwan | 台湾-01~03 | Trojan/AnyTLS/Hysteria2 |
| Singapore | 新加坡-01~02 | SS |
| Hong Kong | 香港-01~04 | Trojan/AnyTLS/Hysteria2 |
| US | 美国-01~05 | SS/Hysteria2 |

Total: 19 nodes. Each 429 rotation picks a random unused node.

## Success Criteria

1. Google search returns results (not 429) through the proxy
2. Scheduler can run 8+ keywords without hitting 429
3. On 429, automatic rotation recovers within 30 seconds
4. User's main Clash Verge Rev traffic is unaffected
5. Real IP never appears as httpbin.org/ip result through CloakBrowser
