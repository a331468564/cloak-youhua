"""
RunTimer — 自动记录脚本执行时间，写入 JSON 供报告脚本读取。
"""

import json
from datetime import datetime
from pathlib import Path

TIMING_FILE = Path("data/.last_run_timing.json")


class RunTimer:
    """Context manager that records start/end/duration and writes to TIMING_FILE."""

    def __enter__(self):
        self.start = datetime.now()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end = datetime.now()
        self.duration = self.end - self.start
        self.duration_seconds = self.duration.total_seconds()
        TIMING_FILE.parent.mkdir(parents=True, exist_ok=True)
        TIMING_FILE.write_text(
            json.dumps(
                {
                    "start": self.start.isoformat(timespec="seconds"),
                    "end": self.end.isoformat(timespec="seconds"),
                    "duration_seconds": round(self.duration_seconds, 1),
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        return False

    @staticmethod
    def load() -> dict | None:
        """Load the last timing record, or None if not available."""
        if not TIMING_FILE.exists():
            return None
        return json.loads(TIMING_FILE.read_text(encoding="utf-8"))
