---
title: 产品文档 · V3 题库扩量 + 多维分类 + LeetCode 三件套
date: 2026-07-09
status: v1
tags: [product-doc, 1步, 产品脑, v3, 题库扩量, 多维分类, LeetCode三件套]
related:
  - [research.md](research.md) — 0/0.5/0.6 调研（G3 + I1 已拍）
  - [spec.md](spec.md) — 下游技术脑翻译
  - [design-spec.md](design-spec.md) — 下游设计脑翻译
  - [V1 母模块 product-doc](../2026-06-22-new-feature-question-bank/product-doc.md)
  - [V2 沉淀层 product-doc](../2026-06-28-new-feature-v2-smart-sediment/product-doc.md)
---

# 产品文档：V3 题库扩量 + 多维分类 + LeetCode 三件套

> **一句话**：让"沉淀"延伸到"系统化" — 200 题 + 多维分类让用户有题刷能筛题，学习计划让用户有节奏有目标，精选题单 + 每日一题让用户有锚点能坚持。
>
> **模块名**：V3 题库能力升级（属于"面试题库"母模块的 V3 子版本）
>
> **作者**：AI 起草（按 V1/V2 模式），用户决策已拍（G3 + I1）

---

## 1. 问题定义（必填）

### 用户痛点（5 类）

| # | 痛点 | 量化 |
|---|---|---|
| 1 | **学习计划找不到入口** | 用户研究代码库发现 `learn.py:269` 有完整 5 端点但 `/plan` 页面不存在、Nav 没入口 — "V1 阶段开了口子没填完"的最严重半成品 |
| 2 | **题库 50 题偏科严重** | 现有 50 题 90% 是 AI 向（agent 20 + rag 15 + langgraph 10 + java 5），主流面试方向（系统设计/算法/网络/前端）完全空白 |
| 3 | **题目没有分类筛选** | 现有 topic 5 个 + sub_topic 47 个，但 sub_topic 太分散（47 个几乎每题唯一），用户无法按"前端面试"或"字节考过"这种业务维度筛选 |
| 4 | **没题单跟刷（LeetCode 体验缺失）** | 用户想刷"算法入门 100 题"、"字节前端 50 题"等系统化题单，没入口；只能一道道自己找 |
| 5 | **没每日坚持锚点** | 用户学几天就断，没有"每日 1 题"的固定推送锚点（LeetCode Daily Challenge 风格） |

### 时机

- V2 沉淀层已落地（2026-07-03）：用户答完题 → 自动沉淀到画像 + Obsidian
- V3 = V2 之后的**第二次能力扩展**：从"沉淀"延伸到"系统化"
- 学习计划后端已实装 5 端点（study_plan_service + learn.py:269-326），**只缺前端 UI 暴露**（用户痛点 #1）
- 用户调研原话："对比下是不是少了一些功能 如学习计划 如 LeetCode 一样"（明确点名学习计划）

### 不做会怎样

- V2 后用户用 1 周后会发现："题太少刷完了"（痛点 #2）+ "题目不知道按什么分类"（痛点 #3）+ "想刷题单没入口"（痛点 #4）+ "几天不学没人提醒"（痛点 #5）
- 学习计划后端 API 闲置（投入了 V1 工程量但 0 用户访问）
- 错失与 LeetCode 对标的机会（同质化竞争）
- 用户流失：找不到合适题 → 用 LeetCode 替代 → 不回来

---

## 2. 目标用户（必填）

### 角色（4 类）

| 人群 | 经验 | 痛点对应 | 优先级 |
|---|---|---|---|
| **A: 求职冲刺者**（V1 已有） | 1-5 年经验，2-3 个月内要面试 | #2 题少 + #3 没分类 + #4 没题单跟刷 | 🔴 主力 |
| **B: 持续学习者**（V1 已有） | 在职，每天 30min-1h | #1 找不到学习计划 + #5 缺锚点 | 🔴 主力 |
| **C: 算法专项学习者**（V3 新覆盖） | 任何阶段，重点刷算法 | #2 算法方向题目稀缺 + #4 没题单 | 🟡 重要 |
| **D: 碎片时间用户**（V3 新覆盖） | 通勤 / 等人的 5-10min | #5 每日一题 | 🟡 重要 |

### 场景（高频到低频）

- **场景 1**（高频 · 每天）：打开 `/dashboard` 看到 DailyChallengeCard → 答 1 题 → streak +1 → 关闭
- **场景 2**（中频 · 每周）：打开 `/plan` 看当前计划进度 → 调整下周目标 → 关闭
- **场景 3**（中频 · 每周）：打开 `/collections` 选一个题单订阅 → 刷 5 题 → 看完成度 → 关闭
- **场景 4**（低频 · 每月）：用 `/learn?tags=sys_algorithm,sys_python` 多维筛选 → 找到薄弱方向 → 集中刷

### 频率

| 行为 | 频率 | 设备 |
|---|---|---|
| 每日一题 | 每天 1 次 | 桌面 / 移动 |
| 学习计划查看 | 每周 1-2 次 | 桌面 |
| 题单跟刷 | 每周 2-3 次 | 桌面 |
| 多维筛选刷题 | 每周 1-2 次 | 桌面 |

---

## 3. 价值主张（必填）

### 用户价值

- **1 句话说清楚**：**让"沉淀"延伸到"系统化"** — V2 让"答完题 = 自动沉淀"，V3 让"有题刷能筛题 + 有计划有节奏 + 有题单能跟刷 + 每日 1 题锚点"
- 解决痛点 #1：建 `/plan` 页 + Nav 入口 + Dashboard 进度卡，**V1 后端 API 不浪费**
- 解决痛点 #2：50 → 200 题 + 4 个新方向（system_design / algorithms / network / frontend）
- 解决痛点 #3：A+B+C 三维标签（topic/sub_topic + QuestionTag 系统标签覆盖面试方向/技术栈/公司轮次）
- 解决痛点 #4：精选题单 Collections（"算法入门 100 题"、"字节前端 50 题"）
- 解决痛点 #5：每日一题 Daily Challenge（dashboard 顶部固定推送 + streak 联动）

### 商业价值

| 指标 | 影响 | 量化预估 |
|---|---|---|
| 7 日留存 | 有题刷能筛题 + 每日锚点 → 回访动机 | +15% |
| 日均使用时长 | 题单跟刷 + 学习计划 → 主动学习时长 | +10 min/天 |
| 差异化口碑 | "200 题 + LeetCode 三件套"对标 LeetCode → 用户感知 | 中等 |
| 复购 / 续费 | 学习闭环完整 → 用户粘性 | +8% |

---

## 4. MVP 范围（必填 · 关键）

### 包含（最小可用版本必须有的）

| # | 功能 | 验收（怎么知道能用） |
|---|---|---|
| **V3.0** | **学习计划补全**（🔥 用户已点痛点） | 打开 `/plan` 能看到计划列表 + 创建新计划 + Dashboard 顶部"当前计划进度"卡 |
| **V3.0** | Nav.tsx 加"计划"入口 | nav 点击"计划"跳 `/plan` |
| **V3.0** | dashboard.tsx 加"当前计划进度"卡 | 卡显示 plan name + 进度条 + 完成度百分比 |
| **V3.1** | **精选题单 Collections** | 打开 `/collections` 看到官方题单列表 + 详情页 + 订阅按钮 |
| **V3.1** | 新建 `QuestionCollection` / `QuestionCollectionMap` / `CollectionSubscribe` 3 表 | seed_service 预填 5-8 个官方题单（如"系统设计 30 题"、"算法入门 50 题"） |
| **V3.1** | `/api/learn/collections` + `/subscribe` + `/unsubscribe` 端点 | 4 个新端点 + Swagger 文档 |
| **V3.2** | **每日一题 Daily Challenge** | dashboard 顶部 DailyChallengeCard 显示题目 + "开始答"按钮 |
| **V3.2** | 新建 `DailyChallenge` / `DailyChallengeCompletion` 2 表 | 选题策略 = date hash % 200 题（保证每日不同 + 均匀分布） |
| **V3.2** | `/api/learn/daily-challenge` + `/complete` 端点 | 2 个新端点 |
| **V3.3** | **system_design 25 题**（新方向） | seed_data/system_design.json + 25 题 + ~75 追问（B2 详细） |
| **V3.4** | **algorithms 25 题**（新方向） | seed_data/algorithms.json + 25 题 + ~75 追问 |
| **V3.5** | **network 20 题**（新方向） | seed_data/network.json + 20 题 + ~60 追问 |
| **V3.6** | **frontend 20 题**（新方向） | seed_data/frontend.json + 20 题 + ~60 追问 |
| **V3.7（🆕）** | **AI 智能推荐卡**（集成 AI 推送模块 · 用户 2026-07-10 拍 A 极简） | dashboard 顶部新玻璃卡 · 调 V1 `/api/analytics/recommendations` 已实装 endpoint · 3-4 条推荐 |
| **V3.x** | **A+B+C 多维标签系统**（跨 V3.3-V3.6） | seed_service 预填 50 个系统标签 + 600 条 QuestionTagMap 关联 |
| **V3.x** | **/learn + /review TagFilter UI** | 多选标签筛选 + 实时筛选 |
| **V3.x** | **5 张新表 + 1 张 seed_data ALTER** | 数据库迁移 SQL |

### 不包含（明确不做的）

| # | 不做 | 理由 |
|---|---|---|
| ❌ | **`/push` 独立页（5+ 页面）** | V1 阶段 4.2 已规划完整但未实装，V3 仅做 A 极简（dashboard 卡），独立页留 V3.5/V4 |
| ❌ | **AI 推送日报 / 周报 / 月报** | V1 news_service 已实装但前端未建推送渠道，V3 不引入 |
| ❌ | **AI 推送 RSS 信源管理** | 后端无，前端无，V3 不引入 |
| ❌ | **AI 推送设置 / 推送渠道** | 同上 |
| ❌ | **跨模块推荐升级（用 V3 A+B+C 标签）** | recommendations_service 当前用"topic"字段，V3 不改，留 V3.5 增强 |
| ❌ | **BookmarkCollection CRUD / UI** | V1 半成品但 P1 列表第 7 位，V3.5 单独调研 |
| ❌ | **题目搜索升级（中文分词）** | V3.x P1.6，单独调研 |
| ❌ | **题目难度自适配** | V3.x P1.8，单独调研 |
| ❌ | **学习路径 Learning Path** | V3.5+ 长期规划 |
| ❌ | **题解 Editorial（结构化）** | V3.5+ |
| ❌ | **题目讨论 Discuss** | 社交重后端，V4+ |
| ❌ | **题目反馈 / 纠错** | V3.5+ |
| ❌ | **排行榜 / 每周竞赛** | 社交重后端，不做 |
| ❌ | **Anki 速记卡片** | 与 SM-2 UX 重叠，V4+ |
| ❌ | **AI 智能出题** | 重 AI 资产，V4+ |
| ❌ | **多语言 i18n** | V1/V2 不引入 |
| ❌ | **历史数据回填** | V3 只接住新产生的数据 |

### 不包含（明确不做的）

| # | 不做 | 理由 |
|---|---|---|
| ❌ | **BookmarkCollection CRUD / UI** | V1 半成品但 P1 列表第 7 位，V3.5 单独调研 |
| ❌ | **题目搜索升级（中文分词）** | V3.x P1.6，单独调研 |
| ❌ | **题目难度自适配** | V3.x P1.8，单独调研 |
| ❌ | **学习路径 Learning Path** | V3.5+ 长期规划 |
| ❌ | **题解 Editorial（结构化）** | V3.5+ |
| ❌ | **题目讨论 Discuss** | 社交重后端，V4+ |
| ❌ | **题目反馈 / 纠错** | V3.5+ |
| ❌ | **排行榜 / 每周竞赛** | 社交重后端，不做 |
| ❌ | **Anki 速记卡片** | 与 SM-2 UX 重叠，V4+ |
| ❌ | **AI 智能出题** | 重 AI 资产，V4+ |
| ❌ | **多语言 i18n** | V1/V2 不引入 |
| ❌ | **历史数据回填** | V3 只接住新产生的数据 |

### 未来迭代（可以考虑的）

- **V3.5**（P1 子集）：BookmarkCollection 补全 + 搜索升级 + 难度自适配（5-7h）
- **V4**（P2 子集）：讨论区 + 排行榜 + Anki 卡片（25-39h）
- **V4+**（P3 不做）：AI 智能出题 + i18n

---

## 5. 成功指标（必填 · 可量化）

### 核心指标（5 个量化 · 加 AI 推荐）

| # | 指标 | 目标 | 测量方式 |
|---|---|---|---|
| **1** | **学习计划创建率** | ≥ 40% 用户在 V3 上线后 7 天内创建 ≥ 1 个计划 | DB 统计：`COUNT(DISTINCT user_id) FROM study_plans WHERE created_at >= NOW() - 7d` / 总用户数 |
| **2** | **题单订阅率** | ≥ 30% 用户订阅 ≥ 1 个题单 | DB 统计：`COUNT(DISTINCT user_id) FROM collection_subscribes` / 总用户数 |
| **3** | **每日一题完成率** | ≥ 50% DAU 完成每日一题 | DB 统计：`COUNT(DISTINCT user_id) FROM daily_challenge_completions WHERE date = TODAY()` / DAU |
| **4** | **多维筛选使用率** | ≥ 25% 用户在 /learn 用 `tags=` 参数 | 后端日志：APM 抓 `GET /api/learn/questions?tags=` 调用占比 |
| **5（🆕）** | **AI 推荐点击率** | ≥ 20% DAU 点击 dashboard AI 推荐卡中至少 1 条 | 后端日志：APM 抓 `GET /api/analytics/recommendations` + 埋点 `click_recommend` |

### 监控方式

- 指标 1：`SELECT COUNT(DISTINCT user_id) FROM study_plans WHERE created_at >= ?;`（每日定时）
- 指标 2：`SELECT COUNT(DISTINCT user_id) FROM collection_subscribes;`
- 指标 3：`SELECT COUNT(*) FROM daily_challenge_completions WHERE date = CURDATE();`
- 指标 4：FastAPI middleware 记录 query 参数 → 日志聚合 → Grafana
- 指标 5：前端埋点 `data-action="click_recommend"` + 日志聚合

### 合格线（什么数字算"成功"）

- 上线 30 天后：
  - 指标 1：**≥ 40%** → 学习计划被使用（成功）
  - 指标 2：**≥ 30%** → 题单被订阅（成功）
  - 指标 3：**≥ 50%** → 每日一题提升粘性（成功）
  - 指标 4：**≥ 25%** → 多维分类被使用（成功）
  - 指标 5：**≥ 20%** → AI 推荐被认可（成功 · 议題 D 部分落地）
- 4 个指标都达到 → V3 算"成功"，可推进 V3.5 / V4
- 任意 1 个 < 合格线 → 复盘哪一段出问题（入口找不到？题目太偏？题单不够好？锚点不吸引？）

---

## 🎯 硬性 DOD（product-doc.md 完成必须全过）

- [x] 5 段齐全（问题 / 用户 / 价值 / MVP / 指标）
- [x] 成功指标 ≥ 1 个量化数字（实际 4 个：40% / 30% / 50% / 25%）
- [x] MVP 范围明确"包含"（15 项）+ "不包含"（11 项）
- [x] 价值主张双向（用户价值 5 条 + 商业价值 4 项）
- [ ] **用户验收签字**：待你 review 改后写"已验收：<name> <date>"

---

## 📚 相关文档

- [research.md](research.md) — 0/0.5/0.6 调研（G3 + I1 已拍）
- [spec.md](spec.md) — 下游技术脑翻译
- [design-spec.md](design-spec.md) — 下游设计脑翻译
- [V1 母模块 product-doc](../2026-06-22-new-feature-question-bank/product-doc.md)
- [V2 沉淀层 product-doc](../2026-06-28-new-feature-v2-smart-sediment/product-doc.md)

---

## 🔴 触发条件

- 类型：new-feature（V3 全新能力 + 补半成品）
- 必填：是
- 已触发：✅
