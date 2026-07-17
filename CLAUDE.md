# 项目开发工作流（强制约束）

> 本文件是项目级的 hook 准则，约束本仓库所有开发活动的执行顺序。
> 任何 AI 助手 / Claude Code 在本项目工作时必须遵守。
>
> ⚠️ **2026-07-02 v2 同步**：流程从 7 步精简为 6 步（砍掉 6 发布，5 验证精简为 L3 整合 + L5 staging）。
> 详见 `~/Obsidian/coding/AI代码工具使用心得/7步工作流最终版/全局流程.md`。
>
> ⚠️ **本文件 § 三「各阶段交付物清单」使用 v1 阶段编号（设计文档/验证/详细化/页面规划/通过/实施），是历史 phase 标记，保留不动**。新框架的阶段交付物映射见各模板。

---

## 0 步：调研前置（不可跳）

| 步 | 名称 | 谁触发 | 触发命令 |
|---|---|---|---|
| **0** | **调研** | 我说"调研" | 按"任务类型"自动选模板（见下表） |

**核心原则**：新功能 / 重构 / 议題关闭 / 大型 bug 修复 / P0 紧急，**开工前必先调研**。直接跳到第 1 步 = 流程违规。

### 0.1 任务类型 → 模板选择

| 触发词包含 | 类型 | 模板 | 时间预算 |
|---|---|---|---|
| `新功能` / `设计` / `feature` / `加` | 新功能 | [`research-new-feature.md`](docs/templates/research-new-feature.md) | 30-60 min |
| `bug` / `修复` / `失败` / `报错` / `fix` | Bug 修复 | [`research-bug.md`](docs/templates/research-bug.md) | 10-30 min |
| `重构` / `refactor` / `拆分` / `优化` | 重构 | [`research-refactor.md`](docs/templates/research-refactor.md) | 20-40 min |
| `关闭` / `议題` / `issue` | 议題关闭 | [`research-issue.md`](docs/templates/research-issue.md) | 10-20 min |
| `P0` / `紧急` / `线上` / `故障` | P0 紧急 | [`research-p0.md`](docs/templates/research-p0.md) | 5-10 min |

> ⚠️ **任务理解段必填**：AI 必须用自己的话复述"用户要做什么"。**复述不对 → 立刻停下等用户确认**，不要继续调研。

### 0.2 通用调研清单（所有类型必做）

- [ ] 任务理解：用自己的话复述（用户确认对）
- [ ] 读 `docs/issues.md`
- [ ] 跑 `git log -10`（最近相关改动）
- [ ] 跑 `git status`（看 unstaged / 多 agent 冲突）
- [ ] 找到 ≥ 3 个相关文件
- [ ] 列出依赖影响（改 A 会影响 B/C）
- [ ] 风险点带等级（🔴/🟡/🟢）+ 缓解方案
- [ ] 给完整 6 步路径建议

### 0.3 产物落地

- **长期调研**（推荐）：写到 `docs/tasks/YYYY-MM-DD-<类型>-<topic>/research.md`
- **临时调研**：直接在 chat 输出，下次开工重做
- **不落地 = 不算完成**

### 0.4 防御对象

- AI 接到"做设计"指令后不看现状 → 重复造轮 / 忽略沉积议題
- AI 不知道哪个任务类型用哪个模板 → 输出格式混乱
- AI 调研 5 分钟就交差 → 用通用清单的 ≥ 3 文件 / ≥ 2 风险点强约束

---

## 一、6 步强制流程（不可跳级）

| 步 | 名称 | 谁触发 | 触发命令 | 产出文档 |
|---|---|---|---|---|
| **0** | **调研** | 我说"调研" | 按任务类型选 4 模板之一 | `research.md`（按 0 步 4 模板） |
| **1** | **规格（三脑交汇）** | 我让"做设计" | product-doc + design-spec + spec 三脑分工 | `product-doc.md`（人）+ `design-spec.md`（人/设计）+ `spec.md`（AI） |
| **2** | **计划 + 技术详细化** | 我说"出方案" | 业务/技术分离；≥ 2 方案对比 | `plan.md` + `db-design.md` + `api-spec.md` + `component-spec.md` |
| **3** | **拆分** | 我说"拆任务" | ≤ 1h AI 工作量原子任务，可独立 commit | `tasks.md` |
| **4** | **实现（TDD）** | 我说"开始实施" | 红→绿→refactor→commit；整合产出 test-cases.md | `test_xxx.py` + `test-cases.md` |
| **5** | **验证** | 我说"verify" | L3 整合测试 + L5 staging 跑通；L1/L2/L4 在 4 步分布式完成 | `verify.md` |
| **6** | **复盘** | 我说"复盘" | 经验沉淀；AI 无跨会话记忆，retro 是唯一通路 | `retro.md` + 更新 `CLAUDE.md` / `DOD.md` / 模板 |

**核心原则**：每一步必须等我的明确指令才能进下一步。没收到指令前只做当前阶段该做的事。

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

### 6.4 违反处置

- 没单测的 commit 不算完成 → 我（AI）会停下来补测
- 你可以拒绝 merge 没单测的代码

### 6.5 任务完成自动更新（2026-07-10 新增 · 用户加规则）

> **规则**：每次执行完任务并标 `TaskUpdate ... completed` 时，**自动更新对应的 `docs/tasks/<task-dir>/tasks.md`**：
> 1. **该任务的 `#### T<n>` 段标题**改为"✅ 已做"标记（如 `- [x] T<n>: ✅ DONE — ...`）
> 2. **该任务的状态行**如有 `本 PR 可延后` 等占位文字，改为"✅ 已实施（N/N 测试通过）"
> 3. **该 PR 的"PR <n> 标志"**行如有 "后做 / 暂缓" 描述，改为"✅ 已做"
> 4. **顶部总览表**（如 §8 "8.2 实施状态" 或 §10 总览）同步状态（✅ 已做 / ⏸ 暂缓）

> **示例**：
> - 完成 PR 6 实施 → 改 `docs/tasks/2026-07-09.../tasks.md`：
>   - PR 6 标题：`(暂缓)` → `(✅ 已做)`
>   - 状态行：`本 PR 可延后` → `✅ 已实施（4/4 测试通过）`
>   - 顶部总览：PR 6 → ✅ 已做
> - 跳过此规则 = 任务追踪不更新 = 用户无法从 tasks.md 看真实进度

### 6.6 verify 后自动写 retro（2026-07-11 新增 · 用户加规则）

> **规则**：`verify.md` 完成并 commit 后，**立即写 `retro.md`**（CLAUDE.md § 一.三阶段 6 = 复盘），不要等用户催。
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
- ❌ 手开 N 个 `Agent` tool 串成循环 — 上下文爆 / 跳出 loop 率高，升级 `Workflow`（见 § 6.7.1）

**memory**：`feedback-verify-loop-self-correct.md` · 为什么 / 怎么用 / 典型错误全在该文件

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

### 8.4 待用户决策

- **是否启动 V2**（补 3 个智能 service）？
- **是否 git push**（8 个 commit 在本地）？
- **是否补 15 个 🟡 部分项**（筛选参数 / 共享组件 / 移动端等）？
