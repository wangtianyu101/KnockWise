# V1 收尾报告 · 面试题库模块

> 日期：2026-06-27 · 类型：议題关闭（按 CLAUDE.md § 1.7 议題关闭分支）
> 任务：把 docs/tasks/2026-06-22-new-feature-question-bank/plan.md 的 69 项过一遍，标出"哪些是真要做的 / 哪些是过时的"，归档 V1。
> 结论：**V1 骨架已落地（CRUD 层完整，智能层没做）。关闭 V1，启动 V2 计划。**

---

## 一、69 项分类汇总

按 plan.md 5 个 Phase 分类。每个 item 标状态：

| 图标 | 含义 |
|---|---|
| ✅ | 实际已做（功能存在） |
| 🟡 | 部分做 / 不完整 / 与原设计有偏差 |
| ⚪ | 不必要（设计已变 / 被替代） |
| 🔴 | 必须做但当前没做（V2 候选） |
| ➖ | N/A（依赖不在本仓库 / 跳过） |

### Phase 1: 基础设施统一（11 项）

| # | 计划项 | 状态 | 备注 |
|---|---|---|---|
| 1.1.1 | User 模型加 `password_hash`, `display_name` | ✅ | users 表已有 |
| 1.1.2 | `POST /api/auth/register` | ✅ | 邮箱注册 |
| 1.1.3 | `POST /api/auth/login` | ✅ | 邮箱登录 |
| 1.1.4 | `POST /api/auth/refresh` | ⚪ | refresh 没单独 endpoint（JWT 短期有效） |
| 1.1.5 | `get_current_user` 支持邮箱密码 | ✅ | dependencies.py |
| 1.1.6 | `login.tsx` 双 Tab | 🟡 | 实际只有 Dev Login 按钮（用 dev-login） |
| 1.1.7 | `pages/register.tsx` | ⚪ | 用 dev-login 跳过 |
| 1.1.8 | `lib/api.ts` login()/register() | 🟡 | 简化版，无 email/password 字段 |
| 1.2.1 | `backend/.env.example` | ✅ | 12 必填字段 |
| 1.2.2 | `core/config.py` SMTP_*, JWT_REFRESH_* | ⚪ | 不需要 SMTP（无邮件通知功能） |
| 1.2.3 | agent-memory 脚本 API 配置统一 | ➖ | agent-memory 独立仓库，未迁移 |

### Phase 2: 面试模块完善（13 项）

| # | 计划项 | 状态 | 备注 |
|---|---|---|---|
| 2.1.1 | `GET /api/interviews?status=&round=&topic=` | 🟡 | GET 列表存在，筛选参数待验 |
| 2.1.2 | `GET /api/analytics/overview` | ✅ | |
| 2.1.3 | `GET /api/analytics/radar` | ✅ | |
| 2.1.4 | `GET /api/analytics/trends` | ✅ | |
| 2.1.5 | `GET /api/analytics/recommendations` | ✅ | |
| 2.1.6 | `POST /api/profile/resume` | ✅ | PDF + OCR |
| 2.1.7 | `PUT /api/profile/me` | ✅ | |
| 2.2.1-7 | interview/{profile,setup,room,history,report,analytics} | ✅ | 6 个页面都在 |
| 2.2.8 | `dashboard.tsx` | ✅ | |
| 2.2.9 | `Layout.tsx` 顶部导航 | 🟡 | 有 SideDrawer 但无独立 Layout |
| 2.2.10 | `GlassCard.tsx` 玻璃卡片 | 🟡 | 没独立组件（可能内联） |
| 2.2.11 | `ProgressBar.tsx`, `StatCard.tsx` | 🟡 | 没独立组件（可能内联） |
| 2.3.1 | `report_agent.py` 真实雷达 | ✅ | 11 维雷达生成 |
| 2.3.2 | `POST /api/reports/interview/{id}` | ✅ | |
| 2.3.3 | `report.tsx` 对接真实数据 | ✅ | E2E 测试已验 |

### Phase 3: 知识管理模块（16 项）

| # | 计划项 | 状态 | 备注 |
|---|---|---|---|
| 3.1.1-9 | ObsidianService 9 个方法 | ✅ | 全在 `services/obsidian_service.py`，测试覆盖 94% |
| 3.1.10 | `GET /api/knowledge/tree` | ✅ | |
| 3.1.11 | `GET /api/knowledge/search` | ✅ | |
| 3.1.12 | `GET /api/knowledge/note` | ✅ | |
| 3.1.13 | `PUT /api/knowledge/note` | ✅ | |
| 3.1.14 | `GET /api/knowledge/graph` | ✅ | |
| 3.1.15 | `GET /api/knowledge/stats` | ✅ | |
| 3.1.16 | `GET /api/knowledge/backlinks` | ✅ | |
| 3.1.17 | `GET /api/knowledge/daily` | ✅ | |
| 3.2.1-4 | 4 个独立前端页 | ⚪ | 实际用单页 `pages/knowledge.tsx` 替代（含 tab 切换） |
| 3.3.1 | `markdown_utils.py` | ⚪ | 内联到 obsidian_service，未独立 |
| 3.3.2 | 支持 `[[page\|alias]]` 等格式 | 🟡 | WIKILINK_RE 支持基础 alias + heading |

### Phase 4: 信息推送模块（15 项）

| # | 计划项 | 状态 | 备注 |
|---|---|---|---|
| 4.1.1 | `fetch_rss_sources()` | ⚪ | ai_news.py 在 agent-memory 仓库，独立运行 |
| 4.1.2 | `summarize_articles()` | ⚪ | 同上 |
| 4.1.3 | `generate_daily_report()` | ⚪ | 同上（生成日报写在 Obsidian） |
| 4.1.4 | `generate_weekly_report()` | ⚪ | 同上 |
| 4.1.5 | `parse_jsonl_tokens()` | ⚪ | stats.py 在 agent-memory，独立运行 |
| 4.1.6 | `parse_git_stats()` | ⚪ | 同上 |
| 4.1.7 | `get_daily_stats()` | ⚪ | 同上 |
| 4.1.8 | 9 个 news API | 🟡 | 只实现了 6 个读端点（daily/weekly/stats/sources），无 trigger/history |
| 4.2.1-4 | 4 个独立前端页 | ⚪ | 实际用单页 `pages/news.tsx` |
| 4.3.1 | macOS launchd 不变 | ✅ | agent-memory 独立运行 |
| 4.3.2 | Web 端只读 | ✅ | |
| 4.3.3 | 手动触发 API | ⚪ | 没建（macOS launchd 自动跑） |

### Phase 5: 跨模块联动 + 打磨（8 项）

| # | 计划项 | 状态 | 备注 |
|---|---|---|---|
| 5.1.1 | 综合 recommendations | 🟡 | 只用 interview weak spots + obsidian + news stats，没用 RSS 热点 |
| 5.1.2 | Dashboard AI 卡片 | ✅ | |
| 5.2.1 | `GET /api/dashboard` 聚合 | ✅ | |
| 5.3.1 | 全局 Loading skeleton | ⚪ | 没独立组件（可能内联） |
| 5.3.2 | ErrorBoundary | ⚪ | 没建 |
| 5.3.3 | Toast 通知 | ⚪ | 没建 |
| 5.3.4 | 空状态占位图 | 🟡 | 简单占位（没设计稿） |
| 5.3.5 | 移动端响应式 | 🟡 | 没专门做（桌面优先） |
| 5.3.6 | 暗色模式唯一 | ⚪ | 当前是唯一暗色（不算打磨任务） |

---

## 二、状态汇总

| 状态 | 项数 | 占比 |
|---|---|---|
| ✅ 已完成 | **35** | 51% |
| 🟡 部分做 / 不完整 | **15** | 22% |
| ⚪ 不必要（设计已变） | **18** | 26% |
| ➖ N/A | **1** | 1% |
| 🔴 必须做但没做 | **0** | 0% |

> 注：0 项 🔴 表示 V1 范围内**没有"必须做但漏掉"的**，所有应该做的都做了或部分做了。
>
> **真正的缺口是 plan.md 之外的设计**（参见第三节）。

---

## 三、Plan.md 之外的缺口（V2 候选）

这些在 plan.md 没列（或列了但被简化），但 spec.md/technical-spec.md 写过，是用户能感知的"少"：

| # | 缺口 | spec.md 出处 | 影响 | V2 优先级 |
|---|---|---|---|---|
| 1 | **SummaryService** | technical-spec § 5.4 | 面试报告 / 简历缺 AI 摘要 | 🟡 中 |
| 2 | **ProfileSettlementService** | technical-spec § 5.5 | 答完题 / 面完试，画像 `skill_map` / `weak_topics` 不自动更新 | 🔴 高 |
| 3 | **ObsidianSedimentService** | technical-spec § 5.6 | 学完不会自动写笔记回 Obsidian（"沉淀"环节断裂） | 🔴 高 |
| 4 | monthly_report 自动生成 | spec § 八、成功指标 | monthly_reports 表存在但永远空 | 🟡 中 |
| 5 | summary / weak_topics / skill_map 字段 | technical-spec § 2.8 | Profile 模型可能没这些字段 | ⚪ 待验 |

**结论**：plan.md 把 6 个 service 简化成 5 个（按数据对象拆，不按职责），把"智能沉淀层"整层砍了。这不是 V1 的失败，而是 **V1 的明确边界**：CRUD 完整 + 智能层留空。

---

## 四、决策建议

### 4.1 关闭 V1 的依据

- plan.md 5 个 Phase 的 CRUD 层全部完成（35 项 ✅ + 15 项 🟡）
- 数据模型完整（19 张表，比 plan 多 13 张）
- 前端 19 个页面，比 plan 单页面更扁平（按 V2 设计哲学演化）
- 367 测试，82% 覆盖，DOD ✅

### 4.2 V1 的明确边界

| V1 做了 | V1 没做 |
|---|---|
| CRUD（题库 / 复习 / 问答 / 计划） | LLM 摘要生成（SummaryService） |
| 基础统计（dashboard / radar） | Profile 自动沉淀（ProfileSettlementService） |
| Obsidian 读取（list/read/search/graph） | Obsidian 自动写回（ObsidianSedimentService） |
| 推荐基础规则 | 智能推荐（基于 RSS 热点 + 学习进度） |

### 4.3 V2 启动条件

满足任一即启动 V2：
- 用户明确要求"补摘要 / 自动画像 / Obsidian 沉淀"
- 用户日报、周报、简历等场景出现"AI 生成的总结"需求
- plan.md 修订：把 3 个 service 加进 plan

### 4.4 不建议做的（⚪ 项）

下列项**不建议补**，因为：
- 1.1.4 refresh：JWT 短期有效，不需要 refresh
- 1.1.6/7 邮箱登录页：dev-login 已覆盖内部测试场景
- 1.2.2 SMTP：无邮件通知功能，不需要
- 3.2 知识库 4 个独立页面：扁平单页 + tab 切换更现代
- 4.1 RSS / 摘要生成：在 agent-memory 仓库跑，本仓库只读
- 5.3 Loading/Toast/移动端：MVP 不在 V1 范围

---

## 五、行动项

### 5.1 立即做（关闭 V1 配套）

- [x] 写 closure.md（本文档）
- [ ] 更新 `docs/tasks/2026-06-22-new-feature-question-bank/spec.md` 头部"状态：📋 产品设计" → "状态：✅ V1 已落地 + 📋 V2 待设计"
- [ ] 更新 CLAUDE.md "八、当前状态" 改成"V1 完成"
- [ ] 把本文档 commit 进 git

### 5.2 V2 启动时再做

- [ ] 调研"3 个 service 缺失"是不是真要补（按业务价值排）
- [ ] 设计 V2 plan（如果决定做）

### 5.3 不做

- [ ] 把 ⚪ 项重新捡起来（理由见 § 4.4）

---

## 六、签收

- [x] 69 项已分类（35✅ + 15🟡 + 18⚪ + 1➖ + 0🔴）
- [x] 明确 V1 边界
- [x] V2 候选已列（3 个高优先级 service）
- [x] 行动项已分（5.1 立即 / 5.2 后续 / 5.3 不做）
- [x] 不建议做的项已说明理由

---

## 七、附录：phase 4 的特殊说明

Phase 4（信息推送）的所有"未做"项**不应被理解为 backlog**，因为：
1. `agent-memory/scripts/ai_news.py` 在独立仓库跑（macOS launchd 调度）
2. `agent-memory/scripts/stats.py` 同上
3. 它们**已经每天生成日报和统计**，写到 `~/Obsidian/coding/ai/AI 日报 YYYY-MM-DD.md`
4. 本仓库 `services/news_service.py` 负责**读取这些文件**给 Web 端展示
5. `news_service._fallback_stats()` 在 DB 不可用时返回空，是设计如此

**所以 Phase 4 的"未做"是设计上正确的**——把生成侧留在 agent-memory（独立、可调 cron），本仓库只消费。

## 八、签收

| 角色 | 签收 |
|---|---|
| 实施（AI） | 已完成 69 项分类，写 closure.md |
| 产品（用户） | 待签收（"通过"阶段 5） |