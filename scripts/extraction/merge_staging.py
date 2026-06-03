"""暂存文件合并脚本。

将 hs_leads_staging.csv 或 b2b_leads_staging.csv 中审核通过的记录合并到 leads.csv。

用法:
  # 查看暂存文件状态
  python -m scripts.extraction.merge_staging --status

  # 合并 HS 发现的潜客（只合并 staging_status=pending 的）
  python -m scripts.extraction.merge_staging --source hs

  # 合并 B2B 平台的潜客
  python -m scripts.extraction.merge_staging --source b2b

  # 合并所有暂存文件
  python -m scripts.extraction.merge_staging --source all

  # 只合并指定状态的记录
  python -m scripts.extraction.merge_staging --source hs --status approved

  # 预览不实际合并
  python -m scripts.extraction.merge_staging --source hs --dry-run

  # 标记暂存记录为 approved/rejected
  python -m scripts.extraction.merge_staging --source hs --mark-approved HS-0001,HS-0002
  python -m scripts.extraction.merge_staging --source hs --mark-rejected HS-0003
"""

import argparse
import csv
import re
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA = PROJECT_ROOT / "data"

STAGING_FILES = {
    "hs": DATA / "hs_leads_staging.csv",
    "b2b": DATA / "b2b_leads_staging.csv",
}


def load_leads():
    """加载现有 leads.csv。"""
    leads_path = DATA / "leads.csv"
    if not leads_path.exists():
        return [], []
    with open(leads_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        return reader.fieldnames, list(reader)


def load_staging(source):
    """加载暂存文件。"""
    staging_path = STAGING_FILES.get(source)
    if not staging_path or not staging_path.exists():
        return [], []
    with open(staging_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        return reader.fieldnames, list(reader)


def get_next_lead_id(existing_rows):
    """获取下一个 lead_id。"""
    max_id = 0
    for row in existing_rows:
        lid = row.get("lead_id", "")
        m = re.search(r'(\d+)', lid)
        if m:
            max_id = max(max_id, int(m.group(1)))
    return max_id


def show_status():
    """显示所有暂存文件的状态。"""
    print("=== 暂存文件状态 ===\n")
    for source, path in STAGING_FILES.items():
        if not path.exists():
            print(f"  [{source}] {path.name}: 不存在")
            continue
        with open(path, "r", encoding="utf-8-sig") as f:
            rows = list(csv.DictReader(f))
        total = len(rows)
        pending = sum(1 for r in rows if r.get("staging_status", "pending") == "pending")
        approved = sum(1 for r in rows if r.get("staging_status") == "approved")
        rejected = sum(1 for r in rows if r.get("staging_status") == "rejected")
        print(f"  [{source}] {path.name}: {total} 条")
        print(f"    pending: {pending} | approved: {approved} | rejected: {rejected}")

    # 显示 leads.csv 现有记录数
    leads_path = DATA / "leads.csv"
    if leads_path.exists():
        with open(leads_path, "r", encoding="utf-8-sig") as f:
            leads_count = sum(1 for _ in csv.DictReader(f))
        print(f"\n  [leads] leads.csv: {leads_count} 条")


def mark_status(source, ids, status):
    """标记暂存记录的状态。"""
    staging_path = STAGING_FILES.get(source)
    if not staging_path or not staging_path.exists():
        print(f"ERROR: 暂存文件不存在: {staging_path}")
        return

    with open(staging_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    id_set = set(ids)
    updated = 0
    for row in rows:
        if row.get("lead_id") in id_set:
            row["staging_status"] = status
            updated += 1

    with open(staging_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"标记 {updated} 条记录为 {status}")


def merge_staging(source, status_filter="pending", dry_run=False):
    """将暂存文件中指定状态的记录合并到 leads.csv。"""
    staging_path = STAGING_FILES.get(source)
    if not staging_path or not staging_path.exists():
        print(f"ERROR: 暂存文件不存在: {staging_path}")
        return 0

    # 加载暂存数据
    with open(staging_path, "r", encoding="utf-8-sig") as f:
        staging_reader = csv.DictReader(f)
        staging_fieldnames = staging_reader.fieldnames
        staging_rows = list(staging_reader)

    # 过滤指定状态
    if status_filter:
        filtered = [r for r in staging_rows if r.get("staging_status", "pending") == status_filter]
    else:
        filtered = staging_rows

    if not filtered:
        print(f"没有 {status_filter} 状态的记录需要合并")
        return 0

    print(f"待合并: {len(filtered)} 条 ({status_filter} 状态)")

    # 加载现有 leads
    leads_path = DATA / "leads.csv"
    if not leads_path.exists():
        print("ERROR: leads.csv 不存在")
        return 0

    with open(leads_path, "r", encoding="utf-8-sig") as f:
        leads_reader = csv.DictReader(f)
        leads_fieldnames = leads_reader.fieldnames
        leads_rows = list(leads_reader)

    # 去重：检查域名和公司名
    existing_domains = set()
    existing_names = set()
    for row in leads_rows:
        website = (row.get("website") or "").strip().lower()
        if website:
            d = website.replace("https://", "").replace("http://", "").replace("www.", "").split("/")[0]
            existing_domains.add(d)
        name = (row.get("company_name") or "").strip().lower()
        if name:
            existing_names.add(name)

    # 准备合并
    max_id = get_next_lead_id(leads_rows)
    now = datetime.now().strftime("%Y-%m-%d")
    merged = 0
    skipped = 0

    new_rows = []
    for row in filtered:
        # 去重检查
        website = (row.get("website") or "").strip().lower()
        domain = ""
        if website:
            domain = website.replace("https://", "").replace("http://", "").replace("www.", "").split("/")[0]

        name = (row.get("company_name") or "").strip().lower()

        if domain and domain in existing_domains:
            skipped += 1
            print(f"  跳过(域名重复): {row.get('company_name', '')} ({domain})")
            continue
        if name and name in existing_names:
            skipped += 1
            print(f"  跳过(名称重复): {row.get('company_name', '')}")
            continue

        # 重新分配 lead_id
        max_id += 1
        prefix = "HS" if source == "hs" else "B2B"
        row["lead_id"] = f"{prefix}-{max_id:04d}"
        row["last_updated"] = now

        # 移除 staging 专属列
        new_row = {k: v for k, v in row.items() if k in leads_fieldnames}
        new_rows.append(new_row)

        if domain:
            existing_domains.add(domain)
        if name:
            existing_names.add(name)
        merged += 1
        safe_name = (row.get("company_name", "")).encode('ascii', 'replace').decode('ascii')
        print(f"  + {row['lead_id']}: {safe_name}")

    if dry_run:
        print(f"\n[DRY RUN] 将合并 {merged} 条，跳过 {skipped} 条")
        return merged

    # 写入 leads.csv
    if new_rows:
        with open(leads_path, "a", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=leads_fieldnames)
            for row in new_rows:
                writer.writerow(row)
        print(f"\n合并完成: {merged} 条写入 leads.csv，跳过 {skipped} 条")

        # 更新暂存文件状态为 merged
        merged_ids = {r["lead_id"] for r in new_rows}
        for row in staging_rows:
            if row.get("staging_status") == status_filter:
                # 标记已合并的记录
                for new_row in new_rows:
                    if (new_row.get("company_name", "").lower() ==
                        row.get("company_name", "").lower()):
                        row["staging_status"] = "merged"
                        break

        with open(staging_path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=staging_fieldnames)
            writer.writeheader()
            writer.writerows(staging_rows)
    else:
        print(f"\n无新记录需要合并（全部重复）")

    return merged


def main():
    parser = argparse.ArgumentParser(description="暂存文件合并到 leads.csv")
    parser.add_argument("--source", choices=["hs", "b2b", "all"], default="all",
                       help="暂存文件来源")
    parser.add_argument("--status", default="pending",
                       help="只合并指定状态的记录 (默认: pending)")
    parser.add_argument("--dry-run", action="store_true", help="预览不实际合并")
    parser.add_argument("--mark-approved", type=str, default="",
                       help="标记指定 ID 为 approved (逗号分隔)")
    parser.add_argument("--mark-rejected", type=str, default="",
                       help="标记指定 ID 为 rejected (逗号分隔)")
    args = parser.parse_args()

    if args.mark_approved:
        ids = args.mark_approved.split(",")
        for source in (["hs", "b2b"] if args.source == "all" else [args.source]):
            mark_status(source, ids, "approved")
        return

    if args.mark_rejected:
        ids = args.mark_rejected.split(",")
        for source in (["hs", "b2b"] if args.source == "all" else [args.source]):
            mark_status(source, ids, "rejected")
        return

    if args.source == "all":
        show_status()
        print()
        total = 0
        for source in ["hs", "b2b"]:
            print(f"\n--- 合并 {source} ---")
            total += merge_staging(source, args.status, args.dry_run)
        print(f"\n总计合并: {total} 条")
    else:
        show_status()
        print()
        merge_staging(args.source, args.status, args.dry_run)


if __name__ == "__main__":
    main()
