# 项目开发工作流（强制约束）

> 本文件是项目级的 hook 准则，约束本仓库所有开发活动的执行顺序。
> 任何 AI 助手 / Claude Code 在本项目工作时必须遵守。
>
> ⚠️ **2026-07-21 v2.1 同步**：6 步流程 + 路径模式 + 条件产物 + 双 gate；砍掉发布，验证为 L3 + L5。
> 详见 `~/Obsidian/coding/AI代码工具使用心得/7步工作流最终版/全局流程.md`。

---

## 0 步：调研前置（不可跳）

| 步 | 名称 | 谁触发 | 触发命令 |
|---|---|---|---|
| **0** | **调研** | 新任务自动进入 | 按任务类型选路径；先复述并等用户确认 |

**核心原则**：新功能 / Bug / 重构 / P0 都先进入 0 步分类。Bug/P0 可以走短路径，但不能完全跳过任务理解、证据和风险判断。

### 0.1 任务类型 → 模板选择

| 触发词包含 | 类型 | 模板 | 时间预算 |
|---|---|---|---|
| `新功能` / `设计` / `feature` / `加` | 新功能 | [`research-new-feature.md`](docs/templates/research-new-feature.md) | 30-60 min |
| `bug` / `修复` / `失败` / `报错` / `fix` | Bug 修复 | [`research-bug.md`](docs/templates/research-bug.md) | 10-30 min |
| `重构` / `refactor` / `拆分` / `优化` | 重构 | [`research-refactor.md`](docs/templates/research-refactor.md) | 20-40 min |
| `P0` / `紧急` / `线上` / `故障` | P0 紧急 | [`research-p0.md`](docs/templates/research-p0.md) | 5-10 min |

> ⚠️ **任务理解段必填**：AI 必须用自己的话复述"用户要做什么"。**复述不对 → 立刻停下等用户确认**，不要继续调研。

### 0.1.1 路径模式

| 模式 | 适用 | 默认路径 |
|---|---|---|
| `full-6` | 新功能；大型/跨模块 Bug | 0→1→2→3→4→5→6 |
| `fix-mini` | 普通 Bug | 0→4（回归测试）→6 |
| `refactor-6` | 重构 | 0→1→2→3→4→5→6；不写 product-doc，非 UI 不写 design-spec |
| `timebox` | P0 | T+30m 止血→T+2h 根因→T+24h 登记→T+48h 永久修复→T+72h 复盘 |

路径模式必须写进 `research.md`；升级或降级路径须说明理由并由用户确认。

### 0.2 通用调研清单（所有类型必做）

- [ ] 任务理解：用自己的话复述（用户确认对）
- [ ] 读 `docs/issues.md`
- [ ] 跑 `git log -10`（最近相关改动）
- [ ] 跑 `git status`（看 unstaged / 多 agent 冲突）
- [ ] 找到 ≥ 3 个相关文件
- [ ] 列出依赖影响（改 A 会影响 B/C）
- [ ] 风险点带等级（🔴/🟡/🟢）+ 缓解方案（**涉及 CI/CD / Agent / 密钥 / 网络 / 文件系统时还要过 § 0.2.1 安全审查**）
- [ ] 给完整 6 步路径建议

### 0.2.1 安全审查清单（涉及 CI/CD / DevOps / Agent / 网络 / 密钥 / 高权限操作时必做）

> 📌 **2026-07-22 新增**（源自 CI auto-fix 任务调研盲点 · 见 [memory `feedback-ai-agent-security-4-gates`](~/.claude/projects/-Users-wangtianyu-IdeaProjects-KnockWise/memory/feedback-ai-agent-security-4-gates.md)）

- [ ] **官方安全文档已读**
  - CI/CD → [GitHub Actions Security Hardening](https://docs.github.com/en/actions/security-guides/security-hardening-for-github-actions)
  - Web → OWASP Top 10 / CWE
  - LLM/Agent → [OWASP LLM Top 10](https://owasp.org/www-project-top-10-for-large-language-model-applications/)
- [ ] **威胁模型 ≥ 3 个场景**（攻击者能力 + 攻击向量 + 影响 + 等级）
- [ ] **权限边界图**（ASCII 画"哪些组件有 secrets / 哪些需要 approval / 哪些只读"）
- [ ] **外部依赖审查**（第三方 Action / 库 / API 必须列出完整 SHA 或锁定版本，**禁止** `@main` / `@beta` / `@v1` 等移动 tag）
- [ ] **不可信输入清单**（LLM/Agent 接收的所有外部数据源 + 净化策略）

### 0.3 产物落地

- **长期调研**（推荐）：写到 `docs/tasks/YYYY-MM-DD-<类型>-<topic>/research.md`
- **临时调研**：直接在 chat 输出，下次开工重做
- **不落地 = 不算完成**

### 0.4 防御对象

- AI 接到"做设计"指令后不看现状 → 重复造轮 / 忽略沉积议題
- AI 不知道哪个任务类型用哪个模板 → 输出格式混乱
- AI 调研 5 分钟就交差 → 用通用清单的 ≥ 3 文件 / ≥ 2 风险点强约束

### 0.5 遗留项关闭核验（非调研类型）

“议題关闭”是任务完成后的**收尾动作**，不与新功能 / Bug / 重构 / P0 并列，也不因用户只提到“议題”或“issue”就自动触发。

- **唯一触发**：用户明确说“关闭议題 X”或“验证并关闭 issue X”
- **事实主账**：[`docs/issues.md`](docs/issues.md)
- **核验模板**：[`issue-closure-template.md`](docs/templates/issue-closure-template.md)
- **无需改代码**：核对代码、测试、commit、文档证据；全部满足后更新主账状态
- **仍需改代码**：按实际性质重新分类为 Bug / 重构 / 新功能，完成对应流程和验证后再关闭
- **禁止**：仅凭“看起来做过了”关闭；任何要求未满足都必须保留为遗留项

---

## 一、6 步强制流程（不可跳级）

| 步 | 名称 | 谁触发 | 触发命令 | 产出文档 |
|---|---|---|---|---|
| **0** | **调研** | 我说"调研" | 按任务类型选 4 模板之一 | `research.md`（按 0 步 4 模板） |
| **1** | **规格（三脑交汇）** | 我让"做设计" | 只定义业务与体验 | 新功能写 `product-doc`；UI 写 `design-spec`；full/refactor 写 `spec` |
| **2** | **计划 + 技术详细化** | 我说"出方案" | ≥2 方案 + 单一推荐 + 用户决策 | `plan.md`；schema/API/UI 变化时分别写 db/api/component-spec |
| **3** | **拆分** | 我说"拆任务" | ≤ 1h AI 工作量原子任务，可独立 commit | `tasks.md` |
| **4** | **实现（TDD）** | 我说"开始实施" | 红→绿→refactor→commit；整合产出 test-cases.md | `test_xxx.py` + `test-cases.md` |
| **5** | **验证** | 我说"verify" | L3 整合测试 + L5 staging 跑通；L1/L2/L4 在 4 步分布式完成 | `verify.md` |
| **6** | **复盘** | verify 后自动起草，用户确认完成 | 量化偏差、根因、改进与规则沉淀 | `retro.md` + 更新 `CLAUDE.md` / `DOD.md` / 模板 |

**双 gate**：每一步必须同时满足该步 DOD 和用户明确验收，才能进入下一步。没收到验收指令前只做当前阶段工作；步骤 6 可自动起草但不能自动判定闭环。

### AI 与人的职责

| AI 负责 | 人负责 |
|---|---|
| 读现状、列证据、填技术契约、提出选项 | 决定是否做、scope、产品与视觉方向 |
| 给 ≥2 方案、风险和明确推荐 | 选择方案并拍板决策点 |
| 写测试、实现、运行验证、整理数据 | review diff、验收行为、决定 merge |
| 起草复盘与规则更新 | 确认改进项和最终闭环 |

**原则**：AI 是执行者，不替用户做产品、设计和发布决策。

### UI 设计子流程

涉及 UI / 页面 / UX 时必须读取 [`docs/rules/design-mockup-workflow.md`](docs/rules/design-mockup-workflow.md)：步骤 1 完成 design-spec + ASCII + HTML mockup + index 并由用户验收；步骤 2 的 component-spec 只引用已验收设计并定义 Props/State/Events，不重新设计页面。

**v1 → v2 变化**（2026-07-02）：
- ❌ 砍掉 **6 发布**（灰度/监控/回滚）—— PR/commit 即交付，纯 AI coding 场景用不上
- 🟡 **5 验证**：5 层 gate → 2 段（L3 整合 + L5 staging），L1/L2 由 pre-commit hook 兜底，L4 review 是活动不是步骤
- ✅ **0/1/2/3/4/6** 步保留

---

## 二、绝对不能动的东西（在设计阶段）

| 对象 | 状态 |
|---|---|
| `backend/seed_data/*.json`（50 道种子题） | ❌ 禁止改、扩、删、动任何字段 |
| `backend/seed_data/expanded/`（如果创建过） | ❌ 禁止创建 |
| `backend/.venv/` | ❌ 禁止改 |
| `backend/.env.local` | ❌ 禁止改 |
| `frontend/node_modules/` | ❌ 禁止改 |
| `livekit.yaml` | ❌ 禁止改 |
| MySQL 真实数据 | ❌ 禁止改、删、清空 |

例外：
- **修复 bug**：如果发现现有代码有明确 bug，可以即时修，但要报告
- **查问题 / 跑测试 / 调命令**：可以即时跑
- **文档整理 / 改名 / 去重**：可以即时做（不算"实施"）
- **读 / 搜索 / 分析代码**：可以即时做

---

## 三、各阶段交付物清单

→ 全文见 [`docs/rules/checklist.md`](docs/rules/checklist.md)

---

## 四、命名规范（已确认）

→ 全文见 [`docs/rules/naming.md`](docs/rules/naming.md)

---

## 五、违反流程的处置

如果我（AI）违反上面的流程：
1. 你会立刻打断
2. 我会停下，回退已做的实施工作（如有）
3. 回到正确的当前阶段
4. 在回复里写"自我复盘"，承认错误

---

## 六、单测强制规则（2026-06-25 新增 · 核心规则）

> **所有写代码的 commit 必须配套单测**。这是硬性要求，不是建议。

### 6.1 适用范围 + § 6.2 测试基础设施

→ 详见 [`docs/rules/testing-rules.md`](docs/rules/testing-rules.md)

---

### 6.3 自检清单（每个代码 commit 前必须过）

- [ ] 新加函数有 happy path 测试
- [ ] 边界值 / 异常输入有测试
- [ ] Pydantic schema 的 Literal/Range 校验有测试
- [ ] Bug 修复有回归测试
- [ ] `pytest` / `vitest` 全绿才 commit
- [ ] **安全审查**（涉及 CI/CD / Agent / 密钥 / 网络 / 文件系统时必做）
  - [ ] 过 § 6.10 节 4 道关（不可信输入净化 / 权限分层 / 供应链防御 / 人工 gate）
  - [ ] 无移动 tag（`@beta` / `@main` / `@v1`）· 第三方 Action 必 pin 完整 SHA
  - [ ] 无 secrets + checkout 非可信代码同 job
  - [ ] 无 LLM 直接读不可信数据（CI 日志 / commit msg / PR 标题视为不可信）
  - [ ] 高权限操作有 environment approval

### 6.4 违反处置

- 没单测的 commit 不算完成 → 我（AI）会停下来补测
- 你可以拒绝 merge 没单测的代码

### 6.5 任务完成自动更新（2026-07-10 新增 · 2026-07-19 加固 · 用户加规则）

> **⚠️ 强约束**：完成每个实现任务时（`TaskUpdate ... completed` 之前），**必须先**回写 `docs/tasks/<task-dir>/tasks.md`。
> **违反代价**：用户无法从 tasks.md 看真实进度 · 重新切入会话时不知道做到哪 · 实际发生一次（2026-07-19 T1/T2/T5 三个 commit 都没回写）。

> **规则**：每次执行完任务并标 `TaskUpdate ... completed` **之前**，**自动更新对应的 `docs/tasks/<task-dir>/tasks.md`**：
> 1. **该任务的 `#### T<n>` 段标题**改为"✅ 已做"标记（如 `- [x] T<n>: ✅ DONE — commit \`hash\``）
> 2. **该任务的状态行**如有 `本 PR 可延后` 等占位文字，改为"✅ 已实施（N/N 测试通过）"
> 3. **该 PR 的"PR <n> 标志"**行如有 "后做 / 暂缓" 描述，改为"✅ 已做"
> 4. **顶部总览表**（如 §8 "8.2 实施状态" 或 §10 总览）同步状态（✅ 已做 / ⏸ 暂缓）
> 5. **§ 6 总估时 / § 7 实施顺序**同步更新（实际 commit hash + 实际耗时 vs 估时）
> 6. **新增 commit 历史表**（task 文件底部 · 实际 commit hash + 实际耗时 · 偏差分析）

> **示例**：
> - 完成 PR 6 实施 → 改 `docs/tasks/2026-07-09.../tasks.md`：
>   - PR 6 标题：`(暂缓)` → `(✅ 已做)`
>   - 状态行：`本 PR 可延后` → `✅ 已实施（4/4 测试通过）`
>   - 顶部总览：PR 6 → ✅ 已做
> - 跳过此规则 = 任务追踪不更新 = 用户无法从 tasks.md 看真实进度
>
> **反面教材（2026-07-19 实际发生）**：
> - T1/T2/T5 三个 commit 完成后 · 我没回写 tasks.md
> - 用户重启会话问"做到哪了？" · 看 tasks.md 仍是 `- [ ]` 全部未勾
> - 用户原话："等等 你实施完毕了 为什么没有回写task.md"
> - 修正成本：手动补 + 3 个 commit 历史 + 反思
> - 预防：每个 commit 完成 → 立即回写 → 再做下一个

### 6.6 verify 后自动写 retro（2026-07-11 新增 · 用户加规则）

> **规则**：`verify.md` 完成后立即起草 `retro.md`，但步骤 6 只有在用户确认改进项后才算完成。
>
> **retro.md 必须包含**：
> 1. **做对了什么**（哪些决策/执行效果好 · 可沉淀为下次模板）
> 2. **踩了什么坑**（bugfix 记录 · 可写 memory 的 feedback 类型）
> 3. **调研偏差修正**（research 阶段声称但实际不符的 · 例：Interview model 没有 radar_data 字段）
> 4. **下次该改什么**（流程优化 · 不光指 AI 改 · 也可指流程/规则改进）
> 5. **memory 更新清单**（列出要写哪些 memory · 不只是说"应该写"）
>
> **路径**：`docs/tasks/<task-dir>/retro.md`（与 verify.md 同目录）
>
> **触发场景**：
> - 多阶段实施完成（≥ 3 阶段）· 用户已经"拍 D 收尾" → AI 主动写 retro
> - 单阶段小改动完成 · 用户明确要求"写 retro" 才写
>
> **示例（V3.8 收尾）**：
> - ✅ 自动写：`docs/tasks/2026-07-11-refactor-v3-mockup-align/retro.md`
> - 调研偏差：Interview model 没有 radar_data 字段（research §9.7 误称）· _safe_radar 兜底
> - 流程改进：§6.5 仅覆盖 tasks.md，未覆盖 verify/retro，§6.6 补上
> - memory 待写：3 条（feedback 类型 · 调研偏差 + Tailwind 4 dev mode bug + Sidebar 折叠状态提升）

### 6.7 实施自校验 Verify-Loop（2026-07-17 新增 · 用户加规则）

> **规则**：实施阶段（步 4）每完成一个单位（默认 **commit 边界**），**主动**开 verifier agent 校验是否对齐"上面的需求计划"。失败则**自我修正**。

**双 agent 模式**（writer → verifier → 修复循环）：

| Agent | 角色 | 触发时机 | 实现 |
|---|---|---|---|
| **writer** | 实施代码 / 测试 | 用户说"开始实施"进入步 4 | 现有 read / write / edit / Agent |
| **verifier** | 独立路径校验 | writer 完成一个 commit 单元 | Claude Code `Agent` tool（`subagent_type=general-purpose`）· 新开 prompt · **不复用 writer 上下文** |

**Verifier 必须做 3 件事**：

1. **对照需求** — 读 `docs/tasks/<task-dir>/plan.md` / `spec.md` / `api-spec.md` 对应 §X 的具体条目
2. **跑相关测试** — `cd backend && ./.venv/bin/python -m pytest tests/test_xxx.py -v` · `cd frontend && npm test -- --run`
3. **实测行为** — 端到端 curl / dev server / 浏览器（如后端端点 / 前端页面路由）
4. **决策同步自检**（§ 6.8）— 若调研阶段做过决策，verify commit 单元前确认 `research.md` § 三/七/八 与当前实现一致（不能停在"调研阶段已决策"忘了同步）

**Verifier 输出格式**：`PASS / FAIL + 具体偏差清单（file:line + 期望 vs 实际）`

**失败自我修正回路**：

```
writer 完成 commit
  ↓
verifier (独立 Agent prompt)
  ↓
├─ PASS → writer 继续下一个单元
└─ FAIL → writer 读 FAIL 清单 → 改代码 / 测试
                    ↓
              再开 verifier → 循环
                    ↓
       连续 2 PASS 或 用户叫停 → 收敛
                    ↓
       仍失败 → 报用户列剩余偏差，等决策（不悄悄绕过）
```

**粒度参考**（可按 step 类型调整）：

| Step 类型 | 验证粒度 | 强制程度 |
|---|---|---|
| 单个 service 函数 / API endpoint / 组件 | 函数级 verify（writer 自驱） | 🟡 推荐 |
| 整 commit 单元（含单测） | **commit 级 verify** | ✅ 必跑（与 § 6.1 单测配套）|
| 整 phase 结束 | 完整 verify（含 L5 staging）| ✅ 必跑（与 § 一.5 验证阶段对齐）|

**反例**（不要做）：

- ❌ 仅看 `pytest -q` 绿灯就 PASS — 没对照需求计划 = 不算 verify
- ❌ verifier 复用 writer 上下文 — 失去独立路径意义，必须新开 `Agent` prompt
- ❌ FAIL 后 writer 反复微调不收敛 — 报用户，不要无止境循环
- ❌ 跳过 verifier 直接写下一个 commit — § 6.7 没生效
- ❌ 调研阶段决策后没回写 `research.md` § 三/七/八 — 违反 § 6.8
- ❌ 手开 N 个 `Agent` tool 串成循环 — 上下文爆 / 跳出 loop 率高，升级 `Workflow`（见 § 6.7.1）

**memory**：`feedback-verify-loop-self-correct.md` · 为什么 / 怎么用 / 典型错误全在该文件

### 6.8 调研文档决策同步（2026-07-22 新增 · 2026-07-22 扩展 · 用户加规则）

> **规则**：调研阶段（§ 0）后，用户做出任何决策后 AI 必须**立即**回写**四个文件位置**（不能累积）：
>
> | # | 位置 | 同步内容 | 主账级别 |
> |---|---|---|---|
> | 1 | `docs/tasks/<task-dir>/research.md` § 三 | 议题"关闭条件 checklist"反映新方向 | 调研详细 |
> | 2 | `docs/tasks/<task-dir>/research.md` § 七 | 风险"缓解方案"反映新方向 | 调研详细 |
> | 3 | `docs/tasks/<task-dir>/research.md` § 八 | 决策清单加 "2026-MM-DD 决策" 列 + ✅/🟡/⏸ + 用户原话 | 调研详细 |
> | 4 | `docs/tasks/<task-dir>/decisions.md`（**决策最权威主账**）| 新增决策项 + 详细记录 + 落地追踪 + 关联 spec/issue/PR | 📌 **决策主账** |
> | 5 | `docs/issues.md`（唯一主账）| 顶部"决策更新"段 + 议题状态字段改为 ✅ / 🟡 | 📌 **议题主账** |
> | 6 | 调研产物 spec.md / design-spec.md（如已写）| Requirement / Scenario 反映新决策 | 规格实施 |

**触发条件**：调研阶段对话中做出任何决策（无论 explicit 指令还是"按推荐来"）。

**同步时机**：决策做出后**下一轮回复**必须更新 · 不能等任务结束批量同步。

> **Why**：2026-07-22 用户提醒 — 调研文档不在决策后同步 = single source of truth 漏洞 · 用户重启会话不知道决策已做 · 后续实施按错误方向走 · 多 agent 协作状态不一致
> **Why（扩展）**：issues.md 是"唯一主账"+ decisions.md 是决策最权威详细记录 — 漏掉这两处 = 用户决策在主账系统中失踪
>
> **How to apply**：
> - 同步**六处固定**（research § 三/七/八 + decisions.md + issues.md + 已写规格文档），不全文档通改
> - 表格加 "2026-MM-DD 决策" 列含 ✅/🟡/⏸ + 用户原话
> - **decisions.md = 决策最权威主账** · 其他 5 处是镜像（按 memory `feedback-doc-design-link-convention` 链接而非冗余）
> - **issues.md 顶部加"决策更新"段 + 议题状态字段同步**（按 docs/issues.md "唯一主账"原则）
> - 同步完告知用户（"research.md § 八 + decisions.md + issues.md 已同步"）
>
> **memory**：
> - `feedback-decisions-sync-to-research.md` · research.md 同步模式
> - `feedback-decisions-sync-to-issues.md`（拟新增）· issues.md 主账同步模式
> - `feedback-decisions-sync-to-decisions.md`（拟新增）· decisions.md 详细记录同步模式

### 6.9 决策记录规则（2026-07-22 新增 · 用户加规则）

> **规则**：调研阶段（§ 0）做出任何决策时，必须在 `docs/tasks/<task-dir>/decisions.md` 建一个**决策最权威详细主账**。结构、命名、同步机制按本节固定。

**触发条件**（任何阶段 · 不限于调研）：
- **§ 0-6 任何阶段**做出任何决策（含 AI 默认决策 + 用户拍板 · 不限于调研阶段）
- **任何后续会话**（不只是本次 session）做出的新决策都追加到当前 task 的 decisions.md
- **任何未来 KnockWise 项目**的决策都按本节结构（CLAUDE.md 是项目级 hook 准则 · 跨项目生效）
- 每个 task 目录独立 `decisions.md` · 不跨任务聚合（避免混淆）
- 即使没决策 · 也可建空文档（仅元信息 + 占位行）

**必备 4 段结构**（缺一不可）：

| 段 | 内容 | 长度 |
|---|---|---|
| **① 顶部权威定位** | 本文件是决策最权威详细主账 + 与 research.md § 八 / issues.md / spec.md 的关系（按 § 6.8 v2 同步规则）+ 关联文档链接（**仅链接不重复**） | ≤ 15 行 |
| **② 决策总览表** | 最新 N 项倒序 · 列：# / 日期 / 决策项 / 选择 / 状态 / 关联 | 随决策数自动增长 |
| **③ 决策详细记录** | 每项独立 H3 段 · 含：日期 / 决策项 / 选项列表 / 选择 / **用户原话** / 理由（≥ 3 条）/ 影响文件 / 关联决策 | 每项 10-30 行 |
| **④ 决策落地追踪 + 元信息** | 落地追踪表（已落地 / 待落地）+ 元信息（位置 / 创建日期 / 决策总数 / 已决策数 / 待确认数 / 暂缓数） | 追踪表动态增长 + 元信息固定 8 行 |

**命名规范**：
- 文件名固定 `decisions.md`（不是 `decision.md` / `decision-log.md` / `decisions-log.md`）
- 位置：`docs/tasks/<task-dir>/decisions.md`（与 `research.md` / `spec.md` 同级）

**与 § 6.8 关系**：
- decisions.md 是 § 6.8 v2 同步的**最权威详细主账**位置
- 其他 5 处（research.md § 三/七/八 + issues.md + spec.md）是镜像（简表 + 链接）
- 按 memory `feedback-doc-design-link-convention` 链接而非冗余

**反例**（不要做）：
- ❌ decisions.md 与 research.md § 八 / issues.md 顶部决策段内容重复（应链接而非冗余）
- ❌ 决策记录模糊化（"按推荐来" 不说具体推荐了什么）
- ❌ 落地追踪表不更新（spec.md / PR 完成后没回写）
- ❌ 把 decisions.md 散在多个 task 目录（统一放 task 目录）

**memory**：`feedback-decisions-sync-to-decisions.md` · 完整例子和反例在该文件

### 6.10 AI Agent 安全强制规则（2026-07-22 新增 · P0 反模式）

> 📌 **2026-07-22 新增**（源自 CI auto-fix 任务自我复盘 · 用户指出 P0 风险）

任何 **"AI Agent + 不可信数据 + 高权限操作"** 场景必须过 **4 道关**：

#### 关 1 · 不可信输入净化
- LLM 接收的所有外部数据视为不可信：PR 标题 / commit msg / CI 日志 / 用户输入 / webhook payload
- **不直接作为指令传 LLM** · 仅作"上下文摘要"（限定字段 + 截断长度 + 类型过滤）
- 例：CI 日志只传"失败 job 名 + 错误类型 + 关键字符串前 200 字符"，不传原始堆栈

#### 关 2 · 权限分层（最小权限）
- 拆 **diagnostic job**（read-only，无 secrets）+ **action job**（env approval 后才有 secrets）
- secrets 仅在 human-approved environment 内暴露
- 单 job 同时有 secrets + checkout 非可信代码 = **反模式**

#### 关 3 · 供应链防御
- 第三方 Action 必须 pin **完整 40 字符 SHA**（非 `@main` / `@beta` / `@v1` / `@latest`）
- 例：`anthropics/claude-code-action@a1b2c3d4e5f6...` （40 字符）
- 升级前先 review 新 SHA 对应 commit · 不自动跟随

#### 关 4 · 人工审批 gate
- "AI 自动 push 到 main" / "AI 触发 workflow_run" / "AI 暴露 secrets" 必须 **environment approval**
- "全自动 commit 推原 PR" = 反模式（除非 threat model 评估通过 + 人工 gate）

#### 反例（不要做）

- ❌ `workflow_run` 触发 + `contents: write` + checkout 非可信代码 + `secrets: ANTHROPIC_API_KEY`
- ❌ LLM 直接读 raw CI 日志并据此改代码
- ❌ Action 用 `@beta` / `@main` / `@v1` 等移动 tag
- ❌ Auto-fix 直接 push 到原 PR 分支（绕开人工 review）
- ❌ 自我豁免标记（`[NO-TEST-NEEDED]`）作为唯一合规手段
- ❌ Fork PR 自动 checkout 并跑任意代码
- ❌ 高权限 workflow 不分 job（read-only 诊断 + 写入同 job）

#### 关联文档

- § 0.2.1 安全审查清单（调研阶段必做）
- § 6.3 自检清单（commit 前必过安全审查）
- § 6.10 即本节（强制规则）

#### memory

- `feedback-ai-agent-security-4-gates.md`（4 道关主规则）
- `feedback-workflow-run-secrets-risk.md`（P0 反模式案例）
- `feedback-no-self-attestation-in-ci.md`（自我豁免不安全）
- `feedback-pin-third-party-action-sha.md`（供应链防御）
- `feedback-untrusted-data-not-instruction.md`（反 prompt injection）

### 6.7.1 进阶路径：Workflow tool（≥ 3 verify cycle 或 ≥ 5 phase 时升级 · 2026-07-17 整合）

Claude Code 已实现 **`Workflow` tool**（确定性 orchestration）。与 § 6.7 默认 `Agent` tool 对比：

| 维度 | `Agent` tool（默认） | `Workflow` tool（进阶） |
|---|---|---|
| 控制方 | Claude 每轮决策 | **脚本决定**（确定性）|
| 中间状态 | context window（50 轮后 100K+ tokens）| **脚本变量**（不污染 context）|
| 可重复 | 弱（重启 turn 即丢）| **强**（`resumeFromRunId` 同会话恢复）|
| 规模 | 数个 / turn | **数十到数百 agents** |
| 适用 | 单 commit verify · 偶发 fix | **≥ 3 cycle** · ≥ 5 phase · 对抗式 verify |

**升级阈值**（推荐）：

| 场景 | 工具 |
|---|---|
| 1-2 verify cycle · 单 phase | 保持 `Agent` tool（§ 6.7 默认）|
| **≥ 3 verify cycle** 或 ≥ 5 phase 任务 | 升级 **`Workflow`** |
| 关键 commit / 涉及安全 / 性能 | **直接 `Workflow` + 对抗式 verify** |

**完整脚本骨架**（含 workflow 主循环 + 对抗式 verify 变体 · 复制改名即可用）：

→ **[`.claude/workflows/verify-loop-example.js`](.claude/workflows/verify-loop-example.js)**

文件含：`meta` 声明 · `WRITER_RESULT_SCHEMA` / `VERIFIER_SCHEMA` · 主循环（writer → verifier → fix）· **对抗式 verify 注释块**（`parallel()` 屏障 + 2/3 共识）

**关键工具速查**：

- `Agent` tool:
  - `subagent_type: "general-purpose"` — 默认
  - `subagent_type: "Plan"` — verifier 用于"对照 architecture"
  - `subagent_type: "Explore"` — verifier 用于"查 reference / 文件搜索"
  - `isolation: "worktree"` — writer + fixer 同时改文件时避免冲突（贵 ~300ms · 仅高冲突场景）
  - `run_in_background: true` — verifier 跑时 writer 可继续（仅 verifier 只读不写时用）
- `Workflow` tool:
  - `pipeline(items, stage1, stage2, ...)` — 默认 stage 串行无屏障
  - `parallel(thunks)` — 屏障（等所有完成）· **对抗式 verify 用这个**
  - `phase(title)` — 进度分组
  - `agent(prompt, {schema})` — `schema` 强制结构化输出，避免自由格式 FAIL 清单模糊
  - `resumeFromRunId` — 中断后同会话恢复
- `ScheduleWakeup` tool — verifier 等外部状态（CI / deploy 完成）时用，**cache-aware 60-3600s**
- `SendMessage` tool — 队友 agent 间发消息（verifier 给 writer 反馈）· 替代"反复开新 Agent"

**资源**：[Dynamic Workflows 深度解析](https://www.cnblogs.com/ai-old-six/p/20245238) · [Workflow 功能实战教程](https://blog.csdn.net/2601_96073073/article/details/161488327) · [Subagent vs Workflow 对比](https://www.cnblogs.com/softlin/p/20231222)

---

## 七、本地启动（强制）

→ 全文见 [`docs/rules/local-dev.md`](docs/rules/local-dev.md)

**强约束**：开工前**必须**先 `./scripts/start.sh` 把基础设施起起来（不在 CLAUDE.md 详述，见 local-dev.md）。

---

## 八、当前状态

### 8.1 阶段追踪（设计流程 · 已移至归档）

原内容已迁移到 [`docs/archive/project-history.md`](docs/archive/project-history.md)。当前进度以 `git log` + 各任务目录 `docs/tasks/<日期>/` 为准。

### 8.2 实施状态

→ 全文见 [`docs/rules/milestones.md`](docs/rules/milestones.md)

### 8.3 git 状态（不在 CLAUDE.md 维护）

- 当前 commit / 分支 / 未 push 数量：`git log --oneline -10` · `git status -sb`
- 历史完整列表 `git log --oneline`（不在 CLAUDE.md 复制粘贴，会自然 stale）

### 8.4 动态事项入口

`CLAUDE.md` 不保存会自然过期的版本、commit 数和待决策列表：遗留问题统一写 [`docs/issues.md`](docs/issues.md)，实施里程碑写 [`docs/rules/milestones.md`](docs/rules/milestones.md)，具体任务进度写对应 `tasks.md`。
