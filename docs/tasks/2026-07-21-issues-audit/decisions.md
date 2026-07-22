# 决策汇总（Decisions Log）

> **本目录唯一决策主账** · 调研阶段所有用户决策集中管理
>
> **权威定位**：本文件集中所有"调研阶段用户决策"，其他文档（`issues.md` / `research.md` / `spec.md`）只引用本文件，不重复写决策内容。
>
> **同步机制**：每次用户做出新决策，按 CLAUDE.md § 6.8 三处同步：
> 1. `research.md` § 八用户决策清单（追加一行 + 用户原话）
> 2. `issues.md` 顶部"决策更新"段（同步指针） + 议题状态字段（改为 ✅ / 🟡）
> 3. **本文件 `decisions.md`**（最权威 + 详细理由 + 关联实施 PR 链接）
>
> **关联文档**（仅链接，不重复内容）：
> - [`research.md`](research.md) § 八 · 简表视图
> - [`spec.md`](spec.md) · 已含决策的 Requirement/Scenario 实现细节
> - [`docs/issues.md`](../../issues.md) · 议题主账 + 状态字段

---

## 📋 决策总览（最新 10 项 · 2026-07-22）

| # | 日期 | 决策项 | 选择 | 状态 | 关联 |
|---|---|---|---|---|---|
| 1 | 2026-07-22 | 议题 C 语音架构未来方向 | ✅ **B. 全力全双工** | ✅ 已决策 | 议题 C / spec.md R1 |
| 2 | 2026-07-22 | 议题 B 拆分路径 | 🟡 **A. 按职责拆**（默认） | 🟡 待最终确认 | 议题 B / spec.md R4 |
| 3 | 2026-07-22 | 债务 4 Alembic 处置 | ⏸ **C. 保留为未来迁移** | ⏸ 暂缓（生产前） | 债务 4 |
| 4 | 2026-07-22 | 债务 5 密码哈希 | ⏸ **C. 接受 600K pbkdf2 + 改注释** | ⏸ 暂缓（生产前） | 债务 5 |
| 5 | 2026-07-22 | 同步更新 docs/issues.md | ✅ **是**（5 处偏差修正） | ✅ 已完成 | 调研偏差 |
| 6 | 2026-07-22 | 启动第 2 步计划 | ⏸ **等用户指令** | ⏸ 待定 | § 一流程 |
| 7 | 2026-07-22 | 议题 C 实施范围 | ✅ **A. 全部语音路径**（Q1=2） | ✅ 已决策 | 议题 C / spec.md R1 |
| 8 | 2026-07-22 | 议题 C UI 形态 | ✅ **B. transcript+语音**（Q2=2） | ✅ 已决策 | 议题 C / design-spec.md |
| 9 | 2026-07-22 | 议题 C VAD/turn 策略 | ✅ **A. LiveKit built-in**（Q3=1） | ✅ 已决策 | 议题 C / spec.md R1 |
| 10 | 2026-07-22 | 是否进 § 1 规格 | ✅ **A. spec.md + design-spec.md + mockup** | ✅ 已决策 | spec.md · design-spec.md 待写 |
| 11 | 2026-07-22 | spec.md 验收 | ✅ **通过** | ✅ 已决策 | spec.md 350 行 · 用户「spec 验收通过」· 接下来 design-spec.md + 3 mockup |
| 12 | 2026-07-22 | mockup 格式与范围 | ✅ **B. ASCII 前后对比 · 仅 room.tsx** | ✅ 已决策 | 用户「B」· 删 3 mockup + index · 改 design-spec.md 聚焦 room.tsx 前后对比 |
| ~~13~~ | ~~2026-07-22~~ | ~~V4 假绿灯处置（债务 9）~~ | → [迁至 V4 任务决策 1](../2026-07-17-new-feature-ai-push/decisions.md) | 🔴 已迁 | V4 决策 1 |
| ~~14~~ | ~~2026-07-22~~ | ~~债务 3 数字偏差（29 → 41）~~ | → [迁至 V4 任务决策 2](../2026-07-17-new-feature-ai-push/decisions.md) | 🔴 已迁 | V4 决策 2 |
| 15 | 2026-07-22 | 还是要 HTML mockup | ✅ **是 · 仅 room.tsx 改后版** | ✅ 已决策 | 用户「我还是需要个html看一下的」· 1 个 HTML · 仅 room.tsx 改后版本 |
| 16 | 2026-07-22 | § 1 规格整体验收 | ✅ **通过** | ✅ 已决策 | 设计 v3 拟人化 + SVG icons + ASCII 前后对比 · 用户「通过」· § 1 规格闭环 |
| 17 | 2026-07-22 | 启动 § 2 计划 | ✅ **是** | ✅ 已决策 | 用户「出方案」· 写 4 份文档（plan / db-design / api-spec / component-spec）|

---

## 📝 决策详细记录

### 决策 1 · 议题 C 语音架构未来方向

**日期**：2026-07-22
**决策项**：议题 C 语音架构未来方向
**选项**：
- A. 纯 PTT 收敛（删 LiveKit 路径）
- B. 全力全双工（启用 LiveKit 客户端）
- C. Hybrid（PTT 默认 + onboarding 试用全双工）

**选择**：✅ **B 全力全双工**
**用户原话**：「需要真实的实时声音」
**理由**：
1. 用户希望模拟面试"像真人面试"——能边说边听（不是"说完一段 → 等 AI 评"的 PTT 模式）
2. 当前 `livekit-server` 一直在跑（livekit.yaml 配置存在）+ `LiveKitVoice.tsx` 存在但无引用 = 前期投入打水漂
3. 议题 A 关闭条件 checklist 从「三套收敛为单一路径」改为「启用 LiveKit 客户端 + 整合 worker」

**影响文件 / 产物**：
- 议题 C：启用 `livekit_worker.py` · `LiveKitVoice.tsx` 在三页面引用 · `lib/livekit.ts` 删除（孤儿）
- spec.md R1（全双工实时语音）
- design-spec.md（3 页面 ASCII wireframe · 待用户拍板后写）

**关联**：决策 7（实施范围）/ 决策 8（UI 形态）/ 决策 9（VAD 策略）

---

### 决策 2 · 议题 B 拆分路径

**日期**：2026-07-22
**决策项**：议题 B `interview.py` 873 行拆分路径
**选项**：
- A. 按职责拆（lifecycle/runtime/query）
- B. CQRS 分离（读 vs 写）
- C. 保留单文件（约定避免互相改）

**选择**：🟡 **A. 按职责拆**（AI 默认，待用户最终确认）
**用户原话**：（未明确指定 · AI 默认决策）
**理由**：
1. `grep -rn "from api.interview import" backend/api/` 仅命中 main.py —— **无反向依赖，拆分零摩擦**
2. 13 端点按 lifecycle（4）/ runtime（5）/ query（4）分组最自然
3. CQRS 对单用户项目过度设计

**影响文件 / 产物**：
- `backend/api/interview_lifecycle.py` + `interview_runtime.py` + `interview_query.py`
- 13 端点单测覆盖（当前 0 覆盖）
- spec.md R4

**待用户确认**：「按职责拆」是 AI 默认 · 用户可改成「保留单文件」或「CQRS」

---

### 决策 3 · 债务 4 Alembic 处置

**日期**：2026-07-22
**决策项**：债务 4 Alembic 处置
**选项**：
- A. 实施 Alembic（替换 `_MIGRATIONS`）
- B. 删依赖（清理 `requirements.txt` alembic）
- C. 保留为未来迁移

**选择**：⏸ **C. 保留为未来迁移**（暂缓）
**理由**：
1. requirements.txt 已经装了 alembic==1.14.0（半完成）
2. 单人项目当前不痛
3. 多协作者/多环境部署前必做——但属于 🟢 低优先级（生产前）

**影响**：暂无（债务暂缓 · requirements.txt 半完成状态保留）

---

### 决策 4 · 债务 5 密码哈希

**日期**：2026-07-22
**决策项**：债务 5 密码哈希（pbkdf2 vs argon2/bcrypt）
**选项**：
- A. 换 argon2-cffi
- B. 换 bcrypt
- C. 接受 600K pbkdf2 + 改 `models/__init__.py:49` 注释"# bcrypt hash" → "# pbkdf2-sha256 hash"

**选择**：⏸ **C. 接受 600K pbkdf2**（暂缓 · 含注释修正）
**理由**：
1. iterations=600_000 已对齐 OWASP 2023 PBKDF2-SHA256 推荐
2. 仍在用 stdlib（不是 argon2/bcrypt）但安全性可接受
3. 生产前要换（标准要求更现代算法）—— 但属于 🟢 低优先级

**影响**：暂无（债务暂缓 · 但注释"# bcrypt hash"误导仍存在 · 等生产前实施）

---

### 决策 5 · 调研偏差同步 docs/issues.md

**日期**：2026-07-22
**决策项**：是否同步修正 `docs/issues.md` 的 6 处调研偏差
**选项**：
- ✅ 是（5 处偏差修正 + 留 1 处给债务 5）
- ❌ 否（等实施阶段一并改）

**选择**：✅ **是**（完成 5 处）
**用户原话**：「调研文件我在做出决策之后修改了吗？这块是不是要加上？」（间接触发）
**修正清单**：
1. 议题 B：8 端点 → **13 端点** + 无反向依赖
2. 议题 C：worker 真相（`interview_room.py` 是真被 spawn 的）+ worker 永远阻塞
3. 议题 D：主路径已真集成 + fallback 占位 + analytics.py 重复实现
4. 议题 F：T15-T19 写了脚手架但零调用方 + trace_id 并发 race
5. 债务 3：测试数 41/20 → **29/25**

> ⚠️ **2026-07-22 反向修正（见 V4 决策 2）**：本条原措辞方向反了 —— 实测 `find backend/tests -name "test_*.py" -type f | wc -l` = **41 个**（递归，含 api/e2e/schemas/services 4 个子目录），顶层 29 个。原意是 audit 报告指出"working tree 写 29 是错的（顶层漏算），实测应为 41"，所以应改为"29 → 41（递归）"。修正详见 [V4 决策 2](../2026-07-17-new-feature-ai-push/decisions.md)。

**影响**：docs/issues.md 净增 50 行 / 删 33 行（外加 2026-07-22 债务 3 数字反向修正 + 债务 9 新增）

---

### 决策 6 · 启动第 2 步计划

**日期**：2026-07-22
**决策项**：是否启动 § 2 计划
**选项**：
- A. 立即启动
- B. 暂缓（先 § 1 规格完整闭环）

**选择**：⏸ **暂缓 · 先完成 § 1 规格闭环**
**理由**：按 CLAUDE.md § 一强制流程，每步必须等明确指令

---

### 决策 7 · 议题 C 实施范围

**日期**：2026-07-22
**决策项**：议题 C 实时语音替换范围
**选项**：
- A. 全部语音路径（/interview/room + /interview/setup + /interview.tsx）
- B. 仅 /interview/room
- C. 文字+PTT 双轨

**选择**：✅ **A. 全部语音路径**
**用户原话**：「按你的推荐来吧」（用户授权 AI 默认 · 我的推荐 = 全部）
**理由**：
1. 议题 C 涉及 3 个页面 · 不全替换会留死角
2. LiveKit built-in VAD 工作量不再需要分版本

---

### 决策 8 · 议题 C UI 形态

**日期**：2026-07-22
**决策项**：实时语音 UI 形态
**选项**：
- A. 居中 AI avatar + 实时波形
- B. 上下分栏：transcript 实时滚动 + 音频波形
- C. 仅音频波形（不显示 transcript）

**选择**：✅ **B. transcript+语音上下分栏**
**用户原话**：「按你的推荐来吧」
**理由**：
1. 兼顾听 + 看（嘈杂环境或没戴耳机时也能跟上 AI 追问）
2. 最接近真人面试体验

---

### 决策 9 · 议题 C VAD/turn 策略

**日期**：2026-07-22
**决策项**：VAD/turn-taking 实现策略
**选项**：
- A. LiveKit built-in（自带 VAD + turn-taking 模型）
- B. 客户端 silero-vad + 后端 silence 计时
- C. 后端 ASR streaming + LLM 判断

**选择**：✅ **A. LiveKit built-in**
**用户原话**：「按你的推荐来吧」
**理由**：
1. 工作量最小（LiveKit 内置）
2. 与"全部语音路径 + LiveKit 客户端"决策一致
3. silero-vad / LLM 判断可作为未来优化（reflection）

---

### 决策 10 · 是否进 § 1 规格

**日期**：2026-07-22
**决策项**：是否进 § 1 规格
**选项**：
- A. spec.md + design-spec.md + mockup（按 checklist.md 完整 § 1）
- B. 跳过 § 1 直接 § 2
- C. 跳过 § 1+2 直接 § 3 拆分

**选择**：✅ **A. spec.md + design-spec.md + mockup**
**用户原话**：「做设计」
**已产出**：
- `spec.md` 350 行（5 Requirement + 17 Scenario · 待用户验收）
- `design-spec.md` 待写（议题 C 3 页面 ASCII wireframe）
- `mockups/01-room.html` 待写（按 design-mockup-workflow.md § 8 继承 V3 视觉）

**关联**：决策 1/7/8/9（议题 C 实施细节）· 决策 2（议题 B 拆分）

---

> **影响**：docs/issues.md 净增 50 行 / 删 33 行（外加 2026-07-22 债务 3 数字反向修正 + 债务 9 新增）

## 🔧 决策落地追踪

| 决策 | 已落地 | 待落地 |
|---|---|---|
| 1 · 议题 C 路径 | spec.md R1 + research.md § 三/七/八 + issues.md 状态 | design-spec.md 待写（等用户验收 spec.md 后） |
| 2 · 议题 B 拆 | spec.md R4 + research.md § 八 + issues.md 状态 | 用户最终确认拆分路径 |
| 3 · 债务 4 | research.md § 八 + issues.md（暂缓标注） | 无 |
| 4 · 债务 5 | research.md § 八 + issues.md（暂缓标注） | 生产前实施 |
| 5 · 偏差同步 | docs/issues.md 5 处修正 + research.md § 九偏差表 | 债务 5 注释修正（生产前） |
| 6 · § 2 计划 | research.md § 八（暂缓标注） | 用户指令进 § 2 |
| 7 · 范围 | spec.md R1.Scenario 1.1 + 全部三页面 | design-spec.md 3 页面 wireframe |
| 8 · UI | spec.md R1.Scenario 1.5 + design-spec.md（待写） | mockup 待写 |
| 9 · VAD | spec.md R1.Scenario 1.3 + design-spec.md（待写） | mockup 待写 |
| 10 · § 1 规格 | spec.md 已写（待验收） | design-spec.md + mockup 待写 |
| 11 · spec 验收 | spec.md 通过验收 | design-spec.md + 3 mockup + index 待写 |
| 12 · mockup 格式 | 之前已写 3 mockup + index（HTML · 范围过大）| 删 mockup + index · 改 ASCII 前后对比聚焦 room.tsx |
| 13 · V4 假绿灯 | （已移走）· 见 [`docs/tasks/2026-07-17-new-feature-ai-push/decisions.md` 决策 1](../2026-07-17-new-feature-ai-push/decisions.md) | 执行中 |
| 14 · 数字偏差 | （已移走）· 见 [`docs/tasks/2026-07-17-new-feature-ai-push/decisions.md` 决策 2](../2026-07-17-new-feature-ai-push/decisions.md) | 已闭环 |
| 15 · 还是要 HTML | 用户原话「我还是需要个html看一下的」· 之前决策 12 后改 ASCII 但 HTML 仍需要看 | 写 1 个 room.tsx 改后版本 HTML mockup |
| 16 · § 1 规格验收 | 用户「通过」· design v3 拟人化 + SVG icons + ASCII 前后对比 | § 1 规格闭环 · 进 § 2 计划（待用户说"出方案"）|
| 17 · § 2 计划 | 用户「出方案」· 反转决策 6 暂缓状态 | 写 plan.md + db-design.md + api-spec.md + component-spec.md |

---

## 📊 元信息

- **文件位置**：`docs/tasks/2026-07-21-issues-audit/decisions.md`
- **创建日期**：2026-07-22
- **决策总数**：15 项（原 17 项 · 13/14 已迁至 [`docs/tasks/2026-07-17-new-feature-ai-push/decisions.md`](../2026-07-17-new-feature-ai-push/decisions.md) 重编号为 1/2 · 因内容全部针对 V4 AI 推送模块 · 按 CLAUDE.md § 6.9 原则迁移）
- **已决策**：12 项（✅ 1/5/7/8/9/10/11/12/15/16/17）· **默认待确认**：1 项（🟡 2）· **暂缓**：2 项（⏸ 3/4）· **不在本主账**：2 项（13/14 → V4 decisions.md）
- **最后更新**：2026-07-22（13/14 迁出）
- **下次 review**：每个新决策后立即更新本文件 + § 6.8 三处同步
- **迁移记录**：决策 13 → V4 决策 1 · 决策 14 → V4 决策 2（内容一字未改）
