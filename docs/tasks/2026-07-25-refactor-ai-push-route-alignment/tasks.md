# Tasks · AI 推送路由对齐 v2 设计（refactor-6）

> 日期：2026-07-25 · 作者：Claude · 版本：v1
> 配套：[plan.md](plan.md) · [research.md](research.md)
> 模板：[docs/templates/tasks-template.md](../../templates/tasks-template.md)
> **策略**：TDD（红→绿→refactor）· 每任务 1 commit · 每任务 ≤ 1h · 配套单测
> **范围**：P0（路由迁移 /ai/* → /push/* + 新建 daily detail 整页）

---

## § 1 · 任务粒度原则

✅ 每任务 ≤ 1h AI 工作量 · 1 commit · ≥ 1 测试
✅ 测试代码与实现代码同 commit（`refactor:` / `feat:` 同 hash）
✅ 依赖关系 DAG（无环 / 拓扑序）
✅ 任务命名 `T<n>: <动词 + 名词>`

---

## § 2 · 任务清单（13 个 · 按阶段 A-D）

### 阶段 A · 路由迁移（4h）

- [ ] **T1**: 迁移 pages/ai/today.tsx → pages/push/index.tsx
  - 文件: `frontend/pages/push/index.tsx`（新）· 删除 `frontend/pages/ai/today.tsx`
  - 测试: snapshot test · 验证路由 `/push` 渲染 today 组件
  - 依赖: —
  - 估时: 15 min
  - commit: `refactor(push): 迁移 /ai/today → /push（v2 设计对齐）`

- [ ] **T2**: 迁移 pages/ai/bookmarks.tsx → pages/push/bookmarks.tsx
  - 文件: `frontend/pages/push/bookmarks.tsx`（新）· 删除 `frontend/pages/ai/bookmarks.tsx`
  - 测试: 路由 `/push/bookmarks` 渲染
  - 依赖: —
  - 估时: 10 min
  - commit: `refactor(push): 迁移 /ai/bookmarks → /push/bookmarks`

- [ ] **T3**: 迁移 pages/ai/settings.tsx → pages/push/settings.tsx
  - 文件: `frontend/pages/push/settings.tsx`（新）· 删除 `frontend/pages/ai/settings.tsx`
  - 测试: 路由 `/push/settings` 渲染
  - 依赖: —
  - 估时: 10 min
  - commit: `refactor(push): 迁移 /ai/settings → /push/settings`

- [ ] **T4**: 迁移 pages/ai/sources.tsx → pages/push/sources.tsx
  - 文件: `frontend/pages/push/sources.tsx`（新）· 删除 `frontend/pages/ai/sources.tsx`
  - 测试: 路由 `/push/sources` 渲染
  - 依赖: —
  - 估时: 10 min
  - commit: `refactor(push): 迁移 /ai/sources → /push/sources`

### 阶段 B · 导航 + 测试同步（1h）

- [ ] **T5**: 更新 Layout.tsx sidebar 导航
  - 文件: `frontend/components/v3/Layout/Layout.tsx`（3 处）
    - L142: `{ page: '/ai/today', href: '/ai/today', ... }` → `{ page: '/push', href: '/push', ... }`
    - L143: `{ page: '/ai/history', href: '/ai/history', ... }` → 保持（history 暂不动）
    - L176: `'/ai/today': '今日推荐'` → `'/push': '今日推荐'`
    - L177: `'/ai/history': '推送历史'` → 保持
  - 测试: snapshot test 验证导航配置
  - 依赖: T1
  - 估时: 15 min
  - commit: `refactor(layout): sidebar 导航 /ai/today → /push`

- [ ] **T6**: 更新 3 个 E2E/Visual spec 文件
  - 文件:
    - `frontend/tests/e2e/pages.spec.ts`
    - `frontend/tests/visual/digest.spec.ts`
    - `frontend/tests/e2e/a11y.spec.ts`
  - 测试: 跑相关 spec 全绿
  - 依赖: T1-T5
  - 估时: 30 min
  - commit: `test(e2e): 更新 /ai/* → /push/* 路由引用`

### 阶段 C · daily detail 新建（2h）

- [ ] **T7**: 新增 useDigestDate hook
  - 文件: `frontend/hooks/useDigest.ts`（追加 `useDigestDate(date)`）
  - 类型: `QueryHookResult<DigestToday>`（同 useDigestToday 接口）
  - URL: `GET /api/digest/daily/${date}`
  - 测试: hook 单测（mock fetch 返回 mock data）
  - 依赖: —
  - 估时: 20 min
  - commit: `feat(hooks): useDigestDate 包装 /api/digest/daily/{date}`

- [ ] **T8**: 新建 pages/push/daily/[date].tsx
  - 文件: `frontend/pages/push/daily/[date].tsx`
  - 内容（按 mockup 02）:
    - 返回今日 5 条 link
    - 双轴标签 + 元信息行
    - 标题 H1
    - 完整摘要
    - 原文来源块（📰 · source_name + URL + 发布时间）
    - 三个按钮：已收藏 / 分享 / 不再推送类似
    - 相关历史 digest 列表（从 `item.related_item_ids` 查 · 暂显示 item title + 跳转回 daily）
    - HideDialog 集成
    - Loading: 5 Skeleton
    - 404 Error: "当日无 digest · 返回今日"
    - 其他 Error: 红 banner + 重试
  - 测试: vitest RTL · 渲染验证 + mock data 验证
  - 依赖: T7
  - 估时: 1.5 h
  - commit: `feat(push): daily/[date] 详情页（mockup 02）`

- [ ] **T9**: e2e/digest.spec.ts 加 daily detail scenario
  - 文件: `frontend/tests/e2e/digest.spec.ts`（追加 scenario）
  - Scenario: 访问 /push/daily/2026-07-17 · 验证渲染
  - 测试: Playwright scenario 通过
  - 依赖: T8
  - 估时: 30 min
  - commit: `test(e2e): daily detail scenario`

### 阶段 D · 验证 + 收尾（30 min）

- [ ] **T10**: tsc --noEmit + npm run build 全绿
  - 文件: —
  - 验证: typecheck 不引入新 error（既有 10 个不动）
  - 依赖: T1-T9
  - 估时: 5 min
  - commit: 与上一个 T 合并

- [ ] **T11**: npm test --run 全绿
  - 文件: —
  - 验证: vitest 全部通过（26+ files / 210+ tests）
  - 依赖: T10
  - 估时: 10 min
  - commit: 与上一个 T 合并

- [ ] **T12**: Playwright e2e + visual 全绿
  - 文件: —
  - 验证: e2e/digest.spec.ts 5+ scenario + visual/digest.spec.ts 通过
  - 依赖: T11
  - 估时: 10 min
  - commit: 与上一个 T 合并

- [ ] **T13**: 写 retro.md（§ 6 复盘）
  - 文件: `docs/tasks/2026-07-25-refactor-ai-push-route-alignment/retro.md`
  - 内容: 做对了什么 / 踩坑 / 调研偏差 / 下次改进 / memory 清单
  - 依赖: T1-T12
  - 估时: 5 min
  - commit: 与最后一个 T 合并

---

## § 3 · 实施顺序（拓扑序）

```
T1 ──┐
T2 ──┤
T3 ──┼──> T5 ──> T6 ──┐
T4 ──┘                │
                      │
T7 ──> T8 ──> T9 ─────┴──> T10 ──> T11 ──> T12 ──> T13
```

可并行：
- T1/T2/T3/T4 互相独立（4 个 page 文件迁移）· 可一起改
- T5 依赖 T1（sidebar 链接要 /push 存在）
- T6 依赖 T1-T5（测试要引用新路径）
- T7 与 T1-T4 并行（hook 独立）

建议 commit 顺序：**T1+T2+T3+T4（1 commit）→ T5 → T7 → T6 → T8 → T9 → T10+T11+T12+T13（1 commit verify）**

总计 6-7 commits。

---

## § 4 · 测试覆盖矩阵

| Page / Hook | vitest RTL | e2e Playwright | visual |
|---|---|---|---|
| /push (today) | 既有 ✅ | T9 追加 daily | 既有 ✅ |
| /push/bookmarks | 既有 ✅ | T6 更新 | 既有 ✅ |
| /push/settings | 既有 ✅ | T6 更新 | — |
| /push/sources | 既有 ✅ | T6 更新 | — |
| /push/daily/[date] | T8 ✅ | T9 新增 | — |
| useDigestDate | T7 ✅ | — | — |

---

## § 5 · 风险 + 缓解

| 风险 | 缓解 |
|---|---|
| type error 累计 | commit 前 tsc 比对 · 不变差 |
| 旧 /ai/* 链接失效 | 后续 P1 加 redirect · 本次接受 404 |
| related items 当前为空 | 页面对 0 条 related 显示"暂无相关历史" |
| mockup 02 与既有 dark glassmorphism 一致 | 实现按 mockup 02 · 风格统一 |

---

## § 6 · 总估时

| 阶段 | 工时 |
|---|---|
| A · 路由迁移 | 45 min |
| B · 导航 + 测试同步 | 45 min |
| C · daily detail 新建 | 2 h |
| D · 验证 + 收尾 | 30 min |
| **合计** | **~4 h AI** |

---

## § 7 · commit 历史表（实施后回填）

| 实际 commit | 估时 vs 实际 | 偏差分析 |
|---|---|---|
| _pending_ | — | — |

---

## § 8 · 元信息

- **任务作者**：Claude
- **任务日期**：2026-07-25
- **路径模式**：refactor-6（路径全 6 步）
- **范围**：P0
- **依赖**：v2 设计 docs/tasks/2026-07-17-new-feature-ai-push/
- **关联**：[`docs/issues.md`](../../issues.md) · [`docs/rules/milestones.md`](../../rules/milestones.md)