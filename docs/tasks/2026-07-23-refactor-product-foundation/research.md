# ♻️ 调研报告 · 重构：产品基础（问题证据 + 指标字典 + 埋点任务）

> 日期：2026-07-23 · 调研人：Claude Code + 4 个独立对抗 Agent
> 路径模式：`refactor-6`
> 当前阶段：0 调研完成 · 自动执行授权下采用单一推荐 · 未进入设计/实施

## 1. 任务理解

- **用户授权**：循环处理 P1+P2 17 项，自动决策，无需用户确认。
- **P1-7**：product-doc 模板与已实施实例都缺 baseline 锚点；CI auto-fix verify.md L4/L5 缺失但仍标"🟢 可进入 6 步"；issues-audit 任务无 verify.md；interview 用户角色碎片化。
- **P1-8**：8 必填 + 4 可选字段双层指标字典；与议题 F 脱钩。
- **P1-9**：T19 实际 dead code；trace_id race（**注：2026-07-27 探查发现 trace_id 模块不存在，已修正为 logger 字段注入**）；audit 9 任务全无埋点；tasks-template 缺 § 9 段。
- **反方关键纠正**：单人项目 / 用户群未稳 / 多数功能未跑通，立即要求完整字典会产生形式主义。
- **目标**：分层 L0-L3 治理产品基础；不实施代码。
- **边界**：不引入分析平台；不动业务表 schema；不立即全量要求完整字典。

**调研前置基线**（实施前必跑）：
- 读 `docs/issues.md`（议题主账）
- 跑 `git log -10`（最近相关改动）
- 跑 `git status`（看 unstaged / 多 agent 冲突）

## 2. 现状分析

### 2.1 P1-7

1. `product-doc-template.md:99` 价值主张示例"DAU +15%"无当前 DAU 数字
2. CI auto-fix product-doc.md:86-90 5 个指标无 baseline_value
3. `spec.md:56` "P95 < 200ms"无当前 P95
4. issues-audit 任务无 verify.md（11 个文件，缺 § 5 验证阶段）
5. V4 任务 docs/issues.md 自承 verify.md 不存在
6. CI auto-fix verify.md L4 🟡 + L5 ❌ 但 L257 仍标"🟢 可进入复盘"
7. interview 角色碎片化：3 任务 3 persona

### 2.2 P1-8

1. 模板 + 已实施实例都缺 8 个核心字段（metric_id / formula 解析 / 分子事件 file:line / 分母事件 file:line / dedup / baseline / owner / failure_action）
2. 议题 F 关闭条件与产品指标字典完全脱钩
3. DigestMetrics 4 counter 与 5 产品指标 schema 错位
4. 5 项产品指标（打开率 40% / 读完率 60% / 收藏率 10% / 屏蔽率 5% / 30 天留存 30%）未验证

### 2.3 P1-9

1. T19 自承 dead code（`backend/utils/metrics.py:1-9` docstring 确认 · 列出 5 步接入指南）
2. **trace_id 模块根本不存在**（`backend/utils/` 只有 `logger.py` + `metrics.py` 2 文件 · 4 个独立 Agent 调研盲点 · 2026-07-27 实施前探查发现）
3. 0 调用方 in backend 业务代码（业务代码全无 `digest_metrics.inc()` 调用 · T19 后续没接进 call site）
4. backend/utils/logger.py 已有 logger 基础设施（无 trace_id 字段注入）
5. RateLimitMiddleware 类存在未注册
6. audit 9 任务全无埋点挂载
7. tasks-template.md 缺 § 9 段
8. 唯一埋点是 console.log（`AIRecommendationCard.tsx:21-33`）

**🔴 调研偏差修正（2026-07-27 实施前探查）**：
- 原 § 2.3 "trace_id 模块全局 race" 不成立 — 模块不存在
- 影响范围：spec SCN-P1.9.1/.2 + spec §4.4 + plan §4 决策 4 + tasks T9-T10 + TC-5
- 修正方向：trace_id 实施合并入 logger 字段注入（仍用 `contextvars.ContextVar` 但通过 `logging.Filter` 注入到现有 `logger.py`）
- 选项 A 用户决策（2026-07-27）：立即修正 spec/plan/tasks · T9 改写为 logger.py 加 `TraceIdFilter` + `trace_id_var` · T10 改写为 `tests/test_logger_trace_id_field.py` 真跑

**🔴 v1.2 调研偏差修正（2026-07-27 T4 实施前 verifier FAIL 发现 4 项）**：

| # | 偏差 | v1.1 假设 | 实际 | 修正方向 |
|---|---|---|---|---|
| 1 | counter 键错误 | spec 写 `push_total / interview_session_started / collect_success / collect_failure` | `backend/utils/metrics.py:32-37` = `push_total / push_failed / fetch_failures / rsshub_routes_broken` | spec + tasks 改写 · api-spec 保留 |
| 2 | T4 checker 已存在 | "T4 新建 scripts/check-product-doc.py" | 2026-07-25 v2 P2-3 决策 1/5 已建（1730 bytes 旧版）| T4 = 修订（v0 框架 + 加 product_baseline frontmatter）|
| 3 | logger.py 已有 trace_id | "logger 无 trace_id 字段" | `TraceFilter` + `setup_logger` 已实现（仅 `global _trace_id` 有 race）| T9 = 改 `global _trace_id` → `contextvars.ContextVar`（v1.1 已部分修正）|
| 4 | 30 pytest 失败基线 | （未涉及）| 30 failed / 817 passed · v40 预存在 · 与 T1-T3 无关（纯文档）| 登记 issues.md 独立 P1 议题（v40 启动前环境整治）|

- 选项 A 用户决策（2026-07-27）：修正 spec/plan/tasks + 修订 T4 + 实施 T4-T5
- 详细：[`decisions.md` 决策 3](decisions.md#决策-3--v12-调研偏差修正4-项偏差--实施-t4-时-verifier-fail-发现)

### 2.4 反方纠正

1. 单人项目 / 用户群未稳 / 多数功能未跑通
2. 立即要求完整字典会产生形式化但虚的形式主义
3. 应分层 L0-L3 而非一刀切
4. 5 项产品指标（40% 等）数字未验证

## 3. 重构方案

| 方案 | 结论 |
|---|---|
| 3 项独立任务 | ❌ 共享模板与埋点表 |
| 立即要求所有功能完整字典 + 独立埋点任务 + 问题证据 | ❌ 反方证据：形式主义 + 边际成本高 |
| **分层 L0-L3 治理 + 模板最小 diff**（**推荐**: 方案 A） | ✅ 自动采用 |

**推荐方案 A 理由**：
1. 决策 1 明确"模板最小 diff" · 方案 A 改 3 个模板段
2. 独立字典文件 `docs/metrics/<id>.yaml` 易维护 + 易 git diff
3. 复用 v39 pre-commit DOD checker 基础设施

### 3.1 P1-7 · 问题证据与基线（决策 1）

**产品脑 baseline 字段**（product-doc-template.md § 0/§ 2/§ 5 必填扩展）：

```yaml
product_baseline:
  problem_evidence:
    - file: <绝对路径>
      line: <行号>
      quote: <原文片段 ≤ 80 字>
      baseline_value: <数字 / "N/A">
      baseline_source: <git_commit | 实测命令 | 估算>
  target_user:
    role: <人/产品/开发者>
    persona_count: <1-N>
    frequency_per_week: <数字>
    device: <桌面/移动/混合>
    network: <高带宽/低带宽/N-A>
  kill_criteria:
    - name: <短名>
      trigger: <什么条件下算 kill>
      evidence: <如何验证 kill>
  dangerous_assumptions:
    - hypothesis: <假设描述>
      falsification: <如何证伪>
      risk_level: 🔴/🟡/🟢
```

**模板加 4 段**：
- § 0 "调研前置必填"：3-5 条 `product_baseline.problem_evidence` + 1-3 条 `kill_criteria`
- § 2 角色表加 4 列（频次/设备/网络/语种）
- § 5 成功指标每条前加 `baseline_value`
- 新建 `scripts/check-product-doc.py`（解析 frontmatter，3 段非空校验）

### 3.2 P1-8 · 成功指标字典（决策 2 · 分层 L0-L3）

**L0（内部/一次性）**：不要求字典。
**L1（探索性）**：1 句话问题假设 + 证据等级（本人痛点/观察/二手/真实访谈）+ 1 核心成功信号 + ≤3 事件
**L2（核心闭环）**：1 北极星 + 2-3 护栏 + 事件清单 + 分母/窗口/去重/身份 + 埋点测试 + SQL 查询
**L3（稳定用户）**：完整字典 + dashboard + cohort + 数据质量 + 隐私/保留 + owner + 决策日志

**8 必填字段**（L2/L3 触发）：
- metric_id（正则 `^[a-z][a-z0-9_]{2,40}$`）
- metric_name
- formula
- num_event（带 file:line）
- den_event（带 file:line）
- dedup（primary_key + window）
- target（value + deadline + source）
- failure_action（≥ 1 条 ≥ 30 字符）

**4 可选字段**（L3 触发）：
- current_baseline
- instrumentation_site
- owner
- observed_at

**机器校验**：`scripts/check_metric_dict.py` + pre-commit POSIX exit 兼容。

**P1-7/8/9/10 与 P1-8 一致**：5 项 AI 推送产品指标视为"未验证假设" → 列入 L1 探索性，需先修主路径（L1/L2 进展）再升级 L3。

### 3.3 P1-9 · 埋点任务（决策 3 · 分层 L0-L3）

**L0**：不埋点；只测试 + 日志 + 失败证据。
**L1**：≤ 3 事件；复用业务表；不引入分析平台。
**L2**：每功能任务加 § 9 埋点挂载点（事件 + metric）；commit gate counter 真增断言。
**L3**：埋点 = 实施任务 + events 实测；verifier 启动服务真跑。

**L1 平台层（基础设施）**（**注：T-P1.1 v1.1 修正为 logger trace_id 字段注入**）：
- ~~T-P1.1 trace_id 改 `contextvars.ContextVar`（关 race）~~ → v1.1：`backend/utils/logger.py` 加 `TraceIdFilter` + `trace_id_var` ContextVar
- T-P1.2 startup 接管 `knockwise.*` logger
- T-P1.3 metrics 暴露 `/api/digest/metrics`

**L1 接入层（per-call-site）**：
- 每产品功能任务 `tasks.md` 必须含 § 9 埋点挂载段
- 3 字段：event_name / trigger 位置 / data fields

**测试门禁**（核心创新）：
- counter 真增断言（不是"方法存在"）
- `pytest` 必须验证 `digest_metrics.inc("push_total") == 1`
- L5 staging 启动服务真跑 + counter 增量真断言

**`tasks-template.md` § 9 埋点挂载点段建议**：
```markdown
## 9. 埋点挂载点（涉及事件 / 指标时必填）

### 9.1 事件挂载

| 任务 | event_name | trigger 位置 | data fields |
|---|---|---|---|
| T1 | interview.session_started | services/interview_service.py start() | session_id, user_id, round |

### 9.2 指标挂载

| 任务 | metric_name | inc 调用位置 | 关联 digest_metrics |
|---|---|---|---|

### 9.3 测试门禁

- [ ] 单测断言 counter 真增
- [ ] tasks.md § 6.5 commit 后回写 + events 表格同步
```

## 4. 输出建议

1. P1-7 模板加 baseline 字段 + check-product-doc.py（最小）
2. P1-8 指标字典 L1/L2/L3 分层（与 P1-7 共享模板）
3. P1-9 埋点任务 L1 平台层（**v1.1：logger trace_id 字段注入**）+ L2 接入层（audit 9 任务后补）
4. CI auto-fix verify.md L4/L5 补登记（同步到 docs/issues.md）

**明确排除**：
- 立即要求所有功能完整指标字典
- 引入新分析平台（PostHog/Segment/Mixpanel/GA）
- 改业务表 schema 强埋点
- 修改 `mock_db / mock_cache / mock_llm` 默认行为
- 任何代码实施与提交（0 步止于调研）

## 5. 风险评估

| 风险 | 等级 | 缓解 |
|---|---|---|
| 阈值未验证 5 项 AI 推送指标锁死 | 🔴 P0 | L1 探索性标记，未验证前不固化 · SCN-P1.8.6 硬阻断 L2 升级 |
| audit verify.md 缺失 | 🟡 | docs/issues.md 决策段补登记 |
| T19 dead code 复制 | 🟡 | counter 真增断言门禁（TC-6） |
| 单人项目承担过重 | 🟡 | L0 不要求，L1 最小 |
| Goodhart 风险 | 🟡 | 配定性证据；指标变更需决策日志 |
| trace_id 调研偏差（v1.1 已修正） | 🟡 | 实施前探查 + 选项 A 修正 spec/plan/tasks |

## 6. 自动决策清单

| 日期 | 决策项 | 选择 | 状态 | 授权原话 | 关联 |
|---|---|---|---|---|---|
| 2026-07-23 | P1-7 + P1-8 + P1-9 合并方案（分层 L0-L3） | 分层 L0-L3 治理 + 模板最小 diff + 埋点按层强制 | ✅ 自动决策 + spec v1.1 + plan v1.1 + tasks v1.1 | "循环把上面哪些问题都处理一遍…不需要我确认了" | [`decisions.md` 决策 1](decisions.md) · [spec.md](spec.md) · [plan.md](plan.md) · [tasks.md](tasks.md) |
| 2026-07-27 | 实施前调研偏差修正（trace_id 模块不存在 · 4 Agent 盲点） | 选项 A · 立即修正 spec/plan/tasks · T9-T10 改写为 logger trace_id 字段注入 | ✅ 用户决策 · 文档 v1.1 修正 | "A" | [`decisions.md` 决策 2](decisions.md#决策-2--实施前调研偏差修正trace_id-模块不存在) |
| 2026-07-27 | v1.2 调研偏差修正（4 项：counter 键 / T4 checker 已存在 / logger 已有 trace_id / 30 pytest 基线）| 选项 A · 修正 spec/plan/tasks + 修订 T4 + 实施 T4-T5 | ✅ 用户决策 · 文档 v1.2 修正 | "A" | [`decisions.md` 决策 3](decisions.md#决策-3--v12-调研偏差修正4-项偏差--实施-t4-时-verifier-fail-发现) |

## 自检

- [x] 任务理解、4 个独立 Agent 已核验
- [x] ≥3 相关文件
- [x] 4 个独立 Agent 对抗核验（设计×3 + 反方×1）
- [x] 修正反方事实：单人项目 / 阈值未验证
- [x] 调研前置基线（docs/issues.md / git log / git status）
- [x] 5 段齐全：任务理解 / 现状分析 / 重构方案 / 输出建议 / 风险评估
- [x] 依赖顺序与排除项明确
- [x] refactor-6 路径建议
- [x] v1.1 调研偏差修正（trace_id 模块不存在 · T9-T10 改写）
