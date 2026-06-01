"""域名缓存系统。

功能：
1. 记录访问过的域名，B区跳过已访问的
2. 保存 cookies/UA，A区复用
3. 定期清理（阈值 5000 + 30 天过期）

缓存位置：E:/cache/domain_cache.json
"""

import json
import time
from datetime import datetime, timedelta
from pathlib import Path

# 缓存配置
_CACHE_DIR = Path("E:/cache")
_CACHE_FILE = _CACHE_DIR / "domain_cache.json"
_MAX_ENTRIES = 5000       # 最大缓存条目
_MAX_AGE_DAYS = 30        # 超过 30 天自动过期

_cache = {}  # {domain: {"visited": str, "valid": bool, "cookies": [...], "ua": str, "ts": float}}
_loaded = False


def _load():
    """加载缓存文件。"""
    global _cache, _loaded
    if _loaded:
        return
    if _CACHE_FILE.exists():
        try:
            _cache = json.loads(_CACHE_FILE.read_text(encoding="utf-8"))
        except Exception:
            _cache = {}
    _loaded = True


def _save():
    """保存缓存文件。"""
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    _CACHE_FILE.write_text(json.dumps(_cache, ensure_ascii=False, indent=2), encoding="utf-8")


def is_visited(domain: str) -> bool:
    """检查域名是否已访问过。"""
    _load()
    return domain in _cache


def is_valid(domain: str) -> bool:
    """检查域名是否是有效公司（上次访问确认过）。"""
    _load()
    entry = _cache.get(domain)
    return entry.get("valid", False) if entry else False


def mark_visited(domain: str, valid: bool = False, cookies: list = None, ua: str = ""):
    """标记域名已访问。

    Args:
        domain: 域名
        valid: 是否是有效公司
        cookies: 浏览器 cookies（A区复用）
        ua: User-Agent（A区复用）
    """
    _load()
    _cache[domain] = {
        "visited": datetime.now().isoformat(timespec="seconds"),
        "valid": valid,
        "cookies": cookies[:20] if cookies else [],  # 最多保存 20 个
        "ua": ua,
        "ts": time.time(),
    }
    _save()
    _maybe_cleanup()


def get_cookies(domain: str) -> tuple[list, str]:
    """获取域名的缓存 cookies 和 UA。A区复用。"""
    _load()
    entry = _cache.get(domain)
    if entry:
        return entry.get("cookies", []), entry.get("ua", "")
    return [], ""


def get_stats() -> dict:
    """返回缓存统计。"""
    _load()
    total = len(_cache)
    valid = sum(1 for v in _cache.values() if v.get("valid"))
    return {
        "total": total,
        "valid": valid,
        "invalid": total - valid,
        "file": str(_CACHE_FILE),
    }


def _maybe_cleanup():
    """检查是否需要清理缓存。"""
    _load()
    total = len(_cache)

    # 阈值清理：超过 MAX_ENTRIES 删除最老的
    if total > _MAX_ENTRIES:
        _cleanup_by_count()

    # 过期清理：删除超过 MAX_AGE_DAYS 的条目
    _cleanup_by_age()


def _cleanup_by_count():
    """按数量清理：保留最新的 MAX_ENTRIES 条。"""
    global _cache
    if len(_cache) <= _MAX_ENTRIES:
        return

    # 按时间戳排序，保留最新的
    sorted_items = sorted(_cache.items(), key=lambda x: x[1].get("ts", 0), reverse=True)
    _cache = dict(sorted_items[:_MAX_ENTRIES])
    _save()
    print(f"[cache] Cleaned by count: kept {_MAX_ENTRIES} / {len(sorted_items)}")


def _cleanup_by_age():
    """按年龄清理：删除超过 MAX_AGE_DAYS 的条目。"""
    global _cache
    cutoff = time.time() - (_MAX_AGE_DAYS * 86400)
    before = len(_cache)
    _cache = {k: v for k, v in _cache.items() if v.get("ts", 0) > cutoff}
    if len(_cache) < before:
        _save()
        print(f"[cache] Cleaned by age: removed {before - len(_cache)} entries")


def force_cleanup():
    """手动触发清理。"""
    _load()
    _cleanup_by_age()
    _cleanup_by_count()
    return get_stats()
