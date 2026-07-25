# ♻️ 调研报告 · 重构：测试基础架构（L1-L5 + 追溯 + Fixture）

> 日期：2026-07-23 · 调研人：Claude Code + 4 个独立对抗 Agent
> 路径模式：`refactor-6`
> 当前阶段：0 调研完成 · 自动执行授权下采用单一推荐 · 未进入设计/实施

## 1. 任务理解

- **用户授权**：循环处理 P1+P2 17 项，自动决策，无需用户确认。
- **P1-1**：测试分层和 Mock 边界模糊，缺统一主账。
- **P1-2**：Requirement → Scenario → TC → Test Node → Evidence 闭环缺失稳定 ID。
- **P1-3**：E2E fixture 没有真实 ORM/MySQL 边界，dev-login 失败会虚拟 token 假绿，缺并行隔离。
- **目标**：建立可机器校验的测试基础架构，覆盖 L1-L5、追溯矩阵、E2E fixture 三块。
- **边界**：不实施代码；不修改测试套件；不引入新测试框架；不动 mock_db/mock_cache/mock_llm 默认行为；保持 seed_data 只读。

## 2. 现状分析

> 调研证据来源：`docs/issues.md`（P1+P2 遗留项主账）· `git log -10`（最近相关改动）· `git status`（unstaged / 多 agent 冲突扫描）。

1. `testing-rules.md` § 6.5 边界已定义，但缺统一表 + 跨层不变量校验。
2. `conftest.py:37-54` `block_external_network` 防止外网，基础牢固。
3. `conftest.py:159-170` `mock_llm` 只 patch `services.qa_service._get_llm`，其他 LLM 入口不受控。
4. `frontend/tests/e2e/digest.spec.ts:39-71` 走整组 `page.route` mock，命名"端到端"但实际非 E2E。
5. `backend/tests/e2e/test_digest_push.py:0-3` 真实内链 + 4 项允许 mock（已合规）。
6. `backend/api/auth.py:218-261` dev-login DB 异常返回虚拟 token，可能假绿。
7. `backend/core/dependencies.py:37-57` 找不到真实 user 时返回虚拟 user，进一步假绿。
8. `frontend/playwright.config.ts:13-19` `workers: 1` 临时压成串行。
9. `frontend/tests/visual/digest.spec.ts` + `tests/e2e/pages.spec.ts` 视觉/截图混用。
10. 缺稳定 ID：spec.md Requirement/Scenario 标题无 `REQ-*`/`SCN-*`；TC 引用 `R1` 但无外键；verify.md 缺 EV/Metric。
11. `tasks-template.md:98-122` 拆成两张半矩阵，无统一 REQ→SCN→TC 闭环。

## 3. 重构方案

| 方案 | 结论 |
|---|---|
| 三块独立方案 | ❌ 共享 schema/ID，需合并 |
| 另建 YAML/JSON 主账 | ❌ 与现有 Markdown 模板冲突 |
| **L1-L5 + Traceability + E2E Fixture 三位一体** | ✅ 自动采用 |

## 4. 单一推荐

### 4.1 L1-L5 Mock 边界主账（决策 1）

**唯一主账**：把以下 5 层表纳入 `testing-rules.md` § 6.5.1：

| 层 | 必真实 | 允许 Mock | 禁止 | 触发命令 |
|---|---|---|---|---|
| L1 单元 | 被测函数 | 纯 fixture · 时间 (freezegun) | 框架 Runtime | `pytest tests/services -q` |
| L2 服务集成 | service 公开方法链 | db · cache · clock · llm · email · rss | service 私有方法 | `pytest -m "not e2e"` |
| L3 API 集成 | router + Pydantic 422 | db (AsyncMock) · get_current_user | mock 整个 handler | `pytest tests/api` + `pytest tests/integration` |
| L4 E2E | scheduler + service + ORM + DB + API | 仅 rss · llm · email · clock | mock 上述 5 层任何 | `RUN_MYSQL_INTEGRATION=1 pytest tests/e2e` |
| L5 Staging | 全栈真服务 | 无 | 任何 mock | `verify.md` 引用 |

**Provider 边界例外**：`service` 命名形如 `_fetch_and_parse` / `_send_email` 的 provider boundary method 在 L2 中可 patch，但**不得**用来证明 service 内部逻辑正确。

**前端补全**：新增 `frontend/vitest.setup.ts` 的 `block_external_network` 等价物。

### 4.2 Traceability Matrix（决策 2）

**唯一主账在 `verify.md`**：10 列规范化矩阵

```
| REQ | SCN | TC | Task | Test Node | Level | E2E Path | Evidence | Metric/Event | Status |
```

**ID 规则**：
- `REQ-\d{3}`：Requirement
- `SCN-\d{3}`：Scenario，引用 REQ
- `TC-\d{3}`：Test Case，引用 SCN
- `T\d+`：沿用现有任务 ID
- Test Node：完整 pytest/Vitest/Playwright node
- `E2E-\d{3}`：L3/L5 路径；不适用写 `—`
- `EV-\d{3}`：Evidence 登记
- `METRIC-\d{3}`：产品指标

**spec/tasks/test-cases/product-doc 关系**：
- spec.md 是需求实体主账
- tasks.md 是实施分配视图
- test-cases.md 是测试执行目录
- verify.md 是最终聚合视图
- product-doc.md 增加 `指标→事件` 映射表

**10 条机器校验不变量**（`check-step.py` 验证）：
1. 所有 ID 唯一
2. SCN 引用存在的 REQ
3. TC 引用存在的 SCN
4. Task 至少引用一个 TC + Test Node
5. PASS TC 至少有一个 L2/L3/L5 evidence
6. E2E 行有 E2E-* + Mock 边界合规
7. EV-* 退出码 0；BLOCKED 可无 artifact 但需原因
8. Metric 绑定事件 + REQ
9. Requirement 全部必需 TC PASS 才 PASS
10. 禁止仅凭任务 checkbox 或全 pytest 绿判 PASS

### 4.3 E2E Fixture 契约（决策 3）

**8 项最小契约**：

1. **DB 边界**：DB 名含 `_test` 或 `test`；setup drop+create+init_db；teardown 只清当前 run/worker 命名空间
2. **测试用户**：每 worker UUIDv5(run_id + workerIndex) + email `e2e+<run>-w<worker>@example.invalid` + 真实 user/profile 写入；不复用 dev_user；不允许 virtual-user fallback
3. **登录态**：调真实 `/dev-login?username=e2e_<run>_<worker>`，验证返回 user_id 能在 DB 查到；写 JWT 到 Playwright storageState；不允许 fallback token
4. **Digest 预生成**：直接写 DB（1 DigestSettings + 2 test DigestSource + 1 DigestDaily + 5 DigestDailyItem），禁止实时 RSS/LLM
5. **seed_data 只读**：不修改 `digest_sources.json`；测试源用 `https://fixtures.invalid/...`
6. **时间/LLM/RSS 固定**：测试时间 `2026-07-22T00:00:00Z`；浏览器 E2E 不调 RSS/LLM；系统 E2E 只 mock 外部边界
7. **清理幂等**：setup/test/teardown 全部幂等；重启 backend/scheduler 后不能产生第二份 Digest
8. **并行隔离**：CI 独立 MySQL service；每 worker 不同 DB `knockwise_e2e_w<N>`；测试必须带 `user_id` 查询；`workers=1` 仅临时

## 5. 依赖顺序

1. P1-1 L1-L5 边界（最基础，优先）
2. P1-2 Traceability Matrix（依赖 P1-1 的 Level 字段）
3. P1-3 E2E Fixture（依赖 P1-1 的 L4 边界 + P1-2 的 ID 体系）

## 6. 风险评估

| 风险 | 等级 | 缓解 |
|---|---|---|
| 全量改造老测试 | 🔴 | 不改老测试；新规范只约束新增；旧任务 LEGACY_UNVERIFIED |
| ID 重编导致跨文档漂移 | 🟡 | check-step.py 双 ID 模式（旧 R1-R10 + 新 REQ-*）过渡期 |
| dev-login fallback 未消除 | 🔴 | 实施前必须改 auth.py 与 dependencies.py，禁止 fallback |
| 浏览器时间与后端时间漂移 | 🟡 | 共享 E2E_NOW clock fixture |
| 旧 e2e 测试不符合新 Fixture 契约 | 🟡 | 仅约束新增 E2E；老 E2E 留 fallback 过渡 |

## 7. 明确排除

- 修改 `mock_db / mock_cache / mock_llm` 默认行为
- 修改 `seed_data/digest_sources.json`
- 改老 e2e 文件以适配新 fixture
- 引入新测试框架（pytest-xdist / testcontainers / pytest-postgresql）
- 实施具体代码、跑测试、提交

## 8. 自动决策清单

| 日期 | 决策项 | 选择 | 状态 | 授权原话 | 关联 |
|---|---|---|---|---|---|
| 2026-07-23 | P1-1+P1-2+P1-3 合并方案 | L1-L5 + Traceability + E2E Fixture 三位一体 | ✅ 自动决策 | "循环把上面哪些问题都处理一遍…不需要我确认了" | [`decisions.md` 决策 1](decisions.md#决策-1--p1-测试基础架构三位一体) |

## 9. 输出建议

- **路径模式**：`refactor-6`（0→1→2→3→4→5→6；不写 product-doc，非 UI 不写 design-spec）。
- **推荐方案**：采用 § 3/§ 4 的 L1-L5 + Traceability + E2E Fixture 三位一体方案。
- **实施顺序**：按 § 5 依赖顺序 P1-1 → P1-2 → P1-3。
- **下一步**：进入步骤 1 规格（spec.md），细化 Requirement/Scenario/TC。

## 自检

- [x] 任务理解、4 个独立 Agent 报告已核验
- [x] ≥3 相关文件
- [x] 4 个独立 Agent 对抗核验（设计×3 + 反方×1）
- [x] 修正反方部分事实（前 Digest spec 确实 mock、后端 E2E 确实真实）
- [x] 依赖关系明确
- [x] refactor-6 路径建议
