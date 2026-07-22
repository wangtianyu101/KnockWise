# Verify · AI 推送 Harness 治理（阶段 5）

日期：2026-07-22

验证快照：`10c11c3`（验证期间工作树存在其他任务的未提交文件，未纳入本结论）

结论：**❌ FAILED · 验证已执行，但 Harness 项目尚未闭环**

> 本文只记录实际命令结果。自动化测试“通过”不等于四条目标链路均已实现；缺失、Mock 越界和运行时失败均按失败记录。

## 1. 结论摘要

| Gate / 链路 | 实际结果 | 结论 |
|---|---|---|
| 空测试质量扫描 | 44 files / 681 AST tests / **0 violations** / exit 0 | ✅ |
| 后端全量 pytest | **698 passed / 1 skipped / 4 xfailed / 0 failed** | ✅ |
| 后端覆盖率 | global line **61.55%**；Digest line **85.61%** / branch **82.00%** | ✅ |
| MySQL 集成 | TEMPORARY TABLE round-trip **1 passed** | ✅ |
| API + RSS + mocked orchestration | **38 passed** | 🟡 仅部分满足 |
| Digest LLM 契约 | `test_digest_llm.py` 不存在；Digest 路径 `ainvoke` 引用为 0 | ❌ |
| 真正 E2E | DB、模型、偏好和 RSS 均被 Mock；Email 断言 `NotImplementedError` | ❌ |
| 前端 Vitest | **26 files / 210 passed** | ✅ |
| 前端 typecheck | exit 2，**12 条 TypeScript diagnostics** | ❌ |
| Next build | exit 1，页面目录中的测试文件被识别为 Next page | ❌ |
| Playwright Digest | **0 passed / 5 failed** | ❌ |
| L5 基础路径 | 5 个服务同时监听；health/login/dashboard/settings/list 均 HTTP 200 | ✅ |
| 后端优雅停机 | `NameError: asyncio is not defined` | ❌ |

**最终判断**：CI 接线与空测试阻断器可信，但“API、LLM、RSS、真正 E2E 各一条真实链路”尚未满足，因此不能把阶段五写成通过。

## 2. 步骤 4 分布式证据引用（L1 / L2 / L4）

### L1 · 类型与构建

- `cd frontend && npx tsc --noEmit` → exit 2，12 条 diagnostics。
- `cd frontend && npm run build` → exit 1；首个错误为 `.next/types/validator.ts` 将 `pages/learn/index.test.tsx` 当作 Page module。
- 结论：**L1 未通过**，CI 的 `frontend-test` 会正确阻断。

### L2 · 单元测试与覆盖率

```bash
python3 scripts/check_test_quality.py backend/tests
cd backend
./.venv/bin/python -m pytest tests/ -q \
  --cov=agents --cov=api --cov=core --cov=models \
  --cov=schemas --cov=services --cov=utils --cov=voice \
  --cov-branch --cov-report=json:coverage.json
./.venv/bin/python ../scripts/check_coverage.py coverage.json \
  --global-lines 61 --file services/digest_service.py \
  --file-lines 80 --file-branches 70
cd ../frontend && npm test
```

实际结果：

- Test quality：44 files / 681 tests / 0 violations。
- Backend：698 passed / 1 skipped / 4 xfailed。
- Coverage gate：global 61.55%；Digest line 85.61%；Digest branch 82.00%。
- Frontend：26 files / 210 tests passed。
- 结论：**L2 自动化基线通过**；它不能替代缺失的契约和真实 E2E。

### L4 · 独立 review

- T34 CI wiring 第一轮 verifier：FAIL，发现不存在的 `setup-node@v7`。
- 修复 commit：`3ff6566`，改为官方有效的 `setup-node@v6` 并修正契约测试。
- 第二轮 verifier：PASS。
- 结论：**L4 仅证明 CI wiring 对齐，不证明业务链路完成**。

## 3. L3 · 整合测试

### L3-1 · API / RSS / 编排回归

```bash
cd backend
./.venv/bin/python -m pytest \
  tests/api/test_digest_api.py \
  tests/services/test_digest_service.py \
  tests/services/test_rss_fetch.py \
  tests/e2e/test_digest_push.py -q
```

结果：**38 passed**。

| 场景 | 期望 | 实际 | 结论 |
|---|---|---|---|
| API contract | 完整 FastAPI app + 真实测试 DB，并断言 DB 状态 | 16 tests 通过，但使用每个 router 的独立 TestClient；没有真实 DB 状态断言 | 🟡 |
| RSS / Atom | 固定 fixture、重试、部分失败、非法 XML、去重、RSSHub fallback | RSS/Atom、重试、部分失败、非法 XML有覆盖；无去重；明确无 RSSHub fallback | 🟡 |
| LLM contract | Mock `ainvoke`，验证 prompt、解析、fallback、超时/限流/异常/scope | `backend/tests/services/test_digest_llm.py` 不存在；Digest service/test 中 `ainvoke` 引用 0 | ❌ |
| Scheduler → DB → API → Email | 仅 Mock RSS/LLM/Email/Clock，内部 Scheduler/Service/ORM/DB/API 全真实 | 测试直接调用 `push_daily`；DB 是 AsyncMock；模型被 patch；没有 Scheduler/API 查询；Email 只验证 `NotImplementedError` | ❌ |

### L3-2 · MySQL round-trip

```bash
cd backend
RUN_MYSQL_INTEGRATION=1 ./.venv/bin/python -m pytest \
  tests/integration/test_mysql_ci.py -v
```

结果：**1 passed**。测试在真实本机 MySQL 创建 TEMPORARY TABLE，完成 insert/select；未写入持久业务数据。

### L3 最终结果

**结果：❌ FAILED**。已有回归测试通过，但缺少 Digest LLM 契约，且 `test_digest_push.py` 不符合约定的真实 E2E 边界。

## 4. L5 · staging 运行时验证

### L5-1 · 五服务与基础用户路径

由于托管沙箱禁止绑定本机端口，使用授权后的持续 PTY 启动服务。验证时以下端口同时 LISTEN：

- MySQL `3306`
- Redis `6379`
- LiveKit `7880`（HTTP 200）
- Backend `8000`
- Frontend `3000`

实际 HTTP 结果：

| 请求 | 期望 | 实际 | 结论 |
|---|---:|---:|---|
| `GET /api/health` | 200 | 200 | ✅ |
| `GET /ai/today` | 200 | 200（但为 EmptyState） | 🟡 |
| `GET /api/auth/dev-login?user_id=1` | 200 | 200 | ✅ |
| `GET /api/dashboard` + Bearer token | 200 | 200 | ✅ |
| `GET /api/digest/settings` + Bearer token | 200 | 200 | ✅ |
| `GET /api/digest/dailies?limit=7` + Bearer token | 200 | 200，空列表 | ✅ |

### L5-2 · Playwright 用户场景

```bash
cd frontend
npx playwright test tests/e2e/digest.spec.ts --project=chromium-desktop
```

结果：**5 failed / 0 passed**。

1. `/ai/today` 期望 5 个 `.digest-card`，实际 0 个。
2. 收藏按钮不存在，等待 30 秒超时。
3. 屏蔽按钮不存在，等待 30 秒超时。
4. `/ai/bookmarks` 运行时报 `No QueryClient set`。
5. `/ai/settings` 运行时报 `No QueryClient set`。

附带事实：每个场景的 `beforeEach` 访问 `/login` 都得到 404，但测试未对登录页做断言。

### L5-3 · 优雅停机

停止 Backend 时，`backend/main.py` 的 shutdown handler 捕获 `asyncio.CancelledError`，但模块未导入 `asyncio`，最终报：

```text
NameError: name 'asyncio' is not defined
Application shutdown failed.
```

### L5 最终结果

**结果：❌ FAILED**。基础服务与只读 API 可达，但 Digest 用户路径 5/5 失败，Backend 优雅停机失败。

## 5. Mock 边界实测

目标边界：RSS / LLM / Email / Clock。

当前实际边界：RSS + 用户偏好 + DB session + ORM models 均被 Mock；LLM 链不存在；Email 尚未实现。

因此当前不能声明：

```text
Scheduler → RSS Mock → LLM Mock → 真实测试数据库 → API → Email Mock
```

实际只能声明：

```text
DigestService.push_daily → RSS/Preference/DB/ORM Mock → 返回值断言
```

## 6. 未通过项与关闭条件

| ID | 未通过项 | 关闭条件 |
|---|---|---|
| V5-01 | Digest LLM contract 缺失 | 实现应用与模型契约并补 prompt/parse/fallback/error/scope 测试 |
| V5-02 | 后端 E2E Mock 越界 | 真实 Scheduler/Service/ORM/MySQL/API；仅 Mock RSS/LLM/Email/Clock |
| V5-03 | Email 未实现 | 替换 `NotImplementedError`，验证 mock provider 只调用一次及幂等 |
| V5-04 | RSSHub fallback 与去重缺失 | 实现并验证 fallback、重复文章和非法 XML |
| V5-05 | 前端 L1 失败 | `tsc --noEmit` 与 `next build` exit 0 |
| V5-06 | Digest Playwright 5/5 失败 | 页面接真实/测试 API，5 scenario 全绿 |
| V5-07 | Backend shutdown 失败 | 导入/使用 `asyncio` 正确，启动后 SIGINT 无 shutdown error |
| V5-08 | GitHub required checks 未配置 | push workflow 后将三个 checks 设为 required |

## 7. 可复现命令

```bash
python3 scripts/check_test_quality.py backend/tests

cd backend
./.venv/bin/python -m pytest tests/ -q --cov=agents --cov=api --cov=core \
  --cov=models --cov=schemas --cov=services --cov=utils --cov=voice \
  --cov-branch --cov-report=json:coverage.json
./.venv/bin/python ../scripts/check_coverage.py coverage.json \
  --global-lines 61 --file services/digest_service.py \
  --file-lines 80 --file-branches 70
RUN_MYSQL_INTEGRATION=1 ./.venv/bin/python -m pytest \
  tests/integration/test_mysql_ci.py -v

cd ../frontend
npm test
npx tsc --noEmit
npm run build
npx playwright test tests/e2e/digest.spec.ts --project=chromium-desktop
```

## 8. 验收状态

- 文档事实核对：✅ 已按 2026-07-22 实测重写。
- L3：❌ 未通过。
- L5：❌ 未通过。

---

## 9. T39 前端增量复验（2026-07-22 22:08～22:10 CST）

> 本节是 V5-05 / V5-06 的最新增量证据，覆盖本文前面对前端失败的历史快照；不自动推导整个阶段五通过。

实现提交：`e57890e test(frontend): complete T39 digest browser harness`

| Gate | 命令 | 结果 | 退出码 |
|---|---|---|---:|
| Vitest | `cd frontend && npm test` | **27 files / 210 passed** | 0 |
| TypeScript | `cd frontend && npx tsc --noEmit` | **0 errors** | 0 |
| Production build | `cd frontend && npm run build` | **compiled / 31 static pages** | 0 |
| Browser E2E | `cd frontend && npx playwright test tests/e2e/digest.spec.ts --reporter=line` | **5 passed / 9.1s** | 0 |

Playwright 五个场景：

1. `/ai/today` 展示 5 条 Digest 与 vibe；
2. 收藏后按钮变为“已收藏”；
3. 屏蔽操作打开 HideDialog；
4. `/ai/bookmarks` 展示收藏数据；
5. `/ai/settings` 保存并回读 `push_hour=7`。

Mock 边界：浏览器侧只拦截 `/api/digest/**`，fixture 固定且不访问公网；因此本节结论是“前端用户路径 E2E”，不冒充 Scheduler / ORM / MySQL 的系统 E2E。

环境记录：`./scripts/start.sh` 确认 MySQL、Redis 在线，但 LiveKit 在沙箱内绑定 UDP 时返回 EPERM。T39 不依赖 LiveKit；该结果不能作为完整 L5 五服务通过证据。

关闭状态：

- V5-05 前端 L1：✅ CLOSED。
- V5-06 Digest Playwright：✅ CLOSED。
- 阶段五总状态：仍保持未闭环，等待后端修复链统一重验、T38 verifier 收口与 GitHub required checks 配置。
- 阶段五：**未通过，等待 V5-01～V5-08 修复后重验**。
- 用户 gate：⏳ 待用户确认本验证结论；不得进入“项目闭环”状态。
