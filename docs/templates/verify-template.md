---
title: 验证文档模板（verify）
date: 2026-06-30
updated: 2026-07-22
status: v3
tags: [verify, 5步, L3, L5, 模板]
related:
  - [test-cases-template.md](test-cases-template.md)
  - [tasks-template.md](tasks-template.md)
---

# 验证文档模板（verify.md）

> **一句话**：步骤 5 只完成 L3 整合测试和 L5 staging；L1/L2/L4 已在步骤 4 分布式完成。
>
> **作者**：AI 主导证据收集，人确认运行结果。
>
> **对应 DOD**：`docs/DOD.md` §七。

## 0. 上游证据（必填）

### 0.1 证据元信息

| 字段 | 值 |
|---|---|
| Commit / 工作树 | `<hash / dirty files>` |
| 日期与时区 | `<YYYY-MM-DD HH:mm TZ>` |
| 工作目录 | `<cwd>` |
| 环境 | `<OS / runtime / DB>` |

> 每条命令必须记录原命令、退出码和分类结果。只贴“passed”或人工摘要不算可复现证据。

| 分布式活动 | 证据位置 | 结果 |
|---|---|---|
| L1 类型检查 | `<command / log / commit>` | ✅ / ❌ |
| L2 单元测试 | `<command / test-cases.md>` | `<N passed / coverage>` |
| L4 review / verifier | `<review / verifier result>` | PASS / FAIL |

> 本段只引用步骤 4 已产生的证据，不在步骤 5 重新制造五层 gate。

### 0.2 测试人口径

| collected | passed | failed | skipped | xfailed | xpassed | quality violations |
|---:|---:|---:|---:|---:|---:|---:|
| N | N | N | N | N | N | N |

> `skip` / `xfail` 不计入 passed；测试类、函数或文件数量不得包装成通过数量。

### 0.3 需求追踪矩阵

| Requirement | 生产代码 | 自动化测试 | 失败时哪条断言变红 | 状态 |
|---|---|---|---|---|
| `<REQ-ID>` | `<file:line>` | `<test node id>` | `<oracle>` | PASS / FAIL / BLOCKED |

## 0.4 Traceability Matrix（必填 · per P1-2）

| REQ | SCN | TC | Task | Test Node | Level | E2E Path | Evidence | Metric/Event | Status |
|---|---|---|---|---|---|---|---|---|---|
| REQ-001 | SCN-001 | TC-001 | T8 | backend/tests/e2e/test_digest_push.py::test_full_cron_to_db_to_api_happy | L3 | E2E-001 | EV-001 | METRIC-002:event=digest_read | PASS |

**ID 规则（per P1-2 决策）**：
- `REQ-NNN` Requirement；`SCN-NNN` Scenario（引用 REQ）；`TC-NNN` Test Case（引用 SCN）
- `EV-NNN` Evidence；`METRIC-NNN` Product Metric

**10 条不变量（per P1-2 spec）**：
1. 所有 ID 唯一
2. SCN 引用存在的 REQ
3. TC 引用存在的 SCN
4. Task 至少引用一个 TC + Test Node（`foo.py::test_xxx`）
5. PASS TC 至少有一个 L2/L3/L5 evidence
6. E2E 行有 E2E-* + L3/L4 标记
7. EV-* 退出码 0；BLOCKED 可无 artifact 但需原因
8. Metric 绑定事件 + REQ
9. Requirement 全部必需 TC PASS 才 PASS
10. 禁止仅凭任务 checkbox 或全 pytest 绿判 PASS

## L3 整合测试（必填）

## L3 整合测试（必填）

- **范围**：<API contract / 数据库事务 / 跨模块 / E2E>
- **命令**：`<可复现命令>`
- **环境**：<local integration / test>
- **结果**：PASSED / FAILED
- **耗时**：<X 秒>

### 场景

| 场景 | 期望 | 实际 | 证据 | 结论 |
|---|---|---|---|---|
| <场景 1> | <期望> | <实际> | `<log / response>` | ✅ / ❌ |
| <场景 2> | <期望> | <实际> | `<log / response>` | ✅ / ❌ |

### Mock 边界账本（API / E2E 必填）

| 层 | Real / Mock | 理由 | 证据 |
|---|---|---|---|
| Scheduler | Real / Mock | `<why>` | `<test/fixture>` |
| Service | Real / Mock | `<why>` | `<test/fixture>` |
| ORM / Database | Real / Mock | `<why>` | `<DB name/assertion>` |
| API | Real / Mock | `<why>` | `<request/response>` |
| RSS / LLM / Email / Clock | Real / Mock | `<why>` | `<provider fixture>` |

> 名为 E2E 的测试若 Mock 了目标 Scheduler、Service、ORM、数据库或 API handler，必须降级命名，不能记为真实 E2E。

### 反证与生命周期

- **故意破坏核心逻辑**：`<mutation / 临时反转条件>`
- **预期红灯**：`<test node id + failure>`
- **恢复后结果**：`<command + exit code>`
- **启动 / 关闭**：`<结果与日志>`
- **重复执行 / 进程重启幂等**：`<结果与数据库证据>`

## L5 staging 运行时验证（必填）

- **环境**：<staging / 本机完整服务；不得只写单元测试环境>
- **启动方式**：`./scripts/start.sh`
- **验证人**：<姓名>
- **日期**：YYYY-MM-DD
- **结果**：PASSED / FAILED

### 真实路径

| 用户路径 | 操作步骤 | 期望 | 实际 | 截图/日志 | 结论 |
|---|---|---|---|---|---|
| <路径 1> | <1...2...> | <期望> | <实际> | `<path>` | ✅ / ❌ |

## 失败与残留风险（必填）

- **失败项**：<无 / 具体项>
- **未覆盖项**：<无 / 具体项及原因>
- **残留风险**：<风险 + owner + 后续动作>

> 无法运行、依赖缺失或没有证据时必须写 FAILED/BLOCKED，不得写成通过。

## 文档事实对账（必填）

- [ ] `tasks.md` 状态与本次证据一致
- [ ] `verify.md` 数量与命令原始输出一致
- [ ] `retro.md` 已覆盖过时结论或明确标注历史快照
- [ ] `docs/issues.md` / milestones 未提前关闭
- [ ] GitHub required checks 已配置；若未配置，已明确记录为外部待办

## 用户验收（必填）

- **结论**：✅ 验证完成 / ❌ 退回步骤 4
- **确认人**：<name>
- **确认日期**：YYYY-MM-DD

## 🎯 硬性 DOD

- [ ] 已引用步骤 4 的 L1/L2/L4 证据
- [ ] L3 整合测试通过且有可复现命令
- [ ] L5 staging 真实路径通过且有日志/截图/浏览器证据
- [ ] 期望与实际逐项记录，失败没有被隐藏
- [ ] 测试计数分类记录，没有把 skip/xfail/测试类计入 passed
- [ ] 需求追踪矩阵与 Mock 边界账本完整
- [ ] 核心逻辑有“破坏后变红”的反证，运行时启动/关闭/重启已覆盖
- [ ] tasks / verify / retro / issues 状态完成事实对账
- [ ] 用户明确确认验证完成

> 任一项未满足，verify.md 不算完成，不能进入步骤 6 复盘。

## 相关文档

- [test-cases-template.md](test-cases-template.md)
- [tasks-template.md](tasks-template.md)
- `docs/DOD.md` §七
