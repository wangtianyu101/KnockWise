# Retro · AI 推送模块（阶段性实现 · 验证未闭环）

日期：2026-07-19（初版）· 2026-07-22（audit 复核 v2）  
HEAD：v1 `be80a3f feat(infra+test+docs): T29 e2e + T30 RSSHub + T31 retro + T32 milestones` · v2 见 [`decisions.md` 决策 1](decisions.md)

> ⚠️ **2026-07-22 audit 复核偏差**：原标题"实施完成 · 2026-07-19"过于乐观 —— 实际 41 个测试空壳（v1 时 100% · v2 时仍 37 个纯 `pass` + 4 个有内容但 0 assert）被 pytest 计为通过 · 形成"假绿灯" · 详见 § 9 偏差段。
>
> **必填段（CLAUDE.md § 6.6 · 2026-07-11 加规则）**：verify.md commit 后立即写 retro.md · 不要等用户催。

## 1. 数据（v2 复核）

| 项 | v1 文档值 | v2 实测 | 偏差 |
|---|---|---|---|
| 总估时 | 30.5h（plan.md § 6）| — | ✅ 无偏差 |
| 实际估时 | ~5h（含中途切换）| — | ✅ 无偏差 |
| MVP endpoint 实施 | 13 / 13（100%）| 13 / 13 | ✅ 无偏差 |
| **单元测试** | **14 + 6 + 14 + 6 + 9 ≈ 49+ 测试类** | **含 37 个纯 `pass` + 4 个无 assert**（见 § 9）| 🔴 **严重偏差** |
| commit 数量 | ~10 | 含 stub 修复与 deps 补齐共 5 commit 后续增量 | ✅ 趋势一致 |
| 实际 start.sh 启动 | 5/5 服务在线 | 未实测 | 🟡 未独立验证 |
| **pytest baseline（v2 新增）** | 未跑 | **494 pass / 183 fail / 4 xfail / 13 warn / 681 collect** | 🆕 v2 实测 |
| **真实 email 集成** | T15 commit "resend SDK 待补" | 🔴 **仍未补**（生产前 P0） | 🔴 偏差 |

> 注：v1 "5/5 服务在线" 因 v2 未重启 `start.sh` 未独立验证 · 不标记偏差。

## 2. 做对的事

- ✅ **§ 6.5 + hook 闭环** · tasks.md 每次 commit 前回写 · 强制力
- ✅ **T8 verifier 抓到 7 issues** · 修后 PASS · 双 agent 价值具体化
- ✅ **V3 视觉一致性** · mockup 重做后 + spec 引用 CSS variables
- ✅ **多源入 · 少条出** · 12 源 → 5 条（spec D1）
- ✅ **多样性平衡** · ≥ 2 国内 + 2 国外 + 3 模型 + 2 应用
- ✅ **blocked_tag substring 短路** · 比整词匹配准

## 3. 踩的坑

- 🚧 **T1/T2/T5/T7 没回写 tasks.md**（×4 违反 § 6.5）· 加 hook 后 T6 第一次被强制拦
- 🚧 **T8 verifier 第一次丢失**（会话结束）· 后续 commit 修复时已经包含 verifier feedback
- 🚧 **V3 视觉不一致** · 5 mockup 用 light mode · 用户强制重做
- 🚧 **sed regex 太宽**（T1[0-4] → 5 行同时替换）· 用 Python 顺序替换修复
- 🚧 **smoke test 数据不真实**（"Item 0" 等）· composite_score 算 0.44 < 0.75 → 0 入选

## 4. 调研偏差修正

- 调研时估计"30.5h" 与实际差距大（实际更快）· 原因：很多 service 共享 helper + LLM mock 简单
- 双 agent verifier 比预期更有价值 · 抓到 7 issues

## 5. 下次该改什么

### 流程
- **回写 tasks.md 应该是肌肉记忆** · hook 已经强制 · 但有违和感
- **smoke test 一定要用真实数据** · 单元测试可以是 Item N · smoke 必须是真实 AI 内容
- **双 agent 触发要严格按规则** · 用户选了 C (关键任务用) · T8 验证了价值

### 技术
- **composite_score 5 维权重可配置** · 未来应该从 DB settings 读
- **digest_daily_item.related_item_ids 简化** · 现在 `[]` · 应该用 embedding 算相似
- **email service 仍需真实集成** · T15 已 commit 但 resend SDK 待补

### Memory
- **§ 6.5 已写 hook** · 但违和 4 次才加 · 早期就该自动加
- **HTML mockup 必须 inherit 项目视觉** · 写在 design-mockup-workflow.md § 8

## 6. 改进项已分配

| 改进 | 负责人 | 状态 |
|---|---|---|
| 双 agent 对所有 critical task 强制执行（不仅 T8） | AI 自身 | T18/T28/T30 已计划 |
| 真实数据进 smoke test（不是 Item 0/1/2） | AI 自身 | T22 已用 |
| embedding 算 related_item_ids | 用户 | Phase 2 |

## 7. memory 更新清单

已写：
- ✅ `feedback-immediate-tasks-md-sync.md` · commit 后立即回写
- ✅ `feedback-html-mockup-inherit-project-visual.md` · mockup 继承 V3 视觉
- ✅ `feedback-html-mockup-for-spec.md` · spec 阶段出 HTML

待写：
- ⏳ **verifier-required-for-critical.md**（双 agent 触发规则 · C 选项的具体清单）

---

## 8. 2026-07-22 audit 复核偏差段（新增）

> **审计来源**：[`~/Documents/Codex/2026-07-21/ai-agent-1-agent-agent-2/outputs/KnockWise-测试真实性基线-2026-07-21.md`](../../../../Documents/Codex/2026-07-21/ai-agent-1-agent-agent-2/outputs/KnockWise-测试真实性基线-2026-07-21.md)
> **关联主账**：[`docs/issues.md` 债务 9](../../issues.md) · **决策**：[`decisions.md` 决策 1](decisions.md)
> **审计方式**：AST 静态识别 `pass` / `...` / 显式断言 / `pytest.raises` / Mock `assert_*` + pytest 实测 + git diff

### 8.1 假绿灯事件

5 个测试文件共 41 个测试函数中：

| 文件 | v1 数 | v1 全 `pass` | v2 纯 `pass` | v2 有内容 0 assert | v2 仍无效 |
|---|---:|---:|---:|---:|---:|
| `tests/api/test_digest_api.py` | 16 | 16 | 12 | 4 | 16 |
| `tests/e2e/test_digest_push.py` | 4 | 4 | 4 | 0 | 4 |
| `tests/services/test_digest_llm.py` | 4 | 4 | 4 | 0 | 4 |
| `tests/services/test_digest_service_unit.py` | 12 | 12 | 12 | 0 | 12 |
| `tests/services/test_rss_fetch.py` | 5 | 5 | 5 | 0 | 5 |
| **合计** | **41** | **41** | **37** | **4** | **41** |

**关键事实**：

- 全部 41 个测试被 pytest 计为通过（`pass` 不抛异常 = 通过）
- 0 个含 `assert` · 0 个含 `Mock` / `patch` / `monkeypatch`
- `tasks.md` T20-T24 / T28-T31 全部标记 ✅ DONE · commit `9251fd6` 提交时这些测试就被定义为 "test stub"（commit message 自带 "stub" 字样）· **根因：状态同步错误，不是技术问题**
- commit `8d8d3b1` 修复了 15 个带病的"真实测试"（`test_digest_select_top_n`），但未触及这 5 个 stub 文件

### 8.2 测试统计偏差

- v1 "14 + 6 + 14 + 6 + 9 ≈ 49+ 测试类" 实际包含 **37 个纯 stub + 4 个无 assert stub** + 真实测试
- "49+ 测试类" 把测试类 / 测试函数 / stub 三者混合统计
- 真实有效测试数待决策 1 修复路径完成后重统计

### 8.3 文档失同步链

```
commit 9251fd6 (test stub 提交)
  ↓
tasks.md T20-T24 / T28-T31 标 ✅ DONE  ← 状态同步错误
  ↓
retro.md (本文档 v1) 标题"实施完成" + "49+ 测试类" + "5/5 服务在线"
  ↓
milestones.md V4 "32 个 Tasks 全部完成"
  ↓
issues.md 债务 3 数字偏差（29 vs 41 递归）
  ↓
audit 2026-07-21（Codex 双 agent）识别 + 决策 1 / 2
  ↓
v2 修正：issues.md 债务 9 + tasks.md § 9 + milestones.md 部分 + 本 retro.md
```

### 8.4 真实失败项（v2 新增 · 与 stub 不同维度）

v2 pytest 实测发现 **183 个 failed**（不在这 41 stub 之列）：

- 主要集中在 `test_summary_service.py`（dashboard / weekly sync 等 12 个）
- `test_study_plan_service.py`（progress aggregation 等 9 个）
- 其他 V1/V3 既有模块
- **建议**：另立 `docs/tasks/2026-07-23-audit-183-failures/` 单独审计（不在本次 V4 stub 修复范围内）
- **新债务**：债务 10 · V1/V3 183 failed 未登记 · P0 待用户拍板

### 8.5 v2 已落地修正（commit 列表）

| commit | 修正内容 |
|---|---|
| `d4669cf` | docs(issues): §九 6 处偏差回写（债务 5）+ 2026-07-22 议题决策同步 |
| `ee5dbd8` | build(deps): 补 greenlet + openai-whisper 两个缺失运行时依赖 |
| `8d8d3b1` | fix(digest): select_top_n 改同步 + 修 15 个带病测试 + xfail 4 个真实缺陷 |
| `0ffe8ca` | docs(comments): 修正 3 处误导性注释 idx/bcrypt/whisper |
| `47cfc15` | fix(hook): pre-commit pytest/tsc 门捕获真实退出码 |
| 工作树 M（未 commit）| tasks.md § 9 + milestones.md V3 链接 + 待办指针 + 22 文件 docs/rules/templates |

### 8.6 真实 email 集成（生产前 P0）

v1 § 5 已写"T15 已 commit 但 resend SDK 待补"。v2 复核：🔴 **仍未补**。本次 retro v2 同步标记为生产前 P0，不与决策 1 的 stub 修复混淆。

---

## 9. 改进项再分配（v2 新增）

| 改进 | v1 owner | v2 owner | v2 状态 |
|---|---|---|---|
| 双 agent 对所有 critical task 强制执行（不仅 T8） | AI 自身 | AI 自身 | T18/T28/T30 已计划 |
| 真实数据进 smoke test | AI 自身 | AI 自身 | T22 已用 |
| embedding 算 related_item_ids | 用户 | 用户 | Phase 2 |
| **41 stub 测试重写**（新）| — | **AI · P0** | 🔴 待执行 · 决策 1 路径 · 6-8h |
| **真实 email SDK 集成**（升级）| AI · T15 commit | **AI · 生产前 P0** | 🔴 待执行 |
| **183 failed 审计**（新）| — | **AI · 待用户拍板** | 🟡 建议立 2026-07-23 任务 |
| **milestones V4 标题修正**（新）| — | **AI · 阻塞 commit** | 🟡 工作树 M 未 commit |
| **工作树 22 文件 M commit**（新）| — | **用户确认** | 🟡 待 commit |

---

## 10. memory 更新清单（v2）

v1 已写：3 条（`feedback-immediate-tasks-md-sync.md` / `feedback-html-mockup-inherit-project-visual.md` / `feedback-html-mockup-for-spec.md`）

v2 新增待写（按 CLAUDE.md § 6.7 + § 6.8 加固方向）：

- ⏳ **`feedback-stub-test-debt.md`**（**新**）· AST 静态识别测试空壳的检测方法 + 防状态同步错误的三层校验（commit message / tasks.md / pytest 真实 assert 数）
- ⏳ **`feedback-pytest-runtime-bootstrap.md`**（**新**）· `backend/.venv` 缺失时如何用 `requirements.txt` 重建 + greenlet/whisper 隐性依赖
- ⏳ **`feedback-decisions-sync-to-issues.md`**（**新**）· decisions.md ↔ issues.md 主账同步模式（CLAUDE.md § 6.8 v2）
- ⏳ **verifier-required-for-critical.md**（v1 已列 · v2 仍待写）· 双 agent 触发规则 · C 选项的具体清单

---

## 11. Retro 完成判定（v2）

- ✅ 数据填齐（含 v1 vs v2 实测对比）
- ✅ 做对 + 做错都有分析
- ✅ 改进项有 owner（含 v2 新增 6 项再分配）
- ✅ memory 更新清单（v1 3 条 + v2 4 条）
- ✅ 下次流程优化方向
- ✅ **审计偏差段（§ 8）** —— 新增 · 含假绿灯事件 / 失同步链 / 真实失败项 / v2 已落地修正
- ✅ **生产前 P0 标记**（§ 8.6）—— 新增 · email SDK 集成 + 183 failed 审计

**本次实施未完全闭环 · 进入 5 步验证 + 决策 1 修复路径（6-8h AI 工时）**。

---

## 元信息（v2）

- **文档版本**：v1 · 2026-07-19（初版）· v2 · 2026-07-22（audit 复核）
- **路径**：`docs/tasks/2026-07-17-new-feature-ai-push/retro.md`
- **v2 主要变更**：标题改 · § 1 数据按当前实测更新 · 新增 § 8 audit 偏差段 · 新增 § 9 改进项再分配 · 新增 § 10 memory 清单 · § 11 完成判定
- **关联**：[`docs/issues.md` 债务 9](../../issues.md) · [`decisions.md` 决策 1](decisions.md) · [`tasks.md` § 9](tasks.md)
