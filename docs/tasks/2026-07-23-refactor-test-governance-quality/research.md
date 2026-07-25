# ♻️ 调研报告 · 重构：测试治理与质量（xfail / AI 评估 / a11y+性能）

> 日期：2026-07-23 · 调研人：Claude Code + 4 个独立对抗 Agent
> 路径模式：`refactor-6`
> 当前阶段：0 调研完成 · 自动执行授权下采用单一推荐 · 未进入设计/实施

## 1. 任务理解

- **用户授权**：循环处理 P1+P2 17 项，自动决策，无需用户确认。
- **P1-4**：4 个 `xfail` 均为 `strict=False`，AST gate 不识别 `xfail`，pytest 全局无 `xfail_strict`，issue 关联过粗。
- **P1-5**：AI 系统 5 入口契约松散，仅 `digest_llm` 有 timeout + 严格 schema，4/5 入口无 eval 体系。
- **P1-6**：a11y 4 P0 运行时违规（VoiceRoom PTT / SidebarGroup 假按钮 / Layout mobileOpen 死代码 / 对比度），0 个 axe/jest-axe/lighthouse/web-vitals 集成，CI 缺 6 个 gate。
- **目标**：建立 xfail 元数据契约、离线 AI eval 体系、a11y+性能非功能测试契约。
- **边界**：不实施代码；不改 mock 默认行为；不动 seed_data；不引入新测试框架；不立即把 4 个 a11y/perf gate 设 hard。

## 2. 现状分析

> 章节别名：调研证据 § 现状扫描 / 现状分析（refactor-6 路径下统一视角）。

### 2.1 xfail

1. 4 个 `xfail` 全部 `strict=False`：test_digest_push_daily.py:73-77, 109-113, 174-178；test_digest_select_top_n.py:37-41
2. reason 都只写"docs/issues.md 债务 9"，但债务 9 是大议题，不稳定
3. `check_test_quality.py:66-73` 只匹配 `.skip`/`.skipif`，不识别 `xfail`
4. `pyproject.toml:13-16` pytest 配置无 `xfail_strict = true`
5. 当前 695 passed / 4 skipped / 4 xfailed / 0 failed

### 2.2 AI eval

1. 5 入口：evaluate_agent / report_agent / followup_match / followup_text / qa_service / digest_llm
2. 4/5 无 timeout，4/5 无严格 schema
3. 共用 `settings.llm_model`，单点升级需双 model 回归
4. `test_digest_llm.py` 是唯一完整契约参考（4 case）
5. `conftest.py:159-170` `mock_llm` 只 patch `qa_service._get_llm`，不覆盖其他 4 入口

### 2.3 a11y + 性能

1. 4 P0 运行时违规
2. 0 axe / jest-axe / pa11y / lighthouse / web-vitals / browserslist 集成
3. CI 3 步：Vitest / tsc / build，无 a11y / perf
4. 暗色主题大量 rgba 硬编码，无对比度审计
5. 响应式仅 1 断点，Layout mobileOpen 死代码
6. LiveKit + MediaRecorder Safari iOS 风险未声明

## 3. 重构方案

> 章节别名：方案比较（refactor-6 路径下统一视角）。

### 3.1 方案比较

| 方案 | 结论 |
|---|---|
| 3 项独立任务 | ❌ 共享 xfail budget / 数量治理 / AST gate |
| YAML registry / pytest plugin | ❌ 引入外部依赖 |
| 立即把 a11y/perf/AI eval 全设 hard gate | ❌ 反方证据：基础薄弱 + CI 不稳 |
| **静态 metadata + 全局 strict + 离线 contract + report-only** | ✅ 自动采用 |

## 4. 单一推荐

### 4.1 P1-4 · xfail/skip 治理（决策 1）

**静态 marker 契约**：

```python
@pytest.mark.xfail(
    reason=(
        "owner=backend-digest; "
        "issue=docs/issues.md#digest-diversity-selection; "
        "expiry=2026-08-15; "
        "reason=select_top_n diversity constraints are not implemented"
    ),
    strict=True,
)
```

| 字段 | 规则 |
|---|---|
| `owner` | 非空、稳定（不写 agent 临时名） |
| `issue` | 指向具体可关闭 issue，不写"债务 9"等大议题 |
| `expiry` | ISO `YYYY-MM-DD`，到期当天 gate 失败 |
| `reason` | 根因描述，不只是"test fails" |
| `strict` | xfail 必须 `True` |

**pytest 全局**：`pyproject.toml` 设 `xfail_strict = true`。

**AST gate 扩展**（`check_test_quality.py`）：
- 识别 decorator + runtime `skip` / `xfail`
- reason 必须静态字符串
- 解析并验证 4 字段
- `xfail` 必须 `strict=True`
- `expiry <= today` 即 violation
- 数量预算比较

**新 violation code**：
- `test-debt-metadata`
- `xfail-not-strict`
- `test-debt-expired`
- `test-debt-budget-exceeded`

**数量预算（只降不升）**：
- `xfail budget = 4`（当前基线）
- `skip budget = 当前受治理 skip 数`
- 任何 PR 不能增加数量；删除 marker 后立即下调预算

**当前 4 条迁移**：
- 3 个 push_daily xfail：共用一个具体 issue，`backend-digest` owner，统一较短 expiry
- 1 个 diversity xfail：独立 issue
- 全部 `strict=True`

### 4.2 P1-5 · AI 评估（决策 2）

**107 case 离线数据集**（`backend/tests/eval/datasets/interview_eval_v1.jsonl`）：

| agent | case 数 |
|---|---|
| evaluate_agent | 30 |
| report_agent | 10 |
| followup_match | 20 |
| followup_text | 15 |
| qa_service | 20 |
| digest_llm | 12 |
| **合计** | **≈107** |

**7 个评估维度**（含硬/软 gate 区分）：

| 维度 | gate 类型 | 阈值 |
|---|---|---|
| 追问相关性 | 软 ≥ 75% / 硬 ≥ 60% | — |
| 评分稳定性 | 硬 | 方差 = 0（temp=0）/ ≤ 1（temp=0.3） |
| 结构化输出成功率 | 软 ≥ 99% / 硬 ≥ 95% | — |
| 幻觉（digest 引入新实体） | 硬 | 0 引入 |
| 评估盲幻觉 | 硬 | 0 越界 |
| Prompt 注入 | 硬 | score 不变 + 盲区反映真实 |
| P95 延迟 | 软 ≤ 8s / 硬 ≤ 15s | — |
| Token 成本 | 趋势 | 不设硬 gate |
| 模型回归 | 硬 | ≥ 3/5 维度不退化 |

**CI 集成**：
- commit gate：digest 12 case + evaluate 5 case（最高 ROI 子集）≈ 30s
- nightly：全量 107 case + 双 model 回归 ≈ 5-10min
- 模型升级 PR：手动 `pytest -m regression`

**EvalCaseResult schema**：
```python
{
  "case_id": "eval-001",
  "agent": "evaluate_agent",
  "passed": bool,
  "metrics": dict,  # score_variance, p95_latency_ms, prompt_tokens, completion_tokens, json_parse_ok
  "invariant_failures": list[str],
  "fallback_used": bool,
  "raw_response": str  # 截断 500 字符
}
```

### 4.3 P1-6 · 可访问性与非功能测试（决策 3）

**9 维度契约（报告型首版）**：

| 维度 | 契约 | 阈值 | 校验 |
|---|---|---|---|
| 键盘导航 | `role="button"` 非 `<button>` 必须 tabindex+Enter/Space | 100% | axe `button-name` + 自定义 |
| 焦点环 | 所有可交互 `:focus-visible` ≥ 2px outline | 100% | axe + 截图 |
| Skip navigation | Layout 顶部 skip-link | 1 处 | Playwright Tab |
| 屏幕阅读器 | 数据可视化 `<title>`/`<desc>` 或 sr-only | 100% | axe |
| 状态 live region | 状态切换 + AI 字幕 + 录音 | 100% | axe + 自定义 |
| 对比度 | WCAG AA 4.5:1 / 3:1 | 100% | axe `color-contrast` |
| 响应式断点 | 3 档：mobile < 768 / tablet 768-1024 / desktop ≥ 1024 | 3 viewport | Playwright 3 projects |
| Lighthouse | Performance ≥ 85 / A11y ≥ 95 / BP ≥ 90 / SEO ≥ 80 | 4 项全过 | `@lhci/cli` |
| Web Vitals | LCP < 2.5s / FID < 100ms / CLS < 0.1 / INP < 200ms | 4 项 | web-vitals v4 + reportWebVitals |
| 浏览器兼容 | browserslist 默认 + Safari iOS ≥ 15 显式 | manifest | `npx browserslist` + Playwright webkit |

**首版 6 gate 全部 report-only**（不阻断 merge）：

| Gate | 触发 | 状态 |
|---|---|---|
| axe-core Playwright 4 页 | 新 CI job `a11y-axe` | 🟢 report-only |
| Vitest jest-axe 6 组件 | 单测加 axe 断言 | 🟢 report-only |
| Playwright 3 viewport | mobile/tablet/desktop | 🟢 report-only |
| Lighthouse CI 4 项 | `@lhci/cli` | 🟢 report-only |
| web-vitals 上报 | `_app.tsx` console-only | 🟢 report-only |
| `.browserslistrc` 检查 | pre-commit 本地 | 🟡 local-block |

**晋升时机**：观察 ≥ 20 次 + 0 flake + 命中阈值后晋升 required。

## 5. 依赖顺序

1. P1-4 xfail 治理（最小、零行为变化）
2. P1-5 AI eval 基础设施（落地 107 case）
3. P1-6 a11y/perf（先报告型，20 次后晋升）

## 4. 风险评估

> 章节别名：风险与缓解（refactor-6 路径下统一视角）。

### 调研证据锚点

- [`docs/issues.md`](../../issues.md) 已查阅（决策 #31 · 债务 #19）
- `git log -10 -- backend/` + `git log -10 -- frontend/` 最近 10 次相关提交已交叉对照
- `git status` 确认当前 staging 区无未提交冲突（重构任务在独立子目录推进）

| 风险 | 等级 | 缓解 |
|---|---|---|
| 老 xfail 迁移需改 reason + strict | 🟡 | 一个 PR 完成 + 旧债务 9 解耦 |
| AI eval 离线 case 少 / 漂移 | 🟡 | 每月 review + 漂移监控 |
| a11y/perf 跑全套太慢 | 🟡 | commit gate 30s 报告型，nightly 全量 |
| CI 容量 | 🟡 | P0-4 启用前清理 xfail 后再加 gate |
| 第三方 Action 移动 tag 风险 | 🟡 | pin 完整 40 字符 SHA |
| LLM 接收不可信 CI 日志 | 🟡 | 仅传"失败 job + 错误类型"摘要 |

| 风险 | 等级 | 缓解 |
|---|---|---|
| 老 xfail 迁移需改 reason + strict | 🟡 | 一个 PR 完成 + 旧债务 9 解耦 |
| AI eval 离线 case 少 / 漂移 | 🟡 | 每月 review + 漂移监控 |
| a11y/perf 跑全套太慢 | 🟡 | commit gate 30s 报告型，nightly 全量 |
| CI 容量 | 🟡 | P0-4 启用前清理 xfail 后再加 gate |

## 7. 明确排除

- 立即把 a11y/perf/AI eval 设 hard gate
- 修改 `mock_db / mock_cache / mock_llm` 默认行为
- 修改 `seed_data/digest_sources.json`
- 引入新测试框架（pytest-xdist / testcontainers / pa11y / lhci 之外的 SaaS）
- 任何代码实施与提交

## 5. 输出建议

> 章节别名：自动决策清单（refactor-6 路径下统一视角）。
>
> **承接 § 8 自动决策清单**：以下为调研阶段自动决策的实际落地追踪，按"决策项 / 选择 / 状态 / 授权原话 / 关联"五列记录，便于后续 spec.md / plan.md / decisions.md 引用。

| 日期 | 决策项 | 选择 | 状态 | 授权原话 | 关联 |
|---|---|---|---|---|---|
| 2026-07-23 | P1-4 + P1-5 + P1-6 合并方案 | xfail 静态 metadata + AI 离线 contract + a11y/perf 报告型 | ✅ 自动决策 | "循环把上面哪些问题都处理一遍…不需要我确认了" | [`decisions.md` 决策 1](decisions.md#决策-1--p1-测试治理与质量三合一) |

| 日期 | 决策项 | 选择 | 状态 | 授权原话 | 关联 |
|---|---|---|---|---|---|
| 2026-07-23 | P1-4 + P1-5 + P1-6 合并方案 | xfail 静态 metadata + AI 离线 contract + a11y/perf 报告型 | ✅ 自动决策 | "循环把上面哪些问题都处理一遍…不需要我确认了" | [`decisions.md` 决策 1](decisions.md#决策-1--p1-测试治理与质量三合一) |

## 自检

- [x] 任务理解、4 个独立 Agent 已核验
- [x] ≥3 相关文件
- [x] 4 个独立 Agent 对抗核验（设计×3 + 反方×1）
- [x] 修正反方事实：xfail 是已知业务缺陷，a11y/perf/AI eval 基础薄弱
- [x] 依赖顺序与排除项明确
- [x] refactor-6 路径建议
