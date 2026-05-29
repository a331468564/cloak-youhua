import csv
import html
import shutil
from collections import Counter
from datetime import datetime
from pathlib import Path


ROOT = Path(".")
DATA = ROOT / "data"
DOCS = ROOT / "docs"
EXPORTS = ROOT / "exports"


def read_csv(path):
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv_bom(path, rows, fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore", quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(rows)


def esc(value):
    return html.escape(str(value or ""))


def link(url, label=None):
    if not url:
        return ""
    label = label or url
    return f'<a href="{esc(url)}" target="_blank" rel="noopener">{esc(label)}</a>'


def count(rows, field, value):
    return sum(1 for r in rows if r.get(field) == value)


def has_any(row, fields):
    return any((row.get(f) or "").strip() for f in fields)


def stat_card(label, value, tone=""):
    return f'<div class="stat {tone}"><span>{esc(value)}</span><label>{esc(label)}</label></div>'


def table(headers, rows):
    head = "".join(f"<th>{esc(h)}</th>" for h in headers)
    body = []
    for row in rows:
        body.append("<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>")
    return f"<table><thead><tr>{head}</tr></thead><tbody>{''.join(body)}</tbody></table>"


def breakdown(counter, limit=12):
    items = counter.most_common(limit)
    return "".join(
        f'<div class="bar-row"><span>{esc(k or "未填写")}</span><b>{v}</b></div>'
        for k, v in items
    )


def main():
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    out = EXPORTS / f"boss-report-{ts}"
    data_out = out / "data"
    docs_out = out / "docs"
    out.mkdir(parents=True, exist_ok=True)
    data_out.mkdir(parents=True, exist_ok=True)
    docs_out.mkdir(parents=True, exist_ok=True)

    leads = read_csv(DATA / "leads.csv")
    contacts = read_csv(DATA / "contacts.csv")
    keywords = read_csv(DATA / "search_keywords.csv")
    runs = read_csv(DATA / "keyword_runs.csv")
    au_leads = [r for r in leads if r.get("country") == "Australia"]
    au_lead_ids = {r.get("lead_id") for r in au_leads}
    au_contacts = [r for r in contacts if r.get("lead_id") in au_lead_ids]

    shutil.copy2(DATA / "leads.csv", data_out / "leads_full.csv")
    shutil.copy2(DATA / "contacts.csv", data_out / "contacts_full.csv")
    shutil.copy2(DATA / "search_keywords.csv", data_out / "search_keywords.csv")
    shutil.copy2(DATA / "keyword_runs.csv", data_out / "keyword_runs.csv")

    lead_fields = [
        "lead_id", "company_name", "website", "city_or_region", "industry_type",
        "customer_type", "customer_strength_level", "follow_up_status",
        "contact_data_level", "primary_contact_method", "company_email",
        "company_phone", "company_contact_page", "company_contact_form_url",
        "key_contact_name", "key_contact_job_title", "contact_priority",
        "next_action", "source_link", "last_updated",
    ]
    contact_fields = [
        "contact_id", "lead_id", "company_name", "contact_name", "job_title",
        "department", "contact_role_type", "email", "phone", "linkedin_url",
        "source_link", "contact_confidence", "contact_status",
        "is_primary_contact", "contact_priority", "notes", "last_updated",
    ]
    write_csv_bom(data_out / "australia_leads_for_boss.csv", au_leads, lead_fields)
    write_csv_bom(data_out / "australia_contacts_for_boss.csv", au_contacts, contact_fields)

    for report in sorted(DOCS.glob("australia*.md")):
        shutil.copy2(report, docs_out / report.name)

    ready = count(au_leads, "follow_up_status", "Ready to Contact")
    need_research = count(au_leads, "follow_up_status", "Need More Research")
    direct = count(au_leads, "contact_data_level", "Direct Key Contact Found")
    key_identified = count(au_leads, "contact_data_level", "Key Person Identified")
    company_only = count(au_leads, "contact_data_level", "Company Contact Only")
    forms = sum(1 for r in au_leads if has_any(r, ["company_contact_page", "company_contact_form_url"]))
    emails = sum(1 for r in au_leads if has_any(r, ["company_email", "key_contact_email"]))
    phones = sum(1 for r in au_leads if has_any(r, ["company_phone", "key_contact_phone"]))
    high_strength = count(au_leads, "customer_strength_level", "High")

    stats = "".join([
        stat_card("澳大利亚线索总数", len(au_leads), "blue"),
        stat_card("可联系 Ready", ready, "green"),
        stat_card("需继续研究", need_research, "amber"),
        stat_card("官方表单/联系页", forms, "green"),
        stat_card("邮箱线索", emails, "blue"),
        stat_card("电话线索", phones, "blue"),
        stat_card("直接关键联系人", direct, "green"),
        stat_card("已识别关键人", key_identified, "blue"),
        stat_card("仅公司联系方式", company_only, "amber"),
        stat_card("高匹配客户", high_strength, "green"),
        stat_card("联系人记录", len(au_contacts), "blue"),
        stat_card("关键词测试记录", len(runs), "blue"),
    ])

    priority = sorted(
        au_leads,
        key=lambda r: (
            r.get("contact_data_level") != "Direct Key Contact Found",
            r.get("contact_data_level") != "Key Person Identified",
            r.get("customer_strength_level") != "High",
            r.get("contact_priority") != "High",
        ),
    )[:25]
    priority_rows = []
    for r in priority:
        contact_bits = []
        if r.get("key_contact_name"):
            contact_bits.append(f'{esc(r.get("key_contact_name"))} {esc(r.get("key_contact_job_title"))}')
        if r.get("company_email"):
            contact_bits.append(esc(r.get("company_email")))
        if r.get("company_phone"):
            contact_bits.append(esc(r.get("company_phone")))
        if r.get("company_contact_form_url"):
            contact_bits.append(link(r.get("company_contact_form_url"), "表单"))
        priority_rows.append([
            esc(r.get("company_name")),
            link(r.get("website"), "官网"),
            esc(r.get("city_or_region")),
            esc(r.get("customer_type")),
            esc(r.get("contact_data_level")),
            "<br>".join(contact_bits),
            esc(r.get("next_action")),
        ])

    direct_contacts = [
        c for c in au_contacts
        if c.get("contact_status") == "Direct Contact Found"
        or c.get("email")
        or c.get("phone")
    ][:30]
    contact_rows = []
    for c in direct_contacts:
        contact_rows.append([
            esc(c.get("company_name")),
            esc(c.get("contact_name")),
            esc(c.get("job_title")),
            esc(c.get("email")),
            esc(c.get("phone")),
            esc(c.get("contact_confidence")),
            link(c.get("source_link"), "来源"),
        ])

    latest_reports = sorted(DOCS.glob("australia*.md"), key=lambda p: p.stat().st_mtime, reverse=True)[:4]
    report_links = "".join(f'<li><a href="docs/{esc(p.name)}">{esc(p.name)}</a></li>' for p in latest_reports)

    city_counter = Counter(r.get("city_or_region") for r in au_leads)
    type_counter = Counter(r.get("customer_type") for r in au_leads)

    html_text = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Ron Group 澳大利亚线索进度汇报</title>
  <style>
    body {{ margin: 0; font-family: Arial, "Microsoft YaHei", sans-serif; background: #f6f7f9; color: #1f2933; }}
    header {{ background: #12343b; color: white; padding: 28px 36px; }}
    header h1 {{ margin: 0 0 8px; font-size: 28px; }}
    header p {{ margin: 0; color: #dce8e9; }}
    main {{ padding: 28px 36px 48px; max-width: 1380px; margin: 0 auto; }}
    section {{ background: white; border: 1px solid #d9e0e6; border-radius: 8px; padding: 20px; margin-bottom: 18px; }}
    h2 {{ margin: 0 0 14px; font-size: 20px; }}
    .summary {{ display: grid; grid-template-columns: repeat(4, minmax(160px, 1fr)); gap: 12px; }}
    .stat {{ border: 1px solid #d9e0e6; border-radius: 8px; padding: 14px; background: #fbfcfd; }}
    .stat span {{ display: block; font-size: 28px; font-weight: 700; }}
    .stat label {{ color: #52616b; font-size: 13px; }}
    .green span {{ color: #137a4d; }} .blue span {{ color: #1d5d9b; }} .amber span {{ color: #a15c07; }}
    .grid-2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }}
    .bar-row {{ display: flex; justify-content: space-between; gap: 12px; border-bottom: 1px solid #edf1f5; padding: 8px 0; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
    th, td {{ border-bottom: 1px solid #e5eaf0; padding: 9px 8px; text-align: left; vertical-align: top; }}
    th {{ background: #eef3f6; color: #25313b; position: sticky; top: 0; }}
    a {{ color: #0b63ce; text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    .note {{ line-height: 1.65; color: #3f4d57; }}
    .files li {{ margin: 8px 0; }}
    @media (max-width: 900px) {{ .summary, .grid-2 {{ grid-template-columns: 1fr; }} main {{ padding: 18px; }} header {{ padding: 22px; }} }}
  </style>
</head>
<body>
  <header>
    <h1>Ron Group 澳大利亚线索进度汇报</h1>
    <p>生成时间：{esc(datetime.now().strftime("%Y-%m-%d %H:%M"))} ｜ 本页面可离线打开，不依赖本地服务器。</p>
  </header>
  <main>
    <section>
      <h2>项目进度概览</h2>
      <div class="summary">{stats}</div>
    </section>

    <section>
      <h2>给老板看的简短结论</h2>
      <div class="note">
        目前澳大利亚方向已经形成一批可复核的 B2B 餐饮/酒店/fit-out/设计/采购类潜在客户。
        数据重点偏向有官网、官方联系表单、邮箱、电话或公开关键人的公司。
        下一步建议先从 Direct Key Contact Found、Key Person Identified 和 High 强度客户里做人工复核与分层外联准备。
      </div>
    </section>

    <section class="grid-2">
      <div>
        <h2>城市/地区覆盖</h2>
        {breakdown(city_counter)}
      </div>
      <div>
        <h2>客户类型覆盖</h2>
        {breakdown(type_counter)}
      </div>
    </section>

    <section>
      <h2>优先查看客户 Top 25</h2>
      {table(["公司", "官网", "城市", "客户类型", "联系等级", "可用联系路径", "下一步"], priority_rows)}
    </section>

    <section>
      <h2>直接或较强联系人样例</h2>
      {table(["公司", "联系人", "职位", "邮箱", "电话", "置信度", "来源"], contact_rows)}
    </section>

    <section>
      <h2>随包文件</h2>
      <ul class="files">
        <li><a href="data/australia_leads_for_boss.csv">data/australia_leads_for_boss.csv</a>：老板版澳大利亚线索表</li>
        <li><a href="data/australia_contacts_for_boss.csv">data/australia_contacts_for_boss.csv</a>：老板版联系人表</li>
        <li><a href="data/leads_full.csv">data/leads_full.csv</a>：完整 leads 数据备份</li>
        <li><a href="data/contacts_full.csv">data/contacts_full.csv</a>：完整 contacts 数据备份</li>
      </ul>
      <h2>最近研究报告</h2>
      <ul>{report_links}</ul>
    </section>
  </main>
</body>
</html>
"""
    (out / "index.html").write_text(html_text, encoding="utf-8")

    readme = f"""老板汇报包使用说明

1. 解压整个文件夹。
2. 双击打开 index.html。
3. 如果要看表格，打开 data/australia_leads_for_boss.csv 和 data/australia_contacts_for_boss.csv。
4. docs 文件夹里是近期研究报告。

注意：请保持 index.html、data 文件夹、docs 文件夹在同一个文件夹里。
生成时间：{datetime.now().strftime("%Y-%m-%d %H:%M")}
"""
    (out / "README_老板先看.txt").write_text(readme, encoding="utf-8-sig")

    print(out)


if __name__ == "__main__":
    main()
