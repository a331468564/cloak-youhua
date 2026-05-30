<!-- DOC_META
lifecycle:  long-term
audience:   agent, user
write_when: 设计方案变更时更新
read_when:  实现并行搜索提速功能时读取
delete_when: 功能废弃后删除
-->
# Parallel Search Speedup Design

**Date:** 2026-05-30
**Status:** Approved
**Goal:** 100 次 Google 搜索从 6.3 分钟降到 1-1.5 分钟（4-5x 提速）

## Problem

当前 Config B 优化后，单次搜索 ~3.8s，瓶颈是 humanize 模式的内置延迟（~2-3s）。串行模式下吞吐量有上限。

## Solution

**方案 C：关闭 humanize + 并行多实例**

- 去掉 humanize 模式（节省 ~2-3s/次）
- 3 个 CloakBrowser 实例并行搜索
- 每个实例绑定独立代理节点
- 自适应降速：单个 worker 连续失败时自动开启 humanize

## Architecture

```
search_google_batch(queries, workers=3)
  │
  ├─ ThreadPoolExecutor(max_workers=3)
  │
  ├─ Worker 1 → CloakBrowser(humanize=False) → proxy=JP-01 → queries 1,4,7...
  ├─ Worker 2 → CloakBrowser(humanize=False) → proxy=US-01 → queries 2,5,8...
  └─ Worker 3 → CloakBrowser(humanize=False) → proxy=HK-01 → queries 3,6,9...
```

## Components

### 1. search_google_batch (新增)

**文件：** `scripts/kp_pipeline/cloak_fetcher.py`

```python
def search_google_batch(queries: list[str], max_results=5, workers=3) -> dict[str, list[str]]:
    """并行 Google 搜索。

    每个 worker 使用独立浏览器实例 + 独立代理节点。
    返回 {query: [urls]} 字典。
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed

    results = {}

    def _search_one(query):
        return query, search_google_single(query, max_results)

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(_search_one, q): q for q in queries}
        for future in as_completed(futures):
            query, urls = future.result()
            results[query] = urls

    return results
```

### 2. search_google_single (从现有 search_google 重构)

现有 `search_google` 重命名为 `search_google_single`，去掉 humanize：

```python
def search_google_single(query, max_results=5, max_retries=3):
    """单次 Google 搜索，无 humanize，自适应配置。"""
    ...
    text, html, cookies, ua, status, error = cloak_fetch(url, timeout=30, humanize=False)
    ...
```

### 3. search_google (保留，向后兼容)

```python
def search_google(query, max_results=5, max_retries=3):
    """单次搜索（向后兼容）。内部调用 search_google_single。"""
    return search_google_single(query, max_results, max_retries)
```

### 4. Worker 隔离

每个 worker 需要：
- 独立的 CloakBrowser 实例（独立 cookies/指纹）
- 独立的代理节点（不同 IP）
- 独立的自适应状态（间隔/模式）

实现方式：
- `_get_browser()` 改为 thread-local 存储（每个线程独立浏览器实例）
- proxy_manager 新增 `assign_nodes_to_workers(n)` 方法，预分配 n 个不同节点
- 每个 worker 线程启动时绑定一个预分配节点

### 5. 429 恢复（per-worker）

```
Worker 触发 429:
  1. 关闭该 worker 的浏览器
  2. 通过 proxy_manager 切换到新节点
  3. 等待 10-15s 冷却
  4. 重建浏览器（humanize=False）
  5. 该 worker 继续下一个查询
  6. 其他 worker 不受影响

自适应降速（per-worker）:
  连续 3 次失败 → 该 worker 开启 humanize + 间隔 3-5s
  连续 20 次成功 → 该 worker 关闭 humanize + 间隔 2-4s
```

## Expected Performance

| 指标 | 当前 (Config B) | 方案 C |
|------|----------------|--------|
| 单次搜索 | 3.8s | ~1.5-2s |
| 100 次串行 | 6.3 分钟 | ~2.5-3 分钟 |
| 100 次并行(3w) | - | **~1-1.5 分钟** |
| 提速 | 1.0x | **4-5x** |
| 429 风险 | 极低 | 低-中（自适应恢复） |

## File Changes

| File | Type | Description |
|------|------|-------------|
| `scripts/kp_pipeline/cloak_fetcher.py` | Modify | 新增 `search_google_batch`，重构 `search_google` → `search_google_single` |
| `scripts/kp_pipeline/proxy_manager.py` | Modify | 新增 `assign_nodes_to_workers` 方法 |

## Success Criteria

1. `search_google_batch(100 queries, workers=3)` 完成时间 < 2 分钟
2. 单个 worker 429 后自动恢复，不影响其他 worker
3. 现有 `search_google` 接口不变，向后兼容
4. 自适应降速在 per-worker 粒度工作
