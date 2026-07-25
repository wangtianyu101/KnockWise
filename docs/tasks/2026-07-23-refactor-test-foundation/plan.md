---
title: 测试基础架构 L1-L5 + 追溯 + Fixture · 计划
type: plan
step: 2
date: 2026-07-23
status: draft
tags: [refactor, test-foundation, plan]
related:
  - research.md
  - spec.md
  - decisions.md
---

# 计划 · 测试基础架构三位一体（P1-1/2/3）

> 路径模式：refactor-6
> 1 步 spec 已落地 → [`spec.md`](spec.md)

---

## 1. ≥ 2 方案对比

### 方案 A · 单 file 增加（推荐）

**结构**：
- `docs/rules/testing-rules.md` 新增 § 6.5.1 + § 6.5.2（add 60-100 行）
- `docs/templates/verify-template.md` § 0.4 新增（add 40 行）
- `docs/templates/tasks-template.md` § 4 加列（modify 10 行）
- `docs/templates/product-doc-template.md` § 5 8+4 字段（modify 30 行）
- `frontend/vitest.setup.ts` 新增 `block_external_network`（add 15 行）
- `backend/tests/e2e/conftest.py` 新增（add 200 行，8 项契约 fixture）
- `scripts/check-step.py` verify step 加 10 不变量（add 80 行）
- `backend/tests/test_check_step.py` 新增测试（add 50 行）

**优**：
- 与现有 `check-step.py` 风格统一
- 与现有 `conftest.py` 同目录
- 与现有模板同一文件追加
- 8 个新文件/修改都是现有路径
- 不引入新目录/新框架

**缺**：
- 跨 4 模板 + 2 脚本 + 2 fixture 改动面广
- 8 个文件须分别独立验证

### 方案 B · 独立 checker 目录

**结构**：
- 新增 `scripts/check-test-foundation/` 目录
- 5 个独立 Python 脚本（layer-boundary / trace-matrix / e2e-fixture / provider-exception / vitest-network）
- 与 `check-step.py` 平行

**优**：
- 单一职责
- 失败信息更精准

**缺**：
- 5 个脚本 5 套维护
- pre-commit 加 25 行 case
- 与现有单 `check-step.py` 风格不一致

### 单一推荐：方案 A

> **推荐**: 方案 A（单 file 增加）。

**决策 1 · 采用方案 A**：
- 选择：方案 A（单文件增量），否决方案 B（独立 checker 目录）
- 理由见下。

**理由**：
1. 跨 8 个文件改动是垂直改造（同一主题 L1-L5 + 追溯 + fixture），与 P0-7 单文件路径风格一致
2. 8 个文件总增量 ~500 行 vs 方案 B 5 个脚本 600+ 行
3. 维护成本更低（同一 PR review）

---

## 2. 单一推荐方案详细

### 2.1 文件改动总览

| # | 文件 | 类型 | 增量 | 估时 |
|---|---|---|---|---|
| 1 | `docs/rules/testing-rules.md` | 修改 | +60 行 | 15 min |
| 2 | `docs/templates/verify-template.md` | 修改 | +40 行 | 10 min |
| 3 | `docs/templates/tasks-template.md` | 修改 | +10 行 | 5 min |
| 4 | `docs/templates/product-doc-template.md` | 修改 | +30 行 | 10 min |
| 5 | `frontend/vitest.setup.ts` | 修改 | +15 行 | 10 min |
| 6 | `backend/tests/e2e/conftest.py` | 新建 | ~200 行 | 45 min |
| 7 | `scripts/check-step.py` | 修改 | +80 行 | 30 min |
| 8 | `backend/tests/test_check_step.py` | 修改 | +50 行 | 15 min |
| **合计** | | | **~485 行** | **~2h 20min** |

### 2.2 关键文件改动核心

#### testing-rules.md § 6.5.1 模板

```markdown
### 6.5.1 L1-L5 边界主账（per P1-1 决策）

| 层 | 必真实 | 允许 Mock | 禁止 | 触发命令 |
|---|---|---|---|---|
| L1 单元 | 被测函数 | 纯 fixture · 时间 (freezegun) | 框架 Runtime | `pytest tests/services -q` |
| L2 服务集成 | service 公开方法链 | db · cache · clock · llm · email · rss | service 私有方法 | `pytest -m "not e2e"` |
| L3 API 集成 | router + Pydantic 422 | db (AsyncMock) · get_current_user | mock 整个 handler | `pytest tests/api` + `pytest tests/integration` |
| L4 E2E | scheduler + service + ORM + DB + API | 仅 rss · llm · email · clock | mock 上述 5 层任何 | `RUN_MYSQL_INTEGRATION=1 pytest tests/e2e` |
| L5 Staging | 全栈真服务 | 无 | 任何 mock | `verify.md` 引用 |

#### 6.5.2 Provider 边界例外

- `service` 命名形如 `_fetch_and_parse` / `_send_email` 的 provider boundary method 在 L2 中可 patch
- **不得**用来证明 service 内部逻辑正确性，仅用于替换 IO provider
```

#### frontend/vitest.setup.ts 关键代码

```ts
// P1-6: block_external_network — 默认拦截真网络请求
import { vi, beforeEach, afterEach } from 'vitest'

let networkAllowed = false

const originalFetch = globalThis.fetch
beforeEach(() => {
  networkAllowed = false
  globalThis.fetch = vi.fn(async () => {
    if (networkAllowed) {
      return originalFetch.apply(globalThis, arguments as any)
    }
    throw new Error('network blocked by vitest.setup.ts — use vi.mocked() to allow')
  }) as any
})
afterEach(() => {
  globalThis.fetch = originalFetch
})

// 标记函数：单测需要真网络时调用
;(globalThis as any).__allowNetwork__ = () => { networkAllowed = true }
```

#### backend/tests/e2e/conftest.py 关键 fixture

```python
"""P1-3 E2E Fixture 8 项契约"""
import os
import uuid
import pytest
from sqlalchemy import create_engine, text
from backend.core.database import Base, init_db
from backend.api.auth import _create_token
from backend.models import User, Profile, DigestSource, DigestSettings, DigestDaily, DigestDailyItem
from datetime import datetime, timezone

# 1. DB 边界 fixture
@pytest.fixture(scope="session")
def e2e_db_url() -> str:
    if "test" not in os.environ.get("DATABASE_URL", "").lower():
        pytest.skip("e2e requires DB name with 'test' or '_test'")
    return os.environ["DATABASE_URL"]

@pytest.fixture(scope="session")
def e2e_engine(e2e_db_url):
    engine = create_engine(e2e_db_url)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    init_db(engine)
    return engine

# 2. 用户命名空间 fixture
@pytest.fixture
def e2e_user_id() -> str:
    run_id = os.environ.get("GITHUB_RUN_ID", uuid.uuid4().hex[:8])
    worker = os.environ.get("PYTEST_XDIST_WORKER", "0")
    return f"e2e_{run_id}_w{worker}"

# 3. 登录态 fixture
@pytest.fixture
def e2e_user(e2e_engine, e2e_user_id) -> User:
    from backend.services.user_service import create_user
    user = create_user(
        email=f"{e2e_user_id}@example.invalid",
        github_id=e2e_user_id,
        display_name=f"E2E User {e2e_user_id}",
    )
    return user

@pytest.fixture
def e2e_jwt(e2e_user) -> str:
    return _create_token(sub=str(e2e_user.id), email=e2e_user.email)

# 4-7. Digest 预生成 fixture (per P1-3 S-4)
@pytest.fixture
def p1_3_digest_arrange(e2e_engine, e2e_user) -> dict:
    fixed_time = datetime(2026, 7, 22, 0, 0, 0, tzinfo=timezone.utc)
    # 1. DigestSettings
    settings = DigestSettings(user_id=e2e_user.id, push_hour=8, push_minute=0, ...)
    # 2. 2 test DigestSource
    sources = [
        DigestSource(id=uuid.uuid4(), user_id=e2e_user.id, is_default=False,
                    url="https://fixtures.invalid/source-1", name="Test Source 1"),
        DigestSource(id=uuid.uuid4(), user_id=e2e_user.id, is_default=False,
                    url="https://fixtures.invalid/source-2", name="Test Source 2"),
    ]
    # 3. 1 DigestDaily
    daily = DigestDaily(user_id=e2e_user.id, date=fixed_time.date(), vibe="calm")
    # 4. 5 DigestDailyItem
    items = [
        DigestDailyItem(id=uuid.uuid4(), daily_id=daily.id, rank=i+1,
                        title=f"Test Item {i+1}", summary=f"...", ...)
        for i in range(5)
    ]
    with e2e_engine.begin() as conn:
        # unique constraint 天然验证幂等
        ...
    return {"user": e2e_user, "settings": settings, "sources": sources, "daily": daily, "items": items}
```

#### scripts/check-step.py verify step 加 10 不变量

```python
# 在 CHECKS 字典中加新 entry
def check_traceability(content: str) -> list:
    """Per spec § 1 REQ-4 + REQ-5: 10 不变量"""
    errors = []
    # 1. ID 唯一
    # 2. SCN → REQ
    # 3. TC → SCN
    # ... 共 10 条
    return errors

CHECKS["traceability"] = check_traceability
```

---

## 3. 实施步骤（4 步 TDD 拆分 · ≤ 1h AI 工作量/每个）

### T1 · 测试先行：写失败 pytest（多组件）
- 改 `backend/tests/test_check_step.py` 加 `test_verify_step_10_invariants` · 10 个 case
- 创建 `backend/tests/test_e2e_fixture.py` 测试 8 项契约
- 创建 `frontend/__tests__/setup.test.ts` 测试 `block_external_network`
- 跑 → 全红

### T2 · 实现：testing-rules.md + 模板 4 处 + scripts/check-step.py
- 改 § 6.5.1 L1-L5 表 + § 6.5.2 Provider 边界例外
- 改 4 个模板（verify / tasks / product-doc / verify-template）
- 改 scripts/check-step.py 加 verify step 10 不变量
- 跑 T1 → 全绿

### T3 · 前端 vitest.setup.ts + 后端 e2e/conftest.py
- 改 `frontend/vitest.setup.ts` 加 `block_external_network`
- 创建 `backend/tests/e2e/conftest.py` 8 项契约 fixture
- 跑 frontend vitest → T1 全绿
- 跑 e2e fixture 测试 → 全绿

### T4 · 全套回归 + EXEMPT 兼容性测试
- 跑 `pytest backend/tests/` 全绿
- 跑 frontend vitest 全绿
- EXEMPT 兼容性：12 个 2026-07 老任务 + docs/archive/ 仍豁免
- 跑 pre-commit 端到端

### T5 · verify.md + retro.md（5+6 步）
- 5 步 verify 写 7 个 verify 场景结果
- 6 步 retro 写实施偏差 + 改进项

---

## 4. 依赖影响

| 改 A | 影响 B | 影响 C |
|---|---|---|
| `testing-rules.md` § 6.5.1 | 新老测试都须按新表自查 | 现有 7 步流程不变 |
| `vitest.setup.ts` 网络拦截 | 现有 vitest 可能依赖真 fetch | 加单测维度 |
| `e2e/conftest.py` 共享 fixture | 现有 e2e 测试仍可独立运行 | 8 项契约作为参考 |
| `check-step.py` verify step | 现有 verify 段更严格 | 旧 verify.md 需重写 |
| 4 个模板更新 | 未来新任务用新模板 | 历史任务不受影响 |

---

## 5. 风险与缓解

| 风险 | 等级 | 缓解 |
|---|---|---|
| 前端 vitest 现有测试依赖真网络 | 🟡 | `__allowNetwork__` 标记 + 单测逐个加白名单 |
| check-step.py 10 不变量误报 | 🟡 | 限制为"traceability 段存在"才校验 |
| e2e/conftest.py 与 backend/.venv 缺失 | 🟡 | 仅新建文件，不依赖 venv 跑 |
| 4 个模板改动影响未来任务 | 🟢 | 模板改动以加段为主，不删旧 |
| 12 老任务路径兼容 | 🟢 | 不动 P0-7 task.yaml 契约 |
| 历史 verify.md 不符新规 | 🟡 | 标 LEGACY 兼容 · 新任务用新规 |

---

## 6. 测试矩阵

| Case | 输入 | 期望 |
|---|---|---|
| T1.test_verify_step_10_invariants | 含 10 个 trace 行（每条破一条） | 10 个错误各自对应 |
| T1.test_p1_3_digest_arrange_creates_5 | fixture 调用 | 5 个 DigestDailyItem |
| T1.test_p1_3_digest_arrange_idempotent | 同一 run 顺序跑 2 次 | 结果完全一致 |
| T1.test_p1_3_digest_arrange_seed_data_unchanged | hash seed_data/*.json | 字节未变 |
| T1.test_block_external_network_rejects | 真 fetch 调用 | reject 错误 |
| T4.test_legacy_12_tasks_exempt | 12 路径 | 全部 EXEMPT |
| T4.test_archive_exempt | docs/archive/ | EXEMPT |
| T4.test_new_task_2026_07_23_not_exempt | 新路径 | NOT EXEMPT |

---

## 7. 关联文档

> **product-doc.md 不适用**：refactor-6 路径不写 product-doc（纯测试基础架构重构，无产品新功能）。
> **design-spec.md 不适用**：本任务非 UI / 页面改动，refactor-6 非 UI 不写 design-spec。

- 调研：[`research.md`](research.md)
- 规格：[`spec.md`](spec.md)
- 决策：[`decisions.md`](decisions.md)
- 主账：`docs/issues.md` 决策 #30 · 债务 #18
- 公共规则：`AGENTS.md` § 0 / § 6.5 / § 6.7 / § 6.8 v2
- 现有机制：`scripts/check-step.py` · `scripts/check_test_quality.py` · `scripts/check-task.py` (P0-7)
- 模板：`docs/templates/tasks-template.md` · `docs/templates/verify-template.md` · `docs/templates/product-doc-template.md`
- 后端 fixture：`backend/tests/conftest.py` · `backend/tests/e2e/conftest.py` (新)
- 前端：`frontend/vitest.setup.ts`
