# 调研报告 · 重构：补核心 service 测试覆盖率

> 日期：2026-06-27 · 调研人：Claude (MiniMax-M3) · 议題编号：T-2026-06-27-01

---

## 1. 任务理解（必填）

- **用户原话**: "补上吧"（接上一条 pytest 覆盖率 12% 的汇报）
- **重构目标**:
  - [x] 可测试性（解耦 / 注入）
  - [ ] 性能
  - [ ] 可读性
  - [ ] 可维护性
  - [ ] 一致性
- **议題编号**: T-2026-06-27-01（新建）
- **不补会怎样**:
  - CLAUDE.md § 1.8 DOD 要求核心 service 覆盖率 ≥ 80%，当前 12%，**阶段 6 实施完毕的硬性门槛过不了**
  - 重构这 6 个 service 时无测试保护，**任何改动都可能是裸奔**
  - 用户报"pytest 92/92 通过"看起来很美，实则**只测了 schema 和纯函数**，业务逻辑零保护

---

## 2. 现状分析（必填）

### 2.1 重构对象（6 个核心 service）

| service | 行数 | 公共函数/类 | DB 依赖 | LLM 依赖 |
|---|---|---|---|---|
| `services/interview_service.py` | 258 | 1 类 (11 公开方法) + 1 helper | Interview | 无（调 agent 但本次不测） |
| `services/question_bank_service.py` | 439 | 17 函数 | Question + 5 | 无 |
| `services/qa_service.py` | 227 | 7 函数 | QASession + 2 | ChatOpenAI（**需 mock**） |
| `services/recommendations_service.py` | 142 | 5 函数 | User + 2 | 无 |
| `services/study_plan_service.py` | 172 | 5 函数 | QuestionProgress + StudyPlan | 无 |
| `services/learning_progress_service.py` | 520 | 11 函数 | 4 个模型 | 无 |
| **总计** | **1758** | **46 个函数** | — | — |

### 2.2 调用方清单（找全，必填）

| service | 调用方 | 频次 |
|---|---|---|
| interview_service | `api/interview.py:20` | 1 处 |
| question_bank_service | `api/learn.py` | 8 处 |
| qa_service | `api/learn.py` | 5 处 |
| recommendations_service | `api/dashboard.py:13` | 1 处 |
| study_plan_service | `api/learn.py` | 5 处 |
| learning_progress_service | `api/learn.py` (8) + `api/interview.py:597` (1) + `tests/test_sm2.py:11` | 10 处 |

> 验证：`grep -rn "from services\." --include="*.py" backend/` 全部命中

### 2.3 当前测试覆盖

| service | 覆盖率 | 现有测试 |
|---|---|---|
| interview_service | **0%** | 无 |
| question_bank_service | **0%** | 无 |
| qa_service | **0%** | 无 |
| recommendations_service | **0%** | 无 |
| study_plan_service | **0%** | 无 |
| learning_progress_service | **27%** | `test_sm2.py` 测了 `calculate_next_srs` / `calc_next_review_at` 两个纯函数 |
| **总覆盖率** | **12%** | — |

> ⚠️ 重构前覆盖率 < 80%（CLAUDE.md § 0.2 红线）。本次任务**正是为了把这个缺口补上**。

### 2.4 依赖关系

- **外部依赖**：
  - `sqlalchemy.ext.asyncio.AsyncSession`（所有 service 都接 db session 参数）
  - `core.cache` Redis（question_bank / learning_progress）
  - `langchain.ChatOpenAI`（仅 qa_service）
  - `agents.*` LangGraph（仅 interview_service，本次不深入测）
- **内部依赖**：
  - `models.*` ORM 模型（每个 service 都依赖）
  - `core.config.settings`（部分）
- **循环依赖**：无

---

## 3. 重构方案（必填，≥ 2 个）

### 方案对比

| 维度 | 方案 A：全 Mock（不接真 DB） | 方案 B：测试 SQLite + 真 DB session |
|---|---|---|
| **思路** | 用 `unittest.mock.AsyncMock` 模拟 AsyncSession 返回值 | 起一个 sqlite 测试库，跑真 SQL |
| **改动范围** | 0 行 production code；新增 ~1500 行测试 | 0 行 production code；新增 ~1500 行测试 + conftest.py |
| **风险等级** | 🟡 中（mock 不全会漏 bug） | 🟢 低（更接近真实） |
| **兼容性** | ✅ 完全兼容 | ⚠️ 部分 SQL 方言差异（MySQL vs SQLite） |
| **测试速度** | 🚀 快（< 5s 全跑完） | 🐢 慢（每测试起事务 ~ 50ms × 200 = 10s+） |
| **现有测试影响** | 不动现有 test_sm2.py | 同左 |
| **可维护性** | 需为每个函数写 mock setup | 简单 setup，pytest fixture 复用 |
| **覆盖价值** | 覆盖业务逻辑分支 | 覆盖业务逻辑 + SQL 正确性 |

### 方案 B 子选项：真 MySQL + 事务回滚
- 接本机 3306 的 `codemock_test` 测试库（不存在则创建）
- 每个测试 `BEGIN ... ROLLBACK`
- 优点：完全真实；缺点：CI 环境可能没 MySQL

### 推荐：**方案 A（全 Mock）**，理由：

1. **目标明确**：CLAUDE.md 要的是 ≥ 80% 覆盖率，证明业务逻辑有保护
2. **速度**：6 service × 平均 15 函数 × 平均 3 case = 270 测试，全 Mock 几秒跑完；接 DB 要几十秒
3. **隔离性**：测试不依赖外部 MySQL/Redis，新人 clone 即可跑
4. **现有测试一致**：test_sm2.py 也是纯函数测试风格
5. **未来可加**：方案 A 跑稳后，可加少量真 DB 集成测试（方案 B）覆盖 SQL 边界

> **例外**：qa_service 有 LLM 调用（`_get_llm` → `ChatOpenAI.ainvoke`）。这部分必须 mock，否则测试要真 LLM key + 网络。

---

## 4. 风险评估（必填）

| 风险 | 等级 | 缓解 |
|---|---|---|
| Mock 不全，测试通过但代码有 bug | 🟡 | 关键 happy path 加 1-2 个 mock 让返回值真实（如 SQLAlchemy Result 对象） |
| Async 测试不易写（pytest-asyncio） | 🟢 | 装 `pytest-asyncio`，用 `@pytest.mark.asyncio` 装饰 |
| ORM 模型字段改了测试挂 | 🟡 | 测试用构造 dict 而非 ORM 实例，减少耦合 |
| 覆盖率计算不准确 | 🟢 | 用 `--cov-report=term-missing` 看具体缺哪些行 |
| 测试运行时间长 | 🟢 | Mock 方案下应 < 5s |
| `interview_service` 涉及 LangGraph 状态机，测不全 | 🟡 | 只测纯状态管理方法，跳过 LangGraph 集成（agent 本身有另外的覆盖策略） |

---

## 5. 输出建议（必填）

### 5.1 推荐方案
- **推荐：方案 A（全 Mock）**
- 理由：
  - 与现有测试风格一致（test_sm2.py / test_schemas.py 都是纯逻辑测试）
  - 速度快、不依赖外部服务
  - 可一次性补齐 6 service 覆盖
  - 业务逻辑覆盖是核心目标，SQL 方言差异不是

### 5.2 推荐路径（按服务拆分 6 个原子任务）

```
0 调研（本文件）
├─ 写 tests/conftest.py（统一 mock AsyncSession + Redis fixture）
├─ tests/test_interview_service.py        → 目标 ≥ 80%
├─ tests/test_question_bank_service.py    → 目标 ≥ 80%
├─ tests/test_qa_service.py               → 目标 ≥ 80%（含 LLM mock）
├─ tests/test_recommendations_service.py  → 目标 ≥ 80%
├─ tests/test_study_plan_service.py       → 目标 ≥ 80%
├─ tests/test_learning_progress_service.py → 从 27% 提到 ≥ 80%
└─ 跑 pytest --cov=services 看最终覆盖率
```

### 5.3 关键决策点

- **是否需要 feature flag**：否
- **是否保留兼容（旧接口）**：N/A（不改动 production code）
- **是否分阶段**：**是** —— 6 service 分 6 个 commit，每 service 单独达标
- **是否需要 AB 测试**：否（纯测试代码）

### 5.4 测试策略统一约定

```
Mock 风格：
- AsyncSession → AsyncMock；链式调用 .execute.return_value.scalars.return_value.all() 等
- Redis cache  → MagicMock；core.cache.cache → MagicMock
- LLM (qa)     → patch("services.qa_service._get_llm")

Case 类别：
- happy path：正常输入返回正常输出
- 边界：None / 空列表 / 0 / 负数
- 异常：DB 抛错 / LLM 抛错 / 用户不存在
- 异步：所有 async 函数加 @pytest.mark.asyncio

覆盖率目标：每个 service ≥ 80%（行覆盖）
```

---

## 自检清单（AI 调研完必过）

- [x] 重构目标明确（覆盖率 12% → ≥ 80%）
- [x] 不重构会怎样有具体痛点（DOD 过不了 / 重构裸奔）
- [x] 调用方清单 ≥ 3 个（用 grep 验证 6 service 调用方）
- [x] 当前测试覆盖率已查（12%）
- [x] 方案对比 ≥ 2 个（方案 A 全 Mock / 方案 B 真 DB）
- [x] 推荐方案有引用证据（与现有测试风格一致 + 速度 + 隔离性）

---

## 附：执行 checklist

- [x] 写完本 research.md
- [ ] 建 conftest.py（共享 fixture）
- [ ] 写 test_interview_service.py（11 方法）
- [ ] 写 test_question_bank_service.py（17 函数）
- [ ] 写 test_qa_service.py（7 函数 + LLM mock）
- [ ] 写 test_recommendations_service.py（5 函数）
- [ ] 写 test_study_plan_service.py（5 函数）
- [ ] 写 test_learning_progress_service.py（11 函数）
- [ ] 跑 pytest --cov=services 验证
- [ ] 写 retro.md 记录这次补测试的得失