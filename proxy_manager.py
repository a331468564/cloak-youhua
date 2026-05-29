"""
独立 mihomo 进程管理 + Clash API 节点轮换。

职责：
1. 启动/停止独立 mihomo 子进程（端口 7898，API 9091）
2. 通过 Clash API 列出/切换节点
3. 429 检测 → 自动轮换节点 → 重建浏览器
4. 代理 IP 验证（httpbin.org/ip）

设计约束：
- 不影响主 Clash Verge Rev（端口 7897/9090）
- mihomo 二进制：D:/Clash Verge/verge-mihomo.exe
- 配置：config/proxy-rotation/cloak-clash.yaml
"""
import json
import random
import subprocess
import time
import urllib.request
from pathlib import Path

_MIHOMO_BIN = r"D:\Clash Verge\verge-mihomo.exe"
_CONFIG_PATH = Path(__file__).parent / "config" / "cloak-clash.yaml"
_PROXY_PORT = 7898
_API_PORT = 9091
_API_BASE = f"http://127.0.0.1:{_API_PORT}"

# 节点池：区域 → 节点名列表
_REGIONS = {
    "JP": ["JP-01", "JP-02", "JP-03", "JP-04", "JP-05"],
    "TW": ["TW-01", "TW-02"],
    "SG": ["SG-01", "SG-02"],
    "HK": ["HK-01", "HK-02", "HK-03", "HK-04"],
    "US": ["US-01", "US-02", "US-03", "US-04", "US-05"],
}
_ALL_NODES = [n for nodes in _REGIONS.values() for n in nodes]

PROXY_URL = f"http://127.0.0.1:{_PROXY_PORT}"


class ProxyManager:
    """管理独立 mihomo 实例和代理节点轮换。"""

    def __init__(self):
        self._process = None
        self._current_node = None
        self._used_nodes: set[str] = set()
        self._consecutive_429 = 0
        self._local_ip = ""

    def start(self) -> bool:
        """启动 mihomo 子进程，等待 API 就绪。返回是否成功。"""
        if self._is_api_alive():
            print("[ProxyManager] mihomo API already alive, reusing")
            return True

        if not Path(_MIHOMO_BIN).exists():
            print(f"[ProxyManager] ERROR: mihomo binary not found: {_MIHOMO_BIN}")
            return False
        if not _CONFIG_PATH.exists():
            print(f"[ProxyManager] ERROR: config not found: {_CONFIG_PATH}")
            return False

        cmd = [_MIHOMO_BIN, "-d", str(_CONFIG_PATH.parent), "-f", str(_CONFIG_PATH)]
        try:
            self._process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0,
            )
        except Exception as e:
            print(f"[ProxyManager] Failed to start mihomo: {e}")
            return False

        # Wait for API to become available (max 10s)
        for _ in range(20):
            time.sleep(0.5)
            if self._is_api_alive():
                print("[ProxyManager] mihomo started, API ready")
                return True

        print("[ProxyManager] mihomo started but API not responding")
        return False

    def stop(self):
        """停止 mihomo 子进程。"""
        if self._process:
            self._process.terminate()
            try:
                self._process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._process.kill()
            self._process = None
            print("[ProxyManager] mihomo stopped")

    def ensure_running(self) -> bool:
        """确保 mihomo 运行中，如未运行则启动。"""
        if self._is_api_alive():
            return True
        return self.start()

    def verify_proxy_ip(self) -> str | None:
        """通过代理访问 IP 检测服务，返回出口 IP。失败返回 None。"""
        for url in ["http://icanhazip.com", "http://api.ipify.org", "https://httpbin.org/ip"]:
            try:
                proxy_handler = urllib.request.ProxyHandler({
                    "http": PROXY_URL,
                    "https": PROXY_URL,
                })
                opener = urllib.request.build_opener(proxy_handler)
                req = urllib.request.Request(url)
                with opener.open(req, timeout=10) as resp:
                    body = resp.read().decode().strip()
                    # icanhazip/ipify return plain IP, httpbin returns JSON
                    if body.startswith("{"):
                        return json.loads(body).get("origin", "")
                    return body
            except Exception:
                continue
        return None

    def verify_ip_is_proxy(self) -> bool:
        """验证代理出口 IP 已变化（即轮换生效）。"""
        proxy_ip = self.verify_proxy_ip()
        if not proxy_ip:
            return False
        if not self._local_ip:
            self._local_ip = self._get_local_ip()
        return bool(self._local_ip) and proxy_ip != self._local_ip

    def select_random_node(self) -> str | None:
        """选一个未用过的随机节点。全部用过则重置。"""
        available = [n for n in _ALL_NODES if n not in self._used_nodes]
        if not available:
            self._used_nodes.clear()
            available = _ALL_NODES[:]
        node = random.choice(available)
        self._used_nodes.add(node)
        return node

    def switch_node(self, node_name: str | None = None) -> bool:
        """通过 Clash API 切换到指定节点（或随机节点）。返回是否成功。"""
        if node_name is None:
            node_name = self.select_random_node()
        if not node_name:
            return False

        # Determine which region group this node belongs to
        region = node_name.split("-")[0]  # "JP-01" → "JP"
        url = f"{_API_BASE}/proxies/{region}"
        payload = json.dumps({"name": node_name}).encode()

        try:
            req = urllib.request.Request(url, data=payload, method="PUT")
            req.add_header("Content-Type", "application/json")
            with urllib.request.urlopen(req, timeout=5):
                self._current_node = node_name
                print(f"[ProxyManager] Switched to {node_name}")
                return True
        except Exception as e:
            print(f"[ProxyManager] Failed to switch to {node_name}: {e}")
            return False

    def get_current_node(self) -> str | None:
        """获取当前选中的节点名。"""
        return self._current_node

    def handle_429(self, browser_close_fn=None) -> bool:
        """处理 429 限流：关闭浏览器 → 切换节点 → 冷却 → 验证 IP。

        Args:
            browser_close_fn: 关闭浏览器的回调函数

        Returns:
            True 如果轮换成功可继续搜索，False 如果应停止
        """
        self._consecutive_429 += 1
        print(f"[ProxyManager] 429 detected (consecutive: {self._consecutive_429})")

        # 3 次连续 429 → 暂停 5 分钟
        if self._consecutive_429 >= 3:
            print("[ProxyManager] 3 consecutive 429s, pausing 5 minutes...")
            if browser_close_fn:
                browser_close_fn()
            time.sleep(300)
            self._consecutive_429 = 0
            self._used_nodes.clear()  # reset used nodes after long pause

        # 关闭浏览器
        if browser_close_fn:
            browser_close_fn()

        # 切换到新节点
        node = self.select_random_node()
        if not node or not self.switch_node(node):
            print("[ProxyManager] No more nodes to try")
            return False

        # 冷却 10-15 秒
        cooldown = random.uniform(10, 15)
        print(f"[ProxyManager] Cooling down {cooldown:.1f}s...")
        time.sleep(cooldown)

        # 验证新 IP
        if self.verify_ip_is_proxy():
            print("[ProxyManager] New IP verified, ready to continue")
            return True
        else:
            print("[ProxyManager] WARNING: Could not verify new proxy IP")
            return True  # continue anyway, best effort

    def reset_429_counter(self):
        """成功搜索后重置 429 计数器。"""
        self._consecutive_429 = 0

    def get_status(self) -> dict:
        """返回当前状态摘要。"""
        return {
            "running": self._is_api_alive(),
            "current_node": self._current_node,
            "used_nodes": sorted(self._used_nodes),
            "consecutive_429": self._consecutive_429,
            "total_nodes": len(_ALL_NODES),
        }

    def list_available_nodes(self) -> list[str]:
        """列出所有可用节点。"""
        return _ALL_NODES[:]

    def _is_api_alive(self) -> bool:
        """检查 Clash API 是否可达。"""
        try:
            req = urllib.request.Request(f"{_API_BASE}/version")
            with urllib.request.urlopen(req, timeout=2):
                return True
        except Exception:
            return False

    def _get_local_ip(self) -> str:
        """获取本机真实 IP（不走任何代理）。"""
        for url in ["http://icanhazip.com", "http://api.ipify.org"]:
            try:
                # Bypass system proxy by using no_proxy handler
                proxy_handler = urllib.request.ProxyHandler({})
                opener = urllib.request.build_opener(proxy_handler)
                req = urllib.request.Request(url)
                with opener.open(req, timeout=10) as resp:
                    return resp.read().decode().strip()
            except Exception:
                continue
        return ""


# Module-level singleton for easy import
_manager: ProxyManager | None = None


def get_manager() -> ProxyManager:
    """获取全局 ProxyManager 单例。"""
    global _manager
    if _manager is None:
        _manager = ProxyManager()
    return _manager
