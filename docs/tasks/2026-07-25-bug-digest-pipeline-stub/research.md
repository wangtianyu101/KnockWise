# Research · AI 推送 digest pipeline stub 修复

> 日期：2026-07-25 · 作者：Claude · 版本：v1
> 配套：[plan.md](plan.md) · [tasks.md](tasks.md)

---

## 0 · 任务理解

用户原话："今日的推送还是失败呀"。

我的理解：v2 AI 推送模块的 backend 实现存在多处 stub / 未启动状态，导致 `/api/digest/today` 永远 404，前端页面看不到内容。

## 1 · 根因排查（已确认）

### 1.1 DB 实测

```sql
SELECT COUNT(*) AS cnt, SUM(IF(enabled,1,0)) AS en FROM digest_sources
-- 结果: cnt=0 · en=None
-- digest_daily count: 0
```

**digest_sources 表 0 行** · digest_daily 表 0 行。

### 1.2 链路缺口（5 处）

| # | 位置 | 问题 | 状态 |
|---|---|---|---|
| 1 | `main.py on_startup` | **不 seed 默认信源**（seed JSON 存在但从未写 DB）| ❌ |
| 2 | `main.py on_startup` | **不启动 DigestScheduler**（类存在但 main.py 不调）| ❌ |
| 3 | `api/digest/sources.py GET` | hardcoded `{system_count:8, items:[]}` 返回 | ❌ |
| 4 | `api/digest/sources.py POST` | 400 stub "待实现" | ❌ |
| 5 | `api/digest/sources.py PATCH` | 403 stub "待实现" | ❌ |

### 1.3 历史 commit 检索

```bash
git log --all --oneline | grep -i "digest.*seed\|digest.*schedul\|sources.*api"
# 找到: T13 (commit pending) Sources API（3 endpoint）
# 实际: stub 状态 · commit message 标 DONE 但代码是 stub
# 与 v2 tasks.md § 9.1 audit "T26 STUB" 一致
```

参考：v2 任务 `docs/tasks/2026-07-17-new-feature-ai-push/tasks.md § 9.1` 已 audit 出 stub 问题，但 2026-07-22 audit 修复时只补了 useDigest 接口，**漏了 seed/scheduler/API stub 这条**。

## 2 · 风险

| 风险 | 等级 | 缓解 |
|---|---|---|
| seed 重复插入（已存在时）| 🟡 | 幂等检查 · 用 `WHERE name + is_default + user_id IS NULL` 不存在才插 |
| scheduler 每分钟跑 → fetch_all_sources 慢 | 🟡 | DEDUP_WINDOW_MIN=60 已限制 · user 没到点直接 skip |
| Sources API POST/PATCH 改 DB 后 spec drift | 🟢 | 严格按 schemas/digest.py 实现（已定义）|
| APScheduler 引入新依赖 | 🟡 | 项目已有 apscheduler 在 venv（grep 验证）· 直接 import |
| RSS 校验 HEAD 网络调用 | 🟡 | spec R5 要求 · 5s timeout · 失败返回 400 |
| 测试 DB 是 TEMPORARY TABLE · 可能干扰 | 🟢 | pytest 用独立 DB · 不影响本地 MySQL |

## 3 · 范围

### 3.1 做（🔴 完整修）

| T# | 任务 | 工时 |
|---|---|---|
| T1 | seed 8 默认信源（main.py 启动逻辑）| 30 min |
| T2 | 启动 DigestScheduler（asyncio task）| 30 min |
| T3 | Sources API GET 改 DB query | 30 min |
| T4 | Sources API POST 改 DB insert | 45 min |
| T5 | Sources API PATCH 改 DB update | 30 min |
| T6 | E2E pipeline 验证（seed→push→fetch→render）| 30 min |
| T7 | verify + retro | 30 min |

### 3.2 不做

- 真实 RSS 抓取测试（依赖网络 + RSSHub · CI 不便跑）
- Email 推送通道（spec R6 · Phase 2）
- V3.1 collections 修复（与本次无关）

## 4 · 关联文档

- `docs/tasks/2026-07-17-new-feature-ai-push/spec.md` § 4 数据契约
- `docs/tasks/2026-07-17-new-feature-ai-push/api-spec.md` § 3.D Sources API
- `docs/tasks/2026-07-17-new-feature-ai-push/db-design.md` § 2 表
- `backend/services/digest_scheduler.py` — 已有类 · 直接用
- `backend/services/digest_service.py` — push_daily 已实现
- `backend/schemas/digest.py` — schemas 已定义

## 元信息

- **调研日期**：2026-07-25
- **路径模式**：fix-mini（普通 Bug · 0→4→6）实际跨多组件按 full-6 跑
- **下次**：[plan.md](plan.md) → [tasks.md](tasks.md) → 实施 T1-T7