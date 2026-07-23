# 🐛 调研报告 · Bug：pre-commit 环境缺失时假绿

> 日期：2026-07-23 · 调研人：Claude Code + 4 个独立对抗 Agent · 紧急度：P0
> 路径模式：`fix-mini`（0 → 4 回归测试与修复 → 6 复盘）

## 1. 任务理解

- **用户原话**："开始吧 对抗调研"；对推荐方案回复"确认"。
- **现象**：相关 backend/frontend 文件已暂存，但 `.venv` 或 `node_modules` 缺失时，`scripts/pre-commit` 警告后跳过测试，最后仍可能显示“全部通过”。
- **期望**：只有对应 Gate 真正具备执行能力并成功运行时才可通过；未触发的技术栈不要求安装环境。
- **任务边界**：风险范围感知的 fail closed + 最小健康探针 + 真实恢复指引 + 8 个回归场景。

## 2. 复现路径

### 2.1 复现步骤

1. 暂存需要后端或前端 Gate 的文件。
2. 删除或破坏对应 `.venv` / `node_modules`。
3. 运行 `scripts/pre-commit`。
4. 当前逻辑在目录缺失时警告并跳过，未执行 pytest/tsc，却继续到成功输出。

### 2.2 触发条件

- 后端：可执行源码、测试、fixture、依赖或测试/运行配置发生改动。
- 前端：TS/JS 源码、测试、依赖、lockfile、类型或构建配置发生改动。
- 对应执行环境缺失或损坏。

### 2.3 稳定性

目录缺失场景稳定发生；目录存在但 binary/依赖损坏目前只会在执行阶段偶然暴露，说明单纯 `-d` 检查不足。

## 3. 影响范围与关闭条件

### 3.1 影响范围

- **直接文件**：`scripts/pre-commit`。
- **关联文件**：`backend/requirements.txt`、`frontend/package-lock.json`、`.github/workflows/ci.yml`、`scripts/start.sh`、`docs/rules/local-dev.md`。
- **流程影响**：本地 L1/L2 fail-fast 信号；当前 required checks 尚未完全配置，不能只依赖 CI 兜底。
- **数据影响**：无业务数据损坏；风险是未经执行的变更被标记为本地通过。

### 3.2 关闭条件

- [ ] 相关后端改动 + 后端环境缺失或损坏 → 阻断。
- [ ] 相关前端改动 + 前端环境缺失或损坏 → 阻断。
- [ ] 测试改动不享受警告放行。
- [ ] 纯文档不触发应用环境检查。
- [ ] 后端以可执行 Python + pytest 探针判断执行能力。
- [ ] 前端以本地 `node_modules/.bin/tsc` 判断执行能力，不使用可能联网的 `npx`。
- [ ] 错误提示使用真实恢复命令，不再引用不存在的 `scripts/setup.sh`。
- [ ] 保留现有紧急 bypass，但输出不得称为“通过”。

## 4. 根因假设与对抗核验

| 假设 | 证据 | 结论 / 验证方法 |
|---|---|---|
| H1：目录缺失时警告放行导致假绿 | `scripts/pre-commit:21-24,43-46` | ✅ 主根因 |
| H2：目录存在即可证明环境健康 | `.venv/bin/python`、`.bin/tsc` 可能缺失 | ❌ 已反驳 |
| H3：纯测试改动可仅靠 AST/CI | 项目刚发生空壳测试假绿；fixture 也可破坏收集 | ❌ 当前不接受 |
| H4：所有 commit 都需全栈环境 | 当前已按 staged path 分流；纯 docs 有独立 checker | ❌ 不采用全局一刀切 |
| H5：CI 可完全兜底 | CI 检查存在，但 required policy 尚未完全配置 | 🟡 不能作为当前放行依据 |

## 5. 最近相关改动与仓库状态

执行证据：

```bash
git log --oneline -10 -- scripts/pre-commit scripts/start.sh .github/workflows/ci.yml docs/issues.md
git status --short --branch
```

相关提交：

- `47cfc15`：pre-commit pytest/tsc 退出码修复。
- `0f64064`：pre-commit tasks.md 同步校验。
- `2fa3b04`：CI auto-fix 安全和 issues 决策同步。

当前工作树已有 `.agents/`、后端 service、多个 task 文档和前端测试结果等其他改动。本任务不得覆盖或整理它们。

相关文件不少于 3 个：

1. `scripts/pre-commit`
2. `scripts/start.sh`
3. `.github/workflows/ci.yml`
4. `backend/requirements.txt`
5. `frontend/package-lock.json`
6. `docs/rules/local-dev.md`

## 6. 输出建议

### 6.1 单一推荐方案

采用**风险范围感知的 fail closed**：

- 相关后端可执行/测试/依赖配置改动触发后端 Gate；环境缺失或损坏则阻断。
- 相关前端可执行/测试/依赖配置改动触发前端 Gate；环境缺失或损坏则阻断。
- 测试文件与生产代码同等要求真实运行。
- 纯文档、缓存和生成物不触发完整应用 Gate。

### 6.2 最小健康探针

后端：

```sh
test -x backend/.venv/bin/python
backend/.venv/bin/python -m pytest --version
```

前端：

```sh
test -x frontend/node_modules/.bin/tsc
```

随后运行真实 pytest/tsc；不维护额外应用依赖 import 白名单。

### 6.3 恢复指引

- 后端：删除不存在的 `./scripts/setup.sh` 指引，给出当前真实的 Python 3.12 venv + requirements 安装命令。
- 前端：使用 `cd frontend && npm ci`，与 lockfile 和 CI 对齐。
- 轻量 backend-test bootstrap/profile 作为独立 P1，不捆绑本项。

### 6.4 八个回归场景

| # | 场景 | 期望 |
|---:|---|---|
| 1 | 纯 docs 改动、环境均缺失 | 不检查应用环境 |
| 2 | 后端相关改动、`.venv` 缺失 | 阻断 + 真实恢复命令 |
| 3 | `.venv` 存在但 Python 不可执行 | 阻断 |
| 4 | Python 可执行但 pytest 探针失败 | 阻断 |
| 5 | 环境健康但 pytest 失败 | 阻断 |
| 6 | 前端相关改动、本地 tsc 缺失 | 阻断 + `npm ci` |
| 7 | tsc 存在但执行失败 | 阻断 |
| 8 | 对应环境健康且 Gate 成功 | 继续 |

## 7. 风险与缓解方案

| 风险 | 等级 | 缓解方案 |
|---|---|---|
| 临时 worktree/首次 clone 安装成本高 | 🟡 | 给真实恢复命令；保留显式紧急 bypass；另立轻量 bootstrap P1 |
| 路径分类遗漏可执行配置 | 🔴 | 回归覆盖源码、测试、依赖与配置；分类集中定义 |
| 仅看目录导致损坏环境假健康 | 🔴 | 检查可执行 binary + 最小工具探针 |
| 依赖 import 白名单与 requirements 漂移 | 🟡 | 不维护白名单，让真实测试收集暴露依赖问题 |
| 范围扩散到 hook 安装/CI/服务健康 | 🟡 | 明确列为排除项 |

明确排除：hook 自动安装、required checks 配置、bypass trailer/reason、新建多 profile `setup.sh`、`start.sh` 服务健康、端口误判、scripts tasks 同步漏口、全量 pre-commit 重构、P0-1。

## 8. 用户决策清单

| 日期 | 决策项 | 选择 | 状态 | 用户原话 | 关联 |
|---|---|---|---|---|---|
| 2026-07-23 | P0-2 环境缺失策略 | 风险范围感知的 fail closed + 最小健康探针 + 8 个回归场景 | ✅ 已决策 | "确认" | [`decisions.md` 决策 1](decisions.md#决策-1--采用风险范围感知的-fail-closed) |

## 自检清单

- [x] 任务理解与用户确认完成
- [x] 已读 `docs/issues.md`
- [x] 已核对相关 git log / git status（沿用同轮 P0 调研执行证据）
- [x] 已定位 ≥ 3 个相关文件
- [x] 已列依赖影响与分级风险
- [x] 已给出 fix-mini 路径建议
- [x] 4 个独立 Agent 完成对抗调研
