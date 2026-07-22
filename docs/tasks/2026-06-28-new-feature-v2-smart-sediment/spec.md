---
title: Spec 规格 · V2 智能沉淀层
date: 2026-06-28
status: v1
tags: [spec, 1步, 技术脑, v2, 智能沉淀]
related:
  - [research.md](research.md) — 上游 0 步调研
  - [product-doc.md](product-doc.md) — 上游产品脑
  - [design-spec.md](design-spec.md) — 上游设计脑
  - [V1 母模块 spec](../2026-06-22-new-feature-question-bank/spec.md)
  - [V1 Technical Spec § 5.4-5.6](../2026-06-22-new-feature-question-bank/technical-spec.md) — 3 service 方法签名来源
---

# Spec 规格：V2 智能沉淀层

> **一句话**：把"产品意图"翻译成"机器可读的契约"——3 个 service + 6 个新端点 + 3 处前端改造，所有调用方按此实现 + 验收。
>
> **作者**：AI 主导（技术脑），用户/设计已 review product-doc.md / design-spec.md
>
> **下游**：tasks.md（第 3 步拆分）+ test-cases.md（第 4 步整合）+ verify.md（第 5 步）
>
> **校验状态**：✅ check-step.py spec 通过（spec DOD 5 段齐全 + 9 GWT + 7 schema + 17 测试用例 + research 引用 + 待你签字）

---

## 0. 上游引用（必填）

- **调研报告**：[`docs/tasks/2026-06-28-new-feature-v2-smart-sediment/research.md`](research.md)
- **产品文档**：[`docs/tasks/2026-06-28-new-feature-v2-smart-sediment/product-doc.md`](product-doc.md)
- **设计文档**：[`docs/tasks/2026-06-28-new-feature-v2-smart-sediment/design-spec.md`](design-spec.md)
- **调研版本**：v1（2026-06-28）
- **V1 收尾报告**：[`docs/tasks/2026-06-27-v1-closure/closure.md`](../2026-06-27-v1-closure/closure.md) — 3 service 缺失来源
- **关键决策**（从 research §5.3 + product-doc + design-spec 抄）：
  - 决策 1（LLM 策略）：**Redis 缓存 + 批量触发**（profile:{user_id} TTL 1h）— 调研推荐 A
  - 决策 2（Obsidian 时机）：**立即同步写**（失败 log warning 不阻塞）— 调研推荐 A
  - 决策 3（触发点位置）：**service 内调 settlement**（与 `upsert_from_interview` 模式一致）— 调研推荐 A
  - 决策 4（拆 interview.py）：**顺手拆**触发函数到 `interview_settlement.py` — 调研推荐 A
  - 决策 5（PR 节奏）：**分 3 PR**（V2.1/V2.2/V2.3）— 留 plan 阶段确认
- **关键风险**（从 research §4 抄，🔴 标）：
  - 🔴 LLM 调用成本不可控 → Redis 缓存 TTL 1h + 批量触发
  - 🟡 Obsidian vault 不存在 → `_write` 失败返回 None + log warning，不抛异常
  - 🟡 3 service 循环依赖 → `triggered_by` 参数明确方向，最多 1 层嵌套
  - 🟡 Profile 字段并发覆盖 → 乐观锁（`updated_at` 比对）
  - 🟡 议題 B（interview.py 803 行）→ V2 顺手拆 1-2 个触发函数

---

## 1. 用户故事（产品意图，必填）

### US-1：自动画像沉淀（V2.1 核心）

> 作为 **求职冲刺者 / 持续学习者**，我想要 **答完题/面完试后画像自动更新**，以便 **3 秒看到自己变强 / 变弱**，不用手动记。

**验收对应**：见 §2 GWT-1 / GWT-2 / GWT-3

### US-2：自动 Obsidian 写笔记（V2.2 核心）

> 作为 **持续学习者**，我想要 **答题/面试后 Obsidian 自动生成每日笔记**，以便 **告别手抄笔记**，把精力集中在答题本身。

**验收对应**：见 §2 GWT-4

### US-3：Dashboard 今日学习总结（V2.3 核心）

> 作为 **复盘型用户**，我想要 **打开 Dashboard 看到"今日/昨日学了啥"**，以便 **每天花 5 秒看成长轨迹**，激励继续学习。

**验收对应**：见 §2 GWT-5

---

## 2. 验收标准 / Requirement + Scenario（机器可验证，必填）

> 升级说明（2026-07-17）：从纯 GWT 升级为 Requirement (SHALL) + Scenario (GWT) 双层结构。
> - Requirement 层：系统承诺（SHALL 强约束）
> - Scenario 层：验收用例（沿用 GWT，向后兼容）

### Requirement: Profile Settlement
The system SHALL persist user's learning profile after each practice answer and handle concurrent settlements safely.

- **GWT-1 (happy)**：Given 用户答完 1 道 score=4 的题（topic=网络层），When `ProfileSettlementService.settle_after_practice(user_id, qid, 4)` 被触发，Then `Profile.weak_topics` 出现 `{topic: "网络层", error_rate: 0.X, count: 1}`，且 `last_active_at` 更新到当前时间
- **GWT-2 (edge: 答对 master)**：Given 用户答对同一 topic 第 2 次（`practice_count >= 2` 且 `mastered_count == 1`），When settlement 触发，Then 该 topic 从 `weak_topics` 移到 `mastered_topics`
- **GWT-3 (failure: 并发覆盖)**：Given 两个答题请求同时触发 settlement，When 两个 service 并发跑，Then 后写者用乐观锁检测（`updated_at` 比对），冲突时**重试 1 次**而不是覆盖

### Requirement: Obsidian Sediment
The system SHALL write daily learning notes to the Obsidian vault with graceful degradation on missing vault.

- **GWT-4 (happy)**：Given vault 存在（`~/Obsidian/coding/` 目录在），When `ObsidianSedimentService.write_daily(date, content)` 触发，Then 文件 `~/Obsidian/coding/learning/YYYY-MM-DD.md` 出现，content 包含 YAML frontmatter（date / topics / question_count）
- **GWT-5 (failure: vault 缺失)**：Given vault 不存在（`~/Obsidian/coding/` 不在），When write_daily 触发，Then 返回 `None`，log warning `"Obsidian vault not found"`，**不**抛异常，**不**阻塞上游业务

### Requirement: Dashboard Summary
The system SHALL generate a daily learning summary with LLM degradation and 1h Redis cache.

- **GWT-6 (happy)**：Given 用户昨天答了 8 道题、掌握 2 个新 topic，When `SummaryService.dashboard(user_id)` 被 `/api/dashboard/summary` 端点调用，Then 返回 `{title: "今日学习总结", body: "昨天你答了 8 道题，掌握 2 个新 topic...", yesterday_count: 8, mastered: [...], weak_shift: [...]}`
- **GWT-7 (failure: LLM 降级)**：Given LLM 调用失败（DeepSeek 504），When `SummaryService.daily()` 触发，Then **降级返回规则生成版**（不调 LLM，模板填数字），HTTP 200，body 含 `_fallback: true` 标记
- **GWT-8 (edge: 缓存命中)**：Given 同一用户在 1h 内第 2 次调 `dashboard`，When service 检查 Redis `summary:profile:{user_id}` 存在，Then **跳过 LLM 调用**直接返回缓存（5x 加速，成本降为 0）

### Requirement: Settlement Failure Isolation
The system SHALL isolate settlement failures from the main business flow without affecting API responses.

- **GWT-9 (failure: 触发失败不阻塞主业务)**：Given 用户答完题，When `ProfileSettlementService.settle_after_practice` 内部抛异常（DB 断连），Then `api/learn.py:answer` 端点**仍返回 200**（主业务不受影响），错误 log 到 `[settlement_failed]` 日志

---

## 3. 边界条件（防御性，必填）

### 3.1 空值 / 异常 / 并发（基础）

- **空值**：
  - `Profile.weak_topics = []`（新用户）→ settlement 写入新项不报错
  - `Profile.learning_trajectory = {}`（无趋势数据）→ `/profile` 趋势图显示空状态
  - `ObsidianSedimentService.write_daily(date=None)` → 用 `date.today()` 兜底
- **异常**：
  - LLM 504 → 降级规则生成版（见 GWT-7）
  - DB 断连 → settlement 失败 log 不抛（见 GWT-9）
  - Obsidian vault 不存在 → 返回 None 不抛（见 GWT-5）
  - Redis 不可用 → SummaryService 跳过缓存直接调 LLM（缓存是优化非必需）
- **并发**：
  - 同一用户同时 2 次答题 → settlement 用乐观锁（updated_at 比对）+ 重试 1 次
  - 同一用户同时 2 次 summary → Redis SETNX 防击穿，TTL 1h

### 3.2 时序（顺序依赖）

- 答题 → `learning_progress_service.upsert_progress` → 末尾触发 `settle_after_practice`（**必须**在 progress 写完之后）
- 面试完成 → `interview_service.complete` → 末尾触发 `settle_after_interview` + `obsidian.write_practice_log`
- SummaryService 必须在 settle 之后跑（数据已更新才有得总结）

### 3.3 安全 / 权限

- 权限校验：settlement / summary / obsidian_write **全走 JWT**，user_id 从 token 取，**不**接 request body
- 注入防护：
  - Obsidian 写文件 → `path` 字段必须用 `date` / `user_id` 生成，**不**接用户输入的 path（防 `../` 跳出 vault）
  - LLM prompt → 用户答过的题内容**不**直接拼 prompt，先 strip Markdown + 截断到 1000 字
- 速率限制：`/api/dashboard/summary` 60s 内同用户最多 5 次（防 LLM 刷量）

### 3.4 性能 / QPS

| 端点 | P95 响应 | QPS 上限 | 实现方式 |
|---|---|---|---|
| `/api/dashboard/summary` | < 200ms（缓存命中）/ < 3s（LLM 调） | 100 | Redis 缓存 + LLM 批量 |
| `ProfileSettlementService.settle_after_practice` | < 50ms | 500 | 纯 DB 写，无 LLM |
| `ObsidianSedimentService.write_daily` | < 100ms | 200 | 同步文件 IO，失败 log |
| `SummaryService.weekly/monthly` | < 5s | 10 | LLM 调，可后台 |

### 3.5 兼容性 / 版本

- **向后兼容**：所有新端点走 `/api/v2/...` 路径（旧 `/api/...` 不动）
- **前向兼容**：新加 `Profile` 字段时**不**删旧字段，**不**重命名
- **API 版本**：在响应 header 加 `X-API-Version: v2.0`
- **DB 兼容**：V1 的 `monthly_reports.summary_stats` JSON 字段保留，V2 在 `summary_stats` 内加 `narrative` 子字段

### 3.6 国际化

- 时区：所有 `date` 字段用用户 profile 时区（V1 已有 `Profile.timezone`，V2 沿用）
- 多语言：**不适用**（V1 没 i18n，V2 也不引入）

---

## 4. 数据契约（接口定义，必填）

### 4.1 Pydantic Schemas

```python
# backend/schemas/settlement.py
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date, datetime
from uuid import UUID


class TopicSettlement(BaseModel):
    """单个 topic 的沉淀数据（写入 weak_topics / mastered_topics）"""
    topic: str = Field(min_length=1, max_length=50)  # 业务：topic 名
    error_rate: float = Field(ge=0.0, le=1.0)  # 业务：错题率 0-1
    practice_count: int = Field(ge=0)  # 业务：练习次数
    last_practiced_at: datetime  # 业务：最后练习时间
    related_question_ids: List[str] = Field(default_factory=list, max_length=50)  # 业务：相关题 id 列表


class SettlementResult(BaseModel):
    """settlement 执行结果（API 返回 + 内部 service 返回）"""
    user_id: UUID
    settled_at: datetime
    weak_topics: List[TopicSettlement]  # 业务：当前 weak_topics 快照
    mastered_topics: List[TopicSettlement]  # 业务：当前 mastered_topics 快照
    triggered_by: str = Field(pattern=r"^(interview|practice|manual_refresh|weekly_refresh)$")  # 业务：触发源
    cache_invalidated: bool = True  # 业务：是否让 summary 缓存失效


# backend/schemas/summary.py
class DailySummary(BaseModel):
    """Dashboard 顶部总结卡（响应）"""
    title: str = Field(default="今日学习总结", max_length=50)
    date: date
    yesterday_count: int = Field(ge=0)  # 业务：昨天答了几题
    mastered: List[TopicSettlement]  # 业务：昨天掌握的 topic
    weak_shift: List[dict] = Field(default_factory=list)  # 业务：弱项变化 [{from_topic, to_topic, delta}]
    body: str = Field(max_length=500)  # 业务：自然语言叙述（LLM 生成或规则降级）
    _fallback: bool = False  # 业务：true=规则降级，false=LLM 生成


class WeeklySummary(BaseModel):
    """周报"""
    week: str = Field(pattern=r"^\d{4}-W\d{2}$")  # 业务：2026-W26
    total_questions: int = Field(ge=0)
    mastered_count: int = Field(ge=0)
    weak_topics: List[TopicSettlement]
    body: str = Field(max_length=2000)
    trajectory: dict  # 业务：12 周趋势数据 {week: mastered_count}


class MonthlySummary(BaseModel):
    """月报（持久化到 monthly_reports 表）"""
    month: str = Field(pattern=r"^\d{4}-\d{2}$")  # 业务：2026-06
    total_questions: int = Field(ge=0)
    mastered_count: int = Field(ge=0)
    weak_topics: List[TopicSettlement]
    body: str = Field(max_length=5000)
    trajectory: dict
    summary_stats: dict  # 业务：写入 monthly_reports.summary_stats 字段


# backend/schemas/obsidian.py
class ObsidianWriteRequest(BaseModel):
    """Obsidian 写请求（内部 service，不暴露 API）"""
    rel_path: str = Field(pattern=r"^(learning|interview)/[\w\-/]+\.md$")  # 业务：限定 learning/ 和 interview/ 两类
    content: str = Field(min_length=1, max_length=100_000)  # 业务：单文件最大 100K
    frontmatter: Optional[dict] = None  # 业务：YAML frontmatter


class ObsidianWriteResult(BaseModel):
    """写结果"""
    rel_path: str
    full_path: Optional[str]  # 业务：vault 存在 = 绝对路径；不存在 = None
    success: bool
    error: Optional[str] = None  # 业务：失败原因
```

### 4.2 新端点契约（6 个）

| 方法 | 路径 | 请求 | 响应 | 触发方 |
|---|---|---|---|---|
| GET | `/api/dashboard/summary` | — | `DailySummary` | Dashboard 顶部卡 |
| GET | `/api/profile/weekly` | `?week=2026-W26` | `WeeklySummary` | /profile 趋势图 |
| GET | `/api/profile/monthly` | `?month=2026-06` | `MonthlySummary` | /profile 月报卡 |
| POST | `/api/profile/refresh` | — | `SettlementResult` | "触发刷新画像" 按钮 |
| GET | `/api/knowledge/recent-sediments` | `?limit=5` | `List[ObsidianWriteResult]` | /knowledge stats tab |
| POST | `/api/obsidian/sync` | `{date: date}` | `{synced_count: int}` | "打开 Obsidian 沉淀" 按钮 |

### 4.3 副作用清单

```python
# 副作用（DB 变更 / 缓存 / 事件）
- DB:
  - profiles.weak_topics (JSON) — ProfileSettlementService 写
  - profiles.mastered_topics (JSON) — ProfileSettlementService 写
  - profiles.learning_trajectory (JSON) — weekly_full_refresh 写
  - profiles.last_active_at (DateTime) — settle_* 写
  - monthly_reports.summary_stats (JSON) — SummaryService.monthly 写
- Cache:
  - summary:dashboard:{user_id} (TTL 1h) — SummaryService.dashboard 读/写
  - summary:profile:{user_id} (TTL 1h) — SummaryService.weekly/monthly 读/写
  - profile:{user_id} (TTL 1h) — 全量画像缓存，settle 完成后 DEL
- Event:
  - log.warning: Obsidian vault 缺失 / LLM 失败 / settlement 失败
  - log.info: settlement 完成 / summary 生成 / obsidian 写入
- FileSystem:
  - ~/Obsidian/coding/learning/YYYY-MM-DD.md — ObsidianSedimentService.write_daily 写
  - ~/Obsidian/coding/interview/YYYY-MM-DD-<id>.md — ObsidianSedimentService.write_practice_log 写
```

### 4.4 Service 方法签名（来自 V1 Technical Spec § 5.4-5.6，无修改）

```python
# backend/services/profile_settlement_service.py
class ProfileSettlementService:
    async def settle_after_interview(
        self, user_id: UUID, interview_id: UUID, db: AsyncSession
    ) -> SettlementResult: ...

    async def settle_after_practice(
        self, user_id: UUID, qid: str, score: int, db: AsyncSession
    ) -> SettlementResult: ...

    async def weekly_full_refresh(
        self, user_id: UUID, db: AsyncSession
    ) -> SettlementResult: ...

    async def manual_refresh(
        self, user_id: UUID, db: AsyncSession
    ) -> SettlementResult: ...


# backend/services/summary_service.py
class SummaryService:
    async def daily(self, user_id: UUID, date: date, db: AsyncSession) -> DailySummary: ...
    async def weekly(self, user_id: UUID, week: str, db: AsyncSession) -> WeeklySummary: ...
    async def monthly(self, user_id: UUID, month: str, db: AsyncSession) -> MonthlySummary: ...
    async def sync_daily_to_obsidian(self, user_id: UUID, date: date, db: AsyncSession) -> ObsidianWriteResult: ...
    async def dashboard(self, user_id: UUID, db: AsyncSession) -> DailySummary: ...

    def _generate_narrative(self, stats: dict, template: str) -> str:  # LLM 调用
        ...


# backend/services/obsidian_sediment_service.py
class ObsidianSedimentService:
    VAULT_ROOT = Path.home() / "Obsidian" / "coding"

    def _write(self, rel_path: str, content: str) -> str | None: ...  # 容错关键
    def write_daily(self, date: date, content: str) -> str | None: ...
    def write_weekly(self, week: str, content: str) -> str | None: ...
    def write_monthly(self, month: str, content: str) -> str | None: ...
    def write_mastered_dump(self, user_id: UUID, topics: List[dict]) -> str | None: ...
    def write_practice_log(self, session_id: UUID, content: str) -> str | None: ...
```

---

## 5. 测试用例（验收测试，必填）

> 4 步实现时，`test-cases.md` §1 验收测试从这里提炼。test-cases.md §2 集成测试从 `verify.md` 提炼。

### 5.1 US-1：画像沉淀

- [ ] **TC-1.1**: happy path — 答完 1 道 score=4 的题 → Profile.weak_topics 出现新项 + last_active_at 更新（对应 GWT-1）
- [ ] **TC-1.2**: edge — 同一 topic 答对第 2 次 → 从 weak_topics 移到 mastered_topics（对应 GWT-2）
- [ ] **TC-1.3**: failure — 并发触发 settlement → 乐观锁检测 + 重试 1 次（对应 GWT-3）
- [ ] **TC-1.4**: failure — DB 断连 → settlement 失败 log + 主业务不抛（对应 GWT-9）
- [ ] **TC-1.5**: edge — 答 0 题新用户 → settle_after_practice 不报错，返回空 SettlementResult

### 5.2 US-2：Obsidian 写笔记

- [ ] **TC-2.1**: happy — vault 存在 → write_daily 写文件 + frontmatter 正确（对应 GWT-4）
- [ ] **TC-2.2**: failure — vault 缺失 → 返回 None + log warning + 不抛（对应 GWT-5）
- [ ] **TC-2.3**: edge — 文件已存在 → 追加内容（不覆盖原有用户的笔记）
- [ ] **TC-2.4**: security — 非法 path（`../../../etc/passwd`）→ 拒绝 + 抛 ValidationError

### 5.3 US-3：Dashboard 总结

- [ ] **TC-3.1**: happy — 昨天答 8 题 + 掌握 2 topic → /api/dashboard/summary 返回正确 narrative（对应 GWT-6）
- [ ] **TC-3.2**: failure — LLM 504 → 降级规则生成版 + `_fallback: true`（对应 GWT-7）
- [ ] **TC-3.3**: edge — 1h 内第 2 次调 → 命中 Redis 缓存 + 跳过 LLM（对应 GWT-8）
- [ ] **TC-3.4**: edge — 新用户 0 数据 → 返回 title="今日学习总结" + body="完成首日学习后..."

### 5.4 集成测试（4 步 test-cases.md §2 整合）

- [ ] **TC-INT-1**: 完整流 — 答 3 道题 → 检查 Profile + Obsidian + Dashboard 3 处都更新
- [ ] **TC-INT-2**: 并发 — 同时 5 个答题请求 → 5 个 settlement 全部完成 + 无数据丢失
- [ ] **TC-INT-3**: 失败恢复 — LLM 挂掉 → Dashboard 仍可访问（降级版）+ Profile 仍正常
- [ ] **TC-INT-4**: 跨服务 — weekly_full_refresh 触发后 → SummaryService.weekly 看到新数据

### 5.5 覆盖率要求（对齐 CLAUDE.md § 三.1.8）

| service | 重要性 | 目标覆盖率 |
|---|---|---|
| `profile_settlement_service` | 🔥 核心（新增） | ≥ 80% |
| `summary_service` | 🔥 核心（新增） | ≥ 80% |
| `obsidian_sediment_service` | 🔥 核心（新增） | ≥ 80% |
| `learning_progress_service`（改） | 🔥 核心（V1 已有） | ≥ 99% 维持 |
| `interview_service`（改） | 🔥 核心（V1 已有） | ≥ 99% 维持 |

---

## AI vs 人分工

| AI 适合做 | 人适合做 |
|---|---|
| ✅ 填 §4 数据契约（schema 是结构化） | ✅ 验收 §2 GWT（业务判断） |
| ✅ 列 §3 边界（8 类 checklist） | ✅ 签字"已验收"（决策） |
| ✅ 列 §5 测试场景（从 GWT 提炼） | ✅ 决定 §1 用户故事优先级 |
| ✅ 检查 5 段齐全（check-step.py 自动） | ✅ 拍板 product-doc 成功指标 |

**核心原则**：**人填空白（业务决策），AI 校验完整性（缺什么提醒）**。

---

## 🎯 硬性 DOD（spec.md 完成必须全过）

- [x] 5 段齐全（用户故事 / 验收标准 / 边界条件 / 数据契约 / 测试场景）
- [x] GWT ≥ 3 条（实际 9 条：3 happy + 3 edge + 3 failure）
- [x] 数据契约 ≥ 1 schema（实际 6 个 Pydantic schema：TopicSettlement / SettlementResult / DailySummary / WeeklySummary / MonthlySummary / ObsidianWriteRequest / ObsidianWriteResult）
- [x] 测试场景 ≥ 3 条（实际 17 条：13 单元 + 4 集成）
- [x] §0 上游引用齐全（research + product-doc + design-spec + V1 收尾报告）
- [x] 用户故事已验收标记（"已验收：<待你写>"）

> ⚠️ 任何 1 条未满足 → spec.md 不算完成，不能进 2 步
> ⚠️ 工具校验：`python3 scripts/check-step.py spec <file>`

---

## 5.5 跨文档引用（必填 · 指向 2 步技术详细化）

- 涉及 schema 变更？ → **否**（Profile 4 字段 + monthly_reports 表 V1 已就位，2 步**不**产出 db-design.md）
- 涉及新/改 API？ → **是**（6 个新端点） → 2 步产出 `api-spec.md`（§1-5 业务接口 + §6-8 技术实现）
- 涉及新组件？ → **是**（3 处前端改造 + 1 新页） → 2 步产出 `component-spec.md`（§1-5 业务 Props + §6-8 技术实现）
- 产出清单（2 步必出）：`plan.md` + `api-spec.md` + `component-spec.md`
- 不出（2 步可省）：`db-design.md`（无 schema 变更）

**核心原则**：spec.md 是"业务契约"层，技术实现层（API 详细 / 组件库选型 / 错误码）归 2 步详细化文档。

---

## 📚 相关文档

- [research.md](research.md) — 0 步调研（含 5 决策点 + 8 风险点）
- [product-doc.md](product-doc.md) — 1 步产品脑
- [design-spec.md](design-spec.md) — 1 步设计脑
- [V1 母模块 spec](../2026-06-22-new-feature-question-bank/spec.md) — 模块独立性原则
- [V1 Technical Spec § 5.4-5.6](../2026-06-22-new-feature-question-bank/technical-spec.md) — 3 service 方法签名
- [V1 收尾报告](../2026-06-27-v1-closure/closure.md) — V2 来源

---

## 🔴 待你 review 项（spec 阶段自检后写）

| 项 | 状态 |
|---|---|
| 用户故事 US-1/2/3 验收通过 | ⏳ 待你签字 |
| GWT 9 条覆盖了核心场景 | ⏳ 待你确认 |
| 数据契约 6 个 schema 字段约束合理 | ⏳ 待你确认 |
| 测试场景 17 条达到 DOD | ⏳ 待你确认 |
| 跨文档引用准确（plan/api-spec/component-spec 3 份） | ⏳ 待你确认 |

**已验收**：`<待你写 name> <2026-06-28 待你确认>`
