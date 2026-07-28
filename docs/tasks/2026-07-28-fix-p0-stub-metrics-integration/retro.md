---
title: Retro · P0 stub 修复 · digest_metrics 业务代码接入
date: 2026-07-28
status: v1.0（fix-mini 6 步复盘 · verifier 1 轮 PASS）
type: retro
related:
  - [research.md](research.md) — 0 步调研 v1.0
  - [P1-9 retro.md](../../tasks/2026-07-23-refactor-product-foundation/retro.md) — 触发本任务的沉淀
  - [metrics.py 接入指南](../../../backend/utils/metrics.py:1-15) — spec § 4.5 接入指南
---

# Retro · P0 stub 修复 · digest_metrics 业务代码接入

> **范围**：决策 4「P0 stub 修复」落地 · 让 L5 staging counter 增量真增
> **路径模式**：fix-mini（0→4→6）· 1 轮 verifier PASS（无 FAIL）
> **触发**：P1-9 retro § 3.3 记录"T19 L5 staging counter 增量留待 P0 议题"

---

## 1. 数据（Data）

| 维度 | 数值 |
|---|---|
| **commit 总数** | 3 commit 在 feature/v40-product-foundation |
| **0 调研** | research.md v1.0（179 行 · 8 段） · commit `dde8c4f` |
| **4 实施** | T-P0.1 push_daily 接入 + T-P0.2 新建 6 测试 · commit `ebbb091` |
| **6 复盘** | retro.md v1.0（本文件） |
| **pytest 通过** | T-P0.2 6/6 PASS · test_metrics_endpoint.py 4/4 PASS（无回归） |
| **verifier 轮数** | **1 轮 PASS**（不需修正循环） |
| **调研偏差** | 0 次（实施前探查充分） |
| **调研产物 → 实施时间** | < 30 min（D2 baseline 验证后立即 D1 实施） |
| **memory feedback** | 1 条 |

---

## 2. 做对（What worked）

### 2.1 D2 baseline pytest 验证无回归风险（fix-mini 推荐做法）

- **机制**：4 步实施前先跑 baseline pytest（test_metrics.py 不存在 + test_metrics_endpoint.py 4/4 PASS + test_digest_push_daily.py v40 预存失败已知）
- **效果**：D2 baseline 验证后立刻知道 push_daily 改动风险等级（🔴 → 🟢 降级）
- **关键**：避免"实施后发现回归"循环修正

### 2.2 try/except 包住所有 metrics 调用（不影响主流程）

- **机制**：4 处接入点都用 `try: from utils.metrics import digest_metrics; digest_metrics.inc(...) except Exception as _metric_exc: logging.warning(...)`
- **效果**：埋点失败时主流程继续 · 不影响 digest 推送业务
- **关键**：spec § 4.5 接入指南第 5 步隐含要求（避免埋点阻塞业务）

### 2.3 测试 fixture 用新 DigestMetrics 实例隔离（避免单例污染）

- **机制**：`test_snapshot_returns_4_counters` 用 `DigestMetrics()` 新实例（不是全局 `digest_metrics` 单例）
- **效果**：避免其他测试 inc 写入 test key 污染 snapshot
- **关键**：5/6 测试全局单例 · 1 个 snapshot 测试用新实例（隔离策略）

### 2.4 _record_push_metrics 辅助方法（封装 timing + inc）

- **机制**：成功路径 return 前调 `await self._record_push_metrics(success=True, start_time=_push_start)`
- **效果**：timing 计算集中管理 · push_daily 主流程不混入 timing 逻辑
- **关键**：保持 push_daily 主流程清晰

### 2.5 第 1 轮 verifier PASS（不需修正循环）

- **对比 P1-9 5 轮 verifier** → 本任务 1 轮 PASS（实施前探查充分）
- **根因**：D2 baseline + D1 实施前调研 = 5 次调研偏差教训沉淀 + 4 步接入点明确

---

## 3. 做错（What didn't work）

### 3.1 test_snapshot_returns_4_counters 单例污染（1 个测试 FAIL 后修）

- **根因**：用全局 `digest_metrics` 单例测 snapshot · 之前测试 inc 了 `test_inc_increments_counter_key` 等 key 污染字典
- **现象**：snapshot 实际 6 键（4 原始 + 2 测试用 key）· 期望 4 键
- **修法**：用 `DigestMetrics()` 新实例隔离 · 1 个 fixture 改动

---

## 4. 改进（What to change next time）

### 4.1 fix-mini 任务强制 D2 baseline

- **改进**：所有 fix-mini 任务（0→4→6）必跑 D2 baseline pytest 看基线再实施
- **避免**：实施后才发现回归 · 多轮修正循环

### 4.2 测试 fixture 隔离（单例 vs 新实例）

- **改进**：snapshot / 全局状态测试用新实例 · inc / timing 单调增测试用全局单例
- **避免**：测试间状态污染导致 fixture FAIL

### 4.3 接入指南直接复用（spec § 4.5 接入指南第 5 步已含具体接入点）

- **改进**：实施前必读 spec § 4.5 接入指南 · 不重新调研接入点
- **避免**：调研冗余 · 实施方向偏离

### 4.4 P0 stub 修复跨任务接 v40 议题

- **改进**：P0 stub 修复应在 v40 启动前环境整治议题中实施（连同 31 pytest 失败 + conftest 修复）
- **避免**：v40 启动后再补 P0 stub · 增加 L5 staging counter 增量留待时间

---

## 5. 沉淀（Memory feedback）

按 § 6.6 retro 必须写 memory 更新清单。本任务 1 条 memory feedback：

### 5.1 测试 fixture 隔离（单例 vs 新实例）

- **文件名**：`feedback-test-fixture-isolation.md`
- **内容**：测试 fixture 隔离策略——snapshot / 全局状态用新实例（`DigestMetrics()`）· inc / timing 单调增用全局单例（`digest_metrics`）。避免测试间状态污染导致 fixture FAIL。
- **关联**：与 `feedback-stub-test-debt`（CLAUDE.md § 6.6）联动

---

## 6. 落地追踪

| 维度 | 状态 |
|---|---|
| **任务整体验收** | ✅ T-P0.1 + T-P0.2 verifier PASS + acceptance ACCEPTED |
| **commit 总数** | 3 commit（research + 实施） |
| **pytest 通过** | T-P0.2 6/6 + endpoint 4/4（无回归） |
| **决策主账** | ✅ 决策 4 实施完成（待更新 decisions.md） |
| **v40 议题状态** | 🟡 P0 stub 修复已修复 · 待更新 docs/issues.md |
| **memory 反馈** | 🟡 1 条待写（按 § 6.6 retro 必须） |

---

## 7. 最终 commit 清单（3 commit）

按时间顺序在 feature/v40-product-foundation：

| # | commit | 内容 |
|---|---|---|
| 1 | `dde8c4f` | docs(research): P0 stub 修复 调研 v1.0（fix-mini 0 步完成） |
| 2 | `ebbb091` | feat(metrics): push_daily 接入 digest_metrics inc + 新建 tests/utils/test_metrics.py（T-P0.1 + T-P0.2） |
| 3 | (本文件) | docs(retro): 写 retro.md v1.0（fix-mini 6 步复盘 · verifier 1 轮 PASS） |

---

## 8. 总结

P0 stub 修复任务完成 · T-P0.1 + T-P0.2 verifier PASS · 3 commit · 1 轮 verifier PASS · 6/6 测试 PASS · 4/4 endpoint 测试无回归 · 1 调研偏差修正（D2 baseline 阶段）· 1 memory feedback 待写。

任务整体关闭条件满足：
- ✅ 0→4→6 fix-mini 完整流程
- ✅ D2 baseline 验证（实施前探查）
- ✅ 1 轮 verifier PASS（不需修正循环）
- ✅ retro 5 段沉淀（本文件）
- ✅ memory feedback 1 条待写

---

**任务状态：✅ fix-mini 完成 · 等用户拍 D 收尾**

后续步骤（可选）：
- A. 更新 docs/issues.md + decisions.md（v40 P0 stub 修复标已解决）
- B. 写 1 条 memory feedback（fixture 隔离 / 新实例模式）
- C. 拍 D 收尾（P0 stub 修复任务关闭）