---
title: Spec 规格 · V3 题库扩量 + 多维分类 + LeetCode 三件套
date: 2026-07-09
status: v1
tags: [spec, 1步, 技术脑, v3, 题库扩量, 多维分类, LeetCode三件套]
related:
  - [research.md](research.md) — 上游 0/0.5/0.6 调研（含 G3 + I1 决策）
  - [V1 母模块 spec](../2026-06-22-new-feature-question-bank/spec.md)
  - [V2 沉淀层 spec](../2026-06-28-new-feature-v2-smart-sediment/spec.md)
---

# Spec 规格：V3 题库扩量 + 多维分类 + LeetCode 三件套

> **一句话**：把"题库扩量 + 多维分类 + 学习计划补全 + 精选题单 + 每日一题"打包成 V3，5 PR / 18-26h，让用户从"答完题 = 自动沉淀"延伸到"系统化刷题 + 计划驱动 + 每日坚持"。
>
> **作者**：AI 主导（技术脑），用户已 review research.md 决策（G3 + I1 ✅）
>
> **下游**：tasks.md（第 3 步拆分）+ test-cases.md（第 4 步整合）+ verify.md（第 5 步）

---

## 0. 上游引用（必填）

- **调研报告**：[`docs/tasks/2026-07-09-new-feature-question-bank-expand/research.md`](research.md)
- **调研版本**：v4（2026-07-09，含 G3 + I1 决策）
- **V3 scope（G3 + I1 已拍）**：
  - G3 = V3 + 学习计划 + 精选题单 + 每日一题（用户 2026-07-09 拍板）
  - I1 = 学习计划先做（用户痛点优先），精选题单 + 每日一题嵌入 V3.1/V3.2 题库扩量
- **关键决策**（从 research 抄）：
  - 决策 A（schema 策略）= **A1** 扩 topic/sub_topic + QuestionTag 系统标签
  - 决策 B（followup 复杂度）= **B2** 保留 V1 详细 2-4 追问/题
  - 决策 C（前端 UI 同步）= **C1** /learn + /review TagFilter
  - 决策 D（PR 拆分）= **D2** 4 PR 按方向拆（+V3.0 学习计划 = 5 PR）
  - 决策 G（V3+ 是否并入）= **G3** V3 加 LeetCode 三件套
  - 决策 I（三件套顺序）= **I1** 学习计划先 → 精选题单 + 每日一题嵌入 V3.1/V3.2
- **关键风险**（从 research §4 + §9 抄，🔴 标）：
  - 🔴 200 题写作工作量大 + B2 详细追问 → 拆 5 PR 降风险
  - 🟡 BookmarkCollection 表已建但 API/UI 没做（V3 不动，V3.5 补）
  - 🟡 QuestionTag 系统标签与现有用户标签 name 冲突 → seed_service 启动检查 + `sys_` 前缀
  - 🟡 5 个 PR 顺序耦合 → V3.0 学习计划独立不依赖题库；V3.1-V3.4 可并行

---

## 1. 用户故事（产品意图，必填 · 4 个核心）

### US-1：题库扩量 + 多维分类（V3 主线 · A+B+C）

> 作为 **求职冲刺者**，我想要 **题库从 50 题扩到 200 题 + 按面试方向/技术栈/公司轮次筛选**，以便 **系统化刷题，不用再刷完一轮就空了**。

**验收对应**：见 §2 GWT-1 / GWT-2 / GWT-3

### US-2：学习计划补全（V3.0 · 用户已点痛点）

> 作为 **持续学习者**，我想要 **打开 nav 看到"计划"入口，能创建/跟踪/完成学习计划**，以便 **按计划刷题有节奏，不会三天打鱼两天晒网**。

**验收对应**：见 §2 GWT-4 / GWT-5

### US-3：精选题单 Collections（V3.1 · LeetCode 风格）

> 作为 **算法学习者**，我想要 **官方/社区精选题单（如"算法入门 100 题"、"字节前端 50 题"）能订阅能跟刷**，以便 **跟着系统化题单刷，不用自己整理**。

**验收对应**：见 §2 GWT-6 / GWT-7

### US-4：每日一题 Daily Challenge（V3.2 · 提升粘性）

> 作为 **碎片时间用户**，我想要 **每天打开 dashboard 看到 1 道固定推送的题**，以便 **有锚点地每天学 5 分钟，养成习惯**。

**验收对应**：见 §2 GWT-8 / GWT-9

### US-5：AI 智能推荐（V3.5 · 集成 AI 推送模块 · 用户 2026-07-10 拍 A 极简）

> 作为 **求职冲刺者**，我想要 **打开 dashboard 看到 AI 智能推荐 3-4 条**（基于我的薄弱点 + 跨模块数据），以便 **不需自己找，系统主动告诉我"该练什么 / 该补什么"**。

**验收对应**：见 §2 GWT-12 / GWT-13

---

## 2. 验收标准 / GWT（机器可验证，必填 · 11 条）

### 2.1 US-1 题库扩量 + 多维分类

- **GWT-1 (happy)**：Given 用户访问 `/learn?tags=sys_algorithm,redis`，When 调 `GET /api/learn/questions?tags=sys_algorithm,redis`，Then 返回的题目**同时**含 `algorithm` topic 或 `redis` 技术栈标签的 200 题（其中 system_design 25 + algorithms 25 + network 20 + frontend 20 + V1 50），并按关联度排序
- **GWT-2 (edge: 多对多映射)**：Given 一道算法题 `algo_005` 同时打 3 个系统标签（`sys_algorithm` + `sys_python` + `sys_bytedance_r2`），When 该题被 3 个标签筛选，Then **3 次都能命中**（QuestionTagMap 多对多验证）
- **GWT-3 (failure: 标签名拼错)**：Given 用户传 `tags=sys_algoritm`（少字母 h），When 调筛选 API，Then 返回**空列表 + 友好提示**（不返 500，不抛异常），HTTP 200

### 2.2 US-2 学习计划补全（V3.0）

- **GWT-4 (happy)**：Given 用户在 `/plan` 创建计划 `name="2 周算法冲刺" weekly_target=[{week_idx:1,target_count:10,target_topics:["algorithms"]}]`，When POST `/api/learn/plans` 成功，Then 计划出现在 `/plan` 列表 + Dashboard 顶部出现"当前计划进度"卡 + 进度条显示 0/10
- **GWT-5 (edge: 完成度聚合)**：Given 用户答完 5/10 道 algorithms 题，When 调 `GET /api/learn/plans/{id}/progress`，Then 返回 `{"total_target":10, "mastered":5, "completion_rate":0.5, "weak_topics_remaining":[]}` + Dashboard 卡进度条更新到 50%

### 2.3 US-3 精选题单 Collections（V3.1）

- **GWT-6 (happy)**：Given 题单 `algorithms_100` 含 25 题（V3.2 写满），When 用户 `POST /api/learn/collections/{id}/subscribe`，Then 用户的 `/collections` 列表出现该题单 + 显示 0/25 进度 + 题单详情页可开始刷题
- **GWT-7 (failure: 题单不存在)**：Given 用户 `subscribe collections_id="nonexistent"`，When POST 请求，Then 返 **404 + `{"error": {"code": "NOT_FOUND"}}`**（V2 L4 改进 #3 错误格式统一）

### 2.4 US-4 每日一题（V3.2）

- **GWT-8 (happy)**：Given 用户今天未完成每日一题，When 打开 `/dashboard`，Then **DailyChallengeCard** 渲染题目文本 + "开始答"按钮 + 完成状态显示"今日 1 题"
- **GWT-9 (edge: 跨天不变题)**：Given 用户 23:50 打开 dashboard 看到今日题 `q001`，When 0:10 第二天打开，Then 仍是 `q001`（每日一题按 UTC 0 点切换，不按用户操作时间）

### 2.5 US-5 AI 智能推荐（V3.5 · 集成 AI 推送模块 · A 极简）

- **GWT-12 (happy)**：Given 用户有 1+ 完成面试 + 答题数据，When 打开 `/dashboard`，Then **"今日 AI 推荐"玻璃卡**渲染 3-4 条推荐（来自 `/api/analytics/recommendations`，按 V1 `recommendations_service.get_recommendations` 逻辑），推荐标题含"[补] 系统设计 · 缓存一致性" / "[练] LRU 缓存" / "[读] 字节面试经验"等前缀
- **GWT-13 (failure: 无数据时降级)**：Given 新用户无面试 + 无答题数据，When 调 `/api/analytics/recommendations`，Then 返 `{"recommendations": [], "message": "Complete at least one interview for recommendations"}` + dashboard 推荐卡显示"完成 1 次面试后解锁 AI 推荐"占位文案（V1 analytics.py:251 已实装）

### 2.6 跨边界 GWT

- **GWT-10 (failure: 学习计划半成品回归保护)**：Given V3.0 学习计划补全改动 `/api/learn/plans` 前端 UI，When 后端 5 端点契约不变，Then 已有 V1 plan 调用方不受影响（接口兼容）
- **GWT-11 (failure: 标签筛选性能)**：Given 题库从 50 扩到 200 + QuestionTag 系统标签 ~50 个，When 多标签筛选（3 个），Then 响应 P95 < 200ms（走 `idx_qtm_tag_question` 覆盖索引）
- **GWT-14 (failure: AI 推荐接口超时降级)**：Given `/api/analytics/recommendations` 超时（>3s），When dashboard fetch 失败，Then 推荐卡**隐藏**（不显示骨架也不报错），其他 dashboard 卡正常显示（决策 7A 不阻塞）

---

## 3. 边界条件（防御性，必填）

### 3.1 空值 / 异常 / 并发（基础）

- **空值**：
  - 题库 200 题扩量后，新用户访问 `/learn` 默认显示所有 200 题（不报错）
  - `QuestionCollection.questions = []`（题单刚创建）→ 显示"题单为空，请联系管理员"
  - `DailyChallenge` 当日无题（数据库故障）→ 隐藏 DailyChallengeCard，不报错
- **异常**：
  - QuestionTag 系统标签名拼错 → 返空列表 + 友好提示（GWT-3）
  - QuestionTagMap 唯一约束冲突（重复打标签）→ 静默忽略，不抛异常
  - LLM/缓存失败 → V3 不依赖 LLM（与 V2 沉淀层独立），失败降级无需
  - seed_service 重跑（force=True）→ QuestionTag 系统标签幂等（重复预填不报错）
- **并发**：
  - 用户同时创建 2 个同名计划 → MySQL UNIQUE 约束触发，返 409
  - 用户同时订阅同一题单 2 次 → QuestionCollectionSubscribe 唯一约束，返 409

### 3.2 时序（顺序依赖）

- seed_service 导入题目 → 同时预填 QuestionTag 系统标签 → QuestionTagMap 关联（**不可分两步**）
- 用户答完题 → `learning_progress_service.upsert_progress` → V2 沉淀层触发 → V3 不修改这条链
- V3.0 学习计划补全**不依赖** V3.1-V3.4 题库扩量（独立 PR）
- V3.1 题单创建 → 题单-题目多对多 → 题单详情可刷题（顺序内嵌 V3.1）
- V3.2 每日一题后台任务 → dashboard 顶部推送（顺序内嵌 V3.2）

### 3.3 安全 / 权限

- 权限校验：所有 V3 新端点走 **JWT**（与 V1/V2 一致）
- 注入防护：
  - QuestionTag 系统标签名**只**从 seed_service 写，**不**接用户输入
  - QuestionCollection name 字段**限制 50 字符 + 转义**（防 XSS）
  - DailyChallenge 题目 ID**只**从 seed_service 选，**不**接用户传入
- 速率限制：复用 V2 沉淀层 slowapi 配置（`/api/learn/collections` 60s/用户 10 次）

### 3.4 性能 / QPS

| 端点 | P95 响应 | QPS 上限 | 实现方式 |
|---|---|---|---|
| `GET /api/learn/questions?tags=a,b,c` | < 200ms | 100 | `idx_qtm_tag_question` 覆盖索引 + Redis 缓存 |
| `GET /api/learn/plans/{id}/progress` | < 150ms | 200 | Redis 缓存 5min + 走 `idx_qp_user_status` |
| `GET /api/learn/collections` | < 100ms | 100 | 单表查询 + Redis 缓存 5min |
| `GET /api/learn/daily-challenge` | < 50ms | 500 | Redis 缓存到当日 0 点（TTL 到 23:59:59） |

### 3.5 兼容性 / 版本

- **向后兼容**：所有 V3 新端点走 `/api/learn/...` 路径（与 V1 同前缀），不破坏 V1 路由
- **前向兼容**：QuestionCollection / DailyChallenge 等新表**不删旧字段**
- **API 版本**：响应 header 仍加 `X-API-Version: v2.0`（V3 不引入 v3，与 V2 沉淀层保持）

### 3.6 国际化

- 时区：所有 `date` 字段用用户 profile 时区（V1 已有）
- 多语言：**不适用**（V1/V2/V3 都不引入）

---

## 4. 数据契约（接口定义，必填）

### 4.1 新增 Pydantic Schemas

```python
# backend/schemas/collection.py
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date as date_type, datetime
from uuid import UUID


class CollectionQuestionItem(BaseModel):
    """题单内单题简略信息"""
    question_id: str
    topic: str
    sub_topic: str
    difficulty: int
    position: int = Field(ge=0)  # 题单内顺序


class QuestionCollection(BaseModel):
    """精选题单"""
    id: str
    name: str = Field(min_length=1, max_length=50)  # 业务：题单名（如"算法入门 100 题"）
    description: Optional[str] = Field(default=None, max_length=500)
    cover_color: Optional[str] = Field(default=None, pattern=r"^#[0-9a-fA-F]{6}$")
    is_system: bool = True  # 业务：true=官方题单 / false=用户自建（V3 仅系统）
    question_count: int = Field(ge=0)
    created_at: datetime
    questions: Optional[List[CollectionQuestionItem]] = None  # 仅详情返回


class CollectionSubscribeResult(BaseModel):
    """题单订阅结果"""
    collection_id: str
    user_id: UUID
    subscribed_at: datetime
    progress: dict  # 业务：{done_count, total_count, completion_rate}


# backend/schemas/daily_challenge.py
class DailyChallengeQuestion(BaseModel):
    """每日一题卡片内容"""
    date: date_type
    question_id: str
    topic: str
    sub_topic: str
    difficulty: int
    question_text: str = Field(max_length=1000)
    estimated_minutes: int = Field(default=5, ge=1, le=30)


class DailyChallengeStatus(BaseModel):
    """每日一题状态"""
    date: date_type
    question: DailyChallengeQuestion
    completed: bool  # 业务：用户今天是否已完成
    streak_days: int = Field(default=0, ge=0)  # 业务：连续 N 天完成


# backend/schemas/study_plan.py（已有 · V3 仅前端补全）
class StudyPlanCreateRequest(BaseModel):
    """学习计划创建请求"""
    name: str = Field(min_length=1, max_length=50)
    description: Optional[str] = Field(default=None, max_length=500)
    goal: Optional[str] = Field(default=None, max_length=200)
    start_date: date_type
    end_date: date_type
    weekly_target: List[dict] = Field(default_factory=list, max_length=12)
    # weekly_target item: {"week_idx": int, "target_count": int, "target_topics": [str]}
```

### 4.2 新端点契约（V3 新增 · 复用 V1 /api/learn 前缀）

| 方法 | 路径 | 请求 | 响应 | 触发方 |
|---|---|---|---|---|
| GET | `/api/learn/collections` | `?limit=20&offset=0` | `List[QuestionCollection]` | /collections 题单页 |
| GET | `/api/learn/collections/{id}` | — | `QuestionCollection` | 题单详情页 |
| POST | `/api/learn/collections/{id}/subscribe` | — | `CollectionSubscribeResult` | "订阅题单"按钮 |
| DELETE | `/api/learn/collections/{id}/subscribe` | — | `{"deleted": true}` | "取消订阅"按钮 |
| GET | `/api/learn/daily-challenge` | `?date=2026-07-09` | `DailyChallengeStatus` | dashboard DailyChallengeCard |
| POST | `/api/learn/daily-challenge/complete` | `{date: date_type}` | `DailyChallengeStatus` | "今日完成"按钮 |

**复用 V1 /api/learn/plans* 端点**（5 端点已存在，前端 UI 补全 V3.0）：
- `GET /api/learn/plans` · `POST /api/learn/plans` · `PATCH /api/learn/plans/{id}` · `DELETE /api/learn/plans/{id}` · `GET /api/learn/plans/{id}/progress`

**复用 V1 /api/learn/questions?tags= 端点**（V3.0 增 tags 参数）：
- `GET /api/learn/questions?topic=...&difficulty=...&tags=sys_algorithm,sys_python&...` → 返回题目列表

### 4.3 副作用清单（V3 新增表 + Redis + 文件）

```python
# 副作用（DB 变更 / 缓存 / 事件）
- DB 新表:
  - question_collections (V3 新建) — id, name, description, cover_color, is_system, created_at
  - question_collection_maps (V3 新建) — collection_id, question_id, position (多对多)
  - collection_subscribes (V3 新建) — id, user_id, collection_id, subscribed_at, progress_json
  - daily_challenges (V3 新建) — date, question_id (unique), created_at
  - daily_challenge_completions (V3 新建) — user_id, date, completed_at (unique on user_id+date)
- DB 已有表新增 seed:
  - question_tags (V1 已建) — 新增 ~50 条系统标签（is_system=True）
  - question_tag_maps (V1 已建) — 新增 ~600 条关联（200 题 × 平均 3 标签）
  - seed_data/*.json (4 旧 + 4 新) — 200 题 + ~600 追问
- Cache:
  - daily_challenge:{date} (TTL 到 23:59:59) — DailyChallenge 题目缓存
  - collection_list:{filter_hash} (TTL 5min) — 题单列表缓存
- 迁移:
  - backend/core/database.py:_MIGRATIONS 增 5 张新表的 CREATE TABLE（如 Alembic 不可用）
```

### 4.4 Service 方法签名（新增）

```python
# backend/services/collection_service.py
class CollectionService:
    async def list_collections(
        self, db: AsyncSession, *, limit: int = 20, offset: int = 0
    ) -> list[QuestionCollection]: ...

    async def get_collection(
        self, db: AsyncSession, collection_id: str, user_id: Optional[str] = None
    ) -> Optional[QuestionCollection]: ...

    async def subscribe_collection(
        self, db: AsyncSession, user_id: str, collection_id: str
    ) -> CollectionSubscribeResult: ...

    async def unsubscribe_collection(
        self, db: AsyncSession, user_id: str, collection_id: str
    ) -> bool: ...


# backend/services/daily_challenge_service.py
class DailyChallengeService:
    async def get_today_challenge(
        self, db: AsyncSession, user_id: str, date: Optional[date_type] = None
    ) -> DailyChallengeStatus: ...

    async def complete_today_challenge(
        self, db: AsyncSession, user_id: str, date: Optional[date_type] = None
    ) -> DailyChallengeStatus: ...

    async def _pick_question_for_date(
        self, db: AsyncSession, date: date_type
    ) -> str: ...  # 选题策略：按 date hash % 总题数


# backend/services/seed_service.py (扩展 V3)
async def seed_question_tag_system_tags(db: AsyncSession):
    """V3.1 预填 50 条系统标签（按 A+B+C 三维）"""

async def seed_question_tag_maps(db: AsyncSession):
    """V3.1 预填 600 条 tag-question 关联（按 question topic/sub_topic 自动映射）"""
```

---

## 5. 测试用例（验收测试，必填 · 17+ 条）

### 5.1 US-1 题库扩量 + 多维分类

- [ ] **TC-1.1**: happy — seed 200 题后，`/api/learn/questions` 总数 = 200（GWT-1）
- [ ] **TC-1.2**: edge — 多标签筛选命中多对多（GWT-2）
- [ ] **TC-1.3**: failure — 标签名拼错返空 + 不 500（GWT-3）
- [ ] **TC-1.4**: edge — seed_service 重跑 force=True → QuestionTag 幂等不报错

### 5.2 US-2 学习计划补全（V3.0）

- [ ] **TC-2.1**: happy — 创建计划 + Dashboard 卡 + 进度条 0/10（GWT-4）
- [ ] **TC-2.2**: edge — 完成 5/10 题后 progress 聚合正确（GWT-5）
- [ ] **TC-2.3**: failure — 同名计划重复创建 → 409
- [ ] **TC-2.4**: failure — V3.0 改动不破坏 V1 plan 调用方（GWT-10）

### 5.3 US-3 精选题单 Collections（V3.1）

- [ ] **TC-3.1**: happy — 订阅题单 + 进度显示（GWT-6）
- [ ] **TC-3.2**: failure — 订阅不存在题单 → 404 + 错误格式统一（GWT-7）
- [ ] **TC-3.3**: failure — 重复订阅 → 409
- [ ] **TC-3.4**: edge — 题单题目顺序按 position 字段排

### 5.4 US-4 每日一题（V3.2）

- [ ] **TC-4.1**: happy — dashboard DailyChallengeCard 渲染（GWT-8）
- [ ] **TC-4.2**: edge — 跨天题目切换（GWT-9）
- [ ] **TC-4.3**: failure — 当日无题 → 隐藏卡片 + 不报错
- [ ] **TC-4.4**: edge — streak 计算正确（连续 7 天完成 = streak_days=7）

### 5.5 集成测试（4 步 test-cases.md §2 整合）

- [ ] **TC-INT-1**: 完整流 — 创建计划 → 答 5 题 → progress 50% → dashboard 卡更新
- [ ] **TC-INT-2**: 完整流 — 订阅题单 → 刷 5 题 → 取消订阅
- [ ] **TC-INT-3**: 完整流 — 完成每日一题 → streak + 1 → 第二天新题
- [ ] **TC-INT-4**: 并发 — 同时 3 个前端请求（标签筛选 + 题单列表 + 每日一题）→ 全 200
- [ ] **TC-INT-5**: 端到端 — V3.0 学习计划 UI + V3.1 题单 + V3.2 每日一题 一起跑通

### 5.6 覆盖率要求（对齐 CLAUDE.md § 三.1.8）

| service | 重要性 | 目标覆盖率 |
|---|---|---|
| `seed_service`（扩展） | 🔥 核心（新增 QuestionTag 预填） | ≥ 80% |
| `collection_service`（新增） | 🔥 核心 | ≥ 80% |
| `daily_challenge_service`（新增） | 🔥 核心 | ≥ 80% |
| `question_bank_service`（加 tags filter） | 🔥 核心（V1 已有） | ≥ 99% 维持 |
| `study_plan_service`（前端补全不需改 service） | 🔥 核心（V1 已有） | ≥ 99% 维持 |

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
- [x] GWT ≥ 3 条（实际 11 条：4 用户故事 × 2-3 GWT + 2 跨边界）
- [x] 数据契约 ≥ 1 schema（实际 7 个 Pydantic schema：CollectionQuestionItem / QuestionCollection / CollectionSubscribeResult / DailyChallengeQuestion / DailyChallengeStatus / StudyPlanCreateRequest）
- [x] 测试场景 ≥ 3 条（实际 17 条：13 单元 + 5 集成）
- [x] §0 上游引用齐全（research v4 + 6 决策 G3 + I1 已拍）
- [x] 用户故事已验收标记（**待你 review 签字**）

> ⚠️ 任何 1 条未满足 → spec.md 不算完成，不能进 2 步
> ⚠️ 工具校验：`python3 scripts/check-step.py spec <file>`

---

## 5.5 跨文档引用（必填 · 指向 2 步技术详细化）

- 涉及 schema 变更？ → **是**（5 张新表） → 2 步产出 `db-design.md`（V3 第一次需要 schema 详细化）
- 涉及新/改 API？ → **是**（6 个新端点 + 复用 V1 5 端点前端补全） → 2 步产出 `api-spec.md`
- 涉及新组件？ → **是**（3 个新页 + 2 个新组件） → 2 步产出 `component-spec.md`
- 产出清单（2 步必出）：`plan.md` + `db-design.md` + `api-spec.md` + `component-spec.md`

**核心原则**：spec.md 是"业务契约"层，技术实现层（DB 详细 / API 详细 / 组件库选型 / 错误码）归 2 步详细化文档。

---

## 📚 相关文档

- [research.md](research.md) — 0/0.5/0.6 调研（G3 + I1 已拍，V3 scope 锁定）
- [product-doc.md](product-doc.md) — 1 步产品脑（V3 MVP + 用户人群 + 成功指标）
- [design-spec.md](design-spec.md) — 1 步设计脑（/plan /collections /dashboard 3 页线框 + 状态机）
- [V1 母模块 spec](../2026-06-22-new-feature-question-bank/spec.md)
- [V2 沉淀层 spec](../2026-06-28-new-feature-v2-smart-sediment/spec.md)

---

## 🔴 待你 review 项（spec 阶段自检后写）

| 项 | 状态 |
|---|---|
| 4 个用户故事（US-1/2/3/4）验收通过 | ⏳ 待你签字 |
| 11 条 GWT 覆盖了核心场景 | ⏳ 待你确认 |
| 7 个 Pydantic schema 字段约束合理 | ⏳ 待你确认 |
| 17 条测试用例达到 DOD | ⏳ 待你确认 |
| 5 张新表 + 6 个新端点契约准确 | ⏳ 待你确认 |

**已验收**：`<待你写 name> <2026-07-09 待你确认>`
