# 目前缺陷与设计议题

> 记录已识别的设计缺陷、技术债务、待讨论议题。**这是动态文档** —— 遇到新发现随时加。
>
> 状态图例：📋 待讨论 · 🚧 进行中 · ✅ 已解决 · ❌ 不会做 · ⚠️ 已知限制
>
> **唯一主账**：任务 `tasks.md` / `retro.md` 或代码 `TODO` 中出现的长期遗留项，必须同步登记到本文；其他文件只能引用，不能成为第二份状态源。
>
> **最近清账**：2026-07-21 · 关闭动作按 [`issue-closure-template.md`](templates/issue-closure-template.md) 核验。
>
> **2026-07-22 决策更新**（同步自 [`research.md` § 八](tasks/2026-07-21-issues-audit/research.md#八用户决策清单不属调研产出需用户拍板)）：
> - ✅ **议题 A + E** 联合实施：service 真调 `graph.ainvoke` + `evaluate_agent` / `report_agent` 用 `with_structured_output`（不升级 LangGraph 框架）
> - 🟡 **议题 B** 默认按职责拆（lifecycle/runtime/query）· 待用户最终确认
> - ✅ **议题 C** 全力全双工（路径 2）：三路径全替换 + transcript+语音 UI + LiveKit built-in VAD
> - 🟡 **议题 D + F** 暂缓，与 🔴 组并行不冲突
> - 🔴 **2026-07-22 新增债务 9**：V4 AI 推送模块存在 **41 个测试空壳被 pytest 计为通过**（详见三、债务 9）· 用户原话「先改两个 P0」
> - 🟡 **2026-07-22 新增任务 · CI 失败自动修复**（[`tasks/2026-07-22-new-feature-ci-autofix/`](tasks/2026-07-22-new-feature-ci-autofix/research.md)）：v2 安全审查完成（research.md v2 + decisions.md 10/10 全拍 · CLAUDE.md § 6.10 4 道关全部对齐）· 进 1 步写 spec.md（10 Requirement）

---

## 决策更新（2026-07-22）

> 📌 **决策主账**（按任务独立 · CLAUDE.md § 6.9）：
> - 审计任务：[`docs/tasks/2026-07-21-issues-audit/decisions.md`](tasks/2026-07-21-issues-audit/decisions.md)（议题 A/B/C/D/F · 1-10/15-17）
> - V4 AI 推送：[`docs/tasks/2026-07-17-new-feature-ai-push/decisions.md`](tasks/2026-07-17-new-feature-ai-push/decisions.md)（V4 决策 1/2 = 原审计 13/14 · 已迁）
> - **CI 失败自动修复（2026-07-22 v2）**：[`docs/tasks/2026-07-22-new-feature-ci-autofix/decisions.md`](tasks/2026-07-22-new-feature-ci-autofix/decisions.md)（决策 1-10 全拍 = 方案 1 + Draft PR + 3 次/commt + job 白名单加固 + 外部 check + $20/月 + Action pin SHA + 双 job + fork 排除 + 日志净化 · 含安全审查 4 道关）
> - **pre-commit DOD checker 退出码（2026-07-23）**：[`docs/tasks/2026-07-23-bug-precommit-p0-gates/p0-1-dod-exit/decisions.md`](tasks/2026-07-23-bug-precommit-p0-gates/p0-1-dod-exit/decisions.md)（决策 1：方案 A · POSIX 显式 `output + rc` + 3 个回归场景 · `fix-mini` · ✅ 已完成 commit `d91fdef`+`ee6da13`+`9841c38`）
> - **pre-commit 环境 Gate（2026-07-23）**：[`docs/tasks/2026-07-23-bug-precommit-p0-gates/p0-2-environment-gate/decisions.md`](tasks/2026-07-23-bug-precommit-p0-gates/p0-2-environment-gate/decisions.md)（决策 1：风险范围感知的 fail closed + 最小健康探针 + 8 个回归场景 · `fix-mini` · ✅ 已完成 commit `e0c9995`）
> - **任务状态语义与传播链（2026-07-23）**：[`docs/tasks/2026-07-23-refactor-task-status-semantics/decisions.md`](tasks/2026-07-23-refactor-task-status-semantics/decisions.md)（决策 1：任务级三事实 + 阶段级验收 · `[x]` 仅表示 implemented · 删除裸 DONE · `refactor-6`）
> - **任务路径、阶段与条件产物契约（2026-07-23）**：[`docs/tasks/2026-07-23-refactor-task-artifact-contract/decisions.md`](tasks/2026-07-23-refactor-task-artifact-contract/decisions.md)（决策 1：最小 task.yaml + check-task.py · 测试证据多落点 · INDEX 校验 · `refactor-6`）
> - **CI Playwright 关键旅程 Smoke（2026-07-23）**：[`docs/tasks/2026-07-23-new-feature-ci-playwright-smoke/decisions.md`](tasks/2026-07-23-new-feature-ci-playwright-smoke/decisions.md)（决策 1：真实 MySQL/FastAPI/Next 核心面试生命周期 · 观察 20 次后再晋升 required · `full-6`）
> - **Required Checks / Branch Protection（2026-07-23）**：[`docs/tasks/2026-07-23-new-feature-required-checks/decisions.md`](tasks/2026-07-23-new-feature-required-checks/decisions.md)（决策 1：Repository ruleset + enforce admins + 启用前清理 + break-glass 契约 · `full-6`）
> - **CI auto-fix v4 修复范围与文档漂移（2026-07-23）**：[`docs/tasks/2026-07-23-bug-ci-autofix-safety-drift/decisions.md`](tasks/2026-07-23-bug-ci-autofix-safety-drift/decisions.md)（决策 1：v3 + 7 项 P0 残留 + 4 处文档漂移同步；不实施代码 · `refactor-6`）
> - **P1 测试基础架构 L1-L5 + 追溯 + Fixture（2026-07-23）**：[`docs/tasks/2026-07-23-refactor-test-foundation/decisions.md`](tasks/2026-07-23-refactor-test-foundation/decisions.md)（决策 1：L1-L5 Mock 边界 + Traceability Matrix + E2E Fixture 三位一体 · `refactor-6`）
> - **P1 测试治理与质量 xfail/AI 评估/a11y+性能（2026-07-23）**：[`docs/tasks/2026-07-23-refactor-test-governance-quality/decisions.md`](tasks/2026-07-23-refactor-test-governance-quality/decisions.md)（决策 1：xfail 静态 metadata + AI 离线 contract + a11y/perf 报告型 · `refactor-6`）
> - **P1 产品基础分层 L0-L3（2026-07-23）**：[`docs/tasks/2026-07-23-refactor-product-foundation/decisions.md`](tasks/2026-07-23-refactor-product-foundation/decisions.md)（决策 1：问题证据 baseline 字段 + 指标字典分层 + 埋点按层强制 · `refactor-6`）
> - **P1 验收与学习 L0-L3（2026-07-23）**：[`docs/tasks/2026-07-23-refactor-product-verification-learning/decisions.md`](tasks/2026-07-23-refactor-product-verification-learning/decisions.md)（决策 1：轻量用户验收 + Outcome Review 7/14/30 + 旅程追踪按 L0-L3 触发 · `refactor-6`）
> - **P2 治理清理 4 项合一（2026-07-23）**：[`docs/tasks/2026-07-23-refactor-p2-governance-cleanup/decisions.md`](tasks/2026-07-23-refactor-p2-governance-cleanup/decisions.md)（决策 1：skill 更新 + 文档 checker + frontmatter 升级 + 长期 §6.11 退役规则 · `refactor-6`）
> - **test_ci_workflow.py 旧断言（v39 · 2026-07-23）**：[`docs/tasks/2026-07-23-bug-ci-workflow-test-stale-assertion/decisions.md`](tasks/2026-07-23-bug-ci-workflow-test-stale-assertion/decisions.md)（决策 1：最小修复 · 单函数重命名 + 删 `@v6` 3 条 + 加 SHA pin 3 条 · `fix-mini` · ✅ 已完成 commit `d5c11e1`）
>
> 本节是简表镜像 · 详细记录请看对应 decisions.md

| # | 决策项 | 选择 | 状态 |
|---|---|---|---|
| 1 | 议题 C 语音架构 | ✅ 全力全双工 | ✅ 已决策 |
| 2 | 议题 B 拆分路径 | 🟡 按职责拆（默认） | 🟡 待最终确认 |
| 3 | 债务 4 Alembic | ⏸ 保留为未来迁移 | ⏸ 暂缓 |
| 4 | 债务 5 密码哈希 | ⏸ 接受 600K pbkdf2 | ⏸ 暂缓 |
| 5 | 同步 issues.md 偏差 | ✅ 是（5 处） | ✅ 已完成 |
| 6 | 启动 § 2 计划 | ⏸ 等用户指令 | ⏸ 待定 |
| 7 | 议题 C 实施范围 | ✅ 全部语音路径（Q1=2） | ✅ 已决策 |
| 8 | 议题 C UI 形态 | ✅ transcript+语音（Q2=2） | ✅ 已决策 |
| 9 | 议题 C VAD 策略 | ✅ LiveKit built-in（Q3=1） | ✅ 已决策 |
| 10 | 进 § 1 规格 | ✅ spec.md + design-spec.md + mockup | ✅ 已决策 |
| 11 | V4 假绿灯处置（债务 9） → [V4 决策 1](tasks/2026-07-17-new-feature-ai-push/decisions.md) | 🔴 **立即修** | 🔴 已决策（执行中） |
| 12 | 债务 3 数字偏差（29 → 41） → [V4 决策 2](tasks/2026-07-17-new-feature-ai-push/decisions.md) | 🔴 **同步修** | 🔴 已决策（执行中） |
| 13 | CI auto-fix 选方案 → [CI 决策 1](tasks/2026-07-22-new-feature-ci-autofix/decisions.md) | ✅ 方案 1（Claude Code Action + SHA 约束） | ✅ 已决策 |
| 14 | CI auto-fix commit 模式（v2 修订）→ [CI 决策 2](tasks/2026-07-22-new-feature-ci-autofix/decisions.md) | ✅ Draft PR（v2 · 修订自推原分支） | ✅ 已决策 |
| 15 | CI auto-fix 失败上限（v2 修订）→ [CI 决策 3](tasks/2026-07-22-new-feature-ci-autofix/decisions.md) | ✅ 3 次/commt（v2 · 修订自 2 次） | ✅ 已决策 |
| 16 | CI auto-fix job 白名单（v2 加固）→ [CI 决策 4](tasks/2026-07-22-new-feature-ci-autofix/decisions.md) | ✅ 含 backend 限 typecheck/coverage + backend service 必走 Draft PR | ✅ 已决策 |
| 17 | CI auto-fix 单测协同（v2 修订）→ [CI 决策 5](tasks/2026-07-22-new-feature-ci-autofix/decisions.md) | ✅ 外部 check（T33 + pytest 实际绿 · v2 修订自自我豁免） | ✅ 已决策 |
| 18 | CI auto-fix API 费用 → [CI 决策 6](tasks/2026-07-22-new-feature-ci-autofix/decisions.md) | ✅ $20/月 | ✅ 已决策 |
| 19 | 🆕 CI auto-fix Action pin SHA（v2 新增）→ [CI 决策 7](tasks/2026-07-22-new-feature-ci-autofix/decisions.md) | ✅ 完整 40 字符 SHA（非 @beta） | ✅ 已决策 |
| 20 | 🆕 CI auto-fix 双 job 权限分层（v2 新增）→ [CI 决策 8](tasks/2026-07-22-new-feature-ci-autofix/decisions.md) | ✅ diagnostic（read-only）+ apply-fix（env approval） | ✅ 已决策 |
| 21 | 🆕 CI auto-fix Fork PR 排除（v2 新增）→ [CI 决策 9](tasks/2026-07-22-new-feature-ci-autofix/decisions.md) | ✅ 不处理 fork PR | ✅ 已决策 |
| 22 | 🆕 CI auto-fix 日志净化（v2 新增）→ [CI 决策 10](tasks/2026-07-22-new-feature-ci-autofix/decisions.md) | ✅ 仅传 job 名 + 错误类型 + 截断字符串 | ✅ 已决策 |
| 23 | 🆕 pre-commit DOD checker 退出码 → [决策 1](tasks/2026-07-23-bug-precommit-p0-gates/p0-1-dod-exit/decisions.md) | ✅ 方案 A：显式 `output + rc` + 3 个回归场景 | ✅ 已完成（commit `d91fdef`+`ee6da13`+`9841c38` · 独立 verifier 4 维度 PASS） |
| 24 | 🆕 pre-commit 环境缺失/损坏 Gate → [决策 1](tasks/2026-07-23-bug-precommit-p0-gates/p0-2-environment-gate/decisions.md) | ✅ 风险范围感知的 fail closed + 8 个回归场景 | ✅ 已完成（commit `e0c9995` · 30/30 + 722/722 PASSED） |
| 25 | 🆕 任务状态语义与传播链 → [决策 1](tasks/2026-07-23-refactor-task-status-semantics/decisions.md) | ✅ task 三事实 + phase acceptance；移除裸 DONE | ✅ 已决策 · 待规格 |
| 26 | 🆕 任务路径、阶段与条件产物契约 → [决策 1](tasks/2026-07-23-refactor-task-artifact-contract/decisions.md) | ✅ 最小 task.yaml + check-task.py；测试证据多落点 | ✅ 自动决策 · 待规格 |
| 27 | 🆕 CI Playwright 关键旅程 Smoke → [决策 1](tasks/2026-07-23-new-feature-ci-playwright-smoke/decisions.md) | ✅ 真实核心面试生命周期；观察 20 次后再 required | ✅ 自动决策 · 待规格 |
| 28 | 🆕 Required Checks / Branch Protection → [决策 1](tasks/2026-07-23-new-feature-required-checks/decisions.md) | ✅ Repository ruleset + enforce admins + break-glass 契约 | ✅ 自动决策 · 待规格 |
| 29 | 🆕 CI auto-fix v4 修复范围与文档漂移 → [决策 1](tasks/2026-07-23-bug-ci-autofix-safety-drift/decisions.md) | ✅ v3 + 7 项 P0 残留 + 4 文档同步 | ✅ 自动决策 · 待实施授权 |
| 30 | 🆕 P1 测试基础架构 L1-L5 + 追溯 + Fixture → [决策 1](tasks/2026-07-23-refactor-test-foundation/decisions.md) | ✅ L1-L5 + Traceability + E2E Fixture 三位一体 | ✅ 自动决策 · 待规格 |
| 31 | 🆕 P1 测试治理与质量 xfail/AI 评估/a11y+性能 → [决策 1](tasks/2026-07-23-refactor-test-governance-quality/decisions.md) | ✅ xfail 静态 metadata + AI 离线 contract + a11y/perf 报告型 | ✅ 自动决策 · 待规格 |
| 32 | 🆕 P1 产品基础分层 L0-L3 → [决策 1](tasks/2026-07-23-refactor-product-foundation/decisions.md) | ✅ 问题证据 baseline 字段 + 指标字典分层 + 埋点按层强制 | ✅ 自动决策 · 待规格 |
| 33 | 🆕 P1 验收与学习 L0-L3 → [决策 1](tasks/2026-07-23-refactor-product-verification-learning/decisions.md) | ✅ 用户验收 + Outcome Review 7/14/30 + 旅程追踪按 L0-L3 触发 | ✅ 自动决策 · 待规格 |
| 34 | 🆕 P2 治理清理 4 项合一 → [决策 1](tasks/2026-07-23-refactor-p2-governance-cleanup/decisions.md) | ✅ skill 更新 + 文档 checker + frontmatter + 长期 §6.11 退役规则 | ✅ 自动决策 · 待规格 |
| 35 | 🆕 test_ci_workflow.py 旧断言（v39） → [决策 1](tasks/2026-07-23-bug-ci-workflow-test-stale-assertion/decisions.md) | ✅ 最小修复：单函数重命名 + SHA pin 3 断言 | ✅ 已完成（commit `d5c11e1` · 714/714 PASSED） |

---

## 一、设计议题（待深入讨论）

### 议题 A — 会话状态机：LangGraph StateGraph 写了但没用上

**状态**：✅ **2026-07-22 已决策**（与议题 E 联合实施）· 进 § 1 规格 · spec.md 已起草

**现状**：`backend/agents/interview_graph.py` 定义了完整的 StateGraph 编译产物，但 `backend/services/interview_service.py:80-150` 实际走的是**直接调用** `question_engine` / `followup_engine` / `evaluate_agent`，绕开了 graph 的状态转移逻辑。

**影响**：
- 失去了 LangGraph 的可视化 trace 能力
- 自定义状态字段（如 `state["questions_asked"]`）在 graph 之外手动维护，存在不一致风险
- 增加新节点（如人机协作、阶段性回顾）需要改 service 而不是改 graph

**可选路径**：
1. **保留现状**：service 是薄封装层，agent 是真正逻辑，graph 暂时是 dead code
2. **真用 graph**：service 改为 `graph.invoke(state)`，所有状态变更走图
3. **完全删 graph**：service 已经是 single source of truth，删 `interview_graph.py` 减少误导

**讨论时机**：状态：A. 状态机重构的代价与扩展性收益对比；B. 现有 50 道种子题 + 追问树是否能在 graph 里清晰表达

---

### 议题 B — `interview.py` 873 行的拆分

**状态**：🟡 **2026-07-22 默认决策**：按职责拆（lifecycle/runtime/query） · 待用户最终确认 · spec.md 已起草

**现状**：`backend/api/interview.py` 单文件 873 行，承担了 13 个端点（议题描述列了 8 个，漏算 5 个）：
- Lifecycle：POST / + POST /complete + POST /{id}/favorite + DELETE /{id}
- Runtime：POST /{id}/next-question + POST /records/{id}/answer + POST /voice/respond + POST /transcribe + POST /livekit-token
- Query：GET / + GET /recent + GET /{id} + GET /{id}/records
- Other：2 个内联 Pydantic 模型（VoiceRespondRequest / LiveKitTokenRequest）

`grep -rn "from api.interview import" backend/api/` 仅命中 main.py —— **无反向依赖，拆分零摩擦**。

**影响**：
- 改动一处容易影响别处
- 单测难以隔离
- 后续加新端点（如 round 切换、题目回看）会让文件更长

**可选路径**：
1. **按职责拆**：`interview_lifecycle.py`（start/complete）+ `interview_runtime.py`（next-q/answer）+ `interview_query.py`（list/records）
2. **CQRS 分离**：写操作（start/complete/answer）vs 读操作（list/records）分文件
3. **保留单文件 + 拆 router prefix**：技术上更轻，团队约定避免互相改

**讨论时机**：模块边界、团队协作模式

---

### 议题 C — 语音架构：3 套并存的最终形态

**状态**：✅ **2026-07-22 已决策**：全力全双工（路径 2）+ 全部语音路径替换（`/interview/room` + `/interview/setup` + `/interview.tsx`）+ transcript+语音 UI（上下分栏）+ LiveKit built-in VAD/turn-taking · spec.md 已起草

**现状**：
- `/interview.tsx` → `VoiceRoom.tsx`（旧 PTT + WebSocket）
- `/interview/setup.tsx` → `/interview/room.tsx` → `VoiceRecord.tsx`（新 PTT）
- `LiveKitVoice.tsx` 组件存在但**没有任何页面用**
- `voice/livekit_worker.py`（61 行）**从未被代码调用** —— 实际被 `_start_voice_worker` spawn 的是 `backend/voice/interview_room.py`（300+ 行），前者是 dead code
- `_start_voice_worker` 在 `start_interview` 时无条件启动 LiveKit worker，但前端 `/interview/room` 走 VoiceRecord（WebSocket ASR/TTS）**从不连 LiveKit 房间** → worker 永远 `wait_for_participant()` 阻塞直到 `/complete`
- `frontend/lib/livekit.ts` helper + `POST /api/interviews/livekit-token` 端点都是孤儿代码

**影响**：
- 维护 3 套组件的认知成本
- 不知道该往哪个方向投入
- `livekit-server` 一直在跑但没被消费

**可选路径**：
1. **文字 + PTT 收敛**：保留 `/interview` 和 `/interview/room` 两套，分别服务"打字用户"和"不想打字用户"
2. **全力上全双工**：废弃 PTT，`room.tsx` 改为 `LiveKitVoice`，等 LiveKit 调通
3. **Hybrid**：默认 PTT（已稳定），新用户在 onboarding 给一次"试试全双工"的选择

**讨论时机**：技术决策，需要明确"未来 6 个月用户主要用什么形态"

---

### 议题 D — 跨模块数据流：AI 推荐如何真正打通

**状态**：📋 待核验（已有后续模块实施，但尚未逐条对照本议题关闭条件）

**现状**：`recommendations_service.py` 主路径已真实集成 Obsidian + News（不再是占位）：
- L14 `from services.obsidian_service import obsidian` · L73 `obsidian.search(spot, limit=3)` 把 `name` / `path` 拼进 `title` / `link`
- L15 `from services.news_service import news_service` · L126 `news_service.get_code_stats(days=7)` 生成 stats 卡
- 但 L87-92 **fallback 仍是占位文案**（obsidian 召回为空时插入硬编码「补充学习「{weak_spots[0]}」」+「知识库中暂无相关笔记，建议添加」）
- `backend/api/analytics.py:236-281` 暴露独立 `/recommendations` 端点，**不调 `recommendations_service`**，自己写一套 blind_spot 计数逻辑（Counter → `{topic, label, frequency, priority}`）—— **两套并行实现并存**

**影响**：
- "AI 副脑"的差异化定位目前只体现在 dashboard 卡片上
- 用户感知不到"面试 → 知识库 → 日报"的联动价值

**可选路径**：
1. **基于关键词匹配**：把 `blind_spots` 关键词（如"记忆管理"）去 `~/Obsidian/coding/` 全文搜，返回 top-3 笔记
2. **基于 embedding**：`blind_spots` + 笔记标题/内容 embedding → 向量检索 → top-k
3. **基于知识图谱**：从 `blind_spots` 对应的 topic 出发，wikilink 遍历 1 跳，推荐相关笔记

**讨论时机**：差异化价值，需要先想清楚"用户能感知到的跨模块体验是什么"

---

### 议题 E — AI Agent 框架：现在的"假 LangGraph"要不要换

**状态**：✅ **2026-07-22 已决策**：与议题 A 联合实施 · `evaluate_agent` / `report_agent` 用 `with_structured_output` · 不升级 LangGraph 2.x / `create_agent` · spec.md 已起草

**现状**：
- `interview_graph.py` 编译了图但运行时绕开
- `followup_agent` / `evaluate_agent` / `report_agent` 都是**直接调 LLM**（langchain `ChatOpenAI.ainvoke`）
- 没有 multi-agent 协作、tool use 链、反思机制

**影响**：
- 未来要做"AI 自己出题 / 自动评估代码 / 模拟面试官间讨论"，需要更强的 agent 框架
- 当前 `evaluate_agent` 是一次性 LLM 调用，没有 RAG、没有反思、没有结构化输出校验（LLM JSON 解析靠正则 fallback）

**可选路径**：
1. **继续 LangGraph 1.x**：把现有的 graph 真用起来，加节点、加 tool、加 human-in-the-loop
2. **换 LangGraph 2.x / LangChain 1.3+ 的 create_agent API**：声明式、build-in 工具多
3. **引入 CrewAI / AutoGen**：多 agent 协作（一个出题、一个评估、一个出报告）

**讨论时机**：3-6 月后的扩展计划，MVP 阶段不必急

---

### 议题 F — 可观测性：零 trace / metrics / structured log

**状态**：📋 待核验（已有相关设计，尚未验证全链路 trace / metrics / error 聚合）

**现状**：
- 73 处 `logger.{info,error,warning,debug}` 调用，绝大多数仍走 stdlib 默认 Formatter（纯文本）
- T15-T19 commit `96566d8` 在 `backend/utils/logger.py` 落了脚手架：
  - `setup_logger()` JSON formatter（ts/level/trace_id/logger/msg/exc）· `DigestMetrics`（push_total/push_failed/fetch_failures/push_latency_ms）· 模块级 `digest_logger` / `digest_metrics` 实例
- **全代码库零调用方** —— grep `from utils.logger` / `digest_metrics.` / `digest_logger.` 全 backend 0 命中（"抽屉里的工具盒"）
- `request_id` / `X-Request` / `correlation_id` 全仓 0 命中（除 logger.py 自己定义外）
- trace_id 是**进程级单值**（模块全局 `_trace_id`），并发请求会互相覆盖 —— 即便接 middleware 也是 race condition，关闭前必修
- `RateLimitMiddleware` 类存在但未注册 · slowapi `app.state.limiter` 但未加 `SlowAPIMiddleware`
- `sentry-sdk` / `glitchtip` / `langfuse` / `opentelemetry-*` 全部 0 命中

**影响**：
- 上线后出问题只能靠用户报
- LLM 成本不可见（每次 evaluate 调几次？多少 token？）
- Agent 行为不可调试（某次面试追问为什么跑偏了？）

**可选路径**：
1. **轻量**：本地 `json_log` + Loki / Grafana 聚合
2. **中等**：OpenTelemetry SDK + Jaeger + Prometheus
3. **AI 专用**：Langfuse / Helicone（专门给 LLM 调用打 trace + 算成本）

**讨论时机**：上线前必须做，可以分阶段引入

---

## 二、已发现 bug（待修复）

当前无已登记且完成证据不足的 Bug。新 Bug 必须写明复现路径、影响、优先级和对应回归测试。

---

## 三、已识别的技术债务

### 债务 8 — `question_progress.user_id` 去掉 FK，应用层保证引用完整性 ⚠️ NEW

**位置**：`backend/models/__init__.py:QuestionProgress`

**背景**：Phase 1a 启用 HASH 分区 (按 user_id 散 16 partition)。MySQL 8 分区表不允许 FK（无论作为父表还是子表），所以从 `QuestionProgress.user_id` 移除了 FK 约束。

**影响**：
- 删除 user 时不会 cascade 清 question_progress 行 → 孤立行
- 当前没有 User.delete API，暂时不痛
- 但如果有 batch data fix / GDPR 删除需求，需要手动写清理逻辑

**建议**：建一个 `UserService.delete_user(user_id)` 方法，应用层清：
```sql
DELETE FROM question_progress WHERE user_id = ?;
DELETE FROM question_tags WHERE user_id = ?;
DELETE FROM user_questions WHERE user_id = ?;
-- ... 其他子表
```

**优先级**：低（上线前要写）

---

### 债务 9 — V4 AI 推送模块存在 41 个测试空壳被 pytest 计为通过 🔴 P0 NEW

**位置**：以下 5 个文件全部位于 V4（`docs/tasks/2026-07-17-new-feature-ai-push/`）模块

**审计来源**：[`KnockWise-测试真实性基线-2026-07-21.md`](~/Documents/Codex/2026-07-21/ai-agent-1-agent-agent-2/outputs/KnockWise-测试真实性基线-2026-07-21.md)（2026-07-21 Codex 双 agent 静态 AST 审计）· 本机 `find backend/tests -name "test_*.py" | wc -l` 递归实测 = **41**（与审计一致）

**背景**：commit `9251fd6` 提交时这些测试在 commit message 就被定义为 **"test stub"**（标题：`test+frontend: T20-T24 + T26 测试 stub + 5 核心组件`），但随后 `tasks.md` / `retro.md` / `milestones.md` 全部标为 ✅ DONE，形成"假绿灯"状态。

**空壳分布**（41 个空壳 + 0 真实测试）：

| 文件 | 测试数 | 全部空壳 | 备注 |
|---|---:|---:|---|
| `backend/tests/api/test_digest_api.py` | 16 | 16 | 15 个纯 `pass` + 1 个 `import + 注释 + pass` |
| `backend/tests/e2e/test_digest_push.py` | 4 | 4 | 全 `pass` |
| `backend/tests/services/test_digest_llm.py` | 4 | 4 | 全 `pass` |
| `backend/tests/services/test_digest_service_unit.py` | 12 | 12 | 全 `pass` + 与真实 Digest 测试**重复** |
| `backend/tests/services/test_rss_fetch.py` | 5 | 5 | 全 `pass` · 12 源 fixture 找不到 |
| **合计** | **41** | **41** | pytest 会全计为通过 |

**额外 3 个弱测试**（不在 41 个内，但建议复核）：
- `test_interview_filters.py::test_status_filter_is_applied` → 准备 Mock 但不调用接口，可认定为假绿灯
- `test_archive_service.py::test_logs_count_when_archived` → 只验"没崩"
- `test_cache.py::test_close_idempotent` → 用"不抛异常"表达幂等

**影响**：
- V4 模块的 "32 个 Tasks 全部完成" 声明不成立（tasks.md T20-T24 / T28-T31 全部 ✅ DONE 但实际无效）
- milestones.md V4 "全部完成" 是统计幻觉
- retro.md "49+ 测试类" 数字混淆（测试类 / 测试函数 / 空壳测试 混算）
- verify.md (`docs/tasks/2026-07-17-new-feature-ai-push/verify.md`) **不存在** · 验证阶段未真正完成
- 邮件真实集成在 retro.md 自己的改进项中仍写"待补"
- 后端当前无 pytest 运行环境（`backend/.venv` 不存在），无法现场验证修复效果

**修复路径**（建议按 § 4 步分批，每任务 1 commit）：
1. **T20 重写**：16 endpoint × happy + invalid + edge 用 `TestClient` + fixture 跑通（约 48 case）
2. **T21 拆分**：删除 `test_digest_service_unit.py` 12 个空壳（与真实测试重复），让 `test_digest_service.py` 12 case + `test_digest_composite_score.py` 23 + `test_digest_push_daily.py` 5 + `test_digest_select_top_n.py` 8 作为真实单测基线
3. **T22 重写**：4 个 LLM mock 测试用 `unittest.mock` 拦截 `ChatOpenAI.ainvoke` + 验证 prompt 含用户偏好 + scope 过滤词
4. **T23 重写**：5 个 RSS mock + 12 源 fixture（实际创建 `backend/tests/fixtures/rss/*.xml`）
5. **T24 重写**：4 个 E2E 用 `TestClient` 跑 `cron → DB → API → email` 全链路（可 mock email）
6. **T28 视觉测试**：创建 `frontend/tests/visual/digest.spec.ts`（spec § 6.7 verify-loop）
7. **T29 E2E**：5 个 Playwright scenario 实跑（已编写但未执行）
8. **T30 RSSHub**：创建 `scripts/deploy-rsshub.sh` + `docker-compose.yml` RSSHub service + `curl http://localhost:1200/juejin/tag/AI` 验证
9. **T31 metrics**：将 `backend/utils/logger.py` 内的 `DigestMetrics` 搬出到独立 `backend/utils/metrics.py` 并暴露接口

**验证手段**：
- 重建 `backend/.venv` 后 `pytest backend/tests --collect-only` 收集所有测试
- `pytest backend/tests/api/test_digest_api.py -v` 跑 16 endpoint 测试
- 跑完用 `pytest --tb=short --cov=backend/services/digest_service --cov-report=term-missing` 输出覆盖率

**优先级**：🔴 **P0（高优工程债务）**——直接影响 V4 模块的可信度与"完成度"声明

**2026-07-22 进展**：
- 紧急修复链反应：8/9 完成（T21/T22/T23/T24/T28/T30/T31 重写或创建）· T29 文件已实化待实跑
- T33 AST 空测试阻断器上线（`scripts/check_test_quality.py` + 24 回归测试 · 6 violations 实时阻断 exit 1）
- T34 三 Gate CI 上线（GitHub Actions quality/typecheck/build · 1 branch protection required policy 待配）
- pytest baseline **698 passed / 1 skipped / 4 xfailed / 0 failed** in 1.60s · 全覆盖行 61.55% / Digest 核心 85.61%
- 债务 9 的核心问题（41 个空壳）已基本清零 · **T20 6 violations 2026-07-22 收尾清零（docstring 占位字样已澄清 · 真断言保留 · T33 阻断器现 0 violations exit 0）**
- T20 实跑 `pytest tests/api/test_digest_api.py -q` = **16 passed** · 前端 Vitest **26 files / 210 tests** 全过
- 详见 [`docs/tasks/2026-07-21-issues-audit/baseline.md`](tasks/2026-07-21-issues-audit/baseline.md)（baseline 完整记录）

**2026-07-22 阶段五复核（最新状态 · 🚧 未关闭）**：

- 空测试治理已通过：44 files / 681 AST tests / 0 violations；后端 698 passed / 1 skipped / 4 xfailed；Digest coverage 85.61% / 82%。
- 但原修复路径 3（T22）未完成：`test_digest_llm.py` 不存在，Digest 路径没有 `ainvoke` 契约。
- 原修复路径 5（T24）未达到 E2E 边界：测试直接调用 service，并 Mock DB/ORM/偏好/RSS；Email 仍为 `NotImplementedError`。
- 原修复路径 7（T29）实跑结果为 5 failed / 0 passed；`/ai/today` 仍是 EmptyState，bookmarks/settings 缺 QueryClientProvider。
- 前端 Vitest 210 passed，但 typecheck 有 12 条 diagnostics，Next build 失败；后端优雅停机另发现 `asyncio` 未导入。
- 完整证据与 V5-01～V5-08 关闭条件见 [`verify.md`](tasks/2026-07-17-new-feature-ai-push/verify.md)。不得再以“8/9 已完成”解释为 Harness 项目闭环。

**修复工时估算（阶段五复核：未闭环）**：原估 ~10.5h；空测试治理已完成，但 V5-01～V5-08 仍需重新拆分估时与实施。

**关联决策**：decisions.md 决策 11 + 12 + 13（2026-07-22 新增）
**关联文档**：
- [`docs/tasks/2026-07-21-issues-audit/baseline.md`](tasks/2026-07-21-issues-audit/baseline.md)（2026-07-22 baseline · 698/1/4/0）
- [`docs/tasks/2026-07-17-new-feature-ai-push/tasks.md`](tasks/2026-07-17-new-feature-ai-push/tasks.md) § 9.1/§ 9.6/§ 9.7（双时间线对照 + T33/T34 实施证据）
- [`docs/tasks/2026-07-17-new-feature-ai-push/retro.md`](tasks/2026-07-17-new-feature-ai-push/retro.md)（标题"实施完成"仍待改为"阶段性实现，验证未完成"）
- [`docs/rules/milestones.md`](rules/milestones.md) V4 状态（"全部完成"应改"核心功能已实现，测试与交付验证修复中"）

---

### 债务 11 — pre-commit DOD checker 失败退出码被管道吞掉 🔴 P0 NEW

**位置**：`scripts/pre-commit:105-107`

**背景**：DOD 校验使用 `if ! python3 scripts/check-step.py ... 2>&1 | tail -10; then`。当前脚本为 `#!/bin/sh` 且只有 `set -e`；checker 返回非零而 `tail` 正常返回 0 时，管道按末端命令返回 0，`!` 后条件为 false，`failed=1` 不执行。

**影响**：不符合 0-6 步 DOD 的任务文档可能通过本地 pre-commit，形成机器 gate 假绿；不影响业务数据。

**2026-07-23 决策**：✅ 采用方案 A——POSIX 兼容的显式 `output + rc` 捕获，并增加 3 个回归场景：合法文档通过、非法文档阻断、长输出截断后仍阻断。明确不捆绑环境 fail-closed、hook 安装、全局 `pipefail` 或 pre-commit 重构。

**状态**：🔴 已决策 · 待用户明确“开始实施”后按 `fix-mini` 进入 4 步。

**关联文档**：
- [`research.md`](tasks/2026-07-23-bug-precommit-p0-gates/p0-1-dod-exit/research.md)
- [`decisions.md`](tasks/2026-07-23-bug-precommit-p0-gates/p0-1-dod-exit/decisions.md)

---

### 债务 12 — pre-commit 环境缺失或损坏时跳过 Gate 🔴 P0 NEW

**位置**：`scripts/pre-commit:21-24,43-46`

**背景**：相关 backend/frontend 文件已暂存时，hook 仅检查 `.venv` / `node_modules` 目录；目录缺失则警告并跳过 pytest/tsc，最后仍可能显示全部通过。现有恢复提示还引用不存在的 `scripts/setup.sh`。

**影响**：本地没有任何测试执行证据却产生成功信号；目录存在但 binary 或工具损坏也缺少明确的前置健康判定。当前 required checks 尚未完全配置，不能仅依赖远程 CI 形成不可绕过闭环。

**2026-07-23 决策**：✅ 采用风险范围感知的 fail closed——相关可执行、测试、依赖和配置改动才触发；测试与生产代码同等要求真实执行；纯文档不触发。后端检查可执行 Python + pytest 探针，前端检查本地 `.bin/tsc`；增加 8 个回归场景并修正恢复命令。

**状态**：🔴 已决策 · 待用户明确“开始实施”后按 `fix-mini` 进入 4 步。

**明确排除**：hook 自动安装、required checks、bypass 审计、多 profile setup、`start.sh` 服务健康、全 hook 重构、债务 11。

**关联文档**：
- [`research.md`](tasks/2026-07-23-bug-precommit-p0-gates/p0-2-environment-gate/research.md)
- [`decisions.md`](tasks/2026-07-23-bug-precommit-p0-gates/p0-2-environment-gate/decisions.md)

---

### 债务 13 — `[x] DONE` 混合实施、测试、验证和用户验收语义 🔴 P0 NEW

**位置**：`AGENTS.md` § 6.5/6.7、`scripts/check-step.py::check_tasks()`、各任务 `tasks.md` / `verify.md` / `retro.md` / `docs/rules/milestones.md`

**背景**：当前 `[x]` 与 `✅ DONE` 会在实现 commit 后写入，但独立 verifier 发生在 commit 之后；因此可能先 DONE、后 FAIL。V4 T29 已出现 tasks DONE 与 Playwright 5 failed / 0 passed 并存，且状态曾继续传播到 retro 和 milestones。

**影响**：任务实施事实、测试结果、独立 verifier 和阶段用户验收被压缩成一个布尔值；FAILED 仍可能被下游解释为完成，反向也会出现 verify 已通过但 tasks 未回写。

**2026-07-23 决策**：✅ 采用最小正交事实模型：task 记录 implementation/test/verifier；phase 记录 acceptance。`[x]` 只表示 implementation 已落入 commit，删除新任务格式中的裸 DONE；`[x] + FAIL` 合法，但 `FAIL + DONE/VERIFIED/阶段完成` 非法。不使用 frontmatter/checkbox/table 三份状态副本，不全量迁移历史任务。

**状态**：🔴 已决策 · 按 `refactor-6` 等待用户指令进入步骤 1 规格。

**关联文档**：
- [`research.md`](tasks/2026-07-23-refactor-task-status-semantics/research.md)
- [`decisions.md`](tasks/2026-07-23-refactor-task-status-semantics/decisions.md)

---

### 债务 14 — 任务路径、阶段与条件产物缺少目录级机器契约 🔴 P0 NEW

**位置**：`scripts/check-step.py`、`scripts/pre-commit`、`docs/DOD.md`、任务模板与 `docs/tasks/*/`

**背景**：当前 checker 只校验已经存在的单个文件，无法发现当前阶段应存在但缺失的核心或条件产物；也无法区分未到阶段、路径模式跳过与真正违规。pre-commit 还以 staged path 触发、却读取 working-tree 内容，存在检查版本与提交版本错位。

**影响**：缺失 `api-spec`、`design-spec`、测试证据等仍可假绿；机械强制 `test-cases.md` 又会催生空模板和 tasks 双账。合法暂停可能被静态最终文件清单误报。

**2026-07-23 自动决策**：✅ 新任务采用最小 `task.yaml`，唯一记录 mode/current_step/step_state/triggers/test_evidence；新增目录级 `check-task.py`，强制真实测试证据但允许 code/tasks-inline/standalone 多落点；pre-commit 固定检查 INDEX 视图。P0-5 的 task 状态继续留在 tasks.md，不复制到 manifest。旧任务标 `LEGACY_UNVERIFIED`，不维护永久白名单。

**状态**：🔴 自动决策 · 按 `refactor-6` 待步骤 1 规格。

**明确排除**：全量历史迁移、时间调度器、事件账本、证据哈希、自动 verifier/mutation test、第一版完整 diff trigger 推断。

**关联文档**：
- [`research.md`](tasks/2026-07-23-refactor-task-artifact-contract/research.md)
- [`decisions.md`](tasks/2026-07-23-refactor-task-artifact-contract/decisions.md)

---

### 债务 15 — CI 缺少真实浏览器关键旅程 Smoke 🔴 P0 NEW

**位置**：`.github/workflows/ci.yml`、`frontend/playwright.config.ts`、`frontend/tests/e2e/`

**背景**：现有 CI 覆盖 pytest、Vitest、typecheck 和 build，但没有 Playwright job。现有 Digest Playwright 五场景主要使用浏览器内 API mock，不能证明 JWT、FastAPI、MySQL 与真实数据链；视觉套件也不适合直接充当功能 required gate。

**影响**：页面路由、Provider、认证、浏览器运行时和前后端接缝问题只能在手工 L5 或审计阶段发现。直接把现有套件设 required 又会形成高成本低置信度假绿或 flaky gate。

**2026-07-23 自动决策**：✅ 新增独立只读观察性 `playwright-smoke`：真实 MySQL + FastAPI + Next production + Chromium，运行 Dev Login → Dashboard → 创建 Interview → Room → Complete → History/API round-trip。零 secrets/写权限，单 worker、0 retries；连续 20 次零 flake且 P95 ≤4 分钟后交 P0-4 决定 required。

**状态**：🔴 自动决策 · 按 `full-6` 待步骤 1 规格。

**明确排除**：现有全套视觉测试、Digest 五场景、语音/LLM/LiveKit/RSS/邮件、Docker Compose 全栈、直接配置 required checks。

**关联文档**：
- [`research.md`](tasks/2026-07-23-new-feature-ci-playwright-smoke/research.md)
- [`decisions.md`](tasks/2026-07-23-new-feature-ci-playwright-smoke/decisions.md)

---

### 债务 16 — 缺少 Required Checks / Branch Protection 安全门禁 🔴 P0 NEW

**位置**：仓库 0 ruleset、`.github/workflows/`、AGENTS § 6.10、CI auto-fix 决策、`docs/issues.md` 多次"待配置"主账

**背景**：CI workflow 已部署，但 3 个 check 未设 required；admin 仍可隐式 bypass；`auto-fix/**` 缺独立保护；emergency hotfix 缺 PR-only + 两人原则 + 不可绕过 break-glass policy + 外部审计。Backend tests 最近 3/3 failure、xfail 仍 `strict=False`、env approval 未配、origin/HEAD 漂移。

**影响**：历史 41 空壳与 183 transient 已证明"workflow 存在 ≠ 阻断合并"。当前不锁即无法阻止下一轮假绿；锁错又会立刻 block main PR；auto-fix 与 break-glass 不区分会让不可信代码跨入默认分支。

**2026-07-23 自动决策**：✅ 启用前清理（xfail→strict、Backend 失败、commit auto-fix-ci.yml、配 auto-fix-approval environment、修 origin/HEAD）后，启用 Repository ruleset `knockwise-quality-gates` 覆盖 main/feature/codex，required = `CI / Test quality` + `CI / Backend tests` + `CI / Frontend tests`，enforce admins=true、bypass 空、strict、non-fast-forward、conversation resolution；独立 `knockwise-auto-fix-branch-protection` 禁 force-push 与删除；break-glass 限于 PR + 两人原则 + incident ID + 不可绕过 policy check + 外部审计。auto-fix bot 永不在 bypass list；不做 merge queue / Playwright smoke required。

**状态**：🔴 自动决策 · 按 `full-6` 待步骤 1 规格。

**明确排除**：merge queue、独立 break-glass-policy check、Playwright smoke required、auto-fix env approval、workflow commit 治理（与 P0-6 协同）、admin 默认 bypass。

**关联文档**：
- [`research.md`](tasks/2026-07-23-new-feature-required-checks/research.md)
- [`decisions.md`](tasks/2026-07-23-new-feature-required-checks/decisions.md)

---

### 债务 17 — CI auto-fix v3 后仍有 7 项 P0 残留与 4 处文档漂移 🔴 P0 NEW

**位置**：`.github/workflows/auto-fix-ci.yml`、`scripts/ci/sanitize_ci_log.py`、`scripts/ci/test_security_e2e.sh`、`docs/tasks/2026-07-22-new-feature-ci-autofix/{spec,verify,retro}.md`

**背景**：v3 决策（commit `4648d50` FU-3 + `66efa3c` SHA pin）后 4 道关在 workflow 行为层面对齐，但调研发现 7 个 P0 残留：diagnostic checkout PR 分支执行未信任脚本；checkout ref 用 `head_branch` 应为 `head_sha`；label description 计数器可被绕过；environment approval 缺 CI 验证；评论 API 错误；`key_string` 仍是 raw log 前 200 字符无 allowlist；filesystem 是 Claude Read 范围但 prompt 未声明为不可信。还有 4 处文档漂移（spec/verify/retro/test）已与现实矛盾。

**影响**：当前 FU-3 改进仅是局部，AGENTS § 6.10 反例 "Fork PR 自动 checkout 并跑任意代码" 仍成立；自我豁免式假绿灯潜伏在 stale 注释与陈旧判断中；下一次 L5 真 CI 触发会立刻暴露。

**2026-07-23 自动决策**：✅ v4 = v3 + 7 项 P0 残留修复（决策 11-17）+ 4 处文档同步（决策 18）。不立即实施代码；登记为实施阶段独立任务。

**状态**：🔴 自动决策 · 按 `refactor-6` 待用户实施授权。

**明确排除**：立即 workflow 重写、env approval 配置、merge queue、break-glass policy、Playwright smoke required、auto-fix env approval。

**关联文档**：
- [`research.md`](tasks/2026-07-23-bug-ci-autofix-safety-drift/research.md)
- [`decisions.md`](tasks/2026-07-23-bug-ci-autofix-safety-drift/decisions.md)

---

### 债务 18 — P1 测试基础架构（L1-L5 边界 + 追溯矩阵 + E2E Fixture）缺统一主账 🔴 P1 NEW

**位置**：`docs/rules/testing-rules.md`、`docs/templates/{tasks,verify,product-doc}-template.md`、`backend/tests/conftest.py`、`frontend/tests/e2e/`、`frontend/playwright.config.ts`

**背景**：当前 L1-L5 Mock 边界散落于 `testing-rules.md § 6.5` + `conftest.py` + `tasks-template.md`，缺统一主账；Requirement→Scenario→TC 闭环没有稳定 ID 体系，verify.md 缺 EV/Metric；E2E fixture 复用默认 dev-user + 共享 DB，dev-login DB 异常回退虚拟 token 制造假绿，前端 `block_external_network` 缺失。

**影响**：测试分类失效、追溯断链、dev-login fallback 可掩盖真实后端故障、E2E 无法真正证明端到端契约。直接进入实施会导致模板/状态机/checks 出现双 schema 漂移。

**2026-07-23 自动决策**：✅ 三位一体合并：L1-L5 边界写入 `testing-rules.md § 6.5.1`；Traceability Matrix 10 列 + 10 条机器校验不变量写在 `verify.md`；E2E Fixture 8 项契约（DB 边界、用户命名空间、登录态、Digest 预生成、seed 只读、时间固定、清理幂等、并行隔离）。不实施代码，不改 mock 默认行为，不动 `seed_data/`，不引入新测试框架。

**状态**：🟡 自动决策 · 按 `refactor-6` 待步骤 1 规格。

**明确排除**：修改 `mock_db / mock_cache / mock_llm` 默认行为；修改 `seed_data/digest_sources.json`；改老 e2e 文件；引入 pytest-xdist / testcontainers / pytest-postgresql；任何代码实施与提交。

**关联文档**：
- [`research.md`](tasks/2026-07-23-refactor-test-foundation/research.md)
- [`decisions.md`](tasks/2026-07-23-refactor-test-foundation/decisions.md)

---

### 债务 19 — xfail/skip / AI 评估 / a11y+性能 缺统一治理 🔴 P1 NEW

**位置**：`backend/tests/**`、xfail marker、`pyproject.toml`、`check_test_quality.py`、AI 5 入口、frontend 组件与样式

**背景**：4 个 xfail 全部 `strict=False` 且 issue 关联粗；pytest 全局无 `xfail_strict`；AST gate 不识别 xfail。AI 系统 5 入口（evaluate/report/followup_match/followup_text/qa_service/digest_llm）仅 1/5 有 timeout + 严格 schema，无离线 eval 体系。a11y 4 个 P0 运行时违规（VoiceRoom PTT 不可键盘 / SidebarGroup 假按钮 / Layout mobileOpen 死代码 / 暗色对比度），0 axe/lighthouse/web-vitals/browserslist 集成。

**影响**：xfail 转 XPASS 不阻断；AI 质量无 golden set 与 judge；a11y/perf 全靠人工。直接设 hard gate 必然假绿/假红。

**2026-07-23 自动决策**：✅ 三合一：xfail 静态 metadata（owner/issue/expiry/reason + strict=True）+ pytest 全局 `xfail_strict=true` + AST gate 扩展 4 violation code + 预算只降不升；AI 107 case 离线数据集 + 7 维度契约 + commit/nightly 双层；a11y/perf 9 维度契约 + 6 gate 全部 report-only + 20 次观察晋升。明确排除立即 hard gate 与新测试框架。

**状态**：🟡 自动决策 · 按 `refactor-6` 待步骤 1 规格。

**明确排除**：立即 hard gate；修改 `mock_db / mock_cache / mock_llm` 默认行为；改 `seed_data/digest_sources.json`；引入新测试框架；任何代码实施与提交。

**关联文档**：
- [`research.md`](tasks/2026-07-23-refactor-test-governance-quality/research.md)
- [`decisions.md`](tasks/2026-07-23-refactor-test-governance-quality/decisions.md)

---

### 债务 20 — 产品基础缺 baseline 锚点、字典与埋点分层 🔴 P1 NEW

**位置**：`docs/templates/product-doc-template.md`、`docs/templates/tasks-template.md`、`docs/tasks/2026-07-17-new-feature-ai-push/product-doc.md`、`docs/tasks/2026-07-21-issues-audit/`、`backend/utils/metrics.py`

**背景**：product-doc 模板与已实施实例成功指标都缺 baseline 锚点（"DAU +15%"无当前值）；议题 F 关闭条件与产品指标字典完全脱钩；T19 observability 实际是 dead code（0 调用方）；trace_id 是进程级单值 race；audit 9 任务全无埋点挂载；tasks-template 缺 § 9 段；interview 用户角色碎片化（3 任务 3 persona）。CI auto-fix verify.md L4/L5 缺失但仍标"🟢 可进入 6 步"；issues-audit 任务无 verify.md。

**影响**：未经验证阈值伪装为事实；埋点形式化但虚；最基本行为事实尚未可靠产生。

**2026-07-23 自动决策**：✅ 分层 L0-L3 治理：L0 内部/一次性不要求；L1 探索性 1 假设 + 1 核心信号 + ≤3 事件；L2 核心闭环 1 北极星 + 2-3 护栏 + 完整字典 + 埋点测试；L3 稳定用户 + dashboard + cohort。product_baseline 字段含 problem_evidence + target_user + kill_criteria + dangerous_assumptions；指标字典 8 必填 + 4 可选；埋点按层强制并加 § 9 段；counter 真增断言门禁；不全量要求 5 项 AI 推送阈值。**反方纠正**：立即要求完整字典会产生形式主义，单人项目应分层。

**状态**：🟡 自动决策 · 按 `refactor-6` 待步骤 1 规格。

**明确排除**：立即要求所有功能完整字典；引入新分析平台；改业务表 schema 强埋点；改 `mock_db / mock_cache / mock_llm` 默认行为；任何代码实施与提交。

**关联文档**：
- [`research.md`](tasks/2026-07-23-refactor-product-foundation/research.md)
- [`decisions.md`](tasks/2026-07-23-refactor-product-foundation/decisions.md)

---

### 债务 21 — 产品验收与学习缺统一治理 🔴 P1 NEW

**位置**：`docs/templates/verify-template.md`、L5 staging 实测、议题 C 路由契约、AI 推送 product-doc 5 项指标、issues-audit verify 缺失、issues.md:516 角色碎片化

**背景**：verify-template § 6 仅 4 行（结论 + 确认人 + 日期），无任务完成率/首次使用耗时/困惑点/访谈；AGENTS 双 gate 由开发者本人 = self-attestation；CI auto-fix verify L4 🟡 L5 ❌ 仍标"🟢 可进入 6 步"；issues-audit 任务无 verify.md；议题 C 路由 3 套并存 + LiveKitVoice 孤儿；AI 推送 `/ai/today` 与设计文档 `/push` 命名冲突；spec.md/api-spec.md 完全无路由契约；前端 hook 字段与后端 schema 无文档化映射；D7 "6-8 周不评估" 已落地但 7/30 天 review 未配套。

**影响**：与已落地 L0-L3 分层冲突；与 5 起流程签字失真同源；立即强制 L2/L3 会推翻 D7 + 在单人项目 / 0 外部用户现状下形式化。

**2026-07-23 自动决策**：✅ P1-10/11/12 三合一按 L0-L3 分层触发：P1-10 用户验收 L0 不要求、L1 1 句话假设、L2 2-3 种子用户、L3 5-10 cohort；P1-11 Outcome Review 三窗口（L2/L3 强制）：Day 7 runtime + Day 14 early-kill + Day 30 outcome，议题 D + F 作为前置依赖追踪内嵌，决策三分类 continue/pivot/kill；P1-12 旅程追踪走"新建 task 目录 + contract.yaml + 4 个机器校验脚本"，不动老 spec/api-spec（避免与议题 C 冲突）。**反方纠正**：与 D7 + L0-L3 + 5 起签字失真同源；前置必做 issues.md:516 角色碎片化合并 + 议题 F 观测基建 + 议题 C 路由收敛。

**状态**：🟡 自动决策 · 按 `refactor-6` 待步骤 1 规格。

**明确排除**：立即 L2/L3 全员强制；推翻 D7；修订已落地 L0-L3；引入新平台；任何代码实施与提交。

**关联文档**：
- [`research.md`](tasks/2026-07-23-refactor-product-verification-learning/research.md)
- [`decisions.md`](tasks/2026-07-23-refactor-product-verification-learning/decisions.md)

---

### 债务 22 — P2 治理流程清理 4 项合一 🔴 P2 NEW

**位置**：`.claude/skills/intervue-dev/SKILL.md` 过时架构、5 模板 TODO、4 research 模板缺 frontmatter、AGENTS.md §6.11 缺失

**背景**：`.claude/skills/intervue-dev/SKILL.md:14-17` 声称 LangGraph 1.0 + Tailwind 4 + docker-compose 起服务（实际 langgraph 0.3.18 / tailwind 3.4.19 / Docker 走不通）= 3 处与现实不符；5 模板 TODO 接入的独立 checker 全部未实施；4 research 模板缺 frontmatter；AGENTS.md §6.5/§6.6 与 pre-commit/check-step 重复；12 个 2026-07-23 治理 task 实施率 8.3%。

**影响**：过时 skill 误导 AI 助手；5 模板硬性 DOD 段未机器强制；4 research 模板不可机器解析；治理流程无退役机制。

**2026-07-23 自动决策**：✅ 4 项合一：P2-2 物理删除 `.claude/skills/intervue-dev/` + deprecation banner；P2-3 扩 `check-step.py` 5 模板 + 共享 `check_spec_base.py` + pre-commit 5 行 + EXEMPT_* 白名单；P2-4 写 `_frontmatter-schema.md` + 4 research 补 frontmatter + 新建 `check-frontmatter.py`；长期 AGENTS.md §6.11 退役规则（5 段：删除条件 / 退役 ≠ 删除 / 季度归档 / retro 必须写明）。**反方纠正**：P2-1 物理拆 AGENTS.md 与 P2-5 立即删段不采纳（治理已饱和 + 实施率 8.3%），先实施已写规则。

**状态**：🟡 自动决策 · 按 `refactor-6` 待步骤 1 规格。

**明确排除**：P2-1 物理拆 AGENTS.md；P2-5 立即删 §6.5/§6.6；任何代码实施与提交。

**关联文档**：
- [`research.md`](tasks/2026-07-23-refactor-p2-governance-cleanup/research.md)
- [`decisions.md`](tasks/2026-07-23-refactor-p2-governance-cleanup/decisions.md)

---

### 债务 10 — V1/V3 旧模块审计发现 183 真实测试失败 ✅ 已验证修复（2026-07-23）

**位置**：audit v1/v2 报告（2026-07-21 / 2026-07-22）记录以下模块当时失败：
- `test_summary_service.py`（dashboard / weekly sync / generate_narrative）
- `test_study_plan_service.py`（progress aggregation / delete plan）
- 其他 V1/V3 既有模块

**审计来源**：[`docs/tasks/2026-07-23-audit-183-failures/research.md`](tasks/2026-07-23-audit-183-failures/research.md)（2026-07-23 实测审计）

**背景**：
- audit v1/v2 报告后端 `pytest` 实测 `183 failed, 494 passed, 4 xfailed`（681 collect）
- 当时 `backend/.venv` 缺失 + greenlet / openai-whisper 隐性依赖未装 + 无 `.env.local` + 可能 DB migration 未 init
- 183 failed 集中在 `summary_service` / `study_plan_service` · 这些测试高度依赖 DB session fixture
- 推测根因：测试环境瞬时状态问题（不是代码 bug）

**修复情况**：✅ **2026-07-23 已验证 0 fail**

实测：
```bash
cd backend && ./.venv/bin/python -m pytest --tb=no -q
# 703 tests collected
# 695 passed, 4 skipped, 4 xfailed, 22 warnings in 1.83s
# 0 failed
```

单跑原本失败的文件验证：
```bash
cd backend && ./.venv/bin/python -m pytest tests/test_summary_service.py tests/test_study_plan_service.py -v
# 48 passed, 1 warning in 0.54s
# 0 failed
```

**根因**：环境设置累积（commit `ee5dbd8` 加 greenlet/whisper + 用户本地 `.env.local` 创建 + DB migration 初始化）· 不是代码 bug · **未做代码修复**（不需要修）

**状态变更**：2026-07-22 登记 🔴 P0 → 2026-07-23 立即标 ✅ 已修复（无需代码改动）

**教训**：
- 审计报告（test environment 状态）有"半衰期" · 环境累积后现象可能自然消失
- 重新实测是必要的 · 不能只看历史报告
- 类似审计应附"实测时间 + 环境状态"元信息

**关联决策**：用户拍板"选项 B：登记 + 立即关闭"（2026-07-23）
**关联文档**：
- [`docs/tasks/2026-07-23-audit-183-failures/research.md`](tasks/2026-07-23-audit-183-failures/research.md)（完整调研 + 验证步骤）

---

### 债务 1 — 数据库缺少复合索引 ⚠️

**位置**：`backend/models/__init__.py` 的 Interview / QuestionRecord

**问题**：
- `interviews` 表有 100+ 行后，`WHERE user_id=? AND status=? AND deleted_at IS NULL` 全表扫
- `question_records` 没有 `(interview_id, created_at)` 复合索引
- JSON 字段（`state_snapshot` / `radar_data`）无全文检索索引

**建议**：
```sql
ALTER TABLE interviews ADD INDEX idx_user_status (user_id, status, deleted_at);
ALTER TABLE question_records ADD INDEX idx_interview_created (interview_id, created_at);
```

**优先级**：中（数据量 < 10k 之前不痛）

---

### 债务 2 — `start_interview` 去重是应用层做的 ⚠️

**位置**：`backend/api/interview.py:241-280`（之前修过 dedup 那个 bug）

**现状**：dedup 逻辑在 Python 层 `SELECT ... LIMIT 1`，并发情况下两个请求同时跑会双 INSERT（因为没有 unique constraint）。

**建议**：
```sql
ALTER TABLE interviews ADD CONSTRAINT uniq_user_inprogress
  UNIQUE (user_id, round, style) /* 仅当 status='in_progress' */;
```
但 MySQL 不支持部分 unique index，需要用 generated column 或业务约束。

**优先级**：低（单用户并发点击的概率小，但严格说应该做）

---

### 债务 3 — 测试覆盖需要持续量化 ⚠️

**状态**：🚧 改善中

**位置**：`backend/tests/` + `frontend/__tests__/`

**现状（2026-07-22 数字修正）**：递归统计 `find backend/tests -name "test_*.py" -type f | wc -l` = **41 个**（含 `api/` `e2e/` `schemas/` `services/` 4 个子目录），顶层 `ls backend/tests/test_*.py | wc -l` = 29 个 —— 之前 29 数字是顶层漏算。**前端 25 个 Vitest 文件不变**（实测 `find frontend -name "*.test.*" -not -path "*/node_modules/*" | wc -l`）。

⚠️ **关联债务 9**：V4 AI 推送模块的 5 个文件含 **41 个确定空壳测试**（纯 `pass`），pytest 会全计为通过。这部分"覆盖"是虚假绿光，详见三、债务 9。

注：`pyproject.toml` 无 coverage 配置；`requirements.txt:29` 列了 `pytest-cov>=6.0.0` 但未启用；无 `.coverage` / `htmlcov` 文件。

**建议优先级**：
1. 核心 service 单测（`interview_service.process_answer`、`report_agent.generate_report`）
2. API contract 测试（OpenAPI snapshot）
3. E2E happy path 1-2 个
4. **修复债务 9**：V4 41 个空壳测试重写

**优先级**：中（重构前必做，否则改完没信心）

---

### 债务 4 — 无 Alembic，迁移全靠 `_MIGRATIONS` 启动 ALTER ⚠️

**位置**：`backend/core/database.py:_MIGRATIONS`

**现状**：每加一列手动 append，schema drift 风险（多人开发时本地 SQL 不一致）。

**建议**：用 Alembic（之前评估过，工时 ~0.5 天）。

**优先级**：低（单人项目不痛，但多协作者/多环境部署前必做）

---

### 债务 5 — 邮箱 + 密码哈希用 stdlib `hashlib.pbkdf2_hmac` 而非 bcrypt/argon2 ⚠️

**位置**：`backend/api/auth.py:38,46` 注册 / 校验路径

**现状（2026-07-21 清账）**：`_hash_password` / `_verify_password` 已使用 **PBKDF2-SHA256 iterations=600_000**（OWASP 2023 推荐值，原议题的"调到 600000+"建议已落实）。仅剩"非 argon2/bcrypt（内存硬度不足）"一点仍成立。
> 关联虚假注释：`backend/models/__init__.py:49` 注释写 `# bcrypt hash`，实际是 pbkdf2 —— 应改注释（见新增发现，非本议题必修项）。

**建议**：若上线前要进一步硬化，换 argon2-cffi（内存硬度更好）；否则接受 600K pbkdf2 现状并修正误导注释即可。

**优先级**：低（600K 已达标，仅算法选择与注释订正）

---

### 债务 6 — 知识库的 vault 路径硬编码 `~/Obsidian/coding/` ⚠️

**位置**：`backend/services/obsidian_service.py:14`

**现状**：路径写死 `Path.home() / "Obsidian" / "coding"`，多 vault / iCloud 同步 / Windows 用户都没法用。

**建议**：写到 `core/config.py` 的 `OBSIDIAN_VAULT_PATH`，从 `.env.local` 读。

**优先级**：低（当前用户用 Mac + 单 vault，不痛）

---

### 债务 7 — 启动时预热 STT 75MB 模型，加载慢 ⚠️

**位置**：`backend/main.py:_warm_stt` + `backend/voice/stt.py:_load_model`

**现状**：后端启动时会下载 + 加载 faster-whisper tiny，第一次启动 + 每次冷启慢。

**建议**：
- 预下载到 `backend/voice/models/` 打包
- 启动失败时不阻塞（已经在做了：`try/except logger.warning`）
- 改成 lazy 加载：第一次 `/api/interviews/transcribe` 时再加载

**优先级**：低

---

## 四、已完成的修复（历史归档）

| 修复 | 时间 | 链接 |
|---|---|---|
| SQLite PRAGMA → MySQL 兼容的迁移 | 2026-06-17 | commit `core/database.py` |
| `start_interview` 同 (user/round/style) 去重 | 2026-06-17 | commit `api/interview.py` |
| `record.question_id` 缺失导致 `total_questions=0` | 2026-06-17 | commit `api/interview.py` |
| 报告生成从全 3 stub 改调真 `ReportAgent` | 2026-06-17 | commit `api/report.py` |
| `get_backlinks` 模糊匹配（去空格） | 2026-06-17 | commit `obsidian_service.py` |
| React StrictMode 双触发防护 | 2026-06-17 | commit `interview/room.tsx` `interview.tsx` |
| 文档英文名 → 中文名 + 合并重构方案 | 2026-06-18 | `docs/` git mv |
| Alembic 启动 ALTER 自动跑 | 2026-06-17 | `core/database.py:_MIGRATIONS` |
| Bug 9：SM-2 测试参数 `repetition_count` → `review_count` | 2026-06-25 | commit `7a5a21e` · commit 记录 92 passed；2026-07-21 代码复核一致，当前环境无 pytest 未重复执行 |

---

## 五、讨论记录区

> 每次讨论某个议题后，把结论记在这里。格式：
> ```
> ### [YYYY-MM-DD] 议题 X — 结论
> **决定**：
> **行动项**：
> **影响文件**：
> ```

### [2026-06-25] Bug 9 — SM-2 测试与签名不一致 — 结论

**决定**：改测试，从 `repetition_count` 改为 `review_count`（与函数签名 / DB 字段一致，无需迁移）。

**行动项**：
1. `test_sm2.py` 全文 `repetition_count` → `review_count`（一次性 replace_all）
2. 跑 `pytest tests/test_sm2.py -v` 验证 10 个测试全绿
3. pre-commit hook 应该自动跑过（如果不通过 → 排查）
4. commit 前缀：`fix(sm2): 测试对齐函数签名`

**影响文件**：
- `backend/tests/test_sm2.py`（改）
- `docs/issues.md`（本文档登记）
