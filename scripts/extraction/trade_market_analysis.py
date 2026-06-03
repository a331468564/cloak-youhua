"""UN Comtrade 市场分析脚本。

查询各目标国家从中国进口餐厅家具的数据，确定高潜力市场。

用法:
  # Preview 模式（不需要 API key，最多 500 条记录）
  python -m scripts.extraction.trade_market_analysis --preview

  # 完整模式（需要 API key）
  python -m scripts.extraction.trade_market_analysis --api-key YOUR_KEY
  python -m scripts.extraction.trade_market_analysis --year 2023

  # 指定年份
  python -m scripts.extraction.trade_market_analysis --preview --year 2023

API key 免费注册：https://comtradeplus.un.org/
"""

import argparse
import csv
import json
import sys
import time
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
CONFIG_FILE = PROJECT_ROOT / "config" / "hs_codes.json"
REPORTS_DIR = PROJECT_ROOT / "reports"
DATA_DIR = PROJECT_ROOT / "data"

# API key 存储文件
API_KEY_FILE = DATA_DIR / ".comtrade_api_key"


def get_api_key(provided_key=None):
    """获取 API key：优先使用参数，其次从文件读取。"""
    if provided_key:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        API_KEY_FILE.write_text(provided_key, encoding="utf-8")
        return provided_key

    if API_KEY_FILE.exists():
        return API_KEY_FILE.read_text(encoding="utf-8").strip()

    return None


def load_config():
    """加载 HS 编码配置。"""
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _parse_records(data):
    """解析 API 返回的数据为统一格式。支持 DataFrame 和 list[dict]。"""
    results = {}
    if data is None:
        return results

    # pandas DataFrame
    try:
        import pandas as pd
        if isinstance(data, pd.DataFrame):
            if data.empty:
                return results
            for _, row in data.iterrows():
                hs = str(row.get("cmdCode", ""))
                value = row.get("primaryValue", 0)
                netweight = row.get("netWgt", 0)
                qty = row.get("qty", 0)
                desc = str(row.get("cmdDesc", ""))

                if hs not in results:
                    results[hs] = {
                        "value_usd": 0,
                        "netweight_kg": 0,
                        "quantity": 0,
                        "description": desc,
                    }
                results[hs]["value_usd"] += float(value or 0)
                results[hs]["netweight_kg"] += float(netweight or 0)
                results[hs]["quantity"] += float(qty or 0)
            return results
    except ImportError:
        pass

    # list[dict]
    if isinstance(data, list) and len(data) > 0:
        for record in data:
            hs = record.get("cmdCode", "")
            value = record.get("primaryValue", 0)
            netweight = record.get("netWgt", 0)
            qty = record.get("qty", 0)
            desc = record.get("cmdDesc", "")

            if hs not in results:
                results[hs] = {
                    "value_usd": 0,
                    "netweight_kg": 0,
                    "quantity": 0,
                    "description": desc,
                }
            results[hs]["value_usd"] += float(value or 0)
            results[hs]["netweight_kg"] += float(netweight or 0)
            results[hs]["quantity"] += float(qty or 0)

    return results


def query_import_data_preview(reporter_code, partner_code, hs_codes, year):
    """使用 preview API 查询（不需要 key，最多 500 条）。"""
    try:
        import comtradeapicall
    except ImportError:
        print("ERROR: comtradeapicall not installed. Run: pip install comtradeapicall")
        return {}

    cmd_code = ",".join(hs_codes)

    try:
        data = comtradeapicall.previewFinalData(
            typeCode="C",
            freqCode="A",
            clCode="HS",
            period=str(year),
            reporterCode=reporter_code,
            cmdCode=cmd_code,
            flowCode="M",
            partnerCode=partner_code,
            partner2Code=None,
            customsCode=None,
            motCode=None,
            maxRecords=500,
            format_output="JSON",
            aggregateBy=None,
            breakdownMode="classic",
            countOnly=None,
            includeDesc=True,
        )
        return _parse_records(data)

    except Exception as e:
        print(f"  WARNING: Preview query failed for reporter={reporter_code}: {e}")
        return {}


def query_import_data_full(api_key, reporter_code, partner_code, hs_codes, year):
    """使用完整 API 查询（需要 key，最多 250K 条）。"""
    try:
        import comtradeapicall
    except ImportError:
        print("ERROR: comtradeapicall not installed. Run: pip install comtradeapicall")
        return {}

    cmd_code = ",".join(hs_codes)

    try:
        data = comtradeapicall.getFinalData(
            subscription_key=api_key,
            typeCode="C",
            freqCode="A",
            clCode="HS",
            period=str(year),
            reporterCode=reporter_code,
            cmdCode=cmd_code,
            flowCode="M",
            partnerCode=partner_code,
            partner2Code=None,
            customsCode=None,
            motCode=None,
            maxRecords=2500,
            format_output="JSON",
            aggregateBy=None,
            breakdownMode="classic",
            countOnly=None,
            includeDesc=True,
        )
        return _parse_records(data)

    except Exception as e:
        print(f"  WARNING: Full query failed for reporter={reporter_code}: {e}")
        return {}


def run_analysis(api_key=None, year=2024, preview=False):
    """运行市场分析。"""
    config = load_config()
    reporter = config["reporter_country"]
    markets = config["target_markets"]
    categories = config["product_categories"]

    # 收集所有 HS 编码
    all_hs_codes = set()
    for cat in categories:
        all_hs_codes.update(cat["hs_codes"])
    all_hs_codes = sorted(all_hs_codes)

    mode = "PREVIEW (无需 API key, 每国最多 500 条)" if preview else "FULL (需要 API key)"
    print(f"=== UN Comtrade 市场分析 ===")
    print(f"模式: {mode}")
    print(f"出口国: {reporter['name']} ({reporter['comtrade_code']})")
    print(f"年份: {year}")
    print(f"HS 编码: {', '.join(all_hs_codes)}")
    print(f"目标市场: {len(markets)} 个国家")
    print()

    results = []
    total = len(markets)

    for i, market in enumerate(markets, 1):
        country = market["country"]
        code = market["comtrade_code"]
        priority = market.get("priority", 99)

        print(f"[{i}/{total}] 查询 {country} ({code})...")

        if preview:
            data = query_import_data_preview(code, reporter["comtrade_code"], all_hs_codes, year)
        else:
            data = query_import_data_full(api_key, code, reporter["comtrade_code"], all_hs_codes, year)

        total_value = sum(r["value_usd"] for r in data.values())
        total_weight = sum(r["netweight_kg"] for r in data.values())

        result = {
            "country": country,
            "country_code": market["code"],
            "comtrade_code": code,
            "priority": priority,
            "total_value_usd": total_value,
            "total_weight_kg": total_weight,
            "year": year,
            "hs_breakdown": data,
        }
        results.append(result)

        if total_value > 0:
            print(f"  总进口额: ${total_value:,.0f}")
            print(f"  总重量: {total_weight:,.0f} kg")
        else:
            print(f"  无数据")

        # API 限流：每次查询间隔 1 秒
        if i < total:
            time.sleep(1)

    # 按进口额排序
    results.sort(key=lambda x: x["total_value_usd"], reverse=True)

    return results


def save_report(results, year):
    """保存分析报告。"""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")

    # CSV 报告
    csv_file = REPORTS_DIR / f"trade_market_analysis_{year}_{timestamp}.csv"
    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "排名", "国家", "国家代码", "UN Comtrade 代码",
            "总进口额 (USD)", "总重量 (KG)", "优先级",
            "HS 编码明细"
        ])
        for i, r in enumerate(results, 1):
            hs_detail = "; ".join(
                f"{hs}: ${d['value_usd']:,.0f}"
                for hs, d in r["hs_breakdown"].items()
                if d["value_usd"] > 0
            )
            writer.writerow([
                i, r["country"], r["country_code"], r["comtrade_code"],
                f"{r['total_value_usd']:.0f}", f"{r['total_weight_kg']:.0f}",
                r["priority"], hs_detail
            ])

    # JSON 详细报告
    json_file = REPORTS_DIR / f"trade_market_analysis_{year}_{timestamp}.json"
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n=== 报告已保存 ===")
    print(f"CSV: {csv_file}")
    print(f"JSON: {json_file}")

    return csv_file, json_file


def print_summary(results):
    """打印分析摘要。"""
    print(f"\n=== 市场排名（按进口额）===")
    print(f"{'排名':<4} {'国家':<20} {'进口额 (USD)':<20} {'重量 (KG)':<15} {'优先级':<6}")
    print("-" * 70)

    for i, r in enumerate(results, 1):
        value = r["total_value_usd"]
        weight = r["total_weight_kg"]
        print(f"{i:<4} {r['country']:<20} ${value:>16,.0f} {weight:>12,.0f} {r['priority']:<6}")

    # 推荐高潜力市场
    high_value = [r for r in results if r["total_value_usd"] > 1_000_000]
    if high_value:
        print(f"\n=== 推荐高潜力市场（进口额 > $1M）===")
        for r in high_value:
            print(f"  - {r['country']}: ${r['total_value_usd']:,.0f}")


def main():
    parser = argparse.ArgumentParser(description="UN Comtrade 市场分析")
    parser.add_argument("--api-key", help="UN Comtrade API key")
    parser.add_argument("--year", type=int, default=2024, help="查询年份 (默认: 2024)")
    parser.add_argument("--preview", action="store_true",
                       help="Preview 模式（不需要 API key，每国最多 500 条）")
    args = parser.parse_args()

    if not args.preview:
        api_key = get_api_key(args.api_key)
        if not api_key:
            print("ERROR: 未找到 UN Comtrade API key")
            print("请先注册: https://comtradeplus.un.org/")
            print("然后运行: python -m scripts.extraction.trade_market_analysis --api-key YOUR_KEY")
            print()
            print("或者使用 preview 模式（不需要 key）:")
            print("  python -m scripts.extraction.trade_market_analysis --preview")
            sys.exit(1)
    else:
        api_key = None

    results = run_analysis(api_key, args.year, preview=args.preview)

    if results:
        print_summary(results)
        save_report(results, args.year)
    else:
        print("WARNING: 未获取到任何数据，请检查网络连接")


if __name__ == "__main__":
    main()
