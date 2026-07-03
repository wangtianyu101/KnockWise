---
title: 产品文档 · V2 智能沉淀层
date: 2026-06-28
status: v1（AI 起草，待 review）
tags: [product-doc, 1步, 产品脑, v2, 智能沉淀]
related:
  - [research.md](research.md) — 上游 0 步调研
  - [spec.md](spec.md) — 下游技术脑翻译
  - [design-spec.md](design-spec.md) — 下游设计脑翻译
  - [V1 spec 2026-06-22](../2026-06-22-new-feature-question-bank/spec.md) — 母模块设计
  - [V1 收尾报告](../2026-06-27-v1-closure/closure.md) — 上游 V1 状态
---

# 产品文档：V2 智能沉淀层

> **一句话**：让"输入→沉淀→回流"闭环跑起来——用户答完题/面完试，画像自动更新、Obsidian 自动写笔记、Dashboard 自动出"今日总结"。
>
> **模块名**：V2 智能沉淀层（不是独立模块，是横切能力：① 面试 / ② 学习复习 / ③ 知识库 三个模块的共同"出"端）
>
> **作者**：AI 起草（按 V1 模式），待你 review/改 1-3 段产品判断
>
> **范围**：横切 ① ② ③ 三个模块的"沉淀"环节，**不**改 3 个模块的"输入"体验

---

## 1. 问题定义（必填）

### 用户痛点

| # | 痛点 | 量化 |
|---|---|---|
| 1 | **答完题看不到自己的成长** | 答了 50 题，打开 Profile 只有"已做 50"4 个字，不知道薄在哪里、强在哪里 |
| 2 | **面试完的 11 维雷达 7 天后忘了** | 面试报告只在 `/interview/report` 看一次，没沉淀到任何地方（笔记 / 画像） |
| 3 | **Obsidian 笔记靠手抄** | 答完一道好题，想写笔记要手动开 Obsidian 复制粘贴 — 80% 时候懒得写 |
| 4 | **Dashboard 进首页看不到"今天学了什么"** | 顶部只有"今日推荐 3 题"，没有"今日总结"反馈 |
| 5 | **月度复盘靠回忆** | 6 月学了啥，只能凭印象 → 写月度报告时没数据支撑 |

### 时机

- V1 收尾时明确：3 个 service（SummaryService / ProfileSettlementService / ObsidianSedimentService）**已写进 technical-spec 但未实施**
- Profile 4 字段 V1 已扩（`weak_topics` / `mastered_topics` / `learning_trajectory` / `last_active_at`）+ `monthly_reports` 表已建
- **基础设施已就位**（schema / fixture / 路径 / 模式），V2 是"最后一公里" — 不做就是沉积 30+ 天的议題
- 竞品（Anki / Obsidian + AI）已经有自动沉淀，但分散 — 我们做的是"统一沉淀层"

### 不做会怎样

- V1 已"看起来完整"（19 张表 + 60+ API），但用户用 1 周后会发现**没沉淀 = 没复盘 = 没成长**
- Profile 4 字段空跑（建了不写），相当于埋了个未启用的功能
- Obsidian 集成 94% 覆盖但**只读不写** — 用户要写笔记还是得手抄
- 议題 B（interview.py 803 行）沉积超过 30 天，V2 实施正好顺手拆

---

## 2. 目标用户（必填）

### 角色

| 人群 | 经验 | 痛点对应 |
|---|---|---|
| **A: 求职冲刺者**（V1 已有） | 1-5 年 | 痛点 1+2（看不到成长 + 面试报告不沉淀） |
| **B: 持续学习者**（V1 已有） | 在职 | 痛点 1+3+4（Profile 空 + Obsidian 靠手抄 + Dashboard 没反馈） |
| **C: 复盘型用户**（V2 新覆盖） | 任何 | 痛点 5（月度复盘） |

### 场景

- **场景 1（高频）**：答完一道题 → 1 秒后看到 Profile `weak_topics` 多了一项 / `mastered_topics` 少了一项
- **场景 2（中频）**：答完 5 道题 → 1 秒后看到 `~/Obsidian/coding/learning/2026-06-28.md` 多了一段
- **场景 3（低频）**：早上打开 `/dashboard` → 看到"今日学习总结"卡片（昨天答了 N 题，弱项从 X→Y）
- **场景 4（极低频）**：月底打开 `/profile` → 看到 6 月 learning_trajectory 趋势图 + monthly_report

### 频率

| 行为 | 频率 | 设备 |
|---|---|---|
| 答题触发沉淀 | 每天 5-20 次 | 桌面 / Web |
| 看 Dashboard 总结 | 每天 1-2 次 | 桌面 / Web |
| 看 Profile 趋势 | 每周 1 次 | 桌面 |
| 看月度报告 | 每月 1 次 | 桌面 |

---

## 3. 价值主张（必填）

### 用户价值

- **1 句话说清楚**：**让"答完题 = 自动沉淀"** —— 用户不用记，Profile / Obsidian / Dashboard 自动长出东西来
- 解决痛点 1：Profile `weak_topics` / `mastered_topics` 自动维护，**3 秒看到成长**
- 解决痛点 2：面试完自动沉淀到 `interview_stats` + Obsidian 笔记
- 解决痛点 3：答题自动写 `learning/YYYY-MM-DD.md`，**告别手抄**
- 解决痛点 4：Dashboard 顶部加"今日学习总结"卡片
- 解决痛点 5：月底 `monthly_reports` 自动生成 narrative

### 商业价值

| 指标 | 影响 | 量化预估 |
|---|---|---|
| 7 日留存 | 用户看到自己成长 → 回访动机 | +10% |
| 日均使用时长 | Dashboard 总结 + Profile 趋势 | +5 min/天 |
| 复购 / 续费（如果有） | 学习闭环完整 → 用户粘性 | +5% |
| 品牌口碑 | "AI 自动沉淀"差异化 | 难量化 |

---

## 4. MVP 范围（必填 · 关键）

### 包含（最小可用版本必须有的）

| # | 功能 | 验收（怎么知道能用） |
|---|---|---|
| **V2.1** | **ProfileSettlementService**：答完题/面完试后，Profile `weak_topics` / `mastered_topics` / `last_active_at` 自动更新 | 答完 5 道题 → 打开 `/profile` 看到 weak_topics 出现新项 |
| **V2.1** | **ProfileSettlementService.weekly_full_refresh**：每周深度重算 `learning_trajectory`（趋势数据） | 周一打开 `/profile` 看到 learning_trajectory 有新数据点 |
| **V2.2** | **ObsidianSedimentService**：答题后写 `learning/YYYY-MM-DD.md`（每日 1 文件） | 答完 3 道题 → 1s 后 `~/Obsidian/coding/learning/2026-06-28.md` 出现新内容 |
| **V2.2** | **ObsidianSedimentService**：面试完写 `interview/YYYY-MM-DD-<id>.md` | 完一场面试 → Obsidian 出现新文件 |
| **V2.3** | **SummaryService.daily**：Dashboard 顶部"今日学习总结"卡片（昨天/今天） | 打开 `/dashboard` → 顶部出现"昨天答了 N 题，弱项从 X→Y"卡片 |
| **V2.3** | **SummaryService.weekly/monthly**：周报 + 月报 + `monthly_reports` 落库 | 调 API 拿到周报/月报，monthly_reports 表有数据 |
| **V2.4** | **前端 UI 改造 3 处**：profile / dashboard / knowledge 3 个页面接数据 | 浏览器打开 3 个页面都看到新内容 |
| **V2.5** | **测试 + 文档**：3 个 service 覆盖率 ≥ 80%，check-step.py 全过 | `pytest` 全绿 + `check-step.py spec/plan/verify` 全绿 |

### 不包含（明确不做的）

| # | 不做 | 理由 |
|---|---|---|
| ❌ | **跨模块推荐** | V1 已明确"4 模块完全独立"，V2 不开这个口子 |
| ❌ | **ML 推荐算法** | V2 用规则（错题率 / 频次）足够，ML 是 V3+ |
| ❌ | **实时推送**（"答完 1s 推送到手机"） | V2 只刷新前端页面，App push 是 AI 推送模块的事 |
| ❌ | **Obsidian 反向链接自动建**（自动加 `[[题目]]`） | V2 只写内容，反向链接是 V3 |
| ❌ | **PDF / 邮件导出** | 沉淀只在 Obsidian / Web 里，导出是 V3 |
| ❌ | **多用户协作沉淀** | V2 是单用户，单机 Obsidian 同步不在范围 |
| ❌ | **历史数据批量回填** | V2 只接住新产生的数据，旧数据不补 |
| ❌ | **自定义沉淀规则** | V2 用 V1 写死的规则（错题率 > 0.5 = weak），用户配置是 V3 |

### 未来迭代（可以考虑的）

- V2.6：Obsidian 双向同步（用户改 Obsidian 同步回 Profile）
- V3.0：ML 弱项识别（不只是错题率，加语义分析）
- V3.1：跨模块沉淀（"在 X 模块答对某题自动 push 到 Y 模块"）
- V3.2：App push 通知（"今天还没复习" / "本月你掌握了 5 个新 topic"）
- V3.3：协作沉淀（团队 / 学习小组）
- V3.4：自定义规则（用户自己写沉淀规则 JSON）

---

## 5. 成功指标（必填 · 可量化）

### 核心指标（1-3 个量化）

| # | 指标 | 目标 | 测量方式 |
|---|---|---|---|
| **1** | **Profile 字段填充率** | ≥ 80% 用户在答题 5 题后 `weak_topics` 非空 | DB 统计：`Profile.weak_topics != '[]'` / 总答题用户数 |
| **2** | **Obsidian 写回成功率** | ≥ 95%（vault 存在时） | `ObsidianSedimentService._write` 返回值非 None 比例 |
| **3** | **Dashboard "今日总结" 点击率** | ≥ 30% DAU 看 Dashboard 时滚动到总结卡 | 前端埋点（V2.4 加）+ 后端日志 |

### 监控方式

- 指标 1：`SELECT COUNT(*) FROM profiles WHERE JSON_LENGTH(weak_topics) > 0;` 每日定时
- 指标 2：`ObsidianSedimentService` 写日志：`[obsidian_write] user=1 path=learning/2026-06-28.md success=true/false`
- 指标 3：前端 `useDashboardSummary` hook 加 `data-view` 埋点

### 合格线（什么数字算"成功"）

- 上线 30 天后：
  - 指标 1：**≥ 80%** → 沉淀层被使用（成功）
  - 指标 2：**≥ 95%** → 写回稳定（成功）
  - 指标 3：**≥ 30%** → 用户认可总结价值（成功）
- 3 个指标都达到 → V2 算"成功"，可推进 V3
- 任意 1 个 < 合格线 → 复盘哪一段出问题（写回失败？总结不准确？UI 找不到？）

---

## 🎯 硬性 DOD（product-doc.md 完成必须全过）

- [x] 5 段齐全（问题 / 用户 / 价值 / MVP / 指标）
- [x] 成功指标 ≥ 1 个量化数字（实际 3 个：80% / 95% / 30%）
- [x] MVP 范围明确"包含"（8 项）+ "不包含"（8 项）
- [x] 价值主张双向（用户价值 5 条 + 商业价值 4 项）
- [ ] **用户验收签字**：待你 review 改后写"已验收：<name> <date>"

---

## 📚 相关文档

- [research.md](research.md) — 上游 0 步调研（含 5 个决策点）
- [spec.md](spec.md) — 下游技术脑翻译
- [design-spec.md](design-spec.md) — 下游设计脑翻译
- [V1 母模块 spec](../2026-06-22-new-feature-question-bank/spec.md) — 4 大模块独立性原则
- [V1 收尾报告](../2026-06-27-v1-closure/closure.md) — V2 缺失 3 service 来源
- [Technical Spec § 5.4-5.6](../2026-06-22-new-feature-question-bank/technical-spec.md) — 3 service 方法签名

---

## 🔴 触发条件

- 类型：new-feature（V2 全新能力，3 service 都不存在）
- 必填：是
- 已触发：✅
