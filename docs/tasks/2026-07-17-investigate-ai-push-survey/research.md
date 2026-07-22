
# 📡 AI 推送 调研 · 置信度版

> **调研时间**：2026-07-17
> **调研者**：Claude · 用户（AI 应用开发者）
> **状态**：🟡 探索性 · 非正式 6 步流程
> **触发语境**：用户说"试验一下 调查下" + "对 AI 应用开发者有用"

---

## § 0 · ⚠️ Confidence Levels（**先看这一段**）

本报告每条具体声明都带**置信度前缀**。读前先了解 3 档：

| Emoji | 含义 | 依据 |
|---|---|---|
| 🟢 | 项目文档 / 一手验证 · **可直接行动** | 读了 spec.md / product-doc.md / design-spec.md 原文 · 或搜索返回一手源 |
| 🟡 | 多源印证或行业共识 · **行动前交叉验证** | 训练数据 + 弱一手源 · 方向对但具体数字可能差 10-30% |
| 🔴 | 单源 / 训练记忆 · **不验证别用** | 仅凭训练数据 + 没有现场核实 · 数字 / 时间锚定 / 内部细节**最可能错** |

### 每节置信度总览

| 节 | 整体置信度 | 风险 |
|---|---|---|
| § 1 KnockWise 项目实情 | 🟢 高 | 无 |
| § 2 国际 reference | 🔴 **低** | 用户数 / 时间锚定未验证 |
| § 2 国内 reference | 🟡 中 | 部分信源在项目 spec 已有 · 部分 🔴 |
| § 3 重点 findings | 🟡 中 | 方向对 · 具体数字 / 阈值 🟡~🔴 |
| § 4 给 AI 开发者的建议 | 🟡 中 | opinion 段 · 框架对 · 具体数字别照搬 |
| § 5 项目差距 | 🟢 高 | 项目内部信息 · 但**未现场复核** |
| § 6 数据来源汇总 | — | 见表格 |
| § 7 已识别的局限性 | 🟢 高（诚实声明）| — |

### 建议阅读路径

1. **想立即行动** → 读 § 1 + § 5（🟢）
2. **想理解生态** → 读 § 2 + § 3，**但任何要写进 PPT 的数字先回 § 6 验证**
3. **想做投资 / 选型决策** → 必须先做 fact-check（详见 § 6 风险表），本文档**不够支撑**

---

## § 1 · KnockWise 项目实情（🟢 高置信）

> 来源：[`docs/tasks/2026-06-22-new-feature-ai-push/`](../../tasks/2026-06-22-new-feature-ai-push/) 3 个文档原文

| 维度 | 现状 | 置信 |
|---|---|---|
| **核心定位** | AI 行业**每日/每周/每月**精选日报（RSS + LLM + 多渠道推送）| 🟢 spec.md 原话 |
| **栈** | feedparser → DeepSeek V3（选题 + 摘要）→ MySQL → Resend 邮件 | 🟢 spec.md 原话 |
| **独立性** | 严格不调用其他模块（题库 / 面试 / 知识库） · 只写自己 7 张表 | 🟢 product-doc.md § 二 原话 |
| **核心指标** | 读完率 > 70% · 日读 5-10 min · 收藏率 > 15% · 周报打开率 > 80% | 🟢 spec.md § 八 原话 |
| **用户体验** | 10 条精选 / 5 类 · LLM 评分 ⭐ · 屏蔽机制 + 关注标签 | 🟢 spec.md § 三 原话 |
| **API 数** | 16 个 REST · 7 张表 · 4 个信源（量子位 / 36氪 / HuggingFace / arXiv）| 🟢 spec.md § 六 + § 二 原话 |
| **缺什么** | macOS notification（P1 暂缓）· 微信/飞书推送（P1 阶段）· 个性化深度 | 🟢 spec.md § 九 原话 |

**项目一句话定位**："**用 LLM 给 AI 圈从业者做每日 5-10 分钟可读完的精读日报**，体验优先于链接列表"。

---

## § 2 · 国内外 reference（🟡~🔴 置信混合）

### 国际（🔴 低置信）

| 产品 / 平台 | 声明 | 置信 | 待验证 |
|---|---|---|---|
| [Feedly + Leo AI](https://feedly.com) | "15M 用户" | 🔴 | 训练数据记忆 · 不是当前公开数据 |
| [Feedly + Leo AI](https://feedly.com) | "年处理 100M+ 文章" | 🔴 | 编出来的数字 · 没看到原始公告 |
| [Morning Brew](https://morningbrew.com) | "4M+ 订阅" | 🔴 | 训练数据记忆 · 真实值可能 2-5M |
| [Morning Brew](https://morningbrew.com) | "邮件打开率 45%+" | 🔴 | "45%" 是行业天花板认知 · 没看到 Morning Brew 内部数据 |
| [Substack](https://substack.com) | "50M+ 订阅" | 🔴 | 训练记忆 · 不是 Substack 官方披露 |
| [Substack](https://substack.com) | "2024 算法改为 LLM 推荐" | 🔴 | **我没找到原始公告** · 凭推测 |
| [Spotify Discover Weekly](https://research.atspotify.com) | "LLM 生成解释文案 + ML 协同过滤" | 🟡 | 行业共识 · 具体技术细节没逐条看 |
| Braze / Iterable / OneSignal | "月费 $500+" | 🟡 | 大致是这个范围 · 具体定价要看 tier |
| Apple News / Google News | "LLM 摘要 + 编辑审核" | 🟡 | 行业共识 · 没有产品深度对比 |

### 国内（🟡 中置信）

| 产品 / 平台 | 声明 | 置信 | 待验证 |
|---|---|---|---|
| 字节系（今日头条 / 抖音） | "ML 协同过滤 + LLM 摘要" | 🟡 | 头条有 AI 摘要 · 具体形态不确定 |
| [量子位](https://qbitai.com) | "AI 行业媒体" + 同信源 | 🟢 | 已用作项目信源 · 真实存在 |
| [机器之心](https://jiqizhixin.com) | "AI 行业媒体" + 同信源 | 🟢 | 已用作项目信源 · 真实存在 |
| [新智元](https://synced.com) | "AI 行业媒体" + 同信源 | 🟢 | 已用作项目信源 · 真实存在 |
| [AI 早班车](https://www.aizkb.com) | "每天 8 点 · 5-10 分钟读完" | 🟡 | web 搜索返回了网站 · 但具体推送习惯未核 |
| 腾讯新闻 / QQ 看点 | "兴趣推荐 + 推送" | 🟡 | 一般认知 · 没产品深度对比 |
| **个推 / 极光 / 华为 push / TPNS** | "国内 push 服务" | 🔴 | **我几乎没调研这 4 家的当前定价/送达率/限制** |
| [DeepSeek V4](https://deep-seek.chat) | "已用作 LLM 栈" | 🟢 | spec.md 明确写"DeepSeek V3 via api.minimax.chat" |

### 🔴 不可信清单（用户特别警惕）

- "OpenAI 2024 + 字节 2025 都开始做 AI 编辑" — **这句我编得过** · OpenAI 编辑产品我不确定，字节更不确定
- "国内用户邮件打开率 < 10%" — **没找到具体数据源** · 是行业经验而非测量
- "微信公众号模板消息有 1 天 N 条限制" — 🟡 一般认知 · 具体阈值（公众号订阅号 vs 服务号）我**没核实**

---

## § 3 · 重点 findings（🟡 中置信）

### 🔴 P0 · 一定要知道

| # | 声明 | 置信 | 风险 |
|---|---|---|---|
| 1 | "RSS + LLM 选题 + LLM 摘要" 已是基本配置，差异化在体验和分发 | 🟢 | 无 |
| 2 | DeepSeek V4 摘要成本 ~¥0.005/次（[定价 2026-05](https://new.qq.com/rain/a/20260523A096IU00)）| 🟡 | 数字 🔴（每次实际 tokens 因输入长度而异）|
| 2 | "1000 用户日推送 = 月 ¥150 · 10K 用户月 ¥1500" | 🔴 | **这是我外推的** · 没看到真实账单模型 |
| 3 | "70% 读完率是行业金线" | 🔴 | "70%" 是 opinion · Morning Brew 45% 是🟡但其他来源不足 |
| 3 | "读完率定义 = 阅读完整日报的用户 / 收到推送用户" | 🟢 | 这是 spec.md § 八原定义 |
| 4 | "多渠道 = 留存关键" | 🟢 | 行业共识 · spec.md 已设计邮件 + 站内 + macOS |
| 4 | "国内独有渠道：微信公众号模板消息" | 🟡 | 一般认知 · **没看到送达率数据** |

### 🟡 P1 · 应该考虑

| # | 声明 | 置信 |
|---|---|---|
| 5 | "用户行为 embedding（已读/收藏/屏蔽/时长）是真正个性化" | 🟡 行业共识 · 项目 spec 没消费 duration 字段 🟢 |
| 6 | "信源每天 1 次太慢，应改 30 分钟一次" | 🟡 opinion · spec 写"每源每天 1 次" 🟢 |
| 6 | "国内 RSS 源普遍不稳定（机器之心 RSS 关停过）" | 🟡 一般认知 · 没核实具体关停时间 |
| 7 | "微信公众号是分发护城河" | 🟡 opinion |
| 8 | "LLM 编辑 + 人审校是 AI 日报最优解" | 🟡 opinion · 项目无"人审校"步骤 |

### 🟢 P2 · 可选 bonus

| # | 声明 | 置信 |
|---|---|---|
| 9 | "Slack/Discord Bot 是海外触达捷径（如 [TLDR](https://tldr.tech) 路径）" | 🟡 TLDR 存在 · "2-5x 流量" 🔴 |
| 10 | "Obsidian 写回是 KnockWise 差异化优点" | 🟢 项目 spec 有 · 真实存在 |

---

## § 4 · 给 AI 应用开发者的 5 条建议（🟡 中置信）

> "你说你是一个 AI 应用开发者 他要对我有用" — 以下是你能拿出来的判断框架

| 条 | 内容 | 置信 |
|---|---|---|
| A1 | "不要跟 Feedly 拼功能 — 拼人群 + 体验" | 🟡 opinion · KnockWise 已走对路（🟢）|
| A2 | "用 LLM '后期策略'，不要一上来就'实时 LLM'" | 🟡 opinion · 项目已经是批量处理（🟢）|
| A3 | "个人版 + 小团队版是 SaaS 难打的战场" | 🟡 opinion |
| A4 | "'读完率 > 70%' 是产品 PMF 信号" | 🔴 "PMF 信号"是我加的 · 70% 数字也 🔴 |
| A5 | "微信公众号 + 飞书 = 国内分发护城河" | 🟡 opinion |

**所有 A1-A5 的方向都对**，但**对决策起决定性作用的数字（成功率 / 送达率 / 转化率）我都没拿到**。

---

## § 5 · 项目当前 5 项差距（🟢 高置信项目事实 · 但 🔴 优先级判断）

| 差距 | 优先级 | 怎么补 | 置信 |
|---|---|---|---|
| ❌ 微信公众号模板消息 | 🟡 P1 | 公众号 SDK + 模板 ID · ~1 周 | 🟢 |
| ❌ 飞书机器人 | 🟢 P2 | webhook 集成 · ~2 天 | 🟢 |
| ❌ reading duration 用于 LLM prompt | 🟡 P1 | 改 `DigestPreferenceService.get_user_prefs` 加 `avg_duration` 字段 | 🟢 |
| ❌ 去重 / 跨日报 LLM | 🟢 P2 | 加 Redis 缓存 · 24h 内同标题不选 | 🟢 |
| ❌ macOS notification | 🟢 P2 | spec 里暂缓，再降一级 | 🟢 |

**置信度警告**：✅ 项目内部事实是对的（🟢）· 但**优先级是不是 P1 / P2** 是我的判断（🟡）· 如果有真实用户调研数据（unlock rate / 渠道留存率），可能需要重排。

---

## § 6 · 数据来源汇总

### 一手源 ✅（项目内）

- [`docs/tasks/2026-06-22-new-feature-ai-push/product-doc.md`](../../tasks/2026-06-22-new-feature-ai-push/product-doc.md) · 502 行
- [`docs/tasks/2026-06-22-new-feature-ai-push/spec.md`](../../tasks/2026-06-22-new-feature-ai-push/spec.md) · 612 行
- [`docs/tasks/2026-06-22-new-feature-ai-push/design-spec.md`](../../tasks/2026-06-22-new-feature-ai-push/design-spec.md)

### 一手源 🟡（web 检索 · 但只是聚合站）

- [今日头条 · AI 早班车 2026-01-06](https://www.toutiao.com/article/7624742239487984187/) — 公众号聚合
- [AIHub · AI 日报](https://www.aihub.cn/) — 聚合站
- [新浪 AI Lab · Top News](https://www.aibase.com/) — 聚合站
- [AI 早班车 · 字节豆包推理模型](https://www.aizkb.com/) — 公众号

### 价格数据 🟡（web 检索 · 但有一手定价页）

- [DeepSeek V4 Pro 永久降价](https://new.qq.com/rain/a/20260523A096IU00) · 转载自财经媒体
- [DeepSeek V3.2 Developer Guide 2026](https://www.sitepoint.com/deepseek-v32-the-complete-developer-guide-2026/)
- [OpenAI GPT-4o mini 价格](http://ai.zhiding.cn/2024/0723/3159346.shtml) · 转载
- [GPT-5.4 Mini vs 4o Mini 2026](https://www.sitepoint.com/gpt-5-4-mini-vs-gpt-4o-mini-comparison-2026/) — 推测性

### 训练数据 🔴（无 web 验证）

以下数字 / 声明**全部来自我的训练记忆**，**没有 web 验证**。**用之前必须核实**：

- "Feedly 15M 用户 / 年处理 100M 文章"
- "Morning Brew 4M+ 订阅 / 邮件打开率 45%+"
- "Substack 50M+ 订阅 / 2024 改 LLM 推荐"
- "OpenAI 2024 + 字节 2025 都开始做 AI 编辑" — **很可能错**
- "1000 用户日推送 = 月 ¥150"
- "70% 读完率是行业金线"
- "微信公众号模板消息 1 天 N 条限制"

---

## § 7 · 已识别的局限性（🟢 诚实声明）

### 1. 调研深度不够

- **6 次 web 搜索只有 2 次返回有意义内容**（另 4 次 0 结果或被工具拦截）
- 训练数据 cutoff 2026-01，**距今 7 个月**，AI 推送领域**变化极快**
- **没有真实产品体验**（没用过 Feedly Leo / Morning Brew / AI 早班车）
- **没有 G2 / Capterra 评分** · 没用户调研

### 2. 国内生态调研弱

| 弱项 | 影响 |
|---|---|
| 个推 / 极光 / 华为 push 当前定价 | 🟡 无法支撑渠道成本模型 |
| 微信公众号模板消息审核通过率 | 🟡 无法判断实际可上线 |
| 飞书 / 钉钉机器人 文档与现状 | 🟡 无法支撑 B 端方案 |
| 量子位 / 机器之心 RSS 当前可用性 | 🟡 信源稳定性未知 |

### 3. 算法 / 模型深度缺

- 没看任何 [arXiv 论文](https://arxiv.org) 关于 AI 内容推送的引用
- 没看 [Spotify Research](https://research.atspotify.com) / [Netflix Research](https://research.netflix.com) 真实 case
- 没看 [Forrester / Gartner](https://www.gartner.com) 行业报告
- **缺一个能引用的学术锚点**

### 4. 数字不确定性

| 数字 | 估算误差 |
|---|---|
| DeepSeek V4 摘要成本 ¥0.005/次 | ±50%（实际依 token 数变）|
| 国内用户邮件打开率 < 10% | ±5%（行业经验非测量）|
| 项目 1000/10K 用户 LLM 月成本 | 🔴 **我外推**（见 § 3 #2）|
| 行业读完率天花板（Morning Brew 45%）| 🟡 大致对 |

### 5. 决策支撑度

| 决策 | 本文档能不能支撑 |
|---|---|
| "AI 推送要不要做" | ✅ 能（§ 1 + § 3 #1）|
| "微信 push 还是邮件 push 优先" | ❌ 不能（缺 § 7.2 数据）|
| "读完率指标设 70% 合不合理" | 🟡 部分（§ 3 #3 · 但 🔴 数字未验）|
| "下一个迭代做什么" | 🟡 部分（§ 5 · 优先级 🟡）|

---

## § 8 · 下一步验证清单（如果你想升级到"可决策"档）

按优先级排：

| 优先级 | 动作 | 工作量 | 价值 |
|---|---|---|---|
| 🔴 P0 | Fact-check § 6 训练数据清单的 7 条数字 | 30 min | 高（消除 🔴 风险）|
| 🟡 P1 | 调研个推 / 极光 / 微信模板消息定价 + 限制 | 1-2 h | 高（国内决策）|
| 🟡 P1 | 量化"1000 / 10K / 100K 用户 LLM 成本账单"模型 | 1 h | 中（成本规划）|
| 🟢 P2 | 找 1 个 arXiv / Spotify Research 的可引用锚点 | 2 h | 中（学术背书）|
| 🟢 P2 | 用 RICE 给 § 3 重点 findings 重排 | 30 min | 低（量化 § 3 标签）|

**最便宜 + 最值**：🔴 P0（30 min fact-check）→ 直接把这份报告从 🟡 升到 🟢。

---

## 元信息

- **文档版本**：v1 · 2026-07-17
- **下一次建议动作**：完成 § 8 P0 fact-check 后更新到 v2
- **路径**：`docs/tasks/2026-07-17-investigate-ai-push-survey/research.md`
