---
title: 开发规范政策单一真源 · 技术方案
type: plan
step: 2
date: 2026-08-09
status: archived
tags: [refactor, governance, policy, plan]
related:
  - research.md
  - spec.md
  - decisions.md
  - task.yaml
  - ../../issues.md
---

# 开发规范政策单一真源 · 技术方案

> **2026-08-09 范围修订**：用户选择「按照最简版 快速修复下冲突」。本计划的 policy registry / adapter 方案暂不实施，保留为后续可复用方向；当前任务降级为 `fix-mini`，只统一既有 task 状态语义和 active consumer。

> 路径模式：`refactor-6`
>
> 本计划只处理 R-01。`product-doc.md` 不适用，`design-spec.md` 不适用；不涉及 UI、API 或数据库变化，因此不创建 component/api/db 技术文档。

## 0. 上游契约与当前基线

- **调研**：[`research.md`](research.md) R-01、§ 3.5、§ 6～8。
- **已验收规格**：[`spec.md`](spec.md)，2026-08-09 用户原话「验收步骤 1，出方案」。
- **决策主账**：[`decisions.md`](decisions.md) D-001/D-002。
- **既有状态语义**：复用债务 13 的 `[x]` 只表示 implementation、禁止裸 `✅ DONE`。
- **既有状态控制面**：复用债务 23 `workflow_state`；本计划不新增事件、投影或状态分支。
- **治理运行时**：本地 `python3` 为 3.9.6，CI 为 Python 3.12；治理 job 已固定 `PyYAML==6.0.3`。
- **现有接线**：CI `Workflow governance` 已调用 `scripts/check-governance.py`；本地 Hook 为 `scripts/pre-commit`。
- **并行状态修正**：债务 23 T18/T19 已于本次决策前完成并提交；当前最小修复基于 T19 后的 HEAD 执行，不再存在原计划中的 T19 并发编辑风险。

## 1. 方案对比

| 维度 | 方案 A：Markdown 权威块 + 解析器 | 方案 B：声明式 YAML registry + validator | 方案 C：Python code-first registry |
|---|---|---|---|
| 核心思路 | 在 `docs/rules/` 的 Markdown 中放结构化 fenced block，解析后验证其他 consumer | `.governance/policies.yaml` 保存稳定语义、rendering 与 consumer；Python CLI 只解释和校验 | Python 类/常量直接定义 rule、rendering、consumer 和验证函数 |
| 改动范围 | 中 | 中 | 中～大 |
| 机器可读性 | 🟡 依赖 Markdown parser | ✅ 原生结构化 | ✅ 原生代码结构 |
| 人类可维护性 | ✅ 文档内直接读 | ✅ YAML 易 review，说明可链接到文档 | 🟠 改规则必须读 Python |
| 通用/项目 overlay | 🟠 需要自定义 Markdown 约定 | ✅ schema 可显式表达 | ✅ 继承/组合可表达，但更难移植 |
| 安全边界 | 🟠 fenced block 解析边界脆弱 | ✅ 数据与执行器分离；可禁止命令字段 | 🟠 policy 本身是可执行代码 |
| Python 3.9/3.12 兼容 | ✅ | ✅ dataclass + PyYAML | ✅，但类型/插件复杂度更高 |
| 新依赖 | 无 | 无；复用 PyYAML | 无 |
| 测试影响 | parser/golden/漂移测试 | schema/loader/golden/consumer/Hook/CI 测试 | import/注册/插件/副作用测试 |
| 复用性 | 🟠 偏当前文档体系 | ✅ 可直接做未来 Repo Kit 内核 | 🟠 强耦合 Python 项目 |
| 预计工作量 | 5～7h | 7～9h | 8～11h |
| 主要风险 | Markdown 格式变化导致误解析 | YAML schema 与 adapter 生成器需同版本演进 | 导入即执行、副作用、非 Python 项目难复用 |

### 方案 A：Markdown 权威块 + 解析器

将权威定义放在 `docs/rules/policies.md` 的 fenced YAML/JSON block 中，CLI 提取后校验。

**优点**：规范和解释在同一文档，迁移小，维护者阅读路径短。

**缺点**：Markdown 标题、代码块、缩进和示例都可能影响提取；“文档即数据”容易再次把说明文字与控制输入混在一起。为防模板残留而存在的现有 checker 已说明文本解析边界容易漂移。

**兼容性**：可兼容现有文件，但跨工具复用仍依赖 KnockWise 的 Markdown 结构。

**测试影响**：需要覆盖多代码块、缺失 fence、示例误识别、中文标点和 frontmatter 组合；负例数量最多。

### 方案 B：声明式 YAML registry + validator（推荐）

新增 `.governance/policies.yaml` 作为唯一政策 authority；数据只允许稳定标识、枚举、文本 rendering、仓库相对路径和受限 assertion 类型，不允许 shell 命令、Python import 或网络地址。`scripts/policyctl.py` 负责严格加载、渲染检查和 consumer coverage。

**优点**：

1. authority 是纯数据，Agent 读取仓库正文不会自动获得执行能力。
2. 已有 governance CI 正好安装 PyYAML，无需新增供应链依赖或独立服务。
3. `--view index|worktree` 可复用现有 Hook/CI 的 staged/checkout 模式。
4. 将来可原样抽入 Repo Kit，但本任务只落 KnockWise 的首条 policy。

**缺点**：需要维护 schema version；人读 adapter 要采用受控 marker 块；行为型 checker 仍需测试证明，而不能只靠字符串存在。

**兼容性**：不改变 `workflow_state`；只把 AGENTS/DOD/template/Hook 提示从手写 authority 降为 generated/validated consumer。现有 PyYAML 6.0.3 与 Python 3.9/3.12 都可运行。

**测试影响**：新增 schema、重复 rule、overlay、marker、digest、INDEX、Hook rc 和 governance CI subprocess 测试；可复用现有临时 Git 仓模式。

### 方案 C：Python code-first registry

在 `scripts/governance_policy/rules.py` 直接构造 `PolicyRule` 对象，consumer 也注册为 Python 函数。

**优点**：类型最强，复杂行为验证容易，调试路径直接。

**缺点**：policy 本身变成可执行代码，违背“仓库文本只作数据”的最小能力方向；非 Python 项目难复用；导入副作用和插件加载扩大攻击面。

**兼容性**：对 KnockWise 可行，但未来抽成跨项目资产时需要 Python runtime。

**测试影响**：除 schema/consumer 测试外，还必须覆盖 import 副作用、注册顺序、重复插件和异常模块。

## 2. 推荐方案与技术架构

**推荐**: 方案 B——`.governance/policies.yaml` + 严格 Python validator + bounded adapter blocks。

```text
.governance/policies.yaml  ← 唯一 policy authority（纯数据）
            │
            v
scripts/policyctl.py validate/render --check
            │
     ┌──────┴───────────┐
     v                  v
generated 文本块       enforced consumer
AGENTS/DOD/template     check_task_state.py + 测试
pre-commit 提示              │
     └─────────┬─────────────┘
               v
scripts/pre-commit (INDEX) / check-governance.py (CI worktree)

workflow_state：保持独立，只提供运行状态事实，不读写 policy authority
```

### 2.1 建议文件布局

```text
.governance/
  policies.yaml
scripts/
  policyctl.py
  governance_policy/
    __init__.py
    models.py
    loader.py
    validator.py
    adapters.py
  check-governance.py
  pre-commit
backend/tests/
  test_governance_policy_models.py
  test_governance_policy_validator.py
  test_governance_policy_cli.py
  test_check_governance.py
  test_task_governance_gate.py
```

### 2.2 v1 Policy 数据结构

```yaml
schema: governance-policy/v1
policy_version: 1.0.0
rules:
  - rule_id: task-status-semantics
    version: 1.0.0
    status: ACTIVE
    scope: PROJECT
    semantics:
      checkbox_meaning: implementation_committed
      naked_done: FORBIDDEN
    renderings:
      human_zh: "[x] 仅表示 implementation 已落入 commit；禁止裸 ✅ DONE。"
      hook_zh: "把对应 task 标为 [x]，并记录 implementation commit；不要写裸 ✅ DONE。"
    consumers:
      - consumer_id: agents-task-sync
        kind: HUMAN_ADAPTER
        mode: GENERATED
        target: AGENTS.md
        marker: task-status-semantics
        rendering: human_zh
      - consumer_id: task-state-checker
        kind: CHECKER
        mode: ENFORCED
        target: scripts/check_task_state.py
        check_id: task-state-naked-done
        test_node: backend/tests/test_task_governance_gate.py::test_no_naked_done
```

上例只表达契约形状；最终字段名可在实施时按已验收语义小幅调整，但不得加入 `command`、`shell`、URL、secret 或任意 Python import 字段。

### 2.3 Adapter 策略

- Markdown 和 Shell 提示使用明确 marker 的小块生成：
  - Markdown：`<!-- policy:<id>:start/end -->`
  - Shell：`# policy:<id>:start/end`
- `policyctl render --check` 只比较 canonical rendering 与 marker 内内容；marker 外仍归人维护。
- `policyctl render --write` 是显式写操作：先打印 diff，目标路径必须在 consumer registry，冲突或缺 marker 时拒绝覆盖。
- Python Checker 不由 YAML 生成代码；registry 只登记稳定 `check_id` 与测试 node，行为由 subprocess 测试证明。

### 2.4 CLI 与退出码

| 命令 | 作用 | 写入 | 退出码 |
|---|---|---|---|
| `policyctl.py validate --view worktree` | schema、唯一性、consumer coverage、adapter digest/内容 | 否 | 0 PASS；1 policy violation；2 invocation/config error |
| `policyctl.py validate --view index` | 校验 staged policy 与 consumer | 否 | 同上 |
| `policyctl.py render --check --view ...` | 检查 bounded block 是否与 rendering 一致 | 否 | 漂移 rc=1 |
| `policyctl.py render --write` | 显式更新已注册 adapter block | 是，仅注册目标 | 冲突/越界 rc 非零 |

CLI 使用 `argparse`、`pathlib`、`subprocess.run(argv)`；不使用 `shell=True`，不执行 policy 中的字符串。

### 2.5 Consumer 接线

1. `scripts/pre-commit`：每次运行 `policyctl validate --view index`；P95 目标小于 2 秒，缺 CLI/policy fail closed。
2. `scripts/check-governance.py`：每次运行 `policyctl validate --view worktree`；现有 CI workflow 无需新增 job 或权限。
3. `check-governance.py` 的临时 Git E2E fixture 必须复制 policyctl、模块、policy 和 consumer fixtures，证明远端入口真实传播 rc。
4. Hook E2E 必须验证 staged INDEX 与 unstaged worktree 分离，不能用 worktree 的绿覆盖 staged 失败。

### 2.6 首条 policy 的迁移范围

| Consumer | 当前问题 | 目标状态 |
|---|---|---|
| `AGENTS.md` § 6.5 | 要求 `- [x] ... ✅ DONE` | generated 人读块只保留 `[x]=implementation`，禁止裸 DONE |
| `docs/DOD.md` | 完成/验收语义分散 | generated 简短引用，不成为状态 authority |
| `docs/templates/tasks-template.md` | 同段同时写 `[x]` 需 verifier+acceptance、又写仅 implementation | 统一为既有债务 13 语义 |
| `scripts/pre-commit` | tasks sync 报错要求写被 checker 禁止的 DONE | generated Hook 提示改为合法格式 |
| `scripts/check_task_state.py` | 行为大体正确，但 consumer 身份未注册 | 登记 `check_id`，保留禁止裸 DONE 行为并补生产 CLI 回归 |

历史 task 文档不全量改写；只有 active adapter 和当前模板必须一致。历史证据中的 `DONE` 通过 legacy 边界保留。

## 3. 实施批次与依赖

### 批次 A · Policy kernel（不碰债务 23 文件）

1. 严格 models/loader，拒绝未知字段、重复 rule/consumer、绝对路径和越界路径。
2. validator + bounded adapter parser，先完成 worktree 模式。
3. `policyctl validate/render --check` 与稳定退出码。

### 批次 B · 首条 policy 与 consumer 迁移

1. 写 `task-status-semantics` canonical policy。
2. 将 AGENTS/DOD/tasks-template/pre-commit 的小段迁入 marker block。
3. 登记 `check_task_state.py` 行为 consumer，补负例 oracle。

### 批次 C · 本地/CI 接线

1. INDEX 读取和 staged/worktree 隔离。
2. pre-commit fail-closed 接线与 Shell rc E2E。
3. check-governance subprocess 接线与临时 Git CI E2E。

### 批次 D · 对账与退役

1. 全局扫描 active consumer，确认不再存在要求写裸 DONE 的指令。
2. 验证 policy validator 连续运行幂等、P95 小于 2 秒。
3. 将旧手写规则标为 generated/validated consumer，不保留第二份 authority。

**依赖顺序**：A → B → C → D。债务 23 可先完成 T18；随后暂停其 T19，完成本任务 A～D，再让 T19 基于 policy consumer contract 修改状态 Gate。两者不得并行编辑 AGENTS/DOD/templates/checker。

## 4. 测试策略

| 层 | 重点测试 | 主要 oracle |
|---|---|---|
| Models | schema version、未知字段、重复 id、路径越界、禁用 command/url | 非法输入构造失败且错误码稳定 |
| Loader | YAML 语法、空文件、类型错误、3.9/3.12 兼容 | rc 分类正确，不吞异常 |
| Adapter | marker 缺失/重复/嵌套、内容漂移、幂等 render | 第二次 render 字节不变 |
| Consumer | DONE 合法/非法文本、checker/test node 存在性 | 旧冲突 fixture 必须红，新 fixture 绿 |
| INDEX | staged 坏 + worktree 好；staged 好 + worktree 坏 | `--view index` 只受 staged 内容影响 |
| Hook | 缺 policyctl、policy 漂移、合法 commit | `/bin/sh` subprocess 真实 rc |
| CI governance | 临时 Git base..head 政策/consumer 变更 | `check-governance.py` 传播子 CLI 非零 rc |
| 安全 | `../`、绝对路径、shell 字段、symlink 越界 | fail closed，无目标外写入或命令执行 |

### 4.1 Spec → 测试映射

| Spec TC | 自动化测试方向 |
|---|---|
| TC-001/002 | models/loader 唯一性测试 |
| TC-003/004 | canonical rendering 与 AGENTS/pre-commit 漂移测试 |
| TC-005/006 | consumer coverage / N/A reason 测试 |
| TC-007 | bounded block digest/内容漂移测试 |
| TC-008 | policy 与 workflow_state 隔离测试 |
| TC-009 | version/migration/retirement 激活测试 |
| TC-010 | 双次 validate/render 幂等测试 |

### 4.2 验证命令目标

```bash
python3 scripts/policyctl.py validate --view worktree
python3 scripts/policyctl.py render --check --view worktree
backend/.venv/bin/python -m pytest \
  backend/tests/test_governance_policy_models.py \
  backend/tests/test_governance_policy_validator.py \
  backend/tests/test_governance_policy_cli.py \
  backend/tests/test_check_governance.py \
  backend/tests/test_task_governance_gate.py -v
sh scripts/pre-commit
```

实施时先跑最小红/绿测试；完整治理回归和全 backend suite 的范围在步骤 3 tasks 中拆分。不得因为测试收集成功就判 PASS。

## 5. 安全与权限方案

### 5.1 四道关落实

1. **不可信输入**：YAML、Markdown、Hook 文本全部是数据；严格 schema、长度上限、稳定枚举、目标路径 allowlist。
2. **最小权限**：`validate`/`render --check` 只读；`render --write` 仅写 registry 中的仓库相对目标，不接 secrets、网络或 Git push。
3. **供应链**：不新增依赖；复用固定 `PyYAML==6.0.3` 和现有 pinned Actions。
4. **人工 Gate**：policy/consumer 变更仍需用户 review；工具不改远端 ruleset、不提交、不推送。

### 5.2 明确禁止

- Policy schema 不允许 `command`、`shell`、`script`、URL、secret 名称或动态 Python import。
- 不允许 consumer target 为绝对路径、`..`、symlink 越出仓库或未注册文件。
- 不把 consumer 文件里出现 `PASS` 当测试证据。
- 不允许 Writer 在 policy 中声明 verifier/acceptance 运行事实。

## 6. 风险与缓解

| 风险 | 等级 | 缓解 |
|---|---|---|
| 与债务 23 T19 并发修改同一文件 | 🔴 | T18 后暂停 T19；R-01 先建立 policy contract，再恢复 T19 |
| YAML 被当成命令配置造成 Agent/CI 代码执行 | 🔴 | v1 纯数据 schema；禁止命令/URL/import；CLI 不用 shell |
| generated block 覆盖 marker 外用户内容 | 🔴 | 精确 marker、路径 allowlist、默认 `--check`、显式 `--write`、冲突拒绝 |
| 只校验字符串存在而误称行为生效 | 🔴 | Checker consumer 必须登记 check_id + 真实 test node；Hook/CI subprocess 验 rc |
| 本地 Python 3.9 与 CI 3.12 行为不同 | 🟠 | 不用 3.10+ union 语法；兼容两版本；CI 和本地 fixture 同输入 golden |
| 每次 Hook 增加明显耗时 | 🟡 | 静态校验无服务启动/网络，P95 <2s；超标则做安全的 path cache，不跳 Gate |
| 历史 `DONE` 被全局扫描误伤 | 🟠 | 只校验 active registered marker/consumer；历史任务保持 legacy |
| schema 与 CLI 版本漂移 | 🟠 | schema/version 严格配对；未知版本 fail closed；golden migration 测试 |

## 7. 兼容、迁移与回滚

### 7.1 兼容策略

- v1 只纳管 `task-status-semantics`，其他规则不自动宣称已迁移。
- 现有 AGENTS/DOD/template 只替换相关小段，不重排整个文档。
- `workflow_state` imports、event schema、state ref、T18 shadow 文件均不改。
- CI 继续使用现有 `Workflow governance` job name和 `contents: read` 权限。

### 7.2 激活策略

1. 一个原子变更同时加入 policy、validator、consumer marker、Hook/CI 接线和测试。
2. 激活前旧冲突 fixture 必须红，新 canonical fixture 必须绿。
3. 无长期双写/Shadow：同一 commit 内迁移 authority；失败则整组不合入。

### 7.3 回滚

- 回滚整个 policy implementation commit，恢复此前文件；不运行数据回滚，因为没有运行状态或数据库写入。
- 不允许只回滚 `.governance/policies.yaml` 而保留依赖它的 Hook；consumer/authority 必须原子回滚。

## 8. 工作量与交付物

| 批次 | 估时 | 交付物 |
|---|---:|---|
| A Policy kernel | 2～2.5h | models/loader/validator/CLI + 单测 |
| B 首条 policy 迁移 | 1.5～2h | canonical policy + 5 个 consumer + 回归测试 |
| C Hook/CI 接线 | 1.5～2h | INDEX/Hook/governance E2E |
| D 对账与文档 | 1～1.5h | 扫描、性能、幂等、文档状态同步 |
| 独立 verifier 修复余量 | 1h | commit 级 PASS/FAIL 循环 |
| **总计** | **7～9h** | R-01 完整关闭证据 |

## 9. 需要用户拍板的决策点

### 决策 1 · 技术载体

- A：Markdown 权威块。
- **B：YAML registry + validator（推荐）**。
- C：Python code-first registry。

**推荐理由**：纯数据、无新依赖、兼容现有治理 job、跨项目复用成本最低。

### 决策 2 · Adapter 策略

- A：所有 consumer 只做人工文本 + semantic lint。
- **B：人读/提示文本使用 bounded generated block；行为 Checker 用测试证明（推荐）**。
- C：整个 AGENTS/DOD/template 全文件生成。

**推荐理由**：B 能消除目标规则漂移，又不会覆盖 marker 外的用户内容。

### 决策 3 · 与债务 23 的实施顺序

- A：等债务 23 T20 全结束再做 R-01。
- **B：允许 T18 完成，随后暂停 T19；先实施 R-01，再恢复 T19（推荐）**。
- C：R-01 与 T19 并行。

**推荐理由**：B 避免同文件冲突，并让 T19 直接遵守新 policy contract；C 禁止。

### 决策 4 · 运行时依赖

- **A：复用 PyYAML + stdlib dataclass/manual strict validation（推荐）**。
- B：治理 job 再安装 Pydantic。

**推荐理由**：A 保持现有供应链和 Python 3.9/3.12 兼容，不扩大治理 bootstrap。

## 10. 步骤 2 Gate

- **计划状态**：`ARCHIVED / SUPERSEDED BY D-003`。
- **推荐组合**：决策 1=B、决策 2=B、决策 3=B、决策 4=A。
- **用户选择**：未采用推荐组合；选择最小冲突修复并降级 `fix-mini`。
- **实施限制**：不创建 `.governance/policies.yaml`、policyctl 或生成器；只改直接冲突的 active consumer 和回归测试。

## 11. 步骤 2 DOD 自检

- [x] 比较了 3 个真实方案，包含优缺点、兼容、工作量与测试影响。
- [x] 给出单一推荐方案及仓库证据。
- [x] 风险均带等级和具体缓解。
- [x] 列出 4 个需要用户拍板的决策点。
- [x] 引用 `research.md`、`spec.md` 与 `decisions.md`。
- [x] `product-doc.md`、`design-spec.md` 明确不适用。
- [x] DB/API/UI schema 不变，条件技术文档不触发。
- [x] 明确与债务 23 T18/T19 的互斥实施顺序。
- [x] 未越级修改 production policy、Hook、Checker 或 CI。
