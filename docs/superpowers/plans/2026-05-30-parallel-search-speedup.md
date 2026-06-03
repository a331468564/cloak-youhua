# Parallel Search Speedup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现 `search_google_batch` 并行搜索，100 次搜索从 6.3 分钟降到 1-1.5 分钟（4-5x 提速）

**Architecture:** 关闭 humanize + 3 个 CloakBrowser 实例并行搜索，每个 worker 使用 thread-local 存储独立的浏览器/代理/自适应状态。

**Tech Stack:** Python concurrent.futures, threading.local(), CloakBrowser, mihomo Clash API

---

## File Structure

| File | Action | Responsibility |
|------|--------|---------------|
| `scripts/kp_pipeline/proxy_manager.py` | Modify | 新增 `assign_nodes_to_workers(n)` |
| `scripts/kp_pipeline/cloak_fetcher.py` | Modify | thread-local 重构 + `search_google_single` + `search_google_batch` |

---

### Task 1: proxy_manager — 新增 assign_nodes_to_workers

**Files:**
- Modify: `scripts/kp_pipeline/proxy_manager.py:131-140`

- [ ] **Step 1: 新增 assign_nodes_to_workers 方法**

在 `ProxyManager` 类中，`select_random_node` 方法之后添加：

```python
    def assign_nodes_to_workers(self, n: int) -> list[str]:
        """预分配 n 个不同节点给并行 worker。

        Returns:
            分配的节点名列表，长度 = min(n, 可用节点数)
        """
        available = [node for node in _ALL_NODES if node not in self._used_nodes]
        if len(available) < n:
            self._used_nodes.clear()
            available = _ALL_NODES[:]

        assigned = random.sample(available, min(n, len(available)))
        for node in assigned:
            self._used_nodes.add(node)
            self.switch_node(node)
        return assigned
```

- [ ] **Step 2: 验证语法**

Run: `python -c "import ast; ast.parse(open('scripts/kp_pipeline/proxy_manager.py', encoding='utf-8').read()); print('OK')"`
Expected: OK

- [ ] **Step 3: Commit**

```bash
git add scripts/kp_pipeline/proxy_manager.py
git commit -m "feat: add assign_nodes_to_workers for parallel search"
```

---

### Task 2: cloak_fetcher — thread-local 存储重构

**Files:**
- Modify: `scripts/kp_pipeline/cloak_fetcher.py:38` (全局变量)
- Modify: `scripts/kp_pipeline/cloak_fetcher.py:70-74` (全局状态)
- Modify: `scripts/kp_pipeline/cloak_fetcher.py:136-191` (自适应配置)
- Modify: `scripts/kp_pipeline/cloak_fetcher.py:194-236` (浏览器管理)

- [ ] **Step 1: 替换全局变量为 thread-local**

将文件顶部的全局变量：

```python
_browser = None
_routes = {}
```

和搜索相关的全局状态：

```python
_current_proxy_ip = None
_last_search_time = 0.0
```

以及自适应配置的全局变量：

```python
_current_config = "B"
_consecutive_fail = 0
_consecutive_ok = 0
```

替换为统一的 thread-local 存储：

```python
import threading

_browser = None
_routes = {}

# Thread-local storage for per-worker state (parallel search)
_tls = threading.local()


def _get_tls(key, default=None):
    """获取 thread-local 值，未设置时返回 default。"""
    return getattr(_tls, key, default)


def _set_tls(key, value):
    """设置 thread-local 值。"""
    setattr(_tls, key, value)
```

- [ ] **Step 2: 重构自适应配置为 thread-local**

将 `_current_config`, `_consecutive_fail`, `_consecutive_ok` 改为 thread-local。替换：

```python
def _get_config():
    """获取当前自适应配置。"""
    return _CONFIGS[_current_config]


def _record_result(ok: bool):
    """记录搜索结果，自动切换配置。"""
    global _current_config, _consecutive_fail, _consecutive_ok

    if ok:
        _consecutive_fail = 0
        _consecutive_ok += 1
        if _current_config == "A" and _consecutive_ok >= _RECOVER_THRESHOLD:
            _current_config = "B"
            _consecutive_ok = 0
            print(f"[adaptive] Recovered → Config B (fast)")
    else:
        _consecutive_ok = 0
        _consecutive_fail += 1
        if _current_config == "B" and _consecutive_fail >= _FAIL_THRESHOLD:
            _current_config = "A"
            _consecutive_fail = 0
            print(f"[adaptive] {_FAIL_THRESHOLD} consecutive issues → Config A (safe)")
```

为：

```python
def _get_config():
    """获取当前自适应配置（per-thread）。"""
    cfg_name = _get_tls("config", "B")
    return _CONFIGS[cfg_name]


def _record_result(ok: bool):
    """记录搜索结果，自动切换配置（per-thread）。"""
    cfg_name = _get_tls("config", "B")
    fail = _get_tls("consecutive_fail", 0)
    ok_count = _get_tls("consecutive_ok", 0)

    if ok:
        fail = 0
        ok_count += 1
        if cfg_name == "A" and ok_count >= _RECOVER_THRESHOLD:
            cfg_name = "B"
            ok_count = 0
            print(f"[adaptive] Recovered → Config B (fast)")
    else:
        ok_count = 0
        fail += 1
        if cfg_name == "B" and fail >= _FAIL_THRESHOLD:
            cfg_name = "A"
            fail = 0
            print(f"[adaptive] {_FAIL_THRESHOLD} consecutive issues → Config A (safe)")

    _set_tls("config", cfg_name)
    _set_tls("consecutive_fail", fail)
    _set_tls("consecutive_ok", ok_count)
```

- [ ] **Step 3: 重构 _enforce_search_interval 为 thread-local**

将 `global _last_search_time` 改为 thread-local：

```python
def _enforce_search_interval(min_seconds=None, max_seconds=None):
    """确保两次搜索之间有合理间隔（per-thread）。"""
    cfg = _get_config()
    if min_seconds is None:
        min_seconds = cfg["interval"][0]
    if max_seconds is None:
        max_seconds = cfg["interval"][1]

    last_time = _get_tls("last_search_time", 0.0)
    if last_time > 0:
        elapsed = time.time() - last_time
        target = random.gauss((min_seconds + max_seconds) / 2, 1.0)
        target = max(min_seconds, min(max_seconds, target))
        if elapsed < target:
            time.sleep(target - elapsed)
    _set_tls("last_search_time", time.time())
```

- [ ] **Step 4: 重构 _get_browser 为 thread-local**

将全局 `_browser` 和 `_current_proxy_ip` 改为 thread-local：

```python
def _get_browser(humanize=False):
    """获取 CloakBrowser 实例（per-thread），自动检测代理 IP 变化并重建。"""
    browser = _get_tls("browser")
    current_ip = _get_tls("current_proxy_ip")

    new_ip = _detect_proxy_ip()
    if new_ip and new_ip != current_ip:
        if browser is not None:
            try:
                browser.close()
            except Exception:
                pass
            browser = None
        _set_tls("current_proxy_ip", new_ip)

    if browser is None:
        from cloakbrowser import launch
        kwargs = {
            "headless": True,
            "proxy": {"server": _PROXY_URL},
        }
        if humanize:
            settings = _pick_humanize_settings()
            kwargs["humanize"] = True
            kwargs["human_preset"] = "careful"
            kwargs["locale"] = settings["locale"]
            kwargs["timezone"] = settings["timezone"]
        browser = launch(**kwargs)
        _set_tls("browser", browser)

    return browser


def close_browser():
    """关闭当前线程的浏览器。"""
    browser = _get_tls("browser")
    if browser:
        try:
            browser.close()
        except Exception:
            pass
        _set_tls("browser", None)
```

- [ ] **Step 5: 验证语法**

Run: `python -c "import ast; ast.parse(open('scripts/kp_pipeline/cloak_fetcher.py', encoding='utf-8').read()); print('OK')"`
Expected: OK

- [ ] **Step 6: Commit**

```bash
git add scripts/kp_pipeline/cloak_fetcher.py
git commit -m "refactor: migrate browser/config/interval to thread-local storage"
```

---

### Task 3: cloak_fetcher — 重构 search_google + 新增 search_google_single

**Files:**
- Modify: `scripts/kp_pipeline/cloak_fetcher.py:396-454`

- [ ] **Step 1: 新增 search_google_single（无 humanize）**

在 `search_google` 函数之前添加：

```python
def search_google_single(query, max_results=5, max_retries=3):
    """单次 Google 搜索（无 humanize），自适应配置。

    并行模式下每个 worker 调用此函数。
    """
    from urllib.parse import quote_plus

    pm = get_manager()
    cfg = _get_config()

    for attempt in range(max_retries):
        _enforce_search_interval()

        url = f"https://www.google.com/search?q={quote_plus(query)}&num={max_results}&hl=en"
        text, html, cookies, ua, status, error = cloak_fetch(url, timeout=30, humanize=False)

        if status == 429 or (error and "429" in str(error)):
            print(f"[search_google_single] 429: {query}")
            _record_result(False)
            if pm.handle_429(browser_close_fn=close_browser):
                continue
            else:
                break

        if status == 403:
            print(f"[search_google_single] 403: {query}")
            _record_result(False)
            if pm.handle_429(browser_close_fn=close_browser):
                continue
            else:
                break

        if error or not html:
            _record_result(False)
            return []

        pm.reset_429_counter()

        if cfg["click_sim"] and random.random() < 0.3:
            _simulate_click_first_result(html)

        result_urls = _extract_google_urls(html, max_results)
        _record_result(bool(result_urls))
        return result_urls

    _record_result(False)
    return []
```

- [ ] **Step 2: 重构 search_google 为向后兼容包装器**

将现有 `search_google` 函数体替换为：

```python
def search_google(query, max_results=5, max_retries=3):
    """单次 Google 搜索（向后兼容）。

    内部调用 search_google_single。
    """
    return search_google_single(query, max_results, max_retries)
```

- [ ] **Step 3: 验证语法**

Run: `python -c "import ast; ast.parse(open('scripts/kp_pipeline/cloak_fetcher.py', encoding='utf-8').read()); print('OK')"`
Expected: OK

- [ ] **Step 4: 验证 search_google 仍然工作**

Run: `python -u -c "
import sys; sys.stdout.reconfigure(encoding='utf-8')
from scripts.kp_pipeline.proxy_manager import get_manager
from scripts.kp_pipeline.cloak_fetcher import search_google, close_browser
pm = get_manager(); pm.start()
urls = search_google('restaurant supplier sydney', max_results=3)
print(f'Results: {len(urls)}')
close_browser()
"`
Expected: Results: 2-3

- [ ] **Step 5: Commit**

```bash
git add scripts/kp_pipeline/cloak_fetcher.py
git commit -m "refactor: extract search_google_single from search_google"
```

---

### Task 4: cloak_fetcher — 新增 search_google_batch

**Files:**
- Modify: `scripts/kp_pipeline/cloak_fetcher.py` (在 search_google 之后添加)

- [ ] **Step 1: 新增 search_google_batch 函数**

在 `search_google` 函数之后添加：

```python
def search_google_batch(queries: list[str], max_results=5, workers=3) -> dict[str, list[str]]:
    """并行 Google 搜索。

    每个 worker 使用独立 CloakBrowser 实例 + 独立代理节点。
    无 humanize 模式（极速），自适应降速 per-worker。

    Args:
        queries: 搜索查询列表
        max_results: 每次搜索最大结果数
        workers: 并行 worker 数（默认 3）

    Returns:
        {query: [urls]} 字典
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed

    pm = get_manager()

    # 预分配节点给 workers
    assigned = pm.assign_nodes_to_workers(workers)
    print(f"[batch] Assigned {len(assigned)} nodes: {assigned}")

    # 轮询分配查询给 workers
    worker_queries = [[] for _ in range(workers)]
    for i, query in enumerate(queries):
        worker_queries[i % workers].append(query)

    results = {}
    start = time.time()

    def _worker_search(worker_id, query_list):
        """单个 worker 的搜索任务。"""
        worker_results = {}
        for query in query_list:
            urls = search_google_single(query, max_results)
            worker_results[query] = urls
        return worker_results

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = []
        for wid in range(workers):
            if worker_queries[wid]:
                futures.append(executor.submit(_worker_search, wid, worker_queries[wid]))

        for future in as_completed(futures):
            worker_results = future.result()
            results.update(worker_results)

    elapsed = time.time() - start
    ok = sum(1 for v in results.values() if v)
    print(f"[batch] {ok}/{len(queries)} OK in {elapsed:.1f}s ({elapsed/60:.1f}min)")

    return results
```

- [ ] **Step 2: 更新模块顶部导出**

在文件顶部的 docstring 中添加 `search_google_batch` 到用法示例（可选）。

- [ ] **Step 3: 验证语法**

Run: `python -c "import ast; ast.parse(open('scripts/kp_pipeline/cloak_fetcher.py', encoding='utf-8').read()); print('OK')"`
Expected: OK

- [ ] **Step 4: Commit**

```bash
git add scripts/kp_pipeline/cloak_fetcher.py
git commit -m "feat: add search_google_batch for parallel search"
```

---

### Task 5: 端到端验证 — 并行搜索测试

**Files:**
- None (runtime test only)

- [ ] **Step 1: 小批量并行测试（10 次）**

Run: `python -u -c "
import sys; sys.stdout.reconfigure(encoding='utf-8')
from scripts.kp_pipeline.proxy_manager import get_manager
from scripts.kp_pipeline.cloak_fetcher import search_google_batch, close_browser
pm = get_manager(); pm.start()
queries = ['restaurant supplier sydney', 'hotel furniture melbourne', 'cafe equipment brisbane',
           'kitchen supply perth', 'bar equipment adelaide'] * 2
results = search_google_batch(queries, max_results=3, workers=3)
for q, urls in results.items():
    print(f'  {q[:40]:40s} → {len(urls)} urls')
close_browser()
"`
Expected: 10 results, ~3-5s total (vs ~38s serial)

- [ ] **Step 2: 中批量并行测试（30 次）**

Run: `python -u -c "
import sys; sys.stdout.reconfigure(encoding='utf-8')
from scripts.kp_pipeline.proxy_manager import get_manager
from scripts.kp_pipeline.cloak_fetcher import search_google_batch, close_browser
pm = get_manager(); pm.start()
queries = ['restaurant supplier sydney', 'hotel furniture melbourne', 'cafe equipment brisbane',
           'kitchen supply perth', 'bar equipment adelaide'] * 6
results = search_google_batch(queries, max_results=3, workers=3)
ok = sum(1 for v in results.values() if v)
print(f'Success: {ok}/{len(queries)}')
close_browser()
"`
Expected: 30 results, ~10-15s total (vs ~2min serial)

- [ ] **Step 3: 100 次并行压力测试**

Run: `python -u -c "
import sys; sys.stdout.reconfigure(encoding='utf-8')
from scripts.kp_pipeline.proxy_manager import get_manager
from scripts.kp_pipeline.cloak_fetcher import search_google_batch, close_browser
pm = get_manager(); pm.start()
queries = ['restaurant supplier sydney', 'hotel furniture melbourne', 'cafe equipment brisbane',
           'kitchen supply perth', 'bar equipment adelaide'] * 20
results = search_google_batch(queries, max_results=3, workers=3)
ok = sum(1 for v in results.values() if v)
print(f'Success: {ok}/{len(queries)}')
close_browser()
"`
Expected: 100 results, < 2 minutes, success rate > 95%

- [ ] **Step 4: 验证向后兼容**

Run: `python -u -c "
import sys; sys.stdout.reconfigure(encoding='utf-8')
from scripts.kp_pipeline.proxy_manager import get_manager
from scripts.kp_pipeline.cloak_fetcher import search_google, close_browser
pm = get_manager(); pm.start()
urls = search_google('restaurant supplier sydney', max_results=3)
print(f'search_google still works: {len(urls)} results')
close_browser()
"`
Expected: search_google still works: 2-3 results

- [ ] **Step 5: Commit 最终版本**

```bash
git add scripts/kp_pipeline/cloak_fetcher.py scripts/kp_pipeline/proxy_manager.py
git commit -m "feat: parallel search with 3 workers, 4-5x speedup"
```
