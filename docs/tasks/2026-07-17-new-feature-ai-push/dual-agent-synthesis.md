# 🔀 AI 推送 · 双 Agent 对抗调研 聚合报告

> 日期：2026-07-17 · 调研模式：2 Agent parallel + 我（synthesis agent）聚合
> Agent 1：机会最大化 · 13 个 opportunities
> Agent 2：红队审稿 · 7 risks + 8 weak assumptions
> 来源：上方两 agent 完整 output

---

## § 0 · 聚合框架

| 维度 | 含义 |
|---|---|
| **CONVERGENCE** | 两 agent 都看出的事 = 高信号 · 你必须看 |
| **DIVERGENCE** | 一边说好的 / 另一边说坏的 = 你拍板 |
| **CRITICAL** | 一边说"最严重" / 另一边没说 = 也得看（红队的责任是提醒）|
| **NEW** | 我（聚合 agent）从两边读出来的洞察 · 不在两边原文中 |

---

## § 1 · CONVERGENCE（双方都看出 · 高信号 · 必看）

### C1 · 5 条固定 vs 1-5 可变 — **双方反对当前"可变"**

| 来源 | 立场 |
|---|---|
| Agent 2 红队 Risk 2 | "Variable 1–5 sabotages habit formation · 用户收到 1 条三次后会 mute · Morning Brew / TLDR 都是固定条数" |
| Agent 1 机会 O2 | "5 条不是'今天的我'是'我订阅的世界' · 周报 deterministic 是 retention KPI 抓手" |

**✅ 聚合结论**：**固定 5 条**（不再可变 1-5）· vibe 改成"内容级注释"不是"长度变化"

### C2 · 邮件不是中国主力渠道 — 双方都提到

| 来源 | 立场 |
|---|---|
| Agent 2 红队 Risk 7 | "Email deliverability for new domains is brutal · 国内用户邮件打开率 < 10% · MVP 缺中国原生渠道" |
| Agent 1 机会 O9 | "公众号模板消息 = 国内分发护城河 · 送达率 > 80% · Feedly/TLDR 都没公众号触达" |

**✅ 聚合结论**：MVP 必须**并行** 飞书/钉钉 webhook（2-3 天可上）+ 公众号资质**立即启动**（4-6 周走流程）

### C3 · LLM 选题需要 fact-check / 引用 — 双方都提

| 来源 | 立场 |
|---|---|
| Agent 2 红队 Risk 5 | "LLM hallucination of numbers · LLM 对 DeepSeek 自家新闻有 bias · 需要 factuality check" |
| Agent 1 机会 O7 | "每条 digest 加「来源 3 篇 / 昨日相关 / 上周对比」三段引用 · 信任成本 ↓ · URL 永久化" |

**✅ 聚合结论**：每条 digest 必须有 `source_url` + `related_digest_ids` + 可点击溯源 · schema 必含

### C4 · 信源数量上限 — 双方都倾向少而精

| 来源 | 立场 |
|---|---|
| Agent 2 红队 § 4.3 | "RSS reader fatigue show best results at 8–15 well-chosen sources · 30 源太多 LLM tokens" |
| Agent 1 机会 全文 | 14 opportunities 多次强调"做深"而非"做多" · O4 "GitHub Trending 做深" · O13 "Open API" |

**✅ 聚合结论**：信源从 30+ 降到 **5-8 核心** + 用户可加自选 · 不是"30 默认"

### C5 · 公众号 + 国内渠道是核心 — 双方共识

| 来源 | 立场 |
|---|---|
| 红队 Risk 7 | "MVP launch 缺中国原生渠道" |
| 机会 O9 | "公众号 = 战略级 moat" |

**✅ 聚合结论**：**公众号资质立即申请**（4-6 周走流程 · 不阻塞 P0 编码）

---

## § 2 · DIVERGENCE（双方分歧 · 你拍板）

### D1 · "用户到底要这个吗？" — 最大分歧

| 红队 | 机会 |
|---|---|
| "**The design is solving a problem the audience does not have** · AI 开发者已经自建 curating pipeline · KnockWise 是**功能 inside mock interview** · 用 upsell 心态做 daily push 会让用户反感" | "用户确实有需求（数据 5 项 weekly tracking 是 retention 抓手） · 差异化通过 enhancement · 不是基础需求错" |

**🟡 双方其实都承认有需求，但深度不同：**
- 红队认为：基础需求**已被满足**（Twitter/HN/RSS reader）· KnockWise 是**第 5 个同类工具**
- 机会认为：基础需求**满足但体验差**（碎片化 · 散在多处）· KnockWise 是**唯一一站式 + 国内公众号分发**

**🎯 你的判断点**：
- A. 接受红队"换 framing" → 把"AI 推送"改成"**peer-attention 信号**"（用户看到的不是"今天 AI 圈发生啥"而是"**和你角色类似的开发者最近在看啥**"）
- B. 接受机会"enhance 当前" → 维持 daily digest framing · 加 14 项 enhancements
- C. **混合**（推荐）→ 维持 daily digest 是入口体验 · "peer attention" 作为周报版（watchlist + 周对比 = peer signal）

### D2 · 信源 list 数量 — 数字分歧

| 红队 | 机会 |
|---|---|
| "5 sources (not 30) · 30 sources means more LLM tokens to filter · best results at 8–15 well-chosen" | "30+ 是合理的（多源入 · 少条出）· 关键是打分筛选" |

**✅ 实际上不冲突**：红队说"5 sources"指最终输出；机会说"30 sources"指信号池。**聚合结论**：**信号池可大（30-50）· 输出必小（5 条固定）· 中间是综合打分** · 你之前的设计方向是对的

### D3 · 是否需要"peer-attention signal"做产品差异化

| 红队 | 机会 |
|---|---|
| "**Peer-group signal is the unmet need here**. Not summary, not curation, not 'vibe' — **evidence of peer attention**" | 14 个 opportunity 都没明确提 peer-attention · 重点是 enhancement · moat = 用户行为数据 + 渠道 |

**🎯 你是否要做 peer-attention feature？**

- A. **做**（推荐看 MVP 完成度）：O11 embedding 个性化 + 加 peer-collaborative filtering · 实现复杂但 moat 强
- B. **不做** · 维持 LLM curator 单一路径 · 风险：被低成本复制
- C. **MVP 后做**（推荐）· Phase 1 先把 daily digest 做稳 · Phase 2 加 peer signal

---

## § 3 · CRITICAL（红队最严重 · 机会没反驳 · 必看）

### X1 · "The design is solving a problem the audience does not have"

> 红队原话："The target audience — AI application developers, Agent builders, large-model practitioners — already has fully-functional, well-tuned, self-curated AI news pipelines."

**✅ 聚合结论**：这句话**值得你内化**。即使你决定做 AI push，也需要意识到这是**红海 + 已有工具做得不错**的市场。

应对方式（双方都暗含）：
- ✅ 公众号（机会 O9 · 红队 Risk 7）= **国内独占渠道**
- ✅ Obsidian 双向（机会 O6）= **唯一与用户笔记共生**
- ✅ Open API / MCP（机会 O13）= **给 AI 开发者用 AI 工具**

### X2 · 评估期 6-8 周

> 红队原话："Habit formation requires 6-8 weeks of daily engagement. The product team will likely misinterpret 'users not opening' as 'feature broken', pivot prematurely, abandon."

**✅ 聚合结论**：MVP 完成后**至少留 6-8 周不评估** · 设 day-14 retention < 20% = 终止实验 · 否则继续看 day-28 / day-56

### X3 · KnockWise 是**功能 inside mock interview** 不是独立 newsletter

> 红队原话："KnockWise is not a newsletter-first product — it's a mock interview platform adding a newsletter feature. The wedge logic is reversed: a user comes for interviews and AI push is an upsell, vs. a user comes for AI push and may later take interviews. This matters for retention math."

**✅ 聚合结论**：**AI push 应该作为 interview 用户的"低频奖励"** 而非独立 daily ritual · 推送频次可能不该每日 · 可以是 interview 后 / 弱信号日 / 周末单条

---

## § 4 · NEW（聚合洞察 · 不在两边原文中）

### N1 · "Daily push" 应该被**改造**

红队说"8 AM 是错的" · 机会说"daily habit 形成" · 但其实**两者都隐含同样的洞察**：

> **真正的 daily 是"用户心里想着'今天我打开 KnockWise' 而不是'我等邮件'"**

**✅ 新建议**：把 push 改成 **"pull-based daily"**——
- 不是"系统发邮件" · 而是"用户打开 KnockWise 时显示今日 5 条"
- 邮件是**复述**（用户已读过的内容备份）
- 微信是**通知**（"今日 digest 已就绪"）
- 主体验在 KnockWise Web/App

**为什么更好**：
- KnockWise 是 mock interview 工具 · 用户已经习惯打开它
- 推送变成"用户登录后的天然起点" · 不是"邮件客户端里的入侵者"
- 减少推送疲劳（红队 X2）

**实现代价**：原 spec 的 "push 渠道" 改成"门户展示" · 邮件/微信退化为"通知 + 备份"

### N2 · "对比自动播报" 应该是主功能不是辅助

机会 O3 提到"对比做成栏目" · 但实际**用户心理角度**，对比比 digest 本身价值更高：

> 当用户看到"GPT-5 vs DeepSeek V4 7 维度对比表" · 这是**截图驱动分享** · AI 圈用户最爱 · 比 5 条分散 digest 强 3-5x

**✅ 新建议**：把对比作为**周报主线**（周一推送"上周模型对比"）· daily digest 是**新闻** · 周报对比是**知识**

### N3 · Watchlist = moat 起点（不是 enhancement）

机会 O2 说"watchlist 是 low effort + high impact" · 但实际**这是个人数据沉淀的起点**：

- 用户 starred X · 系统知道用户关注 X
- 用户 starred X 100 次 · 系统知道用户的"领域画像"
- 1000 用户 × 100 starred = **10 万次信号** = 训练 embedding 模型的 corpus

**✅ 新建议**：把 watchlist 当作**核心数据资产** · 不是 feature · 是 **future moat 的种子**

---

## § 5 · 聚合后的 design 优先级（重排 research.md § 5.2）

### 5.1 必须做（双方共识 · 阻塞实施）

| 优先级 | 行动 | 来源 | 工作量 |
|---|---|---|---|
| 🔴 P0-1 | **固定 5 条 · 不再可变** | C1 | 0.5d（service 重命名）|
| 🔴 P0-2 | **每条 digest 必须含 source_url + 引用溯源** | C3 | 0.5d（schema 加字段）|
| 🔴 P0-3 | **信源默认 5-8 核心 + 用户可加自选** | C4 | 1d（settings UI）|
| 🟡 P1-1 | **公众号资质立即申请**（4-6 周走流程 · 不阻塞 P0）| C5 + 红队 Risk 7 | 0（申请工作）|
| 🟡 P1-2 | **MVP 完成后 6-8 周不评估**（commit to this）| X2 | 0（约定）|

### 5.2 强烈建议（机会派独大 · 必做）

| 优先级 | 行动 | 来源 | 工作量 |
|---|---|---|---|
| 🟢 P2-1 | **关注追踪 (watchlist) — 1 周内上线** | 机会 O2 + N3 | 5d |
| 🟢 P2-2 | **GitHub Trending 独立页** | 机会 O4 | 4d |
| 🟢 P2-3 | **对话式 digest**（用户追问 AI 编辑）| 机会 O1 | 2 周 |
| 🟢 P2-4 | **Obsidian 双向同步** | 机会 O6 + N3 | 1 周 |

### 5.3 战略级（4-6 周以后）

| 优先级 | 行动 | 来源 |
|---|---|---|
| 🔵 P3-1 | **公众号模板消息上线** | 机会 O9 + 红队 Risk 7 |
| 🔵 P3-2 | **Open API / MCP endpoint** | 机会 O13 |
| 🔵 P3-3 | **用户 embedding 个性化** | 机会 O11 |

### 5.4 不该做（红队 + 机会都不支持）

- ❌ macOS notification（P1 暂缓是对的）
- ❌ 微信小程序
- ❌ 自研播客 App

---

## § 6 · 新增的待拍板问题（2 个）

### Q1 · "Daily push" 应该改成 "Pull-based daily" 吗？

**当前 design**：邮件 + 微信主动推 5 条
**新选项 N1**：邮件/微信只发"今日 digest 已就绪"通知 · 用户打开 KnockWise 看 5 条

| 选项 | 优势 | 劣势 |
|---|---|---|
| A · 保持 push | 实现简单 · 用户不打开 KnockWise 也能看到 | 推送疲劳 · 反感知（红队 X1） |
| B · pull-based | 主体验在产品内 · 推送退化为通知 | 用户不打开 KnockWise = 完全不知道 |
| C · 混合（推荐）| Pull-based 主路径 · push 作 fallback | 实现复杂 · 需 careful UX |

### Q2 · 是否纳入 "peer-attention signal" 做差异化？

| 选项 | 优势 | 劣势 |
|---|---|---|
| A · 不做 · 维持 LLM curator | 实现简单 · 与 spec 一致 | 红海 + 易复制（红队 X1）|
| B · MVP 后做 · Phase 2 加 | 路径清晰 · 先把 digest 做稳 | 机会成本 · 可能永远不做 |
| C · 现在规划（不实施）| 知道未来方向 · 不浪费设计 | 长期可能不会做 |

---

## § 7 · 我的 5 条最 actionable 建议

1. **先做 fixed 5 条 + 引用溯源**（2 行改动 · 解决双方共识 C1 + C3）
2. **信源从 30+ 降到 8 核心** · 改 sources-investigation.md Tier 1
3. **公众号资质本周启动申请**（0 工程量 · 4-6 周走流程）
4. **MVP 范围明确化** · Phase 1 = digest + email + 引用 · 公众号/微信/Obsidian 都是 P2+
5. **架构思考加 N1 · push-based → pull-based** · 邮件/微信退化为通知 · 主体验在 KnockWise

---

## 元信息

- **文档版本**：v1 · 2026-07-17
- **路径**：`docs/tasks/2026-07-17-new-feature-ai-push/dual-agent-synthesis.md`
- **下一步**：
  1. 你对 Q1 / Q2 拍板
  2. 更新 sources-investigation.md（Tier 1 = 8 源 · 删 30+ 默认）
  3. 更新 research.md（5.2 优先级重排 · 5.4 增加 pull-based 选项）
  4. 进 1 步写 spec.md

---

## Sources / agents

- Agent 1（机会最大化）：报告 + 13 opportunities + moat 分析
- Agent 2（红队审稿）：报告 + 7 risks + 8 weak assumptions + 5 竞品 + critical issue
- 聚合洞察（§ 4 NEW）：来自两边对话的 integration，非任一原文
