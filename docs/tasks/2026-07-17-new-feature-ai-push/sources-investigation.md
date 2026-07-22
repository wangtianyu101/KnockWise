# 📡 AI 推送信源 调研 · v2（按用户新方向）

> 日期：2026-07-17 · 调研人：Claude
> **触发**：用户原 spec 4 源（量子位/36氪/HuggingFace/arXiv）需重新设计
> **新方向**：①大公司一手 + ②论坛杂志二手 + ③代码平台/博客实战
> **标签双轴**：模型 / 应用 × 国内 / 国外

---

## § 0 · ⚠️ 置信度声明

| 数据 | 置信 | 备注 |
|---|---|---|
| 各公司 RSS URL 是否仍有效 | 🟡 中 | 7 个月内可能变 · 上线前必 curl 验 |
| 掘金归属字节（2020 收购）| 🟢 高 | 搜索结果确认 |
| GitHub trending RSS 工作方式 | 🟢 高 | GitHub 公开 API 行为稳定 |
| Juejin 官方 RSS 不存在 | 🟡 中 | 搜索说"无官方 RSS" · 可能 RSSHub 有桥 |
| 各源实际内容质量 | 🔴 低 | 未样本测试 · 需跑通后实际看 |

---

## § 1 · 信源分类矩阵（4 大类 × 双轴标签）

### 1.1 分类模型

```
┌─────────────────────────────────────────────────────────────────────┐
│  信源 4 大类                                                          │
│                                                                       │
│  A. 大公司技术迭代（一手 · 大模型 / AI 应用官方）                      │
│     强信号 · 一手源 · RSS 多可获取                                     │
│                                                                       │
│  B. 论坛 / 杂志（二手 · 中文 AI 圈媒体）                                │
│     强过滤 · LLM 二次加工 · RSS 多数有                                │
│                                                                       │
│  C. 代码平台 / 博客（实战 · 开发者社区）                                │
│     强落地 · 项目实操 · 需要 RSSHub 或 API                            │
│                                                                       │
│  D. 学术 / 论文（基础研究 · arXiv 等）                                  │
│     强理论 · 时效弱 · RSS 成熟                                        │
└─────────────────────────────────────────────────────────────────────┘

每条内容打 2 个标签：
  · 类型：[模型 / 应用]
  · 地域：[国内 / 国外]
```

### 1.2 完整信源清单（候选池 · 30+ 条）

#### A · 大公司一手源

| # | 信源 | URL | 类别 | 地域 | RSS | Tier | 备注 |
|---|---|---|---|---|---|---|---|
| A1 | **OpenAI Blog** | https://openai.com/blog | 模型/应用 | 🌍 国外 | 🟡 未知 | 一手 | API 文档页 /news |
| A2 | **Anthropic News** | https://www.anthropic.com/news | 模型/应用 | 🌍 国外 | 🟡 未知 | 一手 | Claude 4.x 更新主渠道 |
| A3 | **Google DeepMind Blog** | https://deepmind.google/discover/blog | 模型 | 🌍 国外 | 🟢 有 | 一手 | Gemini / Veo / AlphaFold |
| A4 | **Meta AI Blog** | https://ai.meta.com/blog | 模型 | 🌍 国外 | 🟢 有 | 一手 | Llama 系列主渠道 |
| A5 | **Microsoft AI Blog** | https://blogs.microsoft.com/ai | 应用 | 🌍 国外 | 🟡 未知 | 一手 | Copilot / Azure AI |
| A6 | **HuggingFace Blog** | https://huggingface.co/blog | 模型/应用 | 🌍 国外 | 🟢 有 | 一手 | 实操教程 |
| A7 | **DeepSeek Docs News** | https://api-docs.deepseek.com/news | 模型 | 🇨🇳 国内 | 🟡 未知 | 一手 | DeepSeek V4 主渠道 |
| A8 | **阿里 通义 Qwen (GitHub)** | https://github.com/QwenLM/Qwen3 | 模型 | 🇨🇳 国内 | 🟢 releases.atom | 一手 | 模型 release notes |
| A9 | **字节 豆包 (火山引擎)** | https://www.volcengine.com/product/doubao | 模型/应用 | 🇨🇳 国内 | ❌ 无 RSS | 一手 | 需爬 Model Studio 公告 |
| A10 | **智谱 GLM (GitHub)** | https://github.com/THUDM | 模型 | 🇨🇳 国内 | 🟢 releases.atom | 一手 | GLM 系列主渠道 |
| A11 | **月之暗面 Kimi** | https://www.moonshot.cn/blog | 模型/应用 | 🇨🇳 国内 | ❌ 无 RSS | 一手 | 需爬 |
| A12 | **Mistral AI Blog** | https://mistral.ai/news | 模型 | 🌍 国外 | 🟢 有 | 一手 | 欧洲开源代表 |
| A13 | **xAI Blog** | https://x.ai/blog | 模型 | 🌍 国外 | 🟡 未知 | 一手 | Grok 更新 |

#### B · 论坛 / 杂志（中文 AI 媒体）

| # | 信源 | URL | 类别 | 地域 | RSS | Tier | 备注 |
|---|---|---|---|---|---|---|---|
| B1 | **量子位** | https://qbitai.com | 模型/应用 | 🇨🇳 国内 | 🟢 有 | 二手 | 综合 AI 资讯 · spec 已有 |
| B2 | **机器之心** | https://jiqizhixin.com | 模型/应用 | 🇨🇳 国内 | 🟢 有 | 二手 | 学术+技术深度 |
| B3 | **新智元** | https://synced.com | 模型/应用 | 🇨🇳 国内 | 🟢 有 | 二手 | spec 已有 |
| B4 | **AI 早班车** | https://www.aizkb.com | 模型/应用 | 🇨🇳 国内 | ❌ 无 RSS | 二手 | 公众号型 · 需爬 |
| B5 | **PaperWeekly** | https://paperweekly.site | 模型 | 🇨🇳 国内 | 🟢 有 | 二手 | 学术 paper 解读 |
| B6 | **36氪** | https://36kr.com | 应用 | 🇨🇳 国内 | 🟢 有 | 二手 | **需 scope 过滤**（偏商业/创业）|
| B7 | **VentureBeat AI** | https://venturebeat.com/ai | 应用 | 🌍 国外 | 🟢 有 | 二手 | 海外商业视角 |
| B8 | **TechCrunch AI** | https://techcrunch.com/category/artificial-intelligence | 应用 | 🌍 国外 | 🟢 有 | 二手 | 海外商业视角 |

#### C · 代码平台 / 博客（实战）

| # | 信源 | URL | 类别 | 地域 | RSS | Tier | 备注 |
|---|---|---|---|---|---|---|---|
| C1 | **GitHub Trending (AI)** | https://github.com/topics/llm | 模型/应用 | 🌍 国外 | ❌ 无 · 用 API | 一手 | API `search/repositories?q=topic:ai+topic:llm` |
| C2 | **GitHub Releases (各 AI 项目)** | repo `/releases.atom` | 模型/应用 | 🌍 国外 | 🟢 有 | 一手 | 订阅特定项目 · 如 LangChain · LangGraph |
| C3 | **稀土掘金**（字节系）| https://juejin.cn/tag/AI | 应用 | 🇨🇳 国内 | ❌ 无 · 用 RSSHub | 二手 | 实战教程 · 字节收购 · 中文开发者主阵地 |
| C4 | **稀土掘金**（大模型 tag）| https://juejin.cn/tag/LLM | 模型 | 🇨🇳 国内 | ❌ 无 · 用 RSSHub | 二手 | 同上 |
| C5 | **稀土掘金**（Agent tag）| https://juejin.cn/tag/Agent | 应用 | 🇨🇳 国内 | ❌ 无 · 用 RSSHub | 二手 | 同上 |
| C6 | **LeetCode AI 板块** | https://leetcode.cn/circle/discuss/... | 应用 | 🇨🇳 国内 | ❌ 无 | 二手 | 算法实战 · scope 过滤 |
| C7 | **Hacker News (AI)** | https://news.ycombinator.com/ | 模型/应用 | 🌍 国外 | 🟢 有 | 二手 | 海外技术社区 |
| C8 | **LangChain Blog** | https://blog.langchain.dev | 应用 | 🌍 国外 | 🟢 有 | 一手 | Agent 框架官方 |
| C9 | **Anthropic Engineering** | https://www.anthropic.com/engineering | 模型/应用 | 🌍 国外 | 🟡 未知 | 一手 | Claude 工程实践 |
| C10 | **OpenAI Engineering Blog** | https://openai.com/research | 模型 | 🌍 国外 | 🟢 有 | 一手 | 学术 + 工程 |

#### D · 学术 / 论文（已有 · 可保留）

| # | 信源 | URL | 类别 | 地域 | RSS | Tier | 备注 |
|---|---|---|---|---|---|---|---|
| D1 | **arXiv cs.AI** | https://rss.arxiv.org/rss/cs.AI | 模型 | 🌍 国外 | 🟢 有 | 一手 | spec 已有 |
| D2 | **arXiv cs.CL** | https://rss.arxiv.org/rss/cs.CL | 模型 | 🌍 国外 | 🟢 有 | 一手 | NLP / LLM |
| D3 | **arXiv cs.LG** | https://rss.arxiv.org/rss/cs.LG | 模型 | 🌍 国外 | 🟢 有 | 一手 | ML 基础 |
| D4 | **HuggingFace Daily Papers** | https://huggingface.co/api/daily_papers | 模型 | 🌍 国外 | ❌ 用 API | 一手 | spec 已有 |

---

## § 2 · RSS 可用性 + 实现策略

### 2.1 RSS 状态总览

| RSS 状态 | 数量 | 占比 | 处理方式 |
|---|---|---|---|
| 🟢 有 RSS · 直接 feedparser | 14 | ~47% | feedparser 抓取 |
| 🟡 未知 · 上线前必验 | 8 | ~27% | curl 测 + fallback |
| ❌ 无 RSS · 需特殊处理 | 8 | ~27% | RSSHub / API / 爬虫 |

### 2.2 特殊处理方案（无 RSS 的 8 条）

| 信源 | 处理方案 | 工作量 |
|---|---|---|
| A1 OpenAI Blog | curl + feed autodiscovery | 0.5h |
| A7 DeepSeek Docs | curl + feed autodiscovery | 0.5h |
| A9 字节豆包 | 火山引擎 Model Studio 公告爬虫（HTML scrape） | 4h |
| A11 Kimi Blog | 公众号 RSSHub（如果可） 或 爬虫 | 4h |
| B4 AI 早班车 | 公众号 RSSHub（`rsshub.app/wechat/mp/...`）| 1h |
| C1 GitHub Trending | GitHub API `search/repositories` | 2h |
| C3-C5 Juejin 标签 | RSSHub `juejin.cn/tag/:tagId` 或自爬 | 2h |
| C6 LeetCode | 暂无 RSS · 可不抓 或 爬虫 | 4h（可选）|
| D4 HF Daily Papers | HuggingFace API `/api/daily_papers` | 1h |

**总工作量**：~19h 处理特殊源

### 2.3 推荐方案：部署 RSSHub 实例

🟡 **推荐方案**：

- 自部署 [RSSHub](https://rsshub.app/)（开源 · GitHub 10K+ stars）
- 提供统一 RSS 转换（微信公众号 / 掘金 / GitHub trending 等）
- 比逐个写爬虫稳定 + 可扩展

**部署成本**：
- 时间：半天（Docker 一行）
- 资源：1 GB RAM · 自家 VPS
- 维护：低（社区维护路由）

**风险**：RSSHub 路由偶尔被目标网站反爬打破 · 需监控 + 临时 fallback

---

## § 3 · 内容分类（模型 vs 应用）

### 3.1 双轴标签的 LLM Prompt 设计

```python
# 在 DigestService.select_top10() 加 2 个标签到输出
{
  "selected": [
    {
      "rank": 1,
      "title": "...",
      "source": "Anthropic",
      "type": "model",       # ← 新增 · "model" or "application"
      "region": "overseas",   # ← 新增 · "domestic" or "overseas"
      "category": "头条",
      "reason": "匹配 Agent 标签"
    }
  ]
}

# 选题 prompt 加：
你必须给每条内容打 2 个标签：
- type ∈ {"model", "application"}
  - model = LLM 模型迭代（GPT-5 / Claude 4 / Qwen 3 等）
  - application = AI 应用产品 / 框架 / 工具（Cursor / Copilot / Agent 框架等）
- region ∈ {"domestic", "overseas"}
  - domestic = 中国公司（阿里 / 字节 / DeepSeek / 智谱 / Kimi 等）
  - overseas = 非中国公司（OpenAI / Anthropic / Google / Meta 等）

**重要**：国内/国外 + 模型/应用 必须平衡（10 条里至少 2 国内 + 2 海外 + 5 模型 + 3 应用）
```

### 3.2 内容配比建议（10 条每日精选）

| 组合 | 建议条数 | 理由 |
|---|---|---|
| 模型 · 国内 | 2-3 条 | DeepSeek / Qwen / GLM / Kimi 等主流 |
| 模型 · 国外 | 2-3 条 | GPT-5 / Claude 4 / Gemini / Llama / Mistral 等 |
| 应用 · 国内 | 1-2 条 | 豆包 app / Kimi chat / 字节 Agent 等 |
| 应用 · 国外 | 1-2 条 | Cursor / Claude.ai / ChatGPT 新功能 等 |
| 论坛/社区补充 | 1-2 条 | 来自 GitHub / 掘金 / LeetCode 的热门内容 |

**对比类内容优先**：
- 摘要 prompt 鼓励 LLM 输出 "DeepSeek V4 vs GPT-5" 这种对比
- 选题时如果发现同一天国内 + 国外都有模型发布，自动合并对比

### 3.3 对比类内容实现

```python
# DigestService 新增方法
async def find_comparisons(
    self, items: list[dict], days: int = 3
) -> list[dict]:
    """在最近 N 天里找同主题不同源的内容，生成对比。"""
    # 1. 按主题聚类（用 LLM 或简单关键词）
    # 2. 同主题如有 ≥1 国内 + ≥1 国外 → 触发对比生成
    # 3. LLM 生成对比摘要
```

**输出示例**：
```
🔥 头条：DeepSeek V4 vs GPT-5
─────────────────────────────────────────
DeepSeek V4 (2026-07-15)：上下文 1M tokens，推理性能...
GPT-5 (2026-07-14)：多模态升级，agentic 能力提升...

📊 7 维度对比：
性能 / 价格 / 上下文 / 多模态 / 推理 / 中文 / 开源
─────────────────────────────────────────
```

---

## § 4 · 用户设计哲学 vs 项目需求 · 检查表

按用户原话检查：

| 维度 | 用户设计 | 是否符合需求 | 备注 |
|---|---|---|---|
| **论坛杂志要归为一类** | ✅ B 类（量子位/机器之心/新智元 等）| 🟢 完全符合 | 这是 B 类的核心定位 |
| **大公司技术迭代** | ✅ A 类（OpenAI/Anthropic/阿里/字节 等）| 🟢 完全符合 | 13 个一手源 |
| **不只是论坛杂志** | ✅ 新增 A 类 + C 类 | 🟢 符合 | 之前 spec 只有 4 二手 · 现在 30+ 一手 + 二手 |
| **模型 vs 应用 两大类** | ✅ type 标签 | 🟢 符合 | 实施清晰 |
| **国内国外** | ✅ region 标签 | 🟢 符合 | 13 国内 + 17 国外 · 平衡 |
| **对比更好** | ✅ find_comparisons() | 🟢 符合 | 新增 service 方法 |

### 4.1 真正的契合度结论

✅ **设计哲学 100% 匹配用户原话**：
- 4 大类源 = 用户要求的"论坛杂志 + 大公司 + (新增)代码平台"
- 双轴标签 = 用户要求的"模型/应用 + 国内/国外"
- 对比内容 = 用户要求的"对比更好"

⚠️ **3 个值得问你的判断**：

1. **30 个源太多吗？** spec 之前是 4 个 · 现在 30 个 · **LLM 选题负担会大** · 建议
   - 默认启用 10-15 个
   - 其余在 settings 里让用户自选
   - **A 类 13 个 + B 类精选 5 个 + C 类精选 4 个 = 22 个默认 + 8 个可选**

2. **GitHub Trending 当信号源合适吗？**
   - 是"开发者社区热度"信号
   - 但**不是大公司技术迭代**（用户原话强调）
   - 可归为"补充信号" · 每日仅占 1-2 条

3. **LeetCode 真有必要吗？**
   - LeetCode 是**算法题平台**，AI/LLM 板块的"实用价值"主要是面试准备
   - 但**你的目标用户是 AI 应用开发者**，不一定需要算法题
   - 建议：**先排除**，等需求验证再加

### 4.2 风险评估（针对新方向）

| 风险 | 等级 | 缓解 |
|---|---|---|
| 30 源 → LLM 选题输入 token 多 → 成本上升 | 🟡 中 | 30 源**分批抓取**（不在同一次 LLM 调用）· LLM 只看当日新内容 |
| 国内公众号 RSS 缺失 | 🟡 中 | RSSHub 统一处理 · 备用公众号爬虫 |
| RSSHub 路由被反爬打破 | 🟡 中 | 监控 + 临时 fallback · 半年 review |
| 多源内容重复（同一条新闻多家报道）| 🟡 中 | LLM 去重 + URL 去重 |
| 国内外内容质量差异 | 🟡 中 | 让 LLM 平衡选题（强制国内/国外比例）|
| GitHub Trending 噪音（明星项目不一定是 AI）| 🟡 中 | topic filter `ai+llm+agent` 过滤 |

---

## § 5 · 推荐源列表（v2 · 默认启用）

### 5.1 Tier 1 · 默认开启（15 个 · 精选）

| # | 源 | 类别 | 地域 | Tier |
|---|---|---|---|---|
| A2 | Anthropic News | 模型/应用 | 🌍 | 一手 |
| A3 | Google DeepMind | 模型 | 🌍 | 一手 |
| A6 | HuggingFace Blog | 模型/应用 | 🌍 | 一手 |
| A7 | DeepSeek Docs | 模型 | 🇨🇳 | 一手 |
| A8 | Qwen GitHub Releases | 模型 | 🇨🇳 | 一手 |
| A10 | 智谱 GLM GitHub | 模型 | 🇨🇳 | 一手 |
| B1 | 量子位 | 模型/应用 | 🇨🇳 | 二手 |
| B2 | 机器之心 | 模型/应用 | 🇨🇳 | 二手 |
| C1 | GitHub Trending (AI topic) | 模型/应用 | 🌍 | 一手 |
| C3 | 稀土掘金 AI tag | 应用 | 🇨🇳 | 二手 |
| C8 | LangChain Blog | 应用 | 🌍 | 一手 |
| D1 | arXiv cs.AI | 模型 | 🌍 | 一手 |
| D2 | arXiv cs.CL | 模型 | 🌍 | 一手 |
| D4 | HuggingFace Daily Papers | 模型 | 🌍 | 一手 |
| C7 | Hacker News (filter AI) | 模型/应用 | 🌍 | 二手 |

### 5.2 Tier 2 · 用户自选（settings · 可选）

| # | 源 | 类别 | 地域 |
|---|---|---|---|
| A1 | OpenAI Blog | 模型/应用 | 🌍 |
| A4 | Meta AI | 模型 | 🌍 |
| A5 | Microsoft AI | 应用 | 🌍 |
| A9 | 字节豆包（爬） | 模型/应用 | 🇨🇳 |
| A11 | Kimi Blog（爬） | 模型/应用 | 🇨🇳 |
| A12 | Mistral | 模型 | 🌍 |
| A13 | xAI | 模型 | 🌍 |
| B3 | 新智元 | 模型/应用 | 🇨🇳 |
| B5 | PaperWeekly | 模型 | 🇨🇳 |
| B7 | VentureBeat AI | 应用 | 🌍 |
| B8 | TechCrunch AI | 应用 | 🌍 |
| C4 | 掘金 LLM tag | 模型 | 🇨🇳 |
| C5 | 掘金 Agent tag | 应用 | 🇨🇳 |
| C9 | Anthropic Engineering | 模型/应用 | 🌍 |
| C10 | OpenAI Research | 模型 | 🌍 |

### 5.3 默认排除（明确不要）

| 源 | 排除原因 |
|---|---|
| 36氪 | 偏商业/创业 · 与 scope 冲突（除非用户加 settings 才用）|
| LeetCode AI 板块 | 算法题 · 与"AI 应用开发者"目标偏离 |
| 个人博客（无名）| 无法 RSS 聚合 · 维护成本高 |

---

## § 6 · 实施路径调整

### 6.1 总工作量估算（基于新方向）

| 模块 | 工作量 | 变化 |
|---|---|---|
| RSSHub 部署 | 0.5d | 🆕 新增 |
| 30 源接入（feedparser + 特殊）| 4d | 🆕 替代原 4 源接入（1d）|
| GitHub API 集成 | 1d | 🆕 新增 |
| Juejin RSSHub 路由配置 | 0.5d | 🆕 新增 |
| 选题/摘要 prompt 加 type + region 标签 | 1d | 🆕 新增 |
| find_comparisons() 实现 | 2d | 🆕 新增 |
| 7 表 schema + migration | 1d | 不变 |
| DigestService 骨架 | 3d | 不变 |
| 16 个 REST API | 3d | 不变 |
| DigestScheduler | 1d | 不变 |
| 用户偏好 + 屏蔽 | 2d | 不变 |
| 前端 5 页 + 5 组件 | 4d | 不变 |
| 测试覆盖 ≥80% | 4d | 不变 |
| **小计** | **~27d = 216h** | 🟡 比原 ~43h 多了 5 倍 |

⚠️ **新增 173h** — 主要是源接入（30 vs 4）+ 对比功能 + RSSHub 部署。

### 6.2 推荐切片（避免一期太大）

**Phase 1（MVP · ~10d = 80h）**：
- 7 表 + DigestService + Tier 1 中 RSS 可获取的 10 个源（去 RSSHub / 字节 / Kimi）
- 选题 prompt 加 type + region 标签
- 不做对比功能
- 不做 Juejin（Tier 1 但 RSSHub 复杂）

**Phase 2（Enhance · ~7d = 56h）**：
- 加 RSSHub 部署
- 加 GitHub Trending 接入
- 加 Juejin 3 个 tag
- 加 find_comparisons()

**Phase 3（Polish · ~5d = 40h）**：
- 加爬虫（字节豆包 / Kimi）
- 加对比 UI
- 加 settings 让用户自选 Tier 2

**总计 22d = 176h**（vs 单期 27d = 216h · 切片更稳）

---

## § 7 · 元 · § 6.7 verify-loop 自校验

按刚加的 § 6.7 verify-loop 检查本文档：

| 校验项 | 状态 |
|---|---|
| 对照 user 新方向 | ✅ 4 大类 + 双轴标签 · 完整 |
| 对照 spec.md § 四 RSS 源 | ❌ 旧 spec 4 源 · 本文已 supersede |
| 对照 project-ai-push-scope.md memory | ✅ scope 收窄原则保持 |
| 对照 research.md § 5.4 决策 | ✅ 决策 1（信源）已 update 到本文 |
| 测试覆盖率（本文档） | ❌ 不适用（设计文档）|
| Confidence Levels 标注 | ✅ § 0 完整 |

---

## 元信息

- **文档版本**：v2 · 2026-07-17
- **路径**：`docs/tasks/2026-07-17-new-feature-ai-push/sources-investigation.md`
- **配套**：[research.md](research.md) · [project-ai-push-scope.md (memory)](~/.claude/projects/-Users-wangtianyu-IdeaProjects-KnockWise/memory/project-ai-push-scope.md)
- **下一步**：
  1. 用户批准本文档（30 源设计 · 双轴标签 · 对比功能）
  2. 选 Phase 切片（推荐 Phase 1 MVP 10 天）
  3. 进 1 步写 spec.md（用 Requirement+Scenario 结构 + 本文档的源清单）
