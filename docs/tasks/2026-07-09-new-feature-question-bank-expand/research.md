---
title: 调研报告 · 新功能：题库扩量 + 多维分类
date: 2026-07-09
status: v1
tags: [research, 0步, 新功能, 题库, 扩量, 分类]
related:
  - V1 母模块设计 [`../2026-06-22-new-feature-question-bank/`](../2026-06-22-new-feature-question-bank/)
  - V2 沉淀层 [`../2026-06-28-new-feature-v2-smart-sediment/`](../2026-06-28-new-feature-v2-smart-sediment/)
  - `docs/issues.md` — 全局议題追踪
---

# 🔍 调研报告 · 新功能：V3 题库扩量 + 多维分类

> 日期：2026-07-09 · 调研人：Claude (MiniMax-M3)
> 路径模式: full-7（涉及 schema + service + API + UI + seed_data，走完整 7 步）
> 用户决策（已拍板）：合成 1 调研 / 解除 seed_data 冻结 / 分类 A+B+C / 扩量 200 道

---

## 1. 任务理解（必填 · 用户已确认）

- **用户原话**: "学习复习的功能 是不是有些缺失？ 同步下来的题目 50道太少了 而且没有明确的分类 调研下相关功能"
- **AI 复述**: 扩展学习复习模块的题库（**50 → 200 道**），并引入**多维分类体系**：A 面试方向（系统设计/算法/网络/前端/后端中间件）+ B 技术栈（Python/Go/Redis/K8s）+ C 公司轮次（字节二面/阿里三面）。让用户能按方向筛题、按技术栈定位、按公司轮次针对性练习。
- **涉及模块**:
  - `learn`（学习复习 — 主战场）
  - `seed_data/*.json`（冻结区已解除）
  - `seed_service.py`（导入逻辑）
  - `question_bank_service.py`（查询逻辑）
  - `Question` 模型（不动字段，利用现有 QuestionTag 系统标签机制）
  - `frontend/pages/learn/` + `/review/`（加标签筛选 UI）
  - `core/database.py:_MIGRATIONS`（不动 — 不加新列）
- **估时**: ~10-14h
  - 200 题 JSON 写作 + followup 树：4-6h
  - seed_service 加 QuestionTag 系统标签预填：1h
  - question_bank_service 多维筛选 API：1-2h
  - learn.py API 加 tag filter：0.5h
  - 前端 /learn + /review 加标签筛选 UI：2-3h
  - 测试 + 文档：1-2h

---

## 2. 现状扫描（必填 · ≥ 3 文件）

### 2.1 相关文件

| 文件 | 当前状态 | V3 改动 |
|---|---|---|
| `backend/seed_data/agent_core.json` | 20 题，topic=agent_architecture | 🆕 扩到 ~40 题，保留旧题不动 |
| `backend/seed_data/rag_tech.json` | 15 题，topic=rag | 🆕 扩到 ~30 题 |
| `backend/seed_data/langgraph.json` | 10 题（含 3 langchain） | 🆕 扩到 ~25 题 |
| `backend/seed_data/java_backend.json` | 5 题，topic=java | 🆕 扩到 ~15 题 |
| `backend/seed_data/system_design.json` | ❌ 不存在 | 🆕 新建 ~25 题（topic=system_design） |
| `backend/seed_data/algorithms.json` | ❌ 不存在 | 🆕 新建 ~25 题（topic=algorithms） |
| `backend/seed_data/network.json` | ❌ 不存在 | 🆕 新建 ~20 题（topic=network） |
| `backend/seed_data/frontend.json` | ❌ 不存在 | 🆕 新建 ~20 题（topic=frontend） |
| `backend/services/seed_service.py` | 96 行，按 SEED_FILES 4 个遍历 | 🆕 扩 SEED_FILES 8 个 + 增 QuestionTag 预填逻辑 |
| `backend/services/question_bank_service.py` | V1 已实装 | 🆕 增 `list_by_tags` / `count_by_direction` 多维查询 |
| `backend/api/learn.py` | 已有 `/api/learn/tags` CRUD | 🆕 增 `/api/learn/questions?tags=a,b,c` 多标签筛 |
| `backend/models/__init__.py:Question` | 字段：topic/sub_topic/difficulty/round | ❌ **不动**（V1 D3 (b) 保留） |
| `backend/models/__init__.py:QuestionTag` | ✅ 系统标签机制已就位（is_system=True） | 🆕 seed_service 预填 A/B/C 三维系统标签 |
| `backend/models/__init__.py:QuestionTagMap` | ✅ 多对多表已建 | 🆕 seed_service 预填 ~600 条 map 行（200 题 × 3 类） |
| `frontend/pages/learn/index.tsx` | 答题入口 | 🆕 加"按标签筛选"组件 |
| `frontend/pages/review/index.tsx` | 复习入口 | 🆕 加"按标签筛选"组件 |
| `frontend/components/learn/` | 目录存在 | 🆕 加 `TagFilter` 共享组件 |
| `docs/api/README.md` | V2 补了 6 端点 | 🆕 V3 加多标签筛选 API 索引 |

### 2.2 相关议題（来自 `docs/issues.md`）

- **议题 A**（LangGraph StateGraph 未用）— 与 V3 无关
- **议题 B**（interview.py 803 行）— 与 V3 无关
- **议题 C**（语音架构 3 套并存）— 与 V3 无关
- **议题 D**（跨模块推荐）— 间接相关：V3 加多维标签后，recommendations_service 可利用 QuestionTag 做更精准推荐（V3 后续可扩展）
- **议题 E-F** — 与 V3 无关
- **Bug 9**（SM-2 测试与签名不一致）— 2026-06-25 已修 ✅
- **债务 1-8** — 与 V3 无关

**无沉积议題阻塞 V3**。

### 2.3 最近相关改动（git log -10）

```
f3d4bbd feat(verify): V2.4 L5 staging 通过 — AI 自动跑全 6 端点 + 4 页面
5cda20b feat(api): news API 补 trigger/daily + trigger/weekly + history
6be85dc feat(api): 补 GET /api/interviews round= 筛选参数（V1 🟡 #10）
e875d25 feat(ui): EmptyState 共享组件 + 4 种 SVG 占位插画
d517a4d feat(ui): 抽 GlassCard + StatCard 共享组件
2478260 fix(api): 422 / 4xx 错误响应统一 spec §3.4 格式（L4 改进 #3）
80c8f81 fix(api): V2 6 端点 slowapi 限流 + 统一错误格式
fc49243 feat(review): V2 L4 review 报告
e009891 fix(retro): 标改进项 #7 完成（antd 装好）
9631d2d fix(ui): 装 antd 6.5 + icons + recharts + 16 V2 测试
```

**关键观察**：
- ✅ 最近 10 commit 没有动 seed_data — V3 接管无冲突
- ✅ V2 收尾 + 错误格式统一已落地（2478260 + 80c8f81），基础设施扎实
- ✅ 共享组件（EmptyState / GlassCard / StatCard）已抽，V3 UI 可直接复用

### 2.4 现有 50 题分布（已扫）

| topic | 题数 | sub_topic 数 | 占比 |
|---|---|---|---|
| `agent_architecture` | 20 | 20（每题唯一） | 40% |
| `rag` | 15 | 14 | 30% |
| `langgraph` (+ `langchain` 3) | 10 | 9 | 20% |
| `java` | 5 | 4 | 10% |
| **合计** | **50** | **47**（高度分散） | 100% |

**difficulty 分布**：2(2) / 3(24) / 4(18) / 5(6) — 极端档过少

**round 分布**：round1(28) / round2(22) — 只有 2 个值

**结论**：题目**有分类**但**偏科严重**（90% AI 向） + **sub_topic 太细碎**（47 个，几乎每题唯一）+ **difficulty 极端档缺** + **round 只有 2 档**。

### 2.5 类似参考（找 1-2 个）

- **参考 A: `backend/services/seed_service.py:seed_questions`** — 已有的 JSON → DB 导入逻辑，按 `SEED_FILES` 列表遍历每题 INSERT。V3 沿用此模式：扩 SEED_FILES 列表 + 每题导入完多写 `QuestionTag` + `QuestionTagMap` 两行。
- **参考 B: `backend/api/learn.py:402-442`** — `/api/learn/tags` CRUD + `/api/learn/questions/{qid}/tags/{tag_id}` 增删 — QuestionTag API 已就位。V3 只需增 `/api/learn/questions?tags=tag1,tag2,tag3` 多标签筛选（GET）。

### 2.6 关键基础设施发现 ✅

`backend/models/__init__.py:303-335` `QuestionTag` 表已有完整**系统标签机制**：
```python
class QuestionTag(Base):
    """is_system=True = 系统预设（如 "高频"/"字节考过"），user_id=NULL"""
    name = Column(String(64), nullable=False)
    is_system = Column(Boolean, nullable=False, default=False)
    user_id_key = Column(String(64), Computed("COALESCE(user_id, '__system__')", persisted=True), ...)
    __table_args__ = (UniqueConstraint("user_id_key", "name", name="uniq_qt_userid_key_name"),)
```

**完美对位 A+B+C 三维标签需求**：
- A 维度（面试方向）= QuestionTag 系统标签，如 `system_design` / `algorithm` / `network`
- B 维度（技术栈）= QuestionTag 系统标签，如 `python` / `go` / `redis` / `k8s`
- C 维度（公司轮次）= QuestionTag 系统标签，如 `bytedance-r2` / `ali-r3` / `tencent-r1`

**结论**：V3 不需要加 Question 模型字段、不需要加 QuestionTag 表，只需在 seed_service 导入题目时**预填 QuestionTag 系统标签 + QuestionTagMap 关联**即可。

---

## 3. 依赖发现（必填 · ≥ 3 影响点）

### 3.1 改这些文件会影响

| 文件 | 影响 | 风险 |
|---|---|---|
| `backend/seed_data/*.json` (4 旧 + 4 新) | seed_service 重新导入 → 现有 50 题 ID 不变，新题 ID 续号 | 🟡 |
| `backend/services/seed_service.py:SEED_FILES` | 新增 4 个文件 + QuestionTag 预填逻辑 | 🟢（单元测试已覆盖） |
| `backend/services/question_bank_service.py` | 增 `list_by_tags(user_id, tags, ...)` 方法 | 🟢（V1 已 99% 覆盖） |
| `backend/api/learn.py:GET /api/learn/questions` | 增 `?tags=tag1,tag2,tag3` Query 参数 | 🟢 |
| `frontend/pages/learn/index.tsx` + `/review/index.tsx` | 加 TagFilter 组件 | 🟢（V2 已有 16 UI 测试经验） |

### 3.2 需要先改的

- **无 schema 变更**：Question 模型字段不动（V1 D3 (b) 保留），QuestionTag 表已存在
- **无 Alembic 迁移**：`_MIGRATIONS` 不用加
- **无新依赖**：antd 已在 V2 装好（commit 9631d2d），tag 筛选 UI 复用 V2 Tag 组件

### 3.3 调用方清单（改之前必查）

- `api/learn.py:list_questions`（line 78）— 已支持 `topic` / `difficulty` filter，加 `tags` 参数不破坏兼容
- `api/interview.py:start_interview`（V1）— 面试选题逻辑可能也要按 tags 筛（影响：V3 后续可扩展，本期不动）
- `api/recommendations.py`（V1）— 推荐 service 可用 QuestionTag 做更精准推荐（影响：V3 后续可扩展）
- `frontend/pages/learn/index.tsx` — 题目列表渲染需读 tag 字段（QuestionTagMap JOIN）
- `frontend/pages/interview/setup.tsx` — 面试选题 UI 可选展示题目 tag（影响：V3 后续）

---

## 4. 风险评估（必填 · ≥ 3 条带等级）

| # | 风险 | 等级 | 缓解 |
|---|---|---|---|
| 1 | 200 题写作工作量超估（followup_tree 复杂） | 🔴 | followup_tree 简化策略：每题 0-2 个追问（V1 是 2-4 个），写入工具化（半自动生成模板） |
| 2 | QuestionTag 系统标签与现有用户标签 name 冲突 | 🟡 | seed_service 启动检查 + 加 `sys_` 前缀（如 `sys_bytedance_r2`）防冲突 |
| 3 | 新 200 题 ID 与旧 50 题 ID 重复 | 🟡 | ID 命名规范：`{topic_short}{3位序号}`，如 `sys_001` / `algo_005` / `java_012` |
| 4 | 前端多标签筛选 UI 性能（> 200 题 + 多 tag） | 🟡 | 服务端预聚合索引（`idx_qtm_tag_question` 已建）+ 前端防抖 300ms |
| 5 | seed_service 改动影响现有 50 题导入 | 🟢 | 现有 50 题 ID 保留，QuestionTag 只给新题预填，旧题不入 tag |
| 6 | 多维标签语义模糊（A/B/C 边界不清） | 🟡 | 在 spec.md 定义明确的 tag 命名空间 + 示例 5 个标签 |
| 7 | V3 改动与 V2 沉淀层冲突（沉淀 trigger 依赖题目结构） | 🟢 | V2 沉淀层 trigger 走 Question 模型字段，V3 不动字段即无冲突 |
| 8 | 估时偏差 > 50%（200 题写作是密集脑力活） | 🟡 | 拆 4 PR（每方向 50 题），每 PR 可独立 commit |

**风险等级合计**：🔴 1 / 🟡 5 / 🟢 2

---

## 5. 输出建议（必填）

### 5.1 推荐路径（按 6 步流程 + 7 步 DOD）

```
0 调研（本文件）✅
    ↓ 用户拍板"调研通过"
1 规格（spec.md + product-doc.md + design-spec.md）     — 2h
    ↓
2 计划（plan.md + api-spec.md + component-spec.md）      — 1.5h
    ↓
3 拆分（tasks.md · 30-40 原子任务）                     — 1h
    ↓
4 实现（TDD · 4 PR · V3.1 system_design + V3.2 algorithms + V3.3 network + V3.4 frontend）  — 8-10h
    ↓
5 验证（verify.md · L1-L5 全层 gate）                  — 1.5h
    ↓
6 复盘（retro.md + 更新 CLAUDE.md + memory）             — 1h

总估时：15-17h
```

### 5.2 关键决策点（≥ 1 · 必填 4 个待你拍板）

> ✅ 已拍决策（8 个 · 全部锁定）：
> - 用户首轮 4 决策：合成 1 调研 / 解除冻结 / A+B+C 三维 / 扩量 200 道
> - 第二轮 4 决策（2026-07-09 拍板）：
>   - **决策 A** = **A1**（扩 topic/sub_topic + QuestionTag 系统标签 — A+B 用 topic/sub_topic，C 用 tag）
>   - **决策 B** = **B2**（保留 V1 详细 followup_tree，每题 2-4 个追问）
>   - **决策 C** = **C1**（/learn + /review 都加 TagFilter UI）
>   - **决策 D** = **D2**（4 个 PR 按新方向拆：V3.1 system_design / V3.2 algorithms / V3.3 network / V3.4 frontend）

### 决策影响下的估时修正（B2 + G3 + I1 翻倍 → 总估时上调）

| 项 | 估时 | 备注 |
|---|---|---|
| 200 题 JSON + 400-800 追问（B2 详细） | **8-12h** | 比 B1 翻倍，每题 5-10 min |
| seed_service 加 QuestionTag 系统标签预填 | 1h | |
| question_bank_service 多维筛选 API | 1-2h | |
| learn.py API 加 tag filter Query 参数 | 0.5h | |
| 前端 /learn + /review TagFilter UI（C1） | 2-3h | |
| **🔥 学习计划补全**（G3） | **2-4h** | 建 `/plan` 页 + Nav 入口 + dashboard 进度卡（用户已点名痛点） |
| **精选题单 Collections**（G3） | **3-5h** | 新建 `QuestionCollection` 模型 + API + UI + 题单-题目多对多 |
| **每日一题 Daily Challenge**（G3） | **2-3h** | dashboard 顶部固定推送 1 题 + 用户完成追踪 |
| 测试 + 文档 + 复盘 | 1.5-2h | |
| **总计** | **21-32h** | G3 扩 7-12h，比 V3 主线 14-20h 增 50% |

### 5.3 元信息

- 是否需要外部评审: **否**（内部功能 + 已有 V1/V2 沉淀层经验）
- 是否涉及 schema 变更: **否**（Question 字段不动，利用现有 QuestionTag 表）
- 是否涉及 seed_data: **是**（已解除冻结，4 旧扩量 + 4 新建）
- 是否需要 AB 测试: **否**（无对照组需求）
- 是否需要用户确认: **是**（决策 A/B/C/D 4 个待拍板 + 7 步流程每步签字）

---

## 6. 自检清单（AI 调研完必过）

- [x] 任务理解段已写且用户复述对（**等你最终确认**）
- [x] 现状扫描覆盖 ≥ 3 个相关文件（实际 17 个文件已列）
- [x] 依赖发现列出 ≥ 3 个影响点（实际 5 个影响点 + 3 个调用方 + 0 个 schema 变更）
- [x] 风险评估 ≥ 3 条带等级（实际 8 条：🔴 1 / 🟡 5 / 🟢 2）
- [x] 输出建议给完整 7 步路径
- [x] 关键决策点 ≥ 1（实际 4 个新待拍 + 4 个已拍）
- [x] 已读 `docs/issues.md`（议题 A-F + Bug 9 + 债务 1-8 全过）
- [x] 已跑 `git log -10` + `git status`（working tree clean，10 commit 都已落地）

---

## 📎 证据清单

- `backend/seed_data/{agent_core,rag_tech,langgraph,java_backend}.json` — 50 题分布（topic 5 / sub_topic 47 / difficulty 4 / round 2）
- `backend/services/seed_service.py:15-20` — `SEED_FILES` 4 个映射
- `backend/services/seed_service.py:38-58` — 现有导入逻辑（V3 沿用）
- `backend/models/__init__.py:131-146` — Question 模型字段（topic/sub_topic/difficulty/round 4 字段，**不动**）
- `backend/models/__init__.py:303-335` — QuestionTag 表系统标签机制（✅ 已就位，V3 直接预填）
- `backend/models/__init__.py:338-349` — QuestionTagMap 多对多表（✅ 已建）
- `backend/api/learn.py:78-91` — `list_questions` 已支持 topic/difficulty filter
- `backend/api/learn.py:402-442` — `/api/learn/tags` CRUD + `/api/learn/questions/{qid}/tags/{tag_id}` 增删
- `frontend/pages/learn/[index.tsx,qid.tsx,index.test.tsx]` — 答题入口 + 单测
- `frontend/pages/review/[index.tsx,index.test.tsx]` — 复习入口 + 单测
- `frontend/components/learn/` — 学习复习共享组件目录（V3 加 TagFilter）
- `docs/issues.md` — 全局议題（无相关阻塞）
- git log 10 个 commit — V2 收尾 + 错误格式统一 + antd 安装已落地

---

## 7. 立即行动（等用户确认后）

### 必读
1. **复述对不对**？任务理解稿等你最终确认
2. **决策 A/B/C/D 4 个新待拍项**等你拍板（schema 策略 / followup 复杂度 / UI 同步 / PR 拆分）
3. **是否冻结解除 + 200 道 + A+B+C 拍板 OK**？若需调整请 push back

### 用户说"调研通过"后立即开 1 步：
1. 建 `docs/tasks/2026-07-09-new-feature-question-bank-expand/spec.md`（1 步技术脑，5 段齐全 + GWT + schema + 测试）
2. 建 `product-doc.md`（1 步产品脑，用户人群 + 价值 + MVP + 成功指标）
3. 建 `design-spec.md`（1 步设计脑，用户旅程 + 页面地图 + 线框 + 状态机）
4. 等用户 3 脑 review

### ⚠️ 关键提醒
- CLAUDE.md § 二 冻结区已通过本调研解除 — 实施时**只动 seed_data/*.json**，**不动其他冻结对象**（.venv / .env.local / livekit.yaml / MySQL 真实数据）
- 7 步流程**每步必须等你的明确指令**才能进下一步（CLAUDE.md § 一）

---

## 8. 给用户的简短提示

调研完成。建议下一步：
- 你说"V3 进" → 我建 spec/plan/tasks/api-spec/component-spec，进入 1 步
- 你有不同想法（比如"只做 V3.1 system_design 不做 V3.4 frontend"）→ 改调研结论再进
- 你想看更细节的某一块（比如 A1 vs A2 vs A3 的 schema 详细对比）→ 我加详细段
- 你想现在拍板决策 A/B/C/D → 我立刻进 1 步

---

## 9. 模块完整性 Gap 分析（V3+ 范围建议）

> 用户提问："这些功能够吗？这个模块是不是还需要别的功能呢？ + 对比 LeetCode / 学习计划" — 本节基于已扫现状（`question_bank_service` 440 行 / `learning_progress_service` 535 行 / `study_plan_service` 173 行 / `learn.py` API 完整 / 前端 3 页面 998 行 + `BookmarkCollection` 模型 + Nav 入口），对比主流刷题平台核心能力，列 V3 范围外**确实存在的功能 gap**。

### 9.0 🔴 学习计划半成品专项（关键遗漏 · 用户已点名）

**用户原话**："对比下是不是少了一些功能 如学习计划 如 LeetCode 一样"

**实际状况**：学习计划**不是缺，是半成品** — 后端**全有**，前端**0 暴露**。

| 维度 | 现状（已扫） | 评估 |
|---|---|---|
| 数据库表 | `StudyPlan` (`models/__init__.py:264-265`) — 含 `weekly_target` + `progress` JSON 字段 + `start_date/end_date/status/goal` | ✅ 完整 |
| Service | `study_plan_service.py` 173 行 — `list_plans / get_plan / create_plan / update_plan / delete_plan / get_plan_progress` | ✅ 完整 |
| Schemas | `CreateStudyPlanInput / UpdateStudyPlanInput / StudyPlan / StudyPlanProgressResponse` | ✅ 完整 |
| REST API | `learn.py:269/272/286/311/317` — `GET /plans / POST /plans / PATCH /plans/{id} / DELETE /plans/{id} / GET /plans/{id}/progress` | ✅ **完整 5 端点** |
| 前端页面 | ❌ **`/frontend/pages/` 无 `/plan` 目录** | ❌ 缺 |
| Nav 入口 | ❌ **Nav.tsx 不含"计划"**（实测只有"仪表盘/面试/学/复习/画像/知识库/信息流"） | ❌ 缺 |
| Dashboard 卡片 | ❌ dashboard.tsx 不展示当前 plan 进度 | ❌ 缺 |
| 前端调用 | ❌ **0 个 `fetch('/api/learn/plans')` 调用** | ❌ 缺 |

**结论**：跟 BookmarkCollection 同性质"半成品"，但学习计划**更严重** — 不是单功能缺，是**整页 + nav 入口 + dashboard 卡** 三处全缺。

**估时补全**：2-4h（建 `/pages/plan/index.tsx` 350 行 + Nav 加入口 + dashboard 加"当前计划进度"卡 + 4-5 个组件测试）

**优先级**：🔴 P1 头号 — 用户已经明确点名。

---

### 9.1 已实装能力清单（V1 + V2 + V2 沉淀层 · 不再补）

| 能力 | 实现位置 | 状态 |
|---|---|---|
| 题库查询（topic/difficulty/q/source/bookmarked/sort） | `question_bank_service.list_questions:55` | ✅ 完整 |
| 用户题 CRUD | `question_bank_service:256-301` | ✅ 完整 |
| Tag 系统（系统 + 用户） | `question_bank_service:315-381` + `/api/learn/tags` | ✅ 完整 |
| 用户题内联笔记 | `UserQuestionNote` + `upsert_user_note` | ✅ 完整 |
| SM-2 间隔重复算法 | `learning_progress_service.calculate_next_srs:52` | ✅ 完整 |
| QuestionProgress CRUD + review_queue (Redis 5min TTL) | `learning_progress_service:115-319` | ✅ 完整 |
| 面试同步（upsert_from_interview） | `learning_progress_service:258` | ✅ 完整（D5 决策） |
| 推荐（weak + new + learning 三路径） | `learning_progress_service.get_recommend:322` | ✅ 完整 |
| LearningSession（start/end/recent） | `learning_progress_service:405-456` | ✅ 完整 |
| 学习统计（total/accuracy/by_status/bookmarked/week_session_sec） | `learning_progress_service.get_learn_stats:464` | ✅ 完整 |
| StudyPlan CRUD + 进度聚合 | `study_plan_service` 全文 | ✅ 后端完整 |
| StudyPlan REST API（5 端点） | `learn.py:269/272/286/311/317` | ✅ 后端完整 |
| StudyPlan 前端页面 / Nav / Dashboard 卡 | ❌ 0 暴露 | 🟡 **半成品** |
| BookmarkCollection 模型 | `models/__init__.py:369-382` | 🟡 **半成品（API/UI 缺）** |
| V2 沉淀层（profile + summary + obsidian） | 3 service + 6 端点 | ✅ 完整 |
| V2 UI（ProfilePage + DailySummaryCard + RecentSedimentsCard） | `frontend/components/v2-settlement/` | ✅ 完整 |
| 前端 /learn 搜索/难度/收藏筛选 UI | `frontend/pages/learn/index.tsx:160-192` | ✅ UI 完整 |

### 9.2 真实存在的 Gap（P1 · V3+ 必做）

| # | Gap | 现状（实装了什么） | 缺什么 | 影响面 | 估时 |
|---|---|---|---|---|---|
| 1 | **题目搜索弱** | UI 有搜索框（`/learn/index.tsx:172`）+ 后端 `q` 参数走 `question_text.contains(q)` | MySQL LIKE %q% 无中文分词、无相关度排序、无高亮 | 用户搜"React Hooks"找不到含"useState"的题；中文搜词断字不准 | 2-3h（接 jieba / Whoosh） |
| 2 | **BookmarkCollection 没实装** | `BookmarkCollection` 表**已定义**（`models/__init__.py:369-382`，含 user_id/name/color/唯一约束），`QuestionProgress.collection_id` FK 引用 | **没 CRUD API**、**没前端 UI** | 收藏 50 题后无法分组管理（"前端面试题"+"高频题"等） | 2-3h（model 已建，纯增量） |
| 3 | **学习模式切换不显** | V1 设计文档提到"4 tab"（学/复习/收藏/计划），但**前端是分页面**（`/learn` `/review`），nav 切换 | 没有"我现在该做什么"引导，新用户决策疲劳 | 新用户进首页不知道从哪个 tab 开始 | 1-2h（仪表盘加"今日推荐模式"卡） |
| 4 | **题目难度自适配缺** | `Question.difficulty` 固定 2-5，答完不调整 | 不根据用户历史答对率动态调整；用户答错 5 次难度仍 3 | 错题一直练不会的题（挫败感） | 3-4h（`upsert_progress` 加自适应逻辑） |
| 5 | **学习时长统计维度单一** | `week_session_sec` 全聚合（`learning_progress_service:503`） | 没按 topic/difficulty 维度拆；没按日热力图 | 用户看不到"今天学了哪个 topic 多久" | 2-3h（增加按维度聚合 + 热力图） |
| 6 | **Streak 学习日历未可视化** | V2 ProfilePage 提到"连续 N 天"卡（设计稿） | 缺 GitHub-style 热力图 / 365 天日历 | 缺 Duolingo 风格的激励视觉 | 2-3h（前端 recharts CalendarHeatmap） |
| 7 | **题目导入（批量）缺** | `UserQuestion.create_user_question` 支持**手动单题** | 没 JSON/CSV/Anki .apkg 批量导入 | 用户已有题库（牛客/力扣导出）没法一次性进 | 3-5h（JSON/CSV 优先，Anki 留 V4） |
| 8 | **AI 学习提醒缺** | review_queue 推到 /review 页（用户主动看） | 没 push 通知 / 邮件 / Dashboard 提醒 | 用户 3 天没学习没人提醒（流失） | 2-3h（议題 D 跨模块推荐的一部分） |
| 9 | **🔥 学习计划半成品**（用户已点名） | 后端 5 端点全实装（`learn.py:269-326`），**前端 0 暴露**（`/plan` 页面/Nav 入口/Dashboard 卡全缺） | 整页 + nav 入口 + dashboard 卡 三处全缺 | 用户找不到学习计划入口（即使后端有 5 端点） | **2-4h**（建 `/plan` 页 + Nav + dashboard 卡） |
| 10 | **精选题单 / Collections（LeetCode 风格）** | `UserQuestion` 只支持手动单题 | 没官方/社区题单（如"算法入门 100 题"、"字节前端 50 题"） | 用户想跟着系统化题单刷，没入口 | 3-5h（新建 `QuestionCollection` 模型 + API + UI） |
| 11 | **每日一题 / Daily Challenge** | review_queue 按到期排，没"今日固定 1 题"概念 | 没每日固定推送 1 题（LeetCode 风格） | 用户每日打开无锚点，粘性低 | 2-3h（轮询 + 推送卡片到 dashboard） |
| 12 | **学习路径 / Learning Path** | 无 | 没"算法入门→进阶"系统化路径（如 LeetCode Explore Cards） | 新用户不知道按什么顺序刷 | 4-6h（路径设计 + UI + 进度联动） |
| 13 | **题解 / Editorial** | `answer_key_points` 字段是 JSON 列表，不是结构化题解 | 没"题目背景/思路/复杂度/参考代码"结构化题解 | 用户答错看不到完整解析 | 3-5h（新建 `QuestionEditorial` 表 + UI 折叠卡） |
| 14 | **题目反馈 / 纠错（用户举报）** | 无 | 用户没法举报错题 / answer_key_points 不准 | 50 → 200 题里如有错题用户被误导 | 1-2h（新建 `QuestionFeedback` 表 + admin 视图） |

**P1 总估时**：19-30h（含学习计划 2-4h + 精选题单 3-5h + 每日一题 2-3h + 学习路径 4-6h + 题解 3-5h + 题目反馈 1-2h）

### 9.3 真实存在的 Gap（P2 · V4+ 不紧急 · 与 §9.2 编号续接）

| # | Gap | 影响面 | 估时 |
|---|---|---|---|
| 15 | 题目讨论 / 评论（社交） | 用户疑问没法讨论（用户感知低） | 4-6h（社交属性，复杂度高） |
| 16 | 题目速记卡片（Anki 风格） | 与 SM-2 重叠，UX 不同 | 4-6h |
| 17 | AI 智能出题（针对薄弱点） | 用户薄弱点没针对性题 | 6-10h（重 AI 资产） |
| 18 | 题目导出 PDF / 分享链接 | 用户想给朋友看 | 2-3h |
| 19 | 题单分享链接（公开题单） | 用户想分享自己整理的题单 | 2-3h |
| 20 | 学习小组 / 排行榜 | 社交激励 | 8-12h（重后端） |

> 注：原 §9.3 里的"题目反馈"已并入 §9.2 Gap 14（P1 头号之一），此处不再重复。

**P2 总估时**：26-40h

### 9.4 ❌ 不做（重资产 / 用户感知不到）

- 题目解题思路视频（视频制作重资产）
- 题目版本控制（用户感知不到）
- 多语言 i18n（V1 没做，V2 不引入）

### 9.5 关键洞察

#### 洞察 1：BookmarkCollection + 学习计划 都是"半成品"（关键发现）
- `BookmarkCollection` 表**已建**（V1 阶段定义）但**没 CRUD API / 前端 UI**
- **`StudyPlan` 也是半成品**：后端 5 端点 + service + schemas **全实装**，但**前端 0 暴露**（`/plan` 页面 / Nav 入口 / Dashboard 卡 全缺）
- **学习计划更严重** — 用户已经明确点名（§9.0），不是单功能缺，是整页 + 入口 + dashboard 三处全缺
- 这是典型的"V1 阶段开了口子没填完"，ROI 最高（纯增量 / 用户感知强）

#### 洞察 2：V3 范围恰好不踩 P1 gap，但学习计划是例外（用户已点名）
- V3 已拍板范围（200 题 + A+B+C + UI 暴露）**确实解决用户提出的"题少 + 没分类"主诉**
- 但**学习计划是用户明确提到的痛点**（§9.0 用户原话："对比下是不是少了一些功能 如学习计划"），且只缺前端（2-4h）
- **决策 G**（§9.10）：G2 / G3 把学习计划纳入 V3 是最稳的扩 scope 方式

#### 洞察 3：P1 是"做完 V3 后用户才会发现"的次级痛点
- V3 → 用户用 1 周后会发现："搜不到题"（Gap 1）"收藏夹分组"（Gap 2）"难度太死"（Gap 4）
- V3.5/4.0 → 单独开调研，每个 gap 一份 research.md

#### 洞察 4：领先能力 = 核心竞争力（§9.8 对比）
- **SM-2 间隔重复**（#15）+ **Obsidian 自动写笔记**（#25）+ **LLM 摘要**（#25）= LeetCode/Anki/Duolingo 都没的差异化
- V3 + 后续 gap 推进时，**这 3 项领先能力应该作为核心宣传点**（"自动沉淀到你的 Obsidian 知识库"）

#### 洞察 5：补半成品 ROI 最高
- 5 个半成品（学习计划 / 题解 / 进度可视化 / 收藏夹 / 搜索）+ 1 个用户已点名（学习计划）= **总估时 12-22h**
- 比"扩量 + 加分类"（V3 主线 14-20h）工作量还小
- **建议**：V3 推进后立刻做"补半成品"专项，每个半成品 1-2h 都能见效

### 9.6 V3 vs V3+ 推荐路径

| | V3（已拍板） | V3.5（建议 · P1 子集） | V4+（P2） |
|---|---|---|---|
| 范围 | 200 题 + A+B+C + UI | 1-2 个 P1 gap（如 Gap 2 收藏夹 + Gap 4 难度自适配） | 全部 P2 |
| 估时 | 14-20h | 4-6h | 25-39h |
| 优先级 | 🔴 用户已痛 | 🟡 用 V3 后会痛 | 🟢 不紧急 |
| 调研方式 | 已写（本文档） | 每 gap 单独开调研 | 整批开 |

### 9.7 决策点（新待拍）

| # | 决策点 | 选项 |
|---|---|---|
| **E** | **V3+ 是否并入 V3？** | E1 V3 保持现状（推荐，最稳）<br>E2 V3 + Gap 2（BookmarkCollection，最快补半成品）<br>E3 V3 + Gap 2 + Gap 4（收藏夹 + 难度自适配，扩 V3 范围 5-7h） |
| **F** | **V3.5 第一批 gap 是哪 2 个？** | 选项 A：Gap 1（搜索）+ Gap 2（收藏夹）— 用户感知最强<br>选项 B：Gap 2 + Gap 4（收藏夹 + 难度）— 半成品 + 自适应<br>选项 C：Gap 6 + Gap 5（Streak + 时长）— 激励 + 统计 |

---

### 9.8 LeetCode / 主流刷题平台核心能力对比矩阵（25 项）

> 用户提问："如 LeetCode 一样" — 本节把 LeetCode + 牛客 + Anki + Duolingo 的核心能力列全，与本项目现状一一对照，标出**领先 / 持平 / 半成品 / 缺失**四档。

| # | 能力 | LeetCode | 牛客 | Anki | Duolingo | 本项目 | 档位 |
|---|---|---|---|---|---|---|---|
| 1 | 题目分类（难度 + 标签） | ✅ | ✅ | ⚠️ | ✅ | ✅ topic/sub_topic/difficulty/round | **持平** |
| 2 | 公司题库（按公司分类） | ✅ | ✅ | ❌ | ❌ | 🟡 V3 C 维度准备做 | **持平（V3 补）** |
| 3 | 精选题单 Collections（官方/社区） | ✅ | ✅ | ⚠️ | ✅ | ❌ Gap 10 | **缺失** |
| 4 | 学习路径 Learning Path（系统化） | ✅ | ⚠️ | ⚠️ | ✅ | ❌ Gap 12 | **缺失** |
| 5 | 每日一题 Daily Challenge | ✅ | ✅ | ❌ | ✅ | ❌ Gap 11 | **缺失** |
| 6 | **学习计划 Study Plan** | ✅ | ✅ | ⚠️ | ✅ | 🟡 **后端完整 / 前端 0 暴露** | **半成品**（用户已点名） |
| 7 | 模拟面试 Mock Interview | ✅ | ✅ | ❌ | ❌ | ✅ V1 interview 模块 | **持平** |
| 8 | 题目讨论 Discuss / 评论 | ✅ | ✅ | ⚠️ | ⚠️ | ❌ Gap 15 | **缺失** |
| 9 | 题解 Editorial（结构化解析） | ✅ | ✅ | ✅ | ⚠️ | ⚠️ `answer_key_points` 不是结构化题解 | **半成品**（Gap 13） |
| 10 | 进度条 / 完成度可视化 | ✅ | ✅ | ✅ | ✅ | 🟡 `get_plan_progress` 有 completion_rate 但 UI 没接 | **半成品**（学习计划 UI 自带） |
| 11 | 收藏夹 My List / 分组 | ✅ | ✅ | ✅ | ✅ | 🟡 BookmarkCollection 表已建 / API/UI 没做 | **半成品**（Gap 2） |
| 12 | 题目搜索（全文 + 标签 + 相关度） | ✅ | ✅ | ⚠️ | ⚠️ | 🟡 MySQL LIKE 无中文分词 | **半成品**（Gap 1） |
| 13 | 题目提交（多语言代码） | ✅ | ✅ | ❌ | ❌ | ⚠️ V1 答题是口语/文字，非编程题 | **持平（场景不同）** |
| 14 | 难度自适配（按历史正确率） | ⚠️ | ⚠️ | ⚠️ | ✅ | ❌ Gap 4 | **缺失** |
| 15 | **间隔重复 SRS（SM-2）** | ⚠️ | ❌ | ✅ | ❌ | ✅ **实装领先** | **🔥 领先** |
| 16 | 个人统计 + 学习时长 | ⚠️ | ⚠️ | ✅ | ✅ | ✅ V2 ProfilePage + Dashboard | **持平** |
| 17 | 排行榜 / 全站对比 | ✅ | ✅ | ❌ | ✅ | ❌ Gap 20 | **缺失** |
| 18 | 每周竞赛 Contest | ✅ | ✅ | ❌ | ❌ | ❌（重后端，不做） | **缺失（不做）** |
| 19 | 题单分享链接（公开） | ✅ | ✅ | ✅ | ⚠️ | ❌ Gap 19 | **缺失** |
| 20 | 多语言 i18n | ✅ | ✅ | ✅ | ✅ | ❌（V1 没做，不引入） | **缺失（不做）** |
| 21 | 答题语言选择 | ✅ | ✅ | ❌ | ❌ | ⚠️ 口语答题场景，不适用 | **持平（场景不同）** |
| 22 | 题目反馈 / 纠错（用户举报） | ✅ | ✅ | ⚠️ | ✅ | ❌ Gap 14 | **缺失** |
| 23 | 题目速记卡片 Anki 风格 | ❌ | ❌ | ✅ | ⚠️ | ⚠️ SM-2 是算法不是 UX | **持平** |
| 24 | AI 智能出题 | ❌ | ❌ | ❌ | ❌ | ❌ Gap 17 | **缺失（V4+）** |
| 25 | **Obsidian 自动写笔记 + LLM 摘要** | ❌ | ❌ | ❌ | ❌ | ✅ **V2 沉淀层实装** | **🔥 领先** |

#### 对比结论（25 项分布）

| 档位 | 数量 | 能力 |
|---|---|---|
| 🔥 领先 LeetCode 等 | **2 项** | SM-2 间隔重复（#15）/ Obsidian + LLM 沉淀（#25） |
| 持平 | **8 项** | #1 #2 #7 #13 #16 #21 #23 |
| 半成品 | **5 项** | #6 学习计划 / #9 题解 / #10 进度可视化 / #11 收藏夹分组 / #12 搜索 |
| 缺失（可做） | **7 项** | #3 精选题单 / #4 学习路径 / #5 每日一题 / #8 讨论 / #14 难度自适配 / #17 排行榜 / #19 题单分享 / #22 题目反馈 |
| 缺失（不做） | **2 项** | #18 每周竞赛（重后端）/ #20 i18n（V1 没做） |
| 缺失（V4+） | **1 项** | #24 AI 智能出题（重 AI 资产） |

#### 关键洞察

**领先能力**：本项目的 SM-2 间隔重复 + Obsidian 自动笔记 + LLM 摘要（#15 #25）是 LeetCode/Anki/Duolingo 都没有的差异化能力，**这是核心竞争力**。

**半成品 = 最大价值洼地**：5 个半成品（#6 #9 #10 #11 #12）都是"V1 阶段开了口子没填完"。补这些工作量小（每个 1-5h）但用户感知强（用户已点名学习计划 #6）。

**缺失 = 长期价值**：7 个可做缺失中，精选题单 #3 + 每日一题 #5 + 学习路径 #4 是 LeetCode 风格的**核心三件套**，加起来 9-14h 可一并做。

---

### 9.9 P1 8 个 Gap 重新整理（按用户感知优先级排序）

> 用户在第 9 节问："学习计划缺 + 如 LeetCode 一样" → 学习计划被提到 P1 头号。其他 gap 按用户感知强烈程度重排：

| 排序 | Gap | 现状（实装了什么） | 缺什么 | 用户感知 | 估时 |
|---|---|---|---|---|---|
| 🔴 P1.1 | **学习计划半成品**（用户点名） | 后端 5 端点全实装，前端 0 暴露 | 整页 + nav + dashboard 卡 | **极强** | 2-4h |
| 🔴 P1.2 | 精选题单 Collections（LeetCode 风格） | `UserQuestion` 只支持手动单题 | 官方/社区题单入口 | 强 | 3-5h |
| 🟡 P1.3 | 每日一题 Daily Challenge | 无 | dashboard 顶部固定推送 1 题 | 强（提升粘性） | 2-3h |
| 🟡 P1.4 | 学习路径 Learning Path（LeetCode Explore） | 无 | 系统化学习路径（如"算法入门→进阶"） | 中 | 4-6h |
| 🟡 P1.5 | 题解 Editorial（结构化） | `answer_key_points` JSON 列表 | 结构化题解（背景/思路/复杂度/参考代码） | 中 | 3-5h |
| 🟡 P1.6 | 题目搜索弱 | UI 有 + LIKE 实现 | 中文分词 + 相关度 + 高亮 | 中 | 2-3h |
| 🟡 P1.7 | BookmarkCollection 半成品 | 表已建 | CRUD API + UI | 中 | 2-3h |
| 🟡 P1.8 | 题目难度自适配 | difficulty 固定 | 按历史正确率动态调整 | 中 | 3-4h |
| 🟢 P1.9 | 学习时长维度单一 | `week_session_sec` 全聚合 | 按 topic/difficulty 拆 + 日历热力图 | 弱 | 2-3h |
| 🟢 P1.10 | Streak 学习日历 | V2 设计稿提到 | GitHub-style 热力图 | 弱 | 2-3h |
| 🟢 P1.11 | 题目导入（批量） | 手动单题 | JSON/CSV 批量导入 | 弱 | 3-5h |
| 🟢 P1.12 | AI 学习提醒 | review_queue 主动看 | push / Dashboard 提醒 | 弱 | 2-3h |
| 🟢 P1.13 | 题目反馈 / 纠错 | 无 | 举报 + admin 视图 | 弱 | 1-2h |
| 🟢 P1.14 | 学习模式切换不显 | 分页面 | Dashboard 引导卡 | 弱 | 1-2h |

**P1 总估时**：31-51h

---

### 9.10 决策点 G（学习计划半成品是否本期补 · 用户已点名）

| # | 决策点 | 选项 | 状态 |
|---|---|---|---|
| **G** | **学习计划半成品是否本期（V3）补全？** | **G1** V3 保持现状（推荐，最稳，14-20h）<br>**G2** V3 + 学习计划补全（+2-4h，最快补用户痛点）<br>**G3** V3 + 学习计划 + 精选题单 + 每日一题（+7-12h，扩 V3 范围最大） | ✅ **G3**（用户 2026-07-09 拍板） |
| **H** | ~~V3.5 第一批做哪 2 个 P1 gap？~~ | ~~H1-H4 选项~~ | ⏸ 跳过（已并入 G3） |
| **I** | **G3 三件套（学习计划 + 精选题单 + 每日一题）实施顺序** | **I1** 学习计划先（用户痛点）→ V3.1/V3.2 题库扩量时同步做精选题单 + 每日一题（推荐，4 PR 内嵌）<br>**I2** 精选题单先 → 学习计划次 → 每日一题最后<br>**I3** 三件套同步做（资源密集） | ✅ **I1**（AI 自决，按"用户痛点优先"） |

### G3 + I1 落地后的 V3 完整 PR 拆分（D2 + G3 + I1 综合）

```
V3.0 学习计划补全（2-4h）              ← 🔥 用户已点痛点，最先做
  - 建 /pages/plan/index.tsx（350 行）
  - Nav.tsx 加"计划"入口（位于"学"和"画像"之间）
  - dashboard.tsx 加"当前计划进度"卡
  - 4-5 组件测试

V3.1 system_design 25 题 + 精选题单 1.0（5-7h）
  - 新建 system_design.json + 25 题 + ~75 追问
  - 新建 QuestionCollection 模型 + API + UI
  - 建 /pages/collections/index.tsx
  - QuestionCollection + QuestionCollectionMap 多对多

V3.2 algorithms 25 题 + 每日一题（5-7h）
  - 新建 algorithms.json + 25 题 + ~75 追问
  - 新建 DailyChallenge 表 + API + UI
  - dashboard.tsx 顶部加 DailyChallengeCard
  - 用户完成追踪 + streak 联动

V3.3 network 20 题（3-4h）
  - 新建 network.json + 20 题 + ~60 追问

V3.4 frontend 20 题（3-4h）
  - 新建 frontend.json + 20 题 + ~60 追问

总计：18-26h（5 个 PR）
```

---

## 10. 更新后的调研总览（v4 版 · 最终）

| 维度 | 状态 |
|---|---|
| 0 调研（V3 主线） | ✅ 完成（§1-§8） |
| 0.5 调研（模块完整性 gap） | ✅ 完成（§9.1-§9.7） |
| 0.6 调研（LeetCode 对比 + 学习计划专项） | ✅ 完成（§9.0 + §9.8 + §9.9 + §9.10） |
| **V3 scope 扩（G3 + I1）** | ✅ 落地（5 PR，18-26h，含学习计划 + 精选题单 + 每日一题） |
| 用户决策 | 8 + 2 + 3 = **13 个**（G3 + I1 ✅ 已拍，H 跳过） |
| 待办 | 进 1 步 spec.md / product-doc.md / design-spec.md（三脑分工） |

---

## 11. 简短提示（v4 版 · 最终）

- 调研**完整结束**，V3 scope 锁定为 G3 + I1
- V3 = **5 PR / 18-26h**：V3.0 学习计划补全 → V3.1-V3.4 题库扩量（含精选题单 + 每日一题内嵌）
- **进 1 步**：建 spec.md（技术脑）+ product-doc.md（产品脑）+ design-spec.md（设计脑），三脑分工
- 1 步完成需要你 review 签字后进 2 步（plan.md + api-spec.md + component-spec.md）

---

## 12. 🔴 AI 推送模块 V3 集成（用户 2026-07-10 拍板）

> **背景**：用户指出 V3 调研遗漏 AI 推送模块（V1 阶段 4.2 已决定独立成模块）。本节调研 V1 现状 + V3 范围。
>
> **用户决策**（2026-07-10）：
> - 模块定位：**保留"学习复习"模块名 + 学/复习 1 个母模块下 2 个子页（V1 既有划分）**
> - AI 推送：纳入 V3 范围（A 极简 · 2-3h）

### 12.1 AI 推送模块 V1 现状（已扫）

| 维度 | 状态 | 评估 |
|---|---|---|
| **V1 规划文档** | ✅ `docs/tasks/2026-06-22-new-feature-ai-push/{spec,product-doc,design-spec}.md` 完整 | V1 阶段 4.2 已决定独立成模块（4 大模块之一） |
| **后端 `news_service`** | ✅ 已实装（`backend/services/news_service.py`） | 每日/每周/每月新闻推送 |
| **后端 `recommendations_service`** | ✅ 已实装（`backend/services/recommendations_service.py` 142 行） | 跨模块推荐（weak_spots → knowledge / interview_recs / stats_context） |
| **API `/api/analytics/recommendations`** | ✅ 已实装（`backend/api/analytics.py:236`） | 跨模块推荐 endpoint |
| **API `/api/learn/recommend`** | ✅ 已实装（`backend/api/learn.py:193`） | 学习推荐 endpoint |
| **前端 `/push` 页面** | ❌ **未建**（V1 设计稿完整但未实装） | 5+ 页面（总览/日报/周报/月报/信源/设置/收藏） |
| **前端 nav "AI 推送" 入口** | ❌ **未建** | — |
| **议題 D（跨模块推荐）** | 📋 沉积 30+ 天 | — |
| **议題 E（AI Agent 框架）** | 📋 与本任务相关但远期 | — |

### 12.2 V3 范围选项（用户已拍 A 极简）

| 选项 | 范围 | 估时 | 评估 |
|---|---|---|---|
| **A · 极简**（**已选**） | dashboard 加 1 个"今日 AI 推荐"卡（3-4 条） | **2-3h** | 调 V1 `/api/analytics/recommendations` 已实装 endpoint |
| B · 中等 | 建 `/push` 总览页 + nav 入口 | 4-6h | 复用 news_service + recommendations_service |
| C · 完整 | `/push` + `/push/daily` 详情 2 页 | 8-10h | 超预算 |
| D · 跨模块推荐增强 | V3 A+B+C 标签 + recommendations 增强 | 4-6h | 缺 AI 推送模块"家" |

**A 极简的取舍**：
- ✅ 后端零改动（V1 已实装）
- ✅ 满足用户原话"纳入 V3 范围（+4-6h）"
- ⚠️ AI 推送模块仍缺独立页（V1 沉积 30+ 天的议題 D 部分落地，留 V3.5/V4 解决）
- ⚠️ recommendations_service 当前用"topic"字段，**没用 V3 A+B+C 标签**（V3 后续可增强）

### 12.3 AI 推送在 V3.0 + V3.1-V3.4 + V3.x 的位置

| 阶段 | AI 推送相关改动 |
|---|---|
| V3.0 学习计划补全 | ❌ 不涉及 |
| V3.1 system_design + 精选题单 | ❌ 不涉及 |
| V3.2 algorithms + 每日一题 | ❌ 不涉及 |
| V3.3 / V3.4 network / frontend | ❌ 不涉及 |
| V3.x **dashboard 加 AI 推荐卡**（🆕） | ✅ **新增 V3.6 = 6 PR**（5 → 6 PR） |

### 12.4 关键决策（新拍 · 跟 G3/I1 同级）

| 决策 | 状态 |
|---|---|
| **决策 J** = A 极简（dashboard 推荐卡） | ✅ **用户 2026-07-10 拍板** |
| **决策 K** = 模块定位保留"学习复习"（V1 既有） | ✅ **用户 2026-07-10 拍板** |

### 12.5 V3 更新后的最终 scope（6 PR / 20-29h）

```
V3.0 学习计划补全（2-4h）                ← 🔥 用户痛点最先
V3.1 system_design 25 题 + 精选题单（5-7h）
V3.2 algorithms 25 题 + 每日一题（5-7h）
V3.3 network 20 题（3-4h）
V3.4 frontend 20 题（3-4h）
V3.5（新增）dashboard 加 AI 推荐卡（2-3h）  ← 🆕 J 决策
                                  ─────────
                                  20-29h（5 → 6 PR）
```

### 12.6 用户决策总览（v5 版 · 最终）

| 决策 | 选项 | 状态 |
|---|---|---|
| A | schema 策略 | ✅ A1 |
| B | followup 复杂度 | ✅ B2 |
| C | 前端 UI 同步 | ✅ C1 |
| D | PR 拆分 | ✅ D2 |
| G | V3+ 是否并入 | ✅ G3 |
| H | V3.5 第一批 gap | ⏸ 跳过 |
| I | LeetCode 三件套顺序 | ✅ I1 |
| **J** | **AI 推送 V3 子范围** | ✅ **A 极简**（2026-07-10） |
| **K** | **学习复习模块定位** | ✅ **保留 1 模块 + 2 子页**（2026-07-10） |

---

## 10. 更新后的调研总览

| 维度 | 状态 |
|---|---|
| 0 调研（V3 主线） | ✅ 完成（§1-§8） |
| 0.5 调研（模块完整性 gap） | ✅ 完成（§9） |
| 用户决策 | 8 + 2 = 10 个（含 §9.7 决策 E/F） |
| 待办 | 进 1 步 spec.md 前需拍 E/F |

---

## 11. 简短提示（更新版）

- 调研完成（V3 主线 + 模块完整性 gap 分析）
- V3 范围**够用**（4 决策已拍，§9.5 洞察 2）— 200 题 + A+B+C + UI 暴露 解决用户主诉
- **额外发现**：BookmarkCollection 是 V1 半成品（表已建 / API 没写 / UI 没做），V3+ 优先级最高
- P1 8 个 gap + P2 6 个 gap 已列（§9.2 §9.3），都是 V3 范围外
- 决策 E/F 待拍（§9.7）：是否扩 V3 / V3.5 优先做哪 2 个
- 你说"V3 进" → 立即写 spec.md
- 你说"E2 / E3" → 改 V3 scope 加 gap，再写 spec.md
- 你说"F = X" → 我把 V3.5 调研先准备着，但 V3 仍推进