---
title: L4 Review 报告 · V2 智能沉淀层
date: 2026-07-06
status: v1（待你 review）
tags: [review, L4, V2, 智能沉淀]
related:
  - [verify.md](verify.md) — V2.4 验证
  - [retro.md](retro.md) — V2.5 复盘
---

# L4 Review 报告：V2 智能沉淀层

> **审查人**: @王天宇（待你签字）
>
> **审查范围**: V2 全部 25 个 commits
>   - **本地未 push**: 11 个 commits（focus of this review）
>   - **已 push origin/main**: 14 个 commits（V2.1 8 + V2.2 6 + V2.3 T16-T19 = 14，**已部分推过**，仅回顾）
> - **审查日期**: 2026-07-06
>
> **审查员**: AI 辅助（@Claude Opus 4.8）

---

## 1. Commit 清单（11 个本地未 push · 重点 review）

| # | hash | 标题 | 类别 | 文件数 | 关键产物 |
|---|---|---|---|---|---|
| 1 | `0e455a3` | feat(api): V2.3-T20-T22 6 端点 + 14 测试 | 后端 | 3 | `api/v2_settlement.py` + `test_api_v2.py` |
| 2 | `96a01e6` | feat(ui): V2.3-T23 DailySummaryCard + 嵌入 dashboard.tsx | 前端 | 2 | `components/v2-settlement/DailySummaryCard.tsx` |
| 3 | `6d9c2e1` | feat(ui): V2.3-T24 RecentSedimentsCard + 嵌入 knowledge.tsx | 前端 | 2 | `RecentSedimentsCard.tsx` |
| 4 | `cb19140` | feat(ui): V2.3-T25 新建 /profile 页 + nav 加画像入口 | 前端 | 1 | `pages/profile.tsx`（350 行） |
| 5 | `a3db146` | feat(verify): V2.4 验证文档 | 文档 | 1 | `verify.md` |
| 6 | `dca9def` | feat(retro): V2.5 复盘 + CLAUDE.md + api README | 文档+配置 | 3 | `retro.md` + CLAUDE.md + api/README.md |
| 7 | `ef8923f` | feat(docs): V2 完整 0-3 步文档 | 文档 | 7 | research/spec/plan/api-spec/component-spec/design-spec/product-doc |
| 8 | `6fed65f` | fix(scripts): check-step.py 兼容 markdown bold | 脚本+测试 | 2 | `scripts/check-step.py` + `tests/test_check_step.py` |
| 9 | `43e3f1f` | fix(retro): 发现 V2 前端 antd 依赖缺口 + 删失败测试 | 文档 | 1 | retro.md 更新 |
| 10 | `9631d2d` | fix(ui): 装 antd 6.5 + icons + recharts + 16 V2 测试 | 依赖+测试 | 5 | `package.json/lock` + 3 测试文件 |
| 11 | `e009891` | fix(retro): 标改进项 #7 完成 | 文档 | 1 | retro.md 标完成 |

---

## 2. 已推 origin/main 的 14 个 commits（仅回顾）

```
V2.1 PR 1（8 commits）:
  a4b0c85  feat(services): V2.1-T1 ProfileSettlementService 骨架 + SettlementResult schema
  d12595b  feat(services): V2.1-T2 settle_after_practice 实施
  1cbc76a  feat(services): V2.1-T3 settle_after_interview 实施
  db2dced  feat(services): V2.1-T4-T5 weekly_full_refresh + manual_refresh 实施
  be598b0  feat(services): V2.1-T6 upsert_progress 末尾触发 settlement
  33f494f  feat(services): V2.1-T7 interview.py:complete 触发链 + 拆 interview_settlement.py
  035ad45  test(services): V2.1-T8 凑齐覆盖率 ≥ 80% + 6 个边界测试

V2.2 PR 2（6 commits）:
  42c04d3  feat(services): V2.2-T9 ObsidianSedimentService 骨架 + _write 容错
  428d208  feat(services): V2.2-T10 write_daily 实现 + YAML frontmatter
  f4a4606  feat(services): V2.2-T11-T12 weekly/monthly/mastered/practice_log 实施
  3d1148e  feat(services): V2.2-T13 settle_after_practice 触发 write_daily
  9de073e  feat(services): V2.2-T14 settle_after_interview 触发 write_practice_log
  9fbfc99  test(services): V2.2-T15 obsidian_sediment 凑齐 100% 覆盖率

V2.3a 后端（4 commits — T16-T19 已在 origin/main）:
  d560e3f  feat(services): V2.3-T16 SummaryService 骨架 + Redis TTL hook
  ad7f9ac  feat(services): V2.3-T17 _generate_narrative 实现（LLM + 降级）
  3fb1de1  feat(services): V2.3-T18 daily + dashboard + Redis TTL 1h 缓存
  e424d58  feat(services): V2.3-T19 weekly/monthly/sync_daily_to_obsidian 实施
```

> 注：14 个 commits 之前你 git push 过，所以不在 `origin/main..HEAD` 范围。但功能上属于 V2 完整交付的一部分。

---

## 3. Spec 对齐检查

| 验收点（spec.md / api-spec.md / component-spec.md） | 状态 | 证据 |
|---|---|---|
| 3 个 service 4+5+5=14 方法 | ✅ | ProfileSettlementService(4) + ObsidianSedimentService(5) + SummaryService(5) |
| 6 个 API 端点 | ✅ | `api/v2_settlement.py` 6 路由 |
| 3 个前端组件 + 1 新页 | ✅ | DailySummaryCard / RecentSedimentsCard / ProfilePage |
| 9 个 GWT 覆盖 | 🟡 | 自动化 L3 覆盖 happy/edge/failure/vault_missing/422/unauthorized，**L5 staging 待你跑** |
| 7 决策全 A | ✅ | plan.md §3 标 ✅（同步链/Redis 1h/service 内触发/拆 interview.py/3 PR/新建 /profile/不抛 + log） |
| Spec §3.2 限流（slowapi） | ⚠️ | **未实现**，代码注释已标"留待 V2.5 优化阶段"（api-spec.md §6.3） |
| Spec §3.4 错误响应统一格式 | 🟡 | API 端点内部抛 HTTPException(422) 走 FastAPI 默认响应，**未严格封装 `{error: {code, message, details}}`** |

---

## 4. 测试覆盖检查

| 维度 | 状态 | 数字 |
|---|---|---|
| **后端单测** | ✅ | 471 → **476 tests pass**（+ 5 check-step.py 回归） |
| **后端覆盖率** | ✅ | profile **82%** / interview **82%** / obsidian **100%** / summary **81%**（全 ≥ 80% DOD） |
| **前端单测** | ✅ | V1 111 + V2 16 = **127 tests pass** |
| **e2e 集成** | ✅ | test_api_v2.py 14 端点 contract tests |
| **Check-step.py 回归** | ✅ | 5 测试覆盖 bold/plain/mixed/over-hour/real V2 docs |

---

## 5. 风险点（按 🔴🟡🟢 排序）

### 🔴 已知生产风险（**必须 L5 跑 3 流程验证**）

1. **V2 端点未实施 slowapi 限流**（commit `0e455a3`）
   - 现状：6 个 `/api/v2/*` 端点无限流
   - 风险：恶意用户可高频调 `/api/v2/dashboard/summary` 打满 LLM 配额 / Redis 缓存
   - 缓解：spec §3.2 限流表格已定义，**V2.5 优化阶段接入**
   - 建议 review 决定：是先 merge 后补限流，还是先补限流再 merge

2. **错误响应未严格统一格式**（commit `0e455a3`）
   - 现状：FastAPI 默认 `{"detail": "..."}`，不是 spec §3.4 要求的 `{"error": {"code", "message", "details"}}`
   - 影响：前端 axios 拦截器要兼容两种格式
   - 建议：在 api-spec.md §3.4 加 note "V2 端点暂用 FastAPI 默认错误格式，V2.5 统一" 或在 T20 加 Pydantic 错误包装

### 🟡 已知但有缓解

3. **antd 装好但 V1 风格不一致**（commit `9631d2d` + `96a01e6`/`6d9c2e1`/`cb19140`）
   - V2 组件用 antd Card/Skeleton/Tag 等，V1 走 Tailwind 自定义
   - 风险：UI 风格不统一（antd 默认 dark theme + V1 深色背景可能冲突）
   - 缓解：L5 staging 实跑看效果
   - 建议：若 L5 发现视觉割裂，V3 统一改 Tailwind（重写 3 组件）

4. **LLM 调用无成本监控**（commit `ad7f9ac` / `3fb1de1`）
   - 现状：每次调 LLM 无费用/配额追踪
   - 风险：用户高频用 → 成本爆
   - 缓解：Redis TTL 1h 缓存命中率预期 >80%
   - 建议：V3 加 token 用量埋点

5. **`/profile` 页 nav 内联**（commit `cb19140`）
   - 现状：/profile 页有自己的 nav 副本（与 dashboard/knowledge 重复 7 个 tab）
   - 风险：nav 改动要改 3 处
   - 缓解：当前 nav 内容相同
   - 建议：V3 抽 `<NavBar />` 共享组件

### 🟢 已规避 / 不在 review 范围

6. ~~check-step.py bold 兼容性~~ — ✅ 改进项 #1 已修
7. ~~antd 依赖缺口~~ — ✅ 改进项 #7 已装
8. ~~覆盖率不足~~ — ✅ 4 service 全 ≥ 80%
9. ~~L4 review 后 GWT 未跑~~ — 等 L5 staging

---

## 6. 代码质量抽样

### ✅ 优点

- **决策 7A 全贯穿**：所有 service 方法 `try/except` + log + return None/降级，主业务不感知
- **乐观锁正确实现**：`commit 失败 → retry 1 次 → 仍失败 log + return None`（spec GWT-3）
- **V1 模式复用**：conftest mock_db / mock_cache / mock_llm 全部沿用
- **Feature flag 兜底**：`V2_ENABLED()` 一键关掉所有 V2 前端
- **Trigger 解耦**：3 个 trigger 函数放 `interview_settlement.py` 拆分 interview.py（决策 4A 实施）
- **测试边界覆盖**：concurrent / db_failure / vault_missing / LLM 降级 / 422 格式错 / unauthorized 都有

### 🟡 待 review 时重点看

- `backend/api/v2_settlement.py` (223 行) — 6 端点全集中，**是否有过度聚合？** 若 V3+ 加端点，应拆 `api/v2/dashboard.py` / `api/v2/profile.py` 等
- `frontend/pages/profile.tsx` (350 行) — `/profile` 单文件含 nav + 4 区块 + 趋势图，**是否可拆组件？** 当前 useState 较多
- `backend/services/summary_service.py` (217 行) — `_generate_narrative` 返回 tuple `(text, llm_success)` 是否合理？或更好用 dataclass？
- `backend/services/profile_settlement_service.py` (234 行) — 4 方法逻辑相似（"读 DB → 算 → 写 Profile → commit 重试 1 次"），**可抽公共方法减少重复**

---

## 7. L4 Review Checklist（**待你 review 后勾选**）

### 7.1 Spec 对齐
- [ ] 3 service / 6 端点 / 3 前端组件全部覆盖
- [ ] 9 GWT 至少 happy/edge/failure 各 1 个测试
- [ ] 7 决策 7A 全落地
- [ ] LLM 降级 + Redis 降级 + vault 降级 3 重都验证
- [ ] 乐观锁（commit 重试 1 次）验证
- [ ] 错误响应格式（spec §3.4）已对齐或接受临时 FastAPI 默认

### 7.2 测试质量
- [ ] 471 + 5 + 16 = 492 tests 全绿
- [ ] 4 service 覆盖率 80%+ 已达 DOD
- [ ] 边界 case（concurrent / vault_missing / llm_504 / 422）覆盖
- [ ] L4 抽 5-10 个测试手验 happy/edge/failure（reviewer 选）

### 7.3 代码质量
- [ ] 函数命名清晰（`settle_after_practice` 比 `update_profile` 更精准）
- [ ] 错误处理一致（决策 7A：log warning + return None，不抛）
- [ ] 类型注解完整（Python type hints + Pydantic schema + TypeScript interface）
- [ ] 注释充分（module docstring + 函数 docstring + spec GWT 引用）

### 7.4 安全 / 权限
- [ ] 6 端点全部 JWT 认证
- [ ] `user_id` 从 JWT token 取（不接 request body）
- [ ] `rel_path` 不接用户输入（防 `../` 跳出 vault）
- [ ] LLM prompt 先 strip markdown + 截断 1000 字（防注入）
- [ ] profile 字段 4 个（weak_topics / mastered_topics / learning_trajectory / last_active_at）都是 V1 已扩字段，**无新 schema 变更**

### 7.5 文档完整
- [ ] verify.md 5 层 gate 标记（L1-L3 自动 ✅，L4-L5 待你签字）
- [ ] retro.md 5 段齐全（数据 / 做对 / 做错 / 改进 / 沉淀）
- [ ] CLAUDE.md §八.8.2 标 V2 完成
- [ ] docs/api/README.md 加 6 V2 端点
- [ ] 7 份 V2 0-3 步文档全 commit

### 7.6 待你决定
- [ ] **是否接受** slowapi 限流未实施（V2.5 优化阶段补）
- [ ] **是否接受** FastAPI 默认错误格式（不是 spec §3.4 严格格式）
- [ ] **是否接受** antd 引入与 V1 风格不一致（V3 决定）
- [ ] **L5 staging** 是否现在跑（./scripts/start.sh + 浏览器 3 流程）

---

## 8. Review 结论模板

请你 copy 这个结论填上：

```markdown
## L4 Review 结论

✅ **通过** / ⚠️ **通过 + 建议** / ❌ **拒绝**

**关键反馈**：
- <每条反馈 1 行>

**要求改进**（如选 ⚠️）：
- [ ] <具体动作 1>
- [ ] <具体动作 2>

**签字**: @<你的名字> <2026-07-06>
```

---

## 9. 推荐 review 顺序

| 优先级 | commit | 理由 |
|---|---|---|
| 🔴 高 | `0e455a3` (T20-T22 6 端点) | 6 端点是用户能直接调用的接口，影响面最大 |
| 🔴 高 | `cb19140` (T25 /profile 新页) | 350 行单文件 + 决策 6A 实施 |
| 🟡 中 | `96a01e6` / `6d9c2e1` (T23/T24 组件) | V2 顶部卡 + 知识库卡 |
| 🟡 中 | `9631d2d` (antd 装) | 依赖变更，决定 L4 是否接受 antd 风格 |
| 🟢 低 | `a3db146` / `dca9def` / `ef8923f` | 文档，纯阅读 |
| 🟢 低 | `6fed65f` / `43e3f1f` / `e009891` | 改进项 fix |

---

## 10. 提醒：L5 staging 跑通后才算 V2 真闭环

L4 review 完成后，**还需要 L5**：
1. `./scripts/start.sh` 起本地
2. 浏览器开 http://localhost:3000
3. 3 流程：
   - 答 3 道题 → 看 dashboard 顶部卡更新
   - 开 /profile → 看 4 区块 + 趋势图
   - 开 /knowledge → 看 stats tab 沉淀卡
4. 截图存档 + 标 verify.md §L4 §L5 ✅

L4 + L5 都签字 → V2 100% 完成 → 可 push。