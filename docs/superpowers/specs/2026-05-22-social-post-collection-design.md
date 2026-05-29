# 社媒帖子收集与 Agent 训练素材系统设计

**日期:** 2026-05-22
**状态:** 草稿
**作者:** Claude Code

## 1. 目标

为 Ron Group 建立社媒帖子收集、分类、训练素材生成系统，支撑：
- **Agent 训练素材：** 收集优秀帖子作为 few-shot examples，训练 AI agent 自动写帖子
- **品牌内容营销：** 为 LinkedIn / Instagram / Facebook 平台产出有特色的品牌内容

**帖子"有特色"的定义：**
- 有人格化 / 真实感（像真人写的，不像 AI 模板）
- 有独特观点 / 争议性（能引发讨论）
- 有本地化 / 时效性（结合澳洲本地文化、时事）
- 有故事性 / 叙事结构（有起承转合）

## 2. 方案选型

| 方案 | 描述 | 采纳 |
|------|------|------|
| A: 搜索引擎发现 | CloakBrowser + Google 搜索发现公开帖子 | 采纳 |
| B: 平台 API 直连 | LinkedIn/Facebook API 拉取 | 暂不采纳（审批周期长） |
| C: 人工精选 | 手动保存优秀帖子 | 采纳（补充高质量种子） |

**最终方案：A + C 混合** — 方案 A 负责规模化发现，方案 C 负责高质量补充。

## 3. 数据模型

### 3.1 主数据文件：`data/social_posts.csv`

| 字段 | 类型 | 说明 |
|------|------|------|
| `post_id` | string | 唯一 ID，格式 `{平台缩写}-{日期}-{序号}`，如 `LI-20260522-001` |
| `platform` | enum | `linkedin` / `instagram` / `facebook` |
| `source_url` | string | 原帖链接 |
| `author_name` | string | 发帖人/品牌名 |
| `author_type` | enum | `peer`（行业同行）/ `cross_industry`（跨行业） |
| `content_text` | string | 帖子正文 |
| `content_type` | enum | 产品展示 / 客户案例 / 行业洞察 / 团队文化 / 活动推广 / 观点表达 |
| `tone_style` | enum | 正式商务 / 轻松幽默 / 故事型 / 数据驱动 / 观点犀利 |
| `industry_theme` | enum | 供应链 / 设备 / 食品安全 / 可持续 / 本地化 / 技术 / 其他 |
| `distinctive_tags` | string | 人格化 / 独特观点 / 本地化 / 故事性（逗号分隔，可多选） |
| `engagement_score` | int | 互动指标（点赞+评论+分享，如可获取，否则留空） |
| `language` | enum | `en` / `zh` |
| `collected_date` | date | 收集日期 |
| `quality_rating` | int | 1-5 人工/AI 评分 |
| `training_flag` | bool | 是否用于训练（quality >= 3 且 distinctive_tags 命中 >= 2 → true） |
| `source_type` | enum | `auto`（自动抓取）/ `manual`（人工补充） |
| `notes` | string | 备注 |

### 3.2 Few-shot Examples：`data/social_post_examples.md`

按分类维度组织的精选帖子全文，Markdown 格式，直接用于 agent 写帖的 few-shot prompting。

### 3.3 结构化训练数据：`data/social_training_data.jsonl`

JSONL 格式，每行一条：
```json
{
  "input": {
    "content_type": "观点表达",
    "tone": "观点犀利",
    "theme": "供应链",
    "platform": "linkedin"
  },
  "output": "帖子全文...",
  "metadata": {
    "quality": 5,
    "distinctive_tags": ["独特观点", "本地化"]
  }
}
```

### 3.4 人工暂存区：`data/manual_posts_queue.md`

临时文件，人工粘贴帖子原文 + URL，脚本定期解析合并到 `social_posts.csv`。

## 4. 收集管线

### 4.1 搜索引擎发现（方案 A）

**脚本：** `scripts/social/collect_posts.py`

**依赖：** `scripts/kp_pipeline/cloak_fetcher.py`（已有 CloakBrowser 基础设施）

**流程：**
1. 读取 `config/social_search_keywords.json`（搜索词配置）
2. 调用 `search_google()` 批量搜索
3. 对每个结果 URL，用 `cloak_fetch()` 抓取帖子原文
4. 提取：帖子文本、作者信息、平台标识
5. 按 `source_url` 去重（对比 `data/social_posts.csv` 中已有记录）
6. 写入 `data/social_posts.csv`，`source_type` = "auto"

**搜索词模板（`config/social_search_keywords.json`）：**
```json
{
  "industry_peer": [
    "site:linkedin.com \"Australian restaurant\" supplier announcement",
    "site:linkedin.com \"food service\" Australia post",
    "site:instagram.com \"Australian hospitality\" supplier",
    "site:facebook.com Australian restaurant equipment"
  ],
  "cross_industry": [
    "site:linkedin.com B2B brand storytelling case study",
    "site:linkedin.com \"supply chain\" brand post engaging"
  ]
}
```

**速率控制：** 每次搜索间隔 3-5 秒，避免触发 Google 429。

### 4.2 人工补充（方案 C）

**方式 1：手动暂存**
- 浏览器看到好帖子 → 复制文本 + URL → 粘贴到 `data/manual_posts_queue.md`
- 格式：`---` 分隔每条帖子，包含 URL 和原文

**方式 2：Dashboard 录入（可选扩展）**
- 在现有 dashboard 中增加"社媒帖子"tab
- 手动填写字段，保存到 CSV

**合并脚本：** `scripts/social/merge_manual_posts.py`
- 读取 `manual_posts_queue.md`
- 解析帖子内容
- 生成 post_id，合并到 `social_posts.csv`，`source_type` = "manual"
- 清空已处理的条目

## 5. AI 分类系统

### 5.1 分类流程

**脚本：** `scripts/social/classify_posts.py`

**流程：**
1. 读取 `social_posts.csv` 中 `content_type` 为空的行
2. 调用 Claude API，传入帖子文本 + 分类 prompt
3. 返回三维度分类 + 特色标签 + 质量评分
4. 写回 CSV

### 5.2 分类维度值域

**内容类型（6 类）：**
| 值 | 定义 |
|----|------|
| 产品展示 | 发布新产品、功能更新、产品特性介绍 |
| 客户案例 | 客户故事、成功案例、合作成果 |
| 行业洞察 | 行业趋势分析、数据报告、市场观察 |
| 团队文化 | 员工故事、公司价值观、内部活动 |
| 活动推广 | 展会参展、促销活动、发布会 |
| 观点表达 | 行业观点、争议性话题、立场声明 |

**语气风格（5 类）：**
| 值 | 定义 |
|----|------|
| 正式商务 | 专业、权威、结构化 |
| 轻松幽默 | 口语化、有梗、亲和力 |
| 故事型 | 叙事驱动，有起承转合 |
| 数据驱动 | 以数据/图表为核心论据 |
| 观点犀利 | 有明确立场，敢下判断 |

**行业主题（7 类）：**
| 值 | 定义 |
|----|------|
| 供应链 | 采购、物流、供应商关系 |
| 设备 | 厨房设备、酒店设施、维护 |
| 食品安全 | 合规、认证、HACCP、标准 |
| 可持续 | 环保、可持续发展、减废 |
| 本地化 | 澳洲本地食材、本地合作、社区 |
| 技术 | 数字化、自动化、SaaS、AI |
| 其他 | 不属于以上分类 |

**特色标签（4 类，多选）：**
| 值 | 定义 |
|----|------|
| 人格化 | 有个人经历、情感、第一人称叙事 |
| 独特观点 | 反直觉视角、挑战行业共识 |
| 本地化 | 澳洲本地文化、地名、行业梗 |
| 故事性 | 有故事线、有转折、有细节 |

### 5.3 质量评分标准

| 分数 | 标准 |
|------|------|
| 5 | 叙事出色、人格化强、观点独特、可直接作为训练范本 |
| 4 | 质量好，有 1-2 个特色亮点 |
| 3 | 合格，可作为训练素材但需要搭配更好的示例 |
| 2 | 一般，缺乏特色，不建议用于训练 |
| 1 | 低质量，模板化或内容空洞 |

**training_flag 判定规则：**
- quality_rating >= 3 AND distinctive_tags 命中 >= 2 → `true`
- 否则 → `false`

### 5.4 分类 Prompt 结构

```
你是一个社媒内容分析专家。请对以下帖子进行分类。

## 分类维度
[维度定义和值域]

## 示例
[2-3 个已分类帖子]

## 待分类帖子
{帖子文本}

## 输出格式（JSON）
{
  "content_type": "...",
  "tone_style": "...",
  "industry_theme": "...",
  "distinctive_tags": ["...", "..."],
  "quality_rating": N,
  "reasoning": "简要说明分类理由"
}
```

随着帖子库增大，few-shot examples 从 `social_post_examples.md` 中动态选取同维度的高质量示例。

## 6. 训练素材生成

### 6.1 Few-shot Examples 生成

**脚本：** `scripts/social/generate_training_data.py`

**流程：**
1. 从 `social_posts.csv` 筛选 `training_flag = true` 的帖子
2. 按 `content_type` + `tone_style` 分组
3. 每组按 `quality_rating` 降序，取 top N
4. 输出到 `data/social_post_examples.md`，格式：

```markdown
## 观点表达 + 观点犀利 + 供应链

### Example 1: Aussie Food Co (LinkedIn, 评分 5/5)
> 帖子全文...

**特色标签:** 独特观点, 本地化

### Example 2: Another Co (LinkedIn, 评分 4/5)
> 帖子全文...

**特色标签:** 人格化, 独特观点
```

### 6.2 JSONL 训练数据生成

同一脚本同时输出 `data/social_training_data.jsonl`，用于未来微调。

## 7. Agent 写帖流程

### 7.1 写帖配置

**文件：** `config/social_post_writing.json`

```json
{
  "brand_voice": "专业但不冷冰冰，有温度，敢表达观点",
  "platform_rules": {
    "linkedin": {
      "max_length": 3000,
      "hashtag_limit": 5,
      "style": "professional"
    },
    "instagram": {
      "max_length": 2200,
      "hashtag_limit": 30,
      "style": "visual_first"
    },
    "facebook": {
      "max_length": 63206,
      "hashtag_limit": 5,
      "style": "conversational"
    }
  },
  "forbidden_patterns": [
    "best in class",
    "world leading",
    "synergy",
    "leverage",
    "innovative solutions"
  ],
  "required_elements": [
    "specific_number_or_data",
    "local_reference_or_story"
  ]
}
```

### 7.2 写帖流程

1. **读取配置：** `social_post_writing.json`
2. **选取 few-shot examples：** 从 `social_post_examples.md` 中按目标分类维度选取 2-3 个示例
3. **读取行业上下文：** 结合 `data/leads.csv` 中的行业数据、客户画像
4. **生成帖子：** agent 基于 few-shot examples + 约束 + 上下文生成
5. **自评打分：** agent 按 4 个特色维度自评，确保至少命中 2 个
6. **输出：** 帖子文本 + 自评报告

## 8. 目录结构

```
data/
  social_posts.csv                # 帖子主数据
  social_post_examples.md         # 精选 few-shot examples
  social_training_data.jsonl      # 结构化训练数据
  manual_posts_queue.md           # 人工暂存区

config/
  social_search_keywords.json     # 搜索词配置
  social_post_writing.json        # 写帖约束配置

scripts/
  social/
    collect_posts.py              # 搜索引擎发现脚本
    classify_posts.py             # AI 自动分类脚本
    generate_training_data.py     # 生成训练素材
    merge_manual_posts.py         # 合并人工补充帖子
```

## 9. 实施步骤

1. **Phase 1 — 基础设施：** 创建目录结构、数据文件、配置文件
2. Phase 2 — 收集脚本： 实现 `collect_posts.py`（搜索引擎发现）和 `merge_manual_posts.py`（人工合并）
3. **Phase 3 — 分类脚本：** 实现 `classify_posts.py`（AI 自动分类）
4. **Phase 4 — 训练素材：** 实现 `generate_training_data.py`（生成 few-shot examples 和 JSONL）
5. **Phase 5 — 写帖配置：** 创建 `social_post_writing.json`，建立 agent 写帖流程

## 10. 风险与限制

- **帖子抓取受限：** LinkedIn/Instagram/Facebook 有反爬措施，只能抓到 Google 索引的公开帖子
- **元数据不完整：** 互动数据（点赞/评论）可能无法获取
- **分类准确性：** AI 分类初期可能不准，需要人工校准 prompt
- **帖子版权：** 收集的帖子仅用于学习分析，不直接复制使用
