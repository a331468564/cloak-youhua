"""Execute keyword-driven searches via existing extraction scripts."""

import csv
import subprocess
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_EXTRACTION_SCRIPT = _PROJECT_ROOT / "scripts" / "extraction" / "extract_public_contact_candidates.py"


def build_extraction_queue(query_queue: list[dict], out_path: Path) -> Path:
    """Write a queue CSV that extract_public_contact_candidates.py can consume.

    Each row: lead_id, company_name, website, query
    """
    fieldnames = ["lead_id", "company_name", "website", "query"]
    with open(out_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for i, item in enumerate(query_queue):
            writer.writerow({
                "lead_id": item.get("keyword_id", f"KW-{i+1:04d}"),
                "company_name": "",
                "website": "",
                "query": item.get("source_query", ""),
            })
    return out_path


def run_extraction(
    queue_path: Path,
    output_prefix: str = "kw-scheduler-",
    limit: int = 10,
    follow_links: int = 2,
    fetcher: str = "static",
    skip_existing: bool = True,
) -> tuple[int, Path]:
    """Run extract_public_contact_candidates.py on the queue.

    Returns (exit_code, output_csv_path).
    """
    reports_dir = _PROJECT_ROOT / "reports"
    cmd = [
        sys.executable,
        str(_EXTRACTION_SCRIPT),
        "--input", str(queue_path),
        "--output-prefix", str(reports_dir / output_prefix),
        "--limit", str(limit),
        "--follow-links", str(follow_links),
        "--fetcher", fetcher,
        "--delay", "2",
    ]
    if skip_existing:
        cmd.append("--skip-existing")

    result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(_PROJECT_ROOT))

    # Find the output CSV
    output_csv = None
    for f in sorted(reports_dir.glob(f"{output_prefix}*.csv"), reverse=True):
        output_csv = f
        break

    return result.returncode, output_csv
