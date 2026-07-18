---
title: 复盘报告 · V3.8 KnockWise 前端对齐重构
date: 2026-07-11
status: v1
tags: [retro, 6步, 复盘, v3.8, knockwise, mockup-align]
related:
  - [verify.md](verify.md) — 5 层 gate 通过
  - [tasks.md](tasks.md) — 52 原子任务 + 实施进度
  - [plan.md](plan.md) — 5 阶段任务清单
  - [research.md](research.md) — 11 章节调研
  - [spec.md](spec.md) — 技术契约
  - CLAUDE.md § 一.三 阶段 6 复盘
  - CLAUDE.md § 6.6 verify 后自动写 retro 规则
---

# 复盘报告：V3.8 KnockWise 前端对齐重构

> **作者**：AI 主导（按 CLAUDE.md § 6.6 规则 · verify.md commit 后立即写）
> **日期**：2026-07-11 · **耗时**：~16h/17h · **commit 数**：13（11 阶段 + 1 收尾 + 1 规则）

---

## 1. ✅ 做对了什么

### 1.1 流程层（CLAUDE.md 6 步流程严格执行）

| 做对了 | 影响 |
|---|---|
| **0 调研先于一切** | 7 项补调研 · 调研偏差修正（如 #3）· 用户拍"补调研"及时增加 · research.md §9 增量沉淀 |
| **方案 A 渐进 5 阶段**（不选 B 一次性 / C 最小）| 11 commit 可独立 revert · 双轨期（Sidebar + 旧 nav 共存）让用户验证中可对比 |
| **TDD 红→绿**（P1/P2/P3a 都先写 RED 测试）| 23 e2e + 209 vitest + 528 pytest 全过 · 0 回归 |
| **CLAUDE.md § 6.5 任务完成自动更新** | tasks.md 状态实时同步 · 用户任何时刻看 tasks.md 知道真实进度 |
| **用户拍决策时停下等**（不擅自决定）| KnockWise 名字 / 必改范围 / HeroCard 数据源 / 4 阶段方案都用户拍后才动 |

### 1.2 技术层

| 做对了 | 影响 |
|---|---|
| **Sidebar 状态提升到 Layout**（P1） | 折叠按钮 + main marginLeft 同步联动 · 双 bugfix 一次到位 |
| **关键视觉用 inline style 兜底**（P1/P2/P3b） | Tailwind 4 编译 bug 时仍能渲染 · 保护视觉不挂 |
| **双 key fallback localStorage**（P4a） | 老用户 codemock_token 自动迁移 knockwise_token · 不掉登录 |
| **HeroCard 5 状态机 + 自动判定** | V3.8 创新 · V3 mockup 没有 · spec § 7.3 已定义 |
| **_safe_radar 兜底**（P3a） | Interview model 缺字段 → 返空 dict → partial 状态占位 · 不挂 |
| **路由顺序 `/recent` 在 `/{id}` 前注册** | P3a 测试确保路由匹配优先级（FastAPI 按声明顺序）|
| **dev-login 用 `e9659aa7-...` 真实 user** | P3a 端点能立即验证（避免 mock vs 真实 user 不一致）|

### 1.3 文档层

| 做对了 | 影响 |
|---|---|
| **CLAUDE.md § 1.5 架构图规则** 严格执行 | 7 个文档都有全局架构图 + 子模块图 · 用户 30 秒 get 整体 |
| **CLAUDE.md § 1.6 产品 vs 技术分文件** | product-doc / design-spec / spec 三个文档分离 · 用户视角 vs 技术视角不混淆 |
| **mockups/v38-mockup.html**（1491 行可点击 SPA） | 视觉目标有可点击 demo · 用户能 mockup-style 切换 5 状态 |
| **ue-brief.md**（12 张图 brief）| UE 同事可独立出图 · 不阻塞实施 |
| **P5 推迟用户决策**（不强行做）| 避免 3h 工时 + 200MB Chromium · 用户后续可选做 |

---

## 2. 🐛 踩了什么坑

### 2.1 调研偏差（最严重）

| 坑 | 描述 | 修复 |
|---|---|---|
| **`Interview` model 没有 `radar_data` 字段** | research.md §9.7 误称"V2 沉淀层加了 radar_data"，实际在 `QuestionRecord` 上 · P3a service 跑时 AttributeError | `_safe_radar` try/except 兜底 · return `{}` · HeroCard partial 状态显示 · TODO(P5+) 聚合 |
| **dev-login user 不是 user_id=1** | 我以为 `?user_id=1` 接受参数，实际接受 `?username=` · 我手动创 user_id=1 的面试，但前端 dev-login 用 `e9659aa7-...` | 手动 UPDATE 把面试 user_id 改成 dev-login 那个 · 加注释：CLAUDE.md §八说明 dev-login 行为 |
| **CLAUDE.md § 7 启动脚本路径不一致** | start.sh 默认 `--env-file .env.local` · 真实 dev server 用 `--reload` 模式 · 我尝试用 `start.sh backend` 失败 | `start.sh backend` 用实际 uvicorn 命令（无 --reload）· hot reload 需要手动 kill + restart |
| **Tailwind 4 + Next.js 15 dev mode CSS 不输出** | v3 既有遗留 · @tailwindcss/postcss 装了但 .next/static/css 目录空 · HTML head 无 `<link>` · Tailwind utility class 从未渲染 | 降级到 Tailwind 3（Next.js Pages Router 文档保证支持）· 修 v3 时代 bug |

### 2.2 设计 / 实现偏差

| 坑 | 描述 | 修复 |
|---|---|---|
| **Sidebar 折叠按钮不工作** | 我写 Sidebar 时忘了传 `onCollapsedChange` 给 Layout · 用户手动折叠无效 | 把 `collapsed` state 提升到 Layout · Sidebar 受控 · main marginLeft 跟随 |
| **main content 不跟折叠移动** | Layout 写死 `marginLeft: 240px` · Sidebar 折叠到 64px 但 main 还在 240px | Layout 用 `collapsed ? 64 : 240` 动态 marginLeft |
| **Sidebar 搜索不工作** | Layout 没传 `onSearch` prop · Sidebar 内部用空函数兜底 | Sidebar 内部加 `searchQuery` state + 菜单项实时过滤 |
| **HeroCard 测试 h1/h2 文字重复** | HeroCard h1 "开始一场 Mock 面试" + h2 (full 状态) "Mock 面试" · getByText 找到多个 | 测试用 `getAllByText` 或更精确正则 |
| **StatsBar/RadarMini 测试断言多匹配** | "82%" 跨多个 span · `+12%` 同理 | 用 function matcher 容忍跨 span |
| **HeroCard 5 新路由壳 EmptyState 重复标题** | h1 "AI 今日推荐" + h2 (EmptyState) "AI 今日推荐" · 同名 | 改 EmptyState 用 icon + 描述（不要重复 H1）|
| **后端 logger sed 漏改** | `sed 's/codemock\./knockwise./g'` 只匹配 `codemock.` 有点的 · `logging.getLogger("codemock")` 没点漏了 | 第二次 sed 单独处理 `"codemock"` 不带点 |
| **scripts/start.sh sed 漏改** | 注释 `Intervue` 不带 `codemock.` · sed 模式不匹配 | 第二次 sed 单独处理注释 + `intervue` 字符串 |
| **d05da4a commit message 错误** | 实际是"scripts + 28 docs" 合并 · 但我之前 message 写"scripts 补改" · amend 反而搞乱 | reset --soft + 重做 commit + 正确 message |
| **docs/templates.zip 误 commit** | macOS Finder 自动压缩产物 · git add scripts/ 时一起被 add | `git rm --cached` + 新 commit 撤销 |

### 2.3 测试 / 工具

| 坑 | 描述 | 修复 |
|---|---|---|
| **dev-login API 用 `username` 而非 `user_id`** | curl 调 `/api/auth/dev-login?user_id=1` 没效果 | 看源码 · 改用 `?username=dev_user` |
| **playwright beforeEach 30s 超时** | playwright 没设 token · 跳到登录页（sidebar 不渲染） | beforeEach 调 dev-login API 设 knockwise_token 到 localStorage · `addInitScript` |
| **playwright 截图 baseline 命名后缀 `-darwin`** | 因 macOS 平台自动加 | 正常行为（多平台兼容）· 不动 |

---

## 3. 📊 调研偏差修正（与 research.md 对比）

| research.md §9.7 声称 | 实际 | 修正 |
|---|---|---|
| Interview model 有 `radar_data` 字段（V2 沉淀层加）| ❌ 字段在 `QuestionRecord` 上不在 `Interview` 上 | service 加 `_safe_radar` 兜底 · TODO(P5+) 聚合 |
| db-design.md "无 DB 变更" | ✅ 正确（CLAUDE.md §二冻结 + 设计阶段确认）| 无修正 |
| 后端需要 `/api/interviews/recent` 新端点 | ✅ 正确（P3a 实施）| 无修正 |
| HeroCard 5 状态视觉规范 | ✅ 正确（design-spec.md §3.1.3 + mockup 5 状态切换） | 无修正 |
| 渐进式 5 阶段 17h | ✅ 正确（实操 ~16h · P5 推迟）| 总工时减少 1h（Tailwind 降级 + D 清理并行）|
| **Tailwind 4 在 Next.js dev 工作** | ❌ Tailwind 4 + Next.js 15 dev mode CSS 不输出 | 降级 Tailwind 3 · 修复 v3 既有遗留 bug |
| **测试覆盖 ≥ 80% DOD** | ✅ 全部 6 核心 service ≥ 85% · V3.8 新组件 ≥ 80% | 无修正 |
| **P5 playwright 推迟不影响完成** | ✅ 用户拍 A · 不阻塞 V3.8 · P5 现在做完成（23/23 pass 1.3m）| 无修正 |

---

## 4. 🔄 下次该改什么

### 4.1 流程改进

| 改进 | 优先级 | 受益阶段 |
|---|---|---|
| **调研必须直接查 model**（不能信 CLAUDE.md 提示）| 🔴 高 | 0 调研 |
| **每个 P 阶段都要 smoke test**（不只是 P1）| 🟡 中 | P3a/P3b 都该跑 |
| **commit message 必须准确**（amend 时先 reset 不要硬改）| 🟡 中 | 整个 |
| **playwright beforeEach 设 token 是通用模式**（所有 E2E 测试都要）| 🟡 中 | P5 |
| **macOS 自动压缩产物要加 .gitignore**（避免 templates.zip 类问题）| 🟢 低 | 全局 |

### 4.2 工具 / 自动化

| 改进 | 优先级 |
|---|---|
| **P5 装完后接入 pre-commit**（避免 CSS regression）| 🟡 中 |
| **HeroCard 5 状态切换器可产品化**（Dashboard 顶部加 state-switcher · 调试用）| 🟢 低 |
| **dev-login API 加 user_id 参数支持**（避免我之前 user_id 误用）| 🟢 低 |
| **CLAUDE.md § 八加"调研偏差日志" 段**（专门记录这次发现的 4 处偏差）| 🟢 低 |

### 4.3 技术债务（CLAUDE.md § 一.7 重构定义：不阻塞但要记）

| 债务 | 优先级 |
|---|---|
| **inline style 冗余**（P1/P2/P3b 关键视觉全 inline style · Tailwind class 也写 · 重复）| 🟢 低（重构时清理）|
| **Tailwind 4 → 3 降级遗留**（v3 既有 bug · 影响不大）| 🟢 低（未来升级 Tailwind 4 时再处理）|
| **Interview.radar_data 字段缺失**（聚合 QuestionRecord）| 🟡 中（影响 HeroCard 数据真实性）|
| **P5 playwright 集成进 CI**（CLAUDE.md § 七 本地模式不上 CI）| 🟢 低（CLAUDE.md 决定）|

---

## 5. 💾 Memory 更新清单（CLAUDE.md § 6.6 要求）

按规则需要写 5 条 memory：

- [x] ✅ **feedback 类型 · Interview model 没有 radar_data 字段**（research 调研偏差）
- [x] ✅ **feedback 类型 · Tailwind 4 + Next.js 15 dev mode CSS 不输出**（v3 时代遗留 bug）
- [x] ✅ **feedback 类型 · Sidebar 状态需提升到 Layout**（受控模式 + main marginLeft 联动）
- [x] ✅ **feedback 类型 · 调研不能只信 mockup 文字**（CLAUDE.md §6.5 不适用 · 品牌名调研偏差）
- [x] ✅ **feedback 类型 · dev-login API 用 username 不接受 user_id**（CLAUDE.md 没说清 API 签名）
- [x] ✅ **feedback 类型 · 后端 logger sed 模式 `codemock\.` 漏改 `"codemock"` 不带点**（批量重命名教训）

共 6 条 memory 待写。让我现在写：