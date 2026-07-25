---
title: 测试基础架构 L1-L5 + 追溯 + Fixture · 规格
type: spec
step: 1
date: 2026-07-23
status: draft
tags: [refactor, test-foundation, l1-l5, traceability, e2e-fixture]
related:
  - research.md
  - decisions.md
  - ../../rules/testing-rules.md
  - ../../templates/tasks-template.md
  - ../../templates/verify-template.md
  - ../../../backend/tests/conftest.py
  - ../../../frontend/vitest.setup.ts
  - ../../../scripts/check-step.py
  - ../../../scripts/check-task.py
---

# 规格 · 测试基础架构三位一体（P1-1/2/3）

> 路径模式：refactor-6
> 调研 0 步已落地 → [`research.md`](research.md)
> 决策已拍板 → [`decisions.md`](decisions.md)

---

## 0. 复述与边界

**核心目标**：建立可机器校验的"路径—阶段—条件触发—测试证据"测试基础架构。

**3 个 P1 子项**：
- **P1-1 L1-L5 Mock 边界**：唯一主账在 `testing-rules.md` § 6.5.1
- **P1-2 Traceability Matrix**：唯一主账在 `verify.md` 10 列规范化表
- **P1-3 E2E Fixture**：8 项契约（DB 边界 / 用户命名空间 / 登录态 / Digest 预生成 / seed 只读 / 时间固定 / 清理幂等 / 并行隔离）

**边界**：
- 不改 `mock_db / mock_cache / mock_llm` 默认行为
- 不改 `seed_data/digest_sources.json`
- 不改老 e2e 文件以适配新 fixture
- 不引入新测试框架

---

## 1. 用户故事与业务契约（Requirement）

> **用户故事**：作为 KnockWise 的开发者与 AI 协作者，我希望有一套可机器校验的测试基础架构（L1-L5 边界 + Traceability + E2E Fixture），以便每个 commit 的测试证据能自动追溯到需求，避免假绿灯。
> **用户故事已验收** checklist
>
> - [ ] ⏸ 待用户正式签字（retro.md 状态 ✅ closed 表明作者闭环）

### Requirement: L1-L5 Mock 边界主账

系统 SHALL 在 `testing-rules.md` § 6.5.1 提供 L1-L5 5 层表（每行：必真实 / 允许 Mock / 禁止 / 触发命令）。

#### Scenario: 开发者查阅 L1-L5 边界主账（happy）
- **Given** 开发者读 `docs/rules/testing-rules.md`
- **When** 查 § 6.5
- **Then** 应见 L1-L5 5 层表（含必真实 / 允许 Mock / 禁止 / 触发命令 4 列）
- **And** § 6.5.2 应见 Provider 边界例外条款

#### Scenario: 前端真网络请求被拦截（invalid）
- **Given** `frontend/vitest.setup.ts` 已含 `block_external_network`
- **When** 组件代码调用 `fetch('https://production.example.com/...')`
- **Then** 测试 SHALL fail（reject 错误）
- **And** 网络未真访问

#### Scenario: E2E fixture 在非测试库拒绝运行（edge/failure）
- **Given** DB 名不含 `_test`/`test`
- **When** E2E fixture setup 执行
- **Then** SHALL 直接报错拒绝运行
- **And** 不对真实库做任何 drop/create

### REQ-1 · L1-L5 Mock 边界主账

`testing-rules.md` § 6.5.1 写入 5 层表（每行：必真实 / 允许 Mock / 禁止 / 触发命令）：

| 层 | 必真实 | 允许 Mock | 禁止 | 触发命令 |
|---|---|---|---|---|
| L1 单元 | 被测函数 | 纯 fixture · 时间 (freezegun) | 框架 Runtime | `pytest tests/services -q` |
| L2 服务集成 | service 公开方法链 | db · cache · clock · llm · email · rss | service 私有方法 | `pytest -m "not e2e"` |
| L3 API 集成 | router + Pydantic 422 | db (AsyncMock) · get_current_user | mock 整个 handler | `pytest tests/api` + `pytest tests/integration` |
| L4 E2E | scheduler + service + ORM + DB + API | 仅 rss · llm · email · clock | mock 上述 5 层任何 | `RUN_MYSQL_INTEGRATION=1 pytest tests/e2e` |
| L5 Staging | 全栈真服务 | 无 | 任何 mock | `verify.md` 引用 |

### REQ-2 · Provider 边界例外条款

`testing-rules.md` § 6.5.2 加一条：
- `service` 命名形如 `_fetch_and_parse` / `_send_email` 的 provider boundary method
- 在 L2 中可 patch
- **不得**用来证明 service 内部逻辑正确性，仅用于替换 IO provider

### REQ-3 · 前端 block_external_network

`frontend/vitest.setup.ts` 加 global fetch 拦截：
- 默认 `vi.spyOn(globalThis, 'fetch').mockImplementation(() => Promise.reject(new Error('network blocked')))`
- 单个测试需要真访问时显式 `vi.unmock(...)` 或加 `// @vitest-environment network` 注释

### REQ-4 · Traceability Matrix 10 列

`docs/templates/verify-template.md` § 0.4 加 `frontend_routes` / `e2e_journey_table` / `cross_doc_alignment` 矩阵（与 P1-12 旅程追踪共用结构）。

`verify.md` 必含 `traceability` 段 10 列：
- REQ | SCN | TC | Task | Test Node | Level | E2E Path | Evidence | Metric/Event | Status

### REQ-5 · ID 规则

- `REQ-NNN` Requirement
- `SCN-NNN` Scenario（引用 REQ）
- `TC-NNN` Test Case（引用 SCN）
- `EV-NNN` Evidence 登记
- `METRIC-NNN` 指标

`check-step.py` 新增 `verify` step 校验 10 条不变量（详见 plan § 1）。

### REQ-6 · E2E Fixture 8 项契约

1. **DB 边界**：DB 名含 `_test` 或 `test`；setup drop+create+init_db；teardown 只清当前 run/worker 命名空间
2. **用户命名空间**：每 worker 真实 user via `e2e_<run-id>_w<worker>@example.invalid` + UUIDv5
3. **登录态**：调真实 `/api/auth/dev-login`，验证返回 user_id 能在 DB 查到；写 JWT 到 Playwright storageState
4. **Digest 预生成**：直接写 DB（1 DigestSettings + 2 test DigestSource + 1 DigestDaily + 5 DigestDailyItem）
5. **seed 只读**：不修改 `backend/seed_data/*.json`；测试源用 `https://fixtures.invalid/...`
6. **时间固定**：`2026-07-22T00:00:00Z`；后端注入 `now_provider`；浏览器 Playwright clock
7. **清理幂等**：setup/test/teardown 全幂等；重启后唯一约束验证
8. **并行隔离**：CI 独立 MySQL service；每 worker 不同 DB `knockwise_e2e_w<N>`；测试必须带 `user_id` 查询

### REQ-7 · 文档/模板 4 处统一更新

| 模板 | 改动 |
|---|---|
| `docs/rules/testing-rules.md` | § 6.5.1 L1-L5 表 + § 6.5.2 Provider 边界例外 |
| `docs/templates/verify-template.md` | § 0.4 Traceability 矩阵 + ID 规则 + 10 不变量 |
| `docs/templates/tasks-template.md` | § 4 任务↔测试映射：加 REQ/SCN/TC 列 |
| `docs/templates/product-doc-template.md` | § 5 成功指标：8 必填 + 4 可选（与 P1-8 决策同步） |

### REQ-8 · EXEMPT 兼容性

12 个 2026-07 老任务 + `docs/archive/` 保持 LEGACY 豁免（不破 P0-7 task.yaml 契约）。

---

## 2. 验收标准（验收场景 · GWT 形式）

### S-1 · L1-L5 边界主账落地
**Given** 开发者读 `docs/rules/testing-rules.md`
**When** 查 § 6.5
**Then** 应见 L1-L5 5 层表（含必真实 / 允许 Mock / 禁止 / 触发命令 4 列）
**And** § 6.5.2 应见 Provider 边界例外条款

### S-2 · 前端网络拦截生效
**Given** `frontend/vitest.setup.ts` 已含 `block_external_network`
**When** 组件代码调用 `fetch('https://production.example.com/...')`
**Then** 测试应 fail（reject 错误）
**And** 网络未真访问

### S-3 · Traceability Matrix 校验
**Given** verify.md 含 traceability 段
**When** check-step.py verify 跑
**Then** 校验 10 条不变量：
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

### S-4 · E2E fixture 8 项契约覆盖
**Given** `backend/tests/e2e/conftest.py` 含 `p1_3_digest_arrange` 等 fixture
**When** 测试调用 fixture 建数据
**Then**：
1. DB 名含 `_test`/`test` 才运行
2. 用户名为 `e2e_<run>_w<worker>@example.invalid` 唯一
3. login 后能从 DB 反查 user_id
4. 5 条 DigestDailyItem 真实持久化
5. seed_data 字节未变
6. 多次跑结果一致（幂等）
7. 清理只删本次 run 命名空间
8. 同一 worker 顺序跑互不污染

### S-5 · 模板 4 处同步更新
**Given** 4 个模板按 REQ-7 改动
**When** 任一新任务走完 6 步
**Then**：
- tasks.md § 4 任务↔测试映射含 REQ/SCN/TC 列
- verify.md 含 Traceability 10 列段
- product-doc § 5 8 必填 + 4 可选字段
- testing-rules.md § 6.5.1 + 6.5.2 落地

### S-6 · 老任务豁免兼容性
**Given** 12 个 2026-07 老任务目录已含 task.yaml（v1 schema）
**When** pre-commit 跑
**Then** 老任务目录豁免（task.yaml v1 仍合法）
**And** docs/archive/ 全豁免

### S-7 · 不破现有
- `conftest.py:159-170` `mock_llm` 默认行为未动
- `seed_data/*.json` 字节未变
- 现有 e2e 测试文件未改
- `scripts/check-step.py` 现有 6 step 校验仍工作

---

## 3. 数据契约（schemas）

### 3.1 L1-L5 行（testing-rules.md § 6.5.1）

```yaml
- level: L1
  name: 单元
  required_real: [被测函数]
  allowed_mock: [纯 fixture, 时间 (freezegun)]
  forbidden: [框架 Runtime]
  trigger: pytest tests/services -q
```

### 3.2 Traceability Matrix（verify.md）

```yaml
traceability:
  - req: REQ-001
    scn: SCN-001
    tc: TC-001
    task: T8
    test_node: backend/tests/e2e/test_digest_push.py::test_full_cron_to_db_to_api_happy
    level: L3
    e2e_path: E2E-001
    evidence: EV-001
    metric_event: METRIC-002:event=digest_read
    status: PASS
```

### 3.3 E2E Fixture 配置（`backend/tests/e2e/conftest.py`）

```python
@pytest.fixture(scope="session")
def e2e_run_id() -> str:
    """CI run id + attempt，本地随机 UUID"""
    return os.environ.get("GITHUB_RUN_ID", uuid.uuid4().hex[:8])

@pytest.fixture(scope="session")
def e2e_db_url(e2e_run_id) -> str:
    """knockwise_e2e_w<run>"""
    return f"mysql+aiomysql://kw:e2e@127.0.0.1:3306/knockwise_e2e_{e2e_run_id[:6]}"

@pytest.fixture(scope="session")
def e2e_user(e2e_run_id) -> User:
    """e2e_<run>_w0@example.invalid 唯一真实 user"""
    ...

@pytest.fixture
def p1_3_digest_arrange(e2e_user) -> dict:
    """1 DigestSettings + 2 test DigestSource + 1 DigestDaily + 5 DigestDailyItem"""
    ...
```

---

## 4. 边界条件与非目标

### 边界

- ✅ `testing-rules.md` § 6.5.1 + § 6.5.2 新增
- ✅ `verify-template.md` § 0.4 + ID 规则
- ✅ `tasks-template.md` § 4 任务↔测试加 REQ/SCN/TC 列
- ✅ `product-doc-template.md` § 5 8 必填 + 4 可选（与 P1-8 同步）
- ✅ `frontend/vitest.setup.ts` 加 `block_external_network`
- ✅ `scripts/check-step.py` verify step 加 10 不变量
- ✅ `backend/tests/e2e/conftest.py` 共享 fixture（最小 8 项契约）
- ✅ 12 老任务 + docs/archive 豁免

### 非目标

- ❌ 不动 `mock_db / mock_cache / mock_llm` 默认行为
- ❌ 不改 `seed_data/*.json`
- ❌ 不改老 e2e 测试文件
- ❌ 不引入新测试框架
- ❌ 不实施业务代码

---

## 5. 测试用例

> 验收测试用例（TC 引用 § 2 Scenario · 详细 pytest 期望见 § 8 测试场景）：

- [ ] **TC-1**（对应 Scenario happy / S-1）：`testing-rules.md` § 6.5 含 L1-L5 5 层表 + § 6.5.2 Provider 例外 → 断言文本存在
- [ ] **TC-2**（对应 Scenario invalid / S-2）：`test_block_external_network_rejects` — 真网络请求被 reject
- [ ] **TC-3**（对应 Scenario edge / S-4）：`test_p1_3_digest_arrange_creates_5_items` — 5 条 DigestDailyItem 真实持久化
- [ ] **TC-4**（对应 S-3）：`test_verify_step_10_invariants` — check-step.py verify 10 条不变量
- [ ] **TC-5**（对应 S-4）：`test_p1_3_digest_arrange_idempotent` — 同 run 顺序跑 2 次结果一致
- [ ] **TC-6**（对应 S-7）：`test_seed_data_unchanged` — seed_data/*.json 字节未变（不破现有）

## 6. 与现有机制关系

| 文件 | 角色 | 关系 |
|---|---|---|
| `testing-rules.md § 6.5` | 现有边界文本 | § 6.5.1/6.5.2 新增 |
| `check_test_quality.py` | AST 拦截 | 不重叠 · 各自负责不同维度 |
| `check-step.py` | 单文件 validator | verify step 加 10 不变量 |
| `check-task.py` (P0-7) | task.yaml 契约 | 与 Traceability 各自独立 |
| `conftest.py` | 现有 fixture | 新增 e2e/conftest.py 不动 conftest.py |
| `verify-template.md` | 现有模板 | § 0.4 新增 |

---

## 6. 安全 / 不可信输入审查

- 不涉及 CI/CD · 不涉及 Agent · 不涉及 secrets · 不涉及网络
- 不涉及文件系统写 · 只读校验 + 模板加段
- 无需 § 0.2.1 安全审查

---

## 7. 测试场景（pytest 期望）

```python
# tests/test_check_step.py 新增

def test_verify_step_10_invariants():
    """S-3: 10 条不变量"""
    # 1. ID 唯一
    # 2. SCN → REQ
    # 3. TC → SCN
    # ... 共 10

# tests/test_vitest_setup.py 新增 (frontend)

def test_block_external_network_rejects():
    """S-2: 真网络请求被拒绝"""
    with pytest.raises(Exception, match="network blocked"):
        await fetch("https://production.example.com/api")

# tests/test_e2e_fixture.py 新增

def test_p1_3_digest_arrange_creates_5_items():
    """S-4: 5 条 DigestDailyItem 真实持久化"""
    ...

def test_p1_3_digest_arrange_idempotent():
    """S-4: 同一 run 顺序跑 2 次结果一致"""
    ...

def test_p1_3_digest_arrange_seed_data_unchanged():
    """S-4: seed_data/*.json 字节未变"""
    ...
```

---

## 8. 实施约束（4 步 TDD 必做）

1. 先写失败 pytest → 红
2. 写实现 → 绿
3. 模板/规则段落更新 + vitest.setup.ts 改 → 跑全部测试
4. EXEMPT 兼容性测试通过

**Verifier agent 必开**：每个 commit 后用独立 verifier agent 跑 § 1 + § 2 + § 7 验证。

---

## 9. 关联文档

- 调研：[`research.md`](research.md)
- 决策：[`decisions.md`](decisions.md)
- 主账：`docs/issues.md` 决策 #30 · 债务 #18
- 公共规则：`AGENTS.md` § 0 / § 6.5 / § 6.7 / § 6.8 v2
- 现有机制：`scripts/check-step.py` · `scripts/check_test_quality.py` · `scripts/check-task.py` (P0-7)
- 模板：`docs/templates/tasks-template.md` · `docs/templates/verify-template.md` · `docs/templates/product-doc-template.md`
- 后端 fixture：`backend/tests/conftest.py` · `backend/tests/e2e/conftest.py` (新)
- 前端：`frontend/vitest.setup.ts`
