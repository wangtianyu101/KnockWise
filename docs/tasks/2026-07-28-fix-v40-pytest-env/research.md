---
title: Research · v40 启动前环境整治 · 修 34 pytest failed
date: 2026-07-28
status: v1.0（fix-mini 0 步调研完成 · 等用户确认进入 4 步）
type: research
related:
  - [P0 stub 修复 retro.md](../../tasks/2026-07-28-fix-p0-stub-metrics-integration/retro.md) — 前置任务
  - [docs/issues.md#v40-启动前环境整治](../../../issues.md) — 议题登记
---

# Research · v40 启动前环境整治 · 修 34 pytest failed

> **任务理解（用户授权）**：修 v40 启动前环境整治议题 · 让 `cd backend && pytest tests/` 全绿
> **路径模式**：fix-mini（0→4→6）· bug fix 类型
> **当前阶段**：0 调研完成 · 等用户确认进入 4 步实施

---

## 0. 任务理解（用户授权确认）

- **用户授权**：用户说 "B" = 继续 P0 启动前环境整治
- **范围**：修 v40 预存 34 pytest failed（不是 31 · 增加 3 个 P1-9 v1.2 回归）
- **目标**：让 `cd backend && pytest tests/` 全绿（0 failed）+ L5 staging 全绿

---

## 1. 复现路径

### 1.1 baseline 跑全量 pytest（2026-07-28 13:50 · 耗时 ≈ 80-95s）

```
34 failed, 850 passed, 2 skipped, 1 xfailed, 26 warnings
```

**34 failed 分类**（9 组）：

| # | 文件 | failed | 根因 |
|---|---|---|---|
| A | `tests/api/test_digest_api.py` | 8 | anyio event loop 跨测试污染 + pymysql FK 约束失败（fixture user_id 在 users 表不存在） |
| B | `tests/eval/test_dataset_integrity.py` | 2 | json.decoder error · 数据集 fixture 含非法 JSON |
| C | `tests/eval/test_*.py` | 12 | LLM 返回非 JSON · fixture 数据集/Prompt 漂移 |
| D | `tests/services/test_digest_composite_score.py` | 1 | composite_score 阈值逻辑回归（v40 预存） |
| E | `tests/services/test_digest_push_daily.py` | 3 | composite_score < 0.75 阈值 → daily_id=None（v40 预存） |
| F | `tests/services/test_digest_select_top_n.py` | 3 | select_top_n 阈值/diversity 逻辑回归（v40 预存） |
| G | `tests/test_check_step.py::TestCheckTasksBoldTolerance` | 3 | P1-9 v1.2 加严 L1/L2 分层校验后 · 老 fixture 缺 `layer: L1` 字段（默认 L2 → § 9 必填 → 失败） |
| H | `tests/test_digest_llm.py` | 1 | injection 测试 expected branch is null |
| I | `tests/test_metrics_endpoint.py::test_metrics_returns_timings_after_timing_call` | 1 | timings 期望 dict 含 push_latency_ms · 实际单例 digest_metrics.timings["push_latency_ms"] 为空（v40 baseline 无业务调用） |

### 1.2 历史 issues.md 登记 vs 实际

- issues.md 登记：**31 pytest failed**（v40 启动前环境整治 P0 议题）
- 实际跑：**34 failed**（多 3 个 P1-9 v1.2 加严后的回归）

---

## 2. 影响范围（≥ 3 文件）

| 文件 | 当前状态 | 接入方式 |
|---|---|---|
| `backend/tests/api/test_digest_api.py` | ❌ 8 failed（event loop + FK 约束） | **修 fixture + 加 autouse fixture 清理 loop** |
| `backend/tests/conftest.py` | ⚠️ v1.2 已部分优雅降级（L226-241） | **保留 + 加 event loop 清理 fixture** |
| `backend/tests/services/test_digest_*.py` | ❌ 7 failed（composite_score 阈值 + select_top_n） | **调研根因 + 修业务逻辑或测试 fixture** |
| `backend/tests/eval/test_*.py` | ❌ 13 failed（json decoder + LLM 漂移） | **调研 fixture 数据集完整性** |
| `backend/tests/test_check_step.py::TestCheckTasksBoldTolerance` | ❌ 3 failed（v1.2 加严回归） | **修 fixture 加 layer: L1** |
| `backend/tests/test_digest_llm.py` | ❌ 1 failed（injection expected null） | **调研 fixture** |

---

## 3. 根因假设

### 3.1 v40 分叉自 v39 + 38 commit
- v40 包含：P1-9（19 commit）+ P0 stub 修复（3 commit）+ 等
- pytest 失败在 v40 继承自 v39 之前的代码 + P1-9 v1.2 加严引入的回归

### 3.2 4 类根因（按优先级）

| 根因 | 影响 | 优先级 |
|---|---|---|
| **P1-9 v1.2 加严回归**（TestCheckTasksBoldTolerance 3 failed） | fixture 缺 `layer: L1` · 默认 L2 → § 9 必填 → 失败 | 🟡 P1（直接相关 · 容易修） |
| **test_digest_api.py 8 failed**（event loop + FK 约束 + StopAsyncIteration） | anyio 跨测试污染 + fixture user_id 不存在 + AsyncMock.side_effect=StopAsyncIteration 异常 · TestDailyAPI / TestBookmarkAPI / TestBehaviorAPI / TestSourcesAPI / TestSettingsAPI | 🔴 P0（业务影响 · 跨任务） |
| **test_metrics_endpoint timings_after_timing_call 1 failed** | v40 baseline 单例 digest_metrics.timings["push_latency_ms"] 为空 · 测试期望 push_latency_ms 存在 · P0 stub 修复后 uvicorn 启动会触发 · 但 pytest 直接 import 不触发 uvicorn | 🟡 P1（v40 baseline 限制 · pytest fixture 隔离） |
| **test_eval/* 13 failed + test_digest_push_daily 3 + test_digest_select_top_n 3 + test_metrics_endpoint 1 = 20 failed** | LLM 漂移 + composite_score 阈值 + select_top_n 业务回归 + pytest fixture 隔离 | 🟡 P1（v40 预存 · 需要深入调研） |

**累计 failed 分类**：
- A test_digest_api 8 + G TestCheckTasksBoldTolerance 3 + I metrics_endpoint 1 = **12 个可直接修复（业务 / fixture 隔离）**
- B test_dataset_integrity 2 + C test_eval 12 + D composite_score 1 + E push_daily 3 + F select_top_n 3 = **21 个需要深入调研**
- 总计 **33 failed** + 1 failed (test_digest_llm injection) = **34 failed**

### 3.3 触发（追溯）
- v40 启动时 P1-9 任务实施过程中 v1.2 加严 L1/L2 分层 → 老 fixture 没声明 layer → 回归 3 个
- v40 继承 v39 之前的 conftest fixture · event loop 跨测试污染问题在 v40 重现
- v40 数据库 schema 与 fixture 数据不匹配（FK 约束失败）
- TestDailyAPI 用 AsyncMock.side_effect=StopAsyncIteration 模拟异步异常 · 但跨测试 event loop 不一致触发 StopAsyncIteration 异常
- test_metrics_endpoint.py::test_metrics_returns_timings_after_timing_call 期望 push_latency_ms 字段存在 · 但 v40 baseline pytest 直接 import · 不通过 uvicorn 启动触发业务调用 → digest_metrics.timings["push_latency_ms"] 仍为空

---

## 4. 最近相关改动

按 `git log --oneline feature/v39-ci-autofix..feature/v40-product-foundation | wc -l`：**38 个 commit**

关键 commit：
- `dde8c4f` docs(research): P0 stub 修复 调研 v1.0
- `ebbb091` feat(metrics): push_daily 接入 digest_metrics inc + 新建 tests/utils/test_metrics.py
- `9375497` feat(checker): T4 + T5 修订 checker + 7/7 PASS（含 § 9 校验扩展）
- `26acc07` feat(checker): check-step.py tasks § 9 埋点挂载点校验
- `316a991` docs(retro): 写 retro.md 5 段
- 其他 v40 之前的 commit（CI auto-fix + 任务治理 Gate + 测试基础架构 + 等等）

---

## 5. 风险评估

| 风险 | 等级 | 缓解 |
|---|---|---|
| 修 test_digest_api.py 引入新回归 | 🔴 P0 | 一次只修一个失败（5 个 TestCase）· 每修一个跑全量 pytest 看 |
| 修 event loop 跨测试污染涉及 conftest.py | 🔴 P0 | conftest 是 v40 共享基础设施 · 改前看 v1.2 优雅降级是否仍生效 |
| 修 test_eval/* 涉及 fixture 数据集修改 | 🟡 P1 | eval fixture 与数据集文件关联 · 先看数据集完整性 |
| 修 composite_score 阈值涉及业务逻辑 | 🟡 P1 | 业务逻辑改动可能影响 V4 AI 推送用户感知 |
| conftest.py v40 预存阻断 | 🟢 P2 | 已用 `--noconftest` 跑 T-P0.2 6/6 PASS（验证优雅降级仍生效） |

---

## 6. 6 步路径建议（fix-mini）

按 AGENTS.md § 0.1 fix-mini 路径（0→4→6）：

### 6.1 0 步调研（当前 · 已完成）

- ✅ 任务理解（用户授权）
- ✅ 复现路径（34 failed 已分类）
- ✅ 影响范围（≥ 6 文件）
- ✅ 根因假设（3 类 · v1.2 加严回归 + event loop + LLM 漂移）
- ✅ 最近相关改动（v40 = v39 + 38 commit）
- ✅ 风险评估 + 缓解（5 项）
- ✅ 6 步路径建议（本节）

### 6.2 4 步实施（等用户确认 · 估时 2-4h）

按优先级分 4 批实施：

**批 1：P1-9 v1.2 加严回归修复**（15 min · 3 failed）
- 修 `tests/test_check_step.py::TestCheckTasksBoldTolerance` 3 个 fixture 加 `layer: L1` 字段

**批 2：test_digest_api.py event loop 污染 + FK 修复**（30-60 min · 8 failed）
- 加 autouse fixture `reset_event_loop()` 在每个测试前清理 anyio 跨 loop 状态
- 修 fixture user_id（用动态生成的用户 + 配套 users 表插入）
- 或：用 SQLite in-memory 替代 pymysql + 真实 MySQL（隔离）

**批 3：test_digest_push_daily + test_digest_select_top_n 业务回归**（30-60 min · 6 failed）
- 调研 composite_score 阈值（默认 0.75 · 测试期望 daily_id 非 None）
- 修 fixture 数据（确保有 ≥1 条 item 过阈值）
- 修 select_top_n 阈值 / diversity 逻辑（v40 继承自 v39 之前代码）

**批 4：test_eval/* LLM 漂移修复**（1-2h · 13 failed）
- 调研 fixture 数据集完整性（`tests/eval/test_dataset_integrity.py` 先修）
- 修 LLM 调用 fixture 或 mock 真实 LLM 响应
- 或：标记为 expected_failure（xfail）· 留待后续 LLM 模型升级时修复

### 6.3 6 步复盘（估时 15 min · 5 段 retro）

按 § 6.6 retro 5 段：
- 1. 数据（commit / failed 数 / 时间）
- 2. 做对（最小 diff · 4 批实施 · 优先级排序）
- 3. 做错（如果有）
- 4. 改进（v40 pytest 治理 gap · pre-commit pytest gate 应允许 PRE_COMMIT_SKIP）
- 5. 沉淀（memory feedback · fixture 隔离 · 优先级排序）

---

## 7. 决策点（待用户确认）

按 § 一 双 gate · 0 调研完成 + 等用户确认进入 4 步：

- **D1**：按上述 4 批优先级实施（批 1 v1.2 加严 → 批 2 digest_api → 批 3 push_daily → 批 4 eval · 推荐）
- **D2**：先 D2 baseline pytest 看哪些失败已消失（部分失败可能因 P0 stub 修复已自动消失）
- **D3**：缩小范围（只修批 1 v1.2 加严 + 批 2 digest_api · 跳过批 3+4 eval/push_daily 跨任务）

按 § 6.7 实施自校验：writer + verifier 双 agent · 4 步实施后启动 verifier

按 § 6.10 AI Agent Security 4 关：本任务不涉及（无 CI/CD / 密钥 / 网络 / 高权限 · 仅测试基础设施修复）

---

## 8. 落地追踪

| 维度 | 状态 |
|---|---|
| 0 调研 | ✅ 已完成（research.md v1.0） |
| 4 实施 | 🟡 等用户确认 |
| 6 复盘 | 🟡 4 步后启动 |
| v40 议题状态 | 🔴 已登记 · 仍独立 P0（修复进行中） |
| docs/issues.md 同步 | 🟡 实施完更新 |

---

**调研产物已 commit · 等用户确认进入 4 步实施**