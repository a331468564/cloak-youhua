---
paths:
  - "scripts/extraction/**"
  - "reports/**"
---

# Extraction and Collection Rules

## Rule 1: Company Information Collection Threshold

**STOP collecting company info when ANY of these conditions are met:**
- Found contact page URL
- Found at least 1 email address
- Found at least 1 phone number
- Found LinkedIn company page
- Searched 3 pages with no new discoveries

**DO NOT continue searching if:**
- All above items are already in `data/leads.csv`
- The lead already has `contact_research_status` = "已找到联系路径"

## Rule 2: Key Person (KP) Search Trigger

**Start searching for KP ONLY when:**
- Company info is complete (email, phone, or contact page found)
- No key person identified yet
- Company has team/about page (indicates larger organization)

**DO NOT search for KP if:**
- Lead already has `key_contact_name` in `data/leads.csv`
- Lead already has contact in `data/contacts.csv`
- Company is sole proprietor (contact_person field already filled)

## Rule 3: KP Search Investment Limits

**STOP searching for KP when ANY of these conditions are met:**
- Time spent > 5 minutes on single lead
- Pages searched > 3 with no new findings
- Ratio of unhelpful pages > 70%
- Found KP name but cannot verify contact method

**ABANDON KP search and mark as "低优先级" if:**
- All above limits reached
- No LinkedIn profile found after 2 search attempts
- Company appears to have no public team page

## Rule 3b: Multi-KP Discovery

**每家公司尽可能找到多个KP和对接人：**
- 不要只找一个KP就停止
- 团队/About页面上的所有决策者都应记录
- 每个KP都需要尝试找到：邮箱、电话、LinkedIn、社交媒体
- LinkedIn 个人URL如果找不到，至少生成搜索URL供人工审核

**KP优先级：**
1. 直联邮箱（firstname.lastname@domain）→ 高价值
2. 直联手机（04xx）→ 高价值
3. LinkedIn 个人主页URL → 中价值
4. LinkedIn 搜索URL（供人工确认）→ 低价值但有用
5. 公司邮箱（info@, hello@）→ 低价值，但仍需记录
6. 公司电话（1300/1800）→ 低价值

**LinkedIn处理规则：**
- 找到个人URL → 直接保存到 contacts.linkedin_url
- 找不到个人URL → 生成搜索URL保存，标记为"待人工确认"
- 不要尝试自动登录LinkedIn或抓取个人页面内容

## Rule 4: Duplicate Prevention

**BEFORE any extraction, check existing data:**
1. Load `data/contacts.csv` - check contact names, emails, phones
2. Load `data/leads.csv` - check contact_person, email_address, phone_number, key_contact_*
3. Skip any candidate that already exists

**Use `--skip-existing` flag (default: true) when running extraction scripts**

## Rule 5: Decision Flowchart

```
START → Load existing data → Company Info Collection
  ├─ Found email/phone/contact page? → Mark "已找到联系路径" → Check KP
  └─ NO → Continue search (max 3 pages) → No result → Mark "需人工确认" → NEXT LEAD

Check Key Person:
  ├─ Already have KP? → Skip, NEXT LEAD
  └─ NO → Start KP search
    ├─ Found KP name? → Try to find contact
    │   ├─ Found → Save to contacts.csv → NEXT LEAD
    │   └─ Not found (5min/3pages) → Mark "已识别联系人" → NEXT LEAD
    └─ NO → Continue search (max 5 min) → Timeout → Mark "低优先级" → NEXT LEAD
```

## Rule 6: Data Quality Standards

**Email classification:**
- `info@`, `admin@`, `contact@` → company_email (low value)
- `sales@`, `procurement@`, `accounts@` → department_email (medium value)
- `firstname.lastname@` → person_email (high value)
- `firstname@` → person_email (medium value, verify)

**Phone classification:**
- 1300/1800 numbers → company_phone (low value)
- Landline (02/03/07/08) → company_phone (medium value)
- Mobile (04xx) → person_phone (high value)

**Confidence levels:**
- High: Verified person contact (name + title + direct contact)
- Medium: Likely person contact (name + role match)
- Low: Company/department contact only

## Rule 7: Script Usage

**Standard extraction command:**
```bash
python scripts/extraction/extract_public_contact_candidates.py \
  --input reports/round1-queue.csv \
  --skip 0 --limit 10 --follow-links 3 \
  --fetcher static --skip-existing \
  --output-prefix "round-N-"
```

**Always use `--skip-existing` to avoid duplicate work**

## Rule 8: Report Review Priority

**Review candidates in this order:**
1. `key_person_name` (score 85-89) - Verify before saving
2. `email` with person patterns (score 100-114) - Classify and save
3. `phone` with mobile pattern (score 90-94) - Verify and save
4. `contact_form` (score 88) - Verify it's actual contact form
5. `team_link` / `contact_link` (score 68-76) - Manual review for KP

**DO NOT save without review:**
- LinkedIn URLs (need person/company fit verification)
- Role context snippets (need name/title confirmation)
- Company emails (need department classification)

## Rule 10: Run Report Generation

**每轮任务跑完后必须生成报告（表单收集、KP 富化、关键词发现等）：**
- 脚本：`scripts/reports/generate_run_report.py`
- 输出目录：`D:\TestProject-v3\reports\`
- 报告内容：进度快照、亮点、问题（可选）、系统优化（可选）
- 用 `--title` 区分任务类型，`--task` 描述本次具体任务
- 报告仅用于人类观察，agent 不需要回读
- 使用 `--auto-stats` 自动从 CSV 读取跑后统计
