# Plan · AI 推送 digest pipeline stub 修复

> 日期：2026-07-25 · 作者：Claude · 版本：v1
> 配套：[research.md](research.md) · [tasks.md](tasks.md)

---

## 1 · 范围（来自 research § 3）

4 组件 · 7 任务 · 总估时 ~3.5h

## 2 · 方案

### 方案 A · 按层修（推荐）

按依赖顺序逐层实现：
```
seed 8 信源 (T1)
  ↓ DB 有数据
启动 scheduler (T2)
  ↓ cron 每分钟检查
修 Sources API GET/POST/PATCH (T3-T5)
  ↓ 用户能管理信源
E2E 验证 (T6-T7)
```

**优点**：每步独立可测 · 失败易定位 · TDD 友好
**缺点**：T1→T2 之间手动跑一次 push_daily 触发一次才好验

### 方案 B · 一次性写完

合并 T1-T5 为单 commit（seed + scheduler + API 一起）。

**优点**：commit 数少
**缺点**：失败定位难 · 违反 § 6.7 实施自校验（每 commit 都应 verify）

### ✅ 推荐：方案 A

理由：
1. AGENTS.md § 6.7 要求每 commit 单元 verify
2. seed 和 API 修改是两个独立 commit（不同关注点）
3. scheduler 启动需要先有 seed 数据 · 顺序明确

## 3 · 各 T 关键决策

### T1 seed 8 信源

- **幂等检查**：`SELECT COUNT(*) FROM digest_sources WHERE user_id IS NULL AND is_default = TRUE` · 已是 8 则跳过
- **数据源**：`backend/seed_data/digest_sources.json`（已存在 · 8 项）
- **额外字段**：seed 时填 `is_default=True`、`enabled=True`、`category` 用 JSON 里的"一手" / "二手"等
- **位置**：放在 `core/database.py:_run_phase1a_optimizations()` 之后 · 与 V3.1 collection seed 平行

### T2 scheduler 启动

- **asyncio 模式**：用 `asyncio.create_task(self._loop())` · 项目已有 archive_service.py 用同样模式
- **每分钟跑**：sleep 60 后再次跑（不是真的 cron · 简单方案）
- **错误处理**：try/except + log · 不让 scheduler 挂掉影响 backend
- **shutdown 取消**：on_shutdown 取消 task · 与 archive_task 模式一致

### T3 Sources API GET

- **DB query**：
  ```sql
  SELECT * FROM digest_sources
  WHERE (user_id = :u OR is_default = TRUE) AND enabled = TRUE
  ```
- **system_count**：`WHERE is_default = TRUE` count
- **user_count**：`WHERE user_id = :u` count
- **响应 shape 不变**（保持向后兼容）

### T4 Sources API POST

- **校验**：URL HEAD 请求 · 5s timeout · 失败 400
- **重复检查**：`UNIQUE(user_id, url)` 约束 · 重复 409
- **写 DB**：`DigestSource(user_id=user.id, enabled=True, is_default=False, ...)`
- **响应 201**：返回创建的对象

### T5 Sources API PATCH

- **所有权**：`source.user_id != user.id` → 403
- **enabled toggle**：`source.enabled = body.enabled` · 同时校验 spec § 2.4 系统默认 disabled 后 24h 自动重新启用（本次先实现基础 toggle · 24h 恢复留 TODO）
- **name rename**：`source.name = body.name`
- **响应 200**：返回更新后的对象

### T6 E2E pipeline 验证

- **步骤**：
  1. 重启 backend（应用 T1+T2+T3 修改）
  2. 验证 DB 中 8 行（`SELECT COUNT(*) FROM digest_sources`）
  3. curl `/api/digest/sources` → 返回 8 行
  4. 手动调用 `digest_scheduler.check_and_push()` 一次 → 验证 digest_daily 有 1 行
  5. curl `/api/digest/today` → 返回 items 数组
  6. curl `/push` 页面 → 看到 digest 卡片

### T7 verify + retro

- pytest backend 全量
- typecheck frontend（保持不变差）
- 写 retro.md（5 段必填）

## 4 · 验收（DOD）

### 4.1 必跑

- [ ] `cd backend && ./.venv/bin/python -m pytest tests/services/test_digest_*.py -v` 全绿
- [ ] `cd backend && ./.venv/bin/python -m pytest tests/api/test_digest_*.py -v` 全绿（新增 T3-T5 测试）
- [ ] 重启 backend 后 DB 中 `digest_sources` 行数 = 8
- [ ] 重启 backend 后 `digest_scheduler` task 已启动（log: "digest scheduler started"）
- [ ] `curl /api/digest/sources` 返回 8 行（不再是 hardcoded `[]`）
- [ ] 手动触发一次 `push_daily` 后 `digest_daily` 行数 = 1
- [ ] `curl /api/digest/today` 返回 200 + items 数组

### 4.2 验证观察

- [ ] 浏览器访问 `/push` 看到 5 张 digest 卡片
- [ ] 点击屏蔽按钮打开 HideDialog
- [ ] Sidebar 今日推荐高亮

## 5 · 风险 + 缓解

| 风险 | 缓解 |
|---|---|
| seed 重复插 | 幂等检查 · COUNT > 0 skip |
| scheduler 启动失败导致 backend 挂 | try/except + log · 不阻断 |
| RSS HEAD 网络 5s 超时 | aiohttp 5s timeout · 失败 400 |
| 系统默认 source PATCH 403 | spec 要求 · 严格按 spec |
| pytest fixture 与本地 DB 冲突 | pytest 用独立 DB（既有约定）|

## 6 · 关联

- [`research.md`](research.md)
- [`tasks.md`](tasks.md)
- `docs/tasks/2026-07-17-new-feature-ai-push/tasks.md § 9.1`（v2 audit stub 记录）
- `docs/issues.md` 债务 9（V4 AI 推送 stub 问题）

## 元信息

- **路径模式**：full-6（0→1→2→3→4→5→6）
- **范围**：🔴 完整修
- **估时**：~3.5h AI
- **commit 计划**：7 commits（T1-T7 各自 1 commit）