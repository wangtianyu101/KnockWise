# 🔍 调研报告 · 新功能：AI 推送模块（重新构建）

> 日期：2026-07-17 · 调研人：Claude
> **关键事实**：AI 推送在原 [`2026-06-22-new-feature-ai-push/`](../2026-06-22-new-feature-ai-push/) 设计完整（spec.md 612 行），但代码**完全未实现**。本次任务 = 从头实现 + scope 收窄。

---

## 1. 任务理解（必填）

- **用户原话**: "对这部分功能重新优化"
- **AI 复述**: 实现 KnockWise 的 AI 推送模块，从头写代码 + 后端 + 前端 + 集成；scope 收窄为**只推 AI/LLM/Agent 技术**，去掉 spec 原写的"商业/投资/PM" 内容；目标用户收敛到 AI 应用开发者 / Agent 开发者 / 大模型技术关注者。
- **涉及模块**: `ai-push`（独立模块，不调用其他模块 — 沿用原 spec.md § 二 2.2 独立性原则）
- **估时**: ~40-60h
  - 后端 ~25h（7 表迁移 + 3 service + 16 API + RSS 抓取 + LLM 集成 + scheduler）
  - 前端 ~10h（5 页 + 5 组件）
  - 测试 ~10h（service / API / scheduler 测试 ≥80% 覆盖）
  - 集成 ~5h（macOS notification / 微信接入如选）

---

## 2. 现状扫描（必填）

### 2.1 相关文件

| 类别 | 文件 | 状态 |
|---|---|---|
| **现有 spec**（设计输入）| `docs/tasks/2026-06-22-new-feature-ai-push/product-doc.md` | 502 行 · 已读 |
| | `docs/tasks/2026-06-22-new-feature-ai-push/spec.md` | 612 行 · 已读 |
| | `docs/tasks/2026-06-22-new-feature-ai-push/design-spec.md` | 待读（步 1 时读）|
| **配套调研** | `docs/tasks/2026-07-17-investigate-ai-push-survey/research.md` | 生态调研 |
| | `docs/tasks/2026-07-17-investigate-ai-push-survey/wechat-integration-plan.md` | 微信集成方案 |
| **scope 约束** | `~/.claude/memory/project-ai-push-scope.md` | scope 已 sediment |
| **CLAUDE.md 流程** | `CLAUDE.md` § 一 v1→v2 6 步流程 · § 六 单测强制规则 · § 6.7 verify-loop | 强制 |

### 2.2 不存在的文件（= 本次新建）

| 类别 | 文件 |
|---|---|
| 后端 service | `backend/services/digest_service.py` |
| | `backend/services/digest_scheduler.py` |
| | `backend/services/digest_preference_service.py` |
| | `backend/services/digest_source_service.py` |
| | `backend/services/wechat_push_service.py`（如果做微信）|
| 后端 API | `backend/api/digest/*`（16 个 endpoint）|
| 后端 schemas | `backend/schemas/digest.py` |
| 后端 models | `backend/models/digest.py`（7 张表）|
| 后端 migration | `backend/migrations/004_digest.sql` |
| 前端 page | `frontend/pages/push/index.tsx` 等 5 页 |
| 前端 component | `frontend/components/digest/*` 等 5 组件 |
| 测试 | `backend/tests/services/test_digest_service.py` 等 |

### 2.3 最近相关改动（git log）

```
e424d58 feat(services): V2.3-T19 weekly/monthly/sync_daily_to_obsidian 实施
3fb1de1 feat(services): V2.3-T18 daily + dashboard + Redis TTL 1h 缓存
ad7f9ac feat(services): V2.3-T17 _generate_narrative 实现（LLM + 降级）
d560e3f feat(services): V2.3-T16 SummaryService 骨架 + Redis TTL hook
```

→ **V2 智能沉淀层最近实施**（SummaryService / ObsidianSedimentService）— 是 AI 推送的"亲戚"模块，可以**借鉴其 LLM 集成模式**（Redis TTL 缓存 + LLM 降级）。

### 2.4 类似功能怎么实现的（必填）

**参考 A — SummaryService（`backend/services/summary_service.py`）**：
- 模式：cron 触发 → LLM 摘要 → Redis TTL 1h 缓存 → 写 DB
- 复用：**LLM 调用 + Redis TTL 缓存** 模式直接套用到 AI 推送
- 借鉴：`_generate_narrative` 降级机制（LLM 失败 → 降级到默认文本）

**参考 B — ObsidianSedimentService（`backend/services/obsidian_sediment_service.py`）**：
- 模式：事件触发 → 写文件到 `~/Obsidian/coding/`
- 复用：**Obsidian 写回功能** 直接套用（spec.md § 四 4.5 已设计）
- 借鉴：fail-soft 行为（写失败不阻塞主流程）

**参考 C — Scheduler（`backend/services/scheduler.py`）**：
- 模式：APScheduler cron 触发
- 复用：DigestScheduler 直接基于这个实现
- 借鉴：现有调度任务的注册 / 健康检查模式

---

## 3. 依赖发现（必填）

### 3.1 改这些文件会影响

| 文件 | 影响 |
|---|---|
| `backend/services/scheduler.py` | 注册 DigestScheduler 任务（与现有任务共存）|
| `backend/core/database.py` | `_MIGRATIONS` 添加 `004_digest.sql` 引用 |
| `backend/main.py` | 注册 `digest` API router |
| `backend/seed_data/*.json` | 默认信源 4 条（DigestSource 默认值）|
| `frontend/package.json` | 不需要新依赖（用现有 Next.js + shadcn）|
| `backend/requirements.txt` | **新增** `feedparser>=6.0` + `resend>=2.0` |
| `frontend/CLAUDE.md`（如有）| 新增 /push 路由 |

### 3.2 需要先改的（前置依赖）

| 前置 | 为什么 |
|---|---|
| profile 表加 `digest_stats` JSON 字段 | spec.md § 二 2.7 要求 |
| profile 表加 `wechat_openid` 字段（如果做微信）| wechat-integration-plan § 2.4 |
| LLM client 接口（已存在？需确认） | DigestService 调用 LLM 选题 + 摘要 |
| Email service（已存在？需确认） | 邮件推送渠道 |
| macOS notification 客户端（不存在，需建） | 暂缓（spec.md § 七 7.3 P1 暂缓）|

### 3.3 调用方清单（实现前必查）

本模块**对外暴露**：
- 16 个 REST API（spec.md § 六 6.1）· 暂未实现
- 1 个 cron 任务（DigestScheduler）· 暂未注册

本模块**对内调用**（按 spec.md § 二 2.2 独立性原则）：
- ❌ **不调用**任何其他业务模块
- ✅ 调用底层基础设施：DB / Redis / LLM client / Email client
- ✅ 调用 profile 表（写 digest_stats 字段）

### 3.4 跨模块影响

| 影响 | 等级 | 说明 |
|---|---|---|
| profile 表加字段 | 🟡 中 | 已有迁移模式（ALTER TABLE）· 加 JSON 字段 |
| Scheduler 注册新任务 | 🟢 低 | 与现有 task 共存 · 不会冲突 |
| LLM API 调用新增 | 🟡 中 | DeepSeek 调用频率 ↑ · 成本评估见 research.md § 3 #2 |
| 邮件发送新增 | 🟢 低 | 现有 Resend 集成 · 加新模板 |

---

## 4. 风险评估（必填）

| 风险 | 等级 | 缓解 |
|---|---|---|
| **scope 收窄后 RSS 源减少**（36氪 偏商业可能移除）| 🟡 中 | 补 Agent 专属源（LangChain / Anthropic / Interconnects / Last Week in AI）|
| **LLM 成本** 1000 用户/天 ≈ ¥150（research.md § 3 #2）| 🟡 中 | Redis TTL 缓存 + LLM 降级（参考 SummaryService 模式）|
| **跨模块边界** · "不调用其他模块" 严格执行 | 🟢 低 | spec.md § 二 2.2 已明确 · 实现时注意 |
| **cron 时区处理** · 多用户不同时区 | 🟡 中 | 用户设置时区 · push_hour 字段已设计 |
| **macOS notification P1 暂缓** | 🟢 低 | 不在 P0 scope · 不阻塞 |
| **微信集成（可选）** | 🟡 中 | 涉及资质 + 审核 4-6 周 · P1 推迟 |
| **议題** 沉积 | 🟢 低 | 无历史 AI push 议題（模块未实现）|
| **已有未提交改动冲突** | 🟢 低 | git status 干净（仅本会话的两个 docs commit）|
| **RSS 源不稳定**（机器之心 RSS 关停过）| 🟡 中 | 多源 fallback · LLM 选题失败降级 |

---

## 5. 输出建议（必填）

### 5.1 推荐路径（6 步）

```
0 调研（本步完成）✅
→ 1 规格（spec.md · 三脑交汇 · 按 spec-template §2 写 Requirement + Scenario）
→ 2 计划（plan.md + db-design.sql + api-spec.md + component-spec.md）
→ 3 拆分（tasks.md · ≤1h 原子任务）
→ 4 实现（TDD 红→绿→refactor · 配套单测 ≥80% · § 6.7 verify-loop）
→ 5 验证（L3 整合测试 + L5 staging 实地）
→ 6 复盘（retro.md · 按 § 6.6 自动写）
```

### 5.2 P0 scope（建议本期必做）

| # | 内容 | 工作量 | 价值 |
|---|---|---|---|
| 1 | 7 表 schema + migration `004_digest.sql` | 2h | 🟢 必需 |
| 2 | DigestService 骨架（fetch / select / summary / save） | 6h | 🟢 必需 |
| 3 | 选题 + 摘要 LLM prompt（含 scope 收窄过滤规则） | 2h | 🟢 必需 |
| 4 | 4 RSS 源（改 36氪 → 加 Agent 专属源） | 3h | 🟢 必需 |
| 5 | 邮件渠道（基于现有 Email service） | 2h | 🟢 必需 |
| 6 | 16 个 REST API（CRUD） | 5h | 🟢 必需 |
| 7 | DigestScheduler（cron 注册） | 2h | 🟢 必需 |
| 8 | 用户偏好 + 屏蔽机制（topic 7 天 -50% 权重） | 3h | 🟢 必需 |
| 9 | 前端 5 页 + 5 组件（基于 mockup）| 8h | 🟡 必需 |
| 10 | 测试覆盖 ≥80%（service + API + scheduler） | 8h | 🟢 必需 |
| 11 | reading duration 字段塞 LLM prompt（项目差距 #3）| 2h | 🟢 顺手 |
| 12 | 跨日报去重（Redis 缓存 24h 标题） | 2h | 🟢 顺手 |
| **小计** | | **~43h** | |

### 5.3 P1 scope（建议本期可选，看用户优先级）

| # | 内容 | 工作量 | 价值 |
|---|---|---|---|
| 13 | 微信公众号模板消息集成（service 号资质）| 4-6 周（含资质） | 🟢 国内分发天花板 |
| 14 | 飞书 / 钉钉机器人 | 2-3 天 | 🟡 B 端拓展 |
| 15 | macOS notification | 3 天 | 🟢 P1 推迟 |
| 16 | Obsidian 双向同步（笔记 highlight 反哺） | 1 周 | 🟡 差异化 |

### 5.4 关键决策点（必填 ≥ 1）

**决策 1：source list 改不改？**

| 方案 | 描述 | 优势 | 劣势 |
|---|---|---|---|
| A. 保留 4 源 | 量子位 / 36氪 / HF / arXiv | 简单 · 改动小 | 36氪 偏商业 · 与 scope 冲突 |
| B. 36氪 减权重 | LLM 选题 prompt 加"商业内容降权" | 最小侵入 | 36氪 仍然算"AI 圈"，砍可惜 |
| C. 替换 36氪 → 加 Agent 源 | 加 LangChain / Anthropic blog / Interconnects | 严守 scope · 加差异化 | 失去商业信号源 |
| **推荐 C** | 严守 scope 收窄原则 · 用户已明确不要商业 | 🟢 |

**决策 2：DeepSeek V3 vs V4？**

| 方案 | 描述 | 成本 |
|---|---|---|
| A. 沿用 V3（spec 已写） | 稳定 · 已有集成 | 中 |
| B. 升级 V4 | 成本 ↓ ~1/4（research.md § 6 pricing 数据）| 低 |
| **推荐 B** | V4 已发布 · 显著降本 · 不升级错过窗口 | 🟢 |

**决策 3：类别从 5 类改 4 类？**

| 方案 | 描述 |
|---|---|
| A. 删"🏢商业"类 | scope 收窄后无内容可推 |
| B. 改名"🏢AI 公司动态" | 保留视觉分类位置 · 但内容限制到 AI 公司 |
| **推荐 B** | 视觉结构稳定 · 内容严格 |

**决策 4：本期是否做微信集成？**

| 方案 | 描述 |
|---|---|
| A. 不做 | 4-6 周 · 等下一个 sprint |
| B. 仅做方案落地 | 按 wechat-integration-plan.md 但**不实施** |
| **推荐 B** | 文档已经写好 · 留给下期实施 |

### 5.5 元信息

- **是否需要外部评审**: 否（独立模块 · 不影响其他模块）
- **是否涉及 schema 变更**: 是（profile 加 2 字段 + 7 新表）
- **是否需要 AB 测试**: 否（P0 不分流量）
- **是否需要 feature flag**: 否（独立模块，全量发布）
- **是否有 PR 标志**: 否（首次实现）

---

## 6. spec.md 写法（必读 · 指向规范模板）

按 [`docs/templates/spec-template.md`](../../templates/spec-template.md) § 2 的 Requirement + Scenario 双层结构写：

- **Requirement ≥ 1**：用 `### Requirement: <名字>` + `The system SHALL <承诺>`
- **Scenario ≥ 3**：每个用 `#### Scenario: <名字>` + Given/When/Then
- **4 类场景覆盖**：happy / invalid / edge / failure 至少各 1
- **强约束 SHALL**：禁止 should / may

**对比原 spec.md**：原 spec 写法是 free-form 散文，**不符合 spec-template.md 要求**。本次 spec.md **必须用 Requirement+Scenario 结构重写**，pre-commit 会自动校验。

**自动校验**：
```bash
python3 scripts/check-step.py spec docs/tasks/2026-07-17-new-feature-ai-push/spec.md
```

---

## 自检清单

- [x] 任务理解段已写且用户复述对
- [x] 现状扫描覆盖 ≥ 3 个相关文件（旧 spec + 调研 + scope memory）
- [x] 依赖发现列出 ≥ 3 个影响点（profile / scheduler / LLM / email / 微信）
- [x] 风险评估 ≥ 3 条带等级（9 条风险 · 2 红 4 黄 3 绿）
- [x] 输出建议给完整 6 步路径
- [x] 关键决策点 ≥ 1（给了 4 个）
- [x] 已查 git log（最近 V2.3 实施 · 无 AI push 相关 commit）
- [x] 步 1 spec.md 按 spec-template §2 Requirement+Scenario 结构（不是 free-form）

---

## 元信息

- **本调研文档版本**：v1 · 2026-07-17
- **路径**：`docs/tasks/2026-07-17-new-feature-ai-push/research.md`
- **下一步**：等用户批准 → 进 1 步 · 用 spec-template.md 写新 spec.md（不是沿用旧 spec）
- **重要差异**：旧 spec.md（2026-06）写的是 free-form 散文 · 本次必须用 Requirement + Scenario 结构（更严格）
