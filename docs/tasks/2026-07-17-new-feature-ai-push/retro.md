# Retro · AI 推送模块（实施完成 · 2026-07-19）

> **必填段（CLAUDE.md § 6.6 · 2026-07-11 加规则）**：verify.md commit 后立即写 retro.md · 不要等用户催

## 1. 数据

| 项 | 数据 |
|---|---|
| 总估时 | 30.5h（plan.md § 6） |
| 实际估时 | ~5h（含中途切换） |
| MVP endpoint 实施 | 13 / 13（100%）|
| 单元测试 | 14 + 6 + 14 + 6 + 9 ≈ 49+ 测试类 |
| commit 数量 | ~10（包含 docs + service + api + frontend） |
| 实际 start.sh 启动 | 5/5 服务在线 |

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

## 8. Retro 完成判定

- ✅ 数据填齐
- ✅ 做对 + 做错都有分析
- ✅ 改进项有 owner
- ✅ memory 更新清单
- ✅ 下次流程优化方向

**本次实施闭环 · 进入 5 步验证阶段**。
