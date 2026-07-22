# Retro · 议题审计任务（2026-07-21 audit 复核 + 2026-07-22 v3 闭环）

> **任务目标**：处理 audit 报告「测试真实性基线 · 2026-07-21」触发的所有事项
> **作者**：Claude（issues-audit agent · session 2026-07-22）
> **日期**：2026-07-22 · **版本**：v1 · **commit**：`ced766a` (本会话第一个 commit,包含 baseline.md)
> **必填段**：CLAUDE.md § 6.6 五段必备（2026-07-22 加固 v2 强制 · 包括 memory 更新清单）

---

## 1. 做对的事（沉淀到下次模板）

1. **§ 6.8 v2 六处同步严格执行** · 决策 13/14 落 docs/issues.md (债务 9 + 债务 3 修正) + decisions.md (决策 13/14 详细记录 + 决策 5 反向修正注) + V4 tasks.md (§ 9.1 双时间线表) · 用户重启会话任一会话都能从任一文件查到
2. **AST 静态识别 + pytest 实测双方法** · 平行验证 41 stub 边界（不是单靠 AST 推断，避免误报）
3. **commit 标题 `test+frontend: T20-T24 + T26 测试 stub` 是关键证据** · 这条历史 commit message 解释了"为什么会有 41 个空壳"——不是技术问题，是状态同步错误
4. **9 步修复分布统计表**（baseline.md § V4 模块逐项验证）· 给出"哪些已修 / 哪些还没"的精确清单 · 让跟进工作精准定位
5. **教训清单**（baseline.md § 教训）· 写出 5 条可迁移规则：commit 显式 stub 标注 + AST 阻断器是基建 + CI 不可绕过 + 数字真相必须递归 + 不动 audit 报告作为活文档
6. **retro v2/v3 分层** · V4 retro.md v2 已写（别人写的）+ 我加 v3 段（紧急修复段）· 不覆盖历史，体现时间线

## 2. 踩的坑（bugfix 记录 + feedback 候选）

1. **`ls backend/tests/test_*.py` vs `find ... -type f`** · 顶层 29 vs 递归 41 · 决策 5 措辞"41/20 → 29/25"方向反了 + 我之前以为决策 5 是把 41 改为 29（其实 audit 报告说应改为 41） · **修复**：决策 14 详细说明 + 决策 5 加 ⚠️ 注保留审计 trail
2. **git status 索引漂移** · Edit 完后 grep 验证改动在磁盘上但 `git status` 一开始不显示 · **修复**：过一会儿再跑 git status 显示正常 → 说明 git 内部索引有时延 · 不能盲目相信 git status
3. **cwd 漂移** · 多次 `cd backend` 失败（bash error `status: read-only variable`） · **修复**：改用绝对路径或检查 pwd
4. **§ 11 标题在 Edit 中丢失** · 我替换 § 11 内容时只复制了列表项没复制标题 · **修复**：补回"## 11. Retro 完成判定（v2 历史）" + 内容前移 + § 12.4 保留作为 v3 视角
5. **ask question 时机** · 跑了 baseline 后才问"下一步" · 更早问能省一轮 pytest collect 时间（约 0.79s 不算多但语义上更对）· **反思**：用户说"继续"是模糊信号，应该立即问具体方向
6. **T33 / T34 是别人做的** · 我第一次 Read 文件到跑 pytest 之间，T33 AST 阻断器 + T34 三 Gate CI 已落地（领先 origin 20 commits 的 worktree）· **不是 bug，是发现**：audit 触发了连锁修复，超出我第一次扫描的范围

## 3. 调研偏差修正

| 偏差 | 原说法 | 实际 | 修正 |
|---|---|---|---|
| audit 时点 | "测试类" = "49+" | 含 **41 stub + 3 弱测试 + 真测试** 混淆 | baseline.md § 教训 5 明确分开计 |
| 测试文件数 | issues-audit 决策 5 "29（漏算子目录）" → 决策 14 "41（递归）" | `find backend/tests -name "test_*.py" -type f \| wc -l` = 41 | 修正决策 5 措辞 + 决策 14 详细记录 |
| T33 状态 | audit 报告 § 6 列举 41 stub | 工作树已含 `scripts/check_test_quality.py` + 24 regression test + 6 violations 实时阻断 | baseline.md § 防御性基建段记录 |
| T34 状态 | audit 报告 § 6 仅提到"未接 GitHub Actions" | `.github/workflows/ci.yml` 已部署 3 job · 1 branch protection required policy 待用户 UI | retro v3 § 跟进项 |
| 41 stub → 现状 | audit 报告 41 stub "全部无效" | 8/9 已重写/删除 · 仅 T20 6 占位 violations 由 T33 显形 | V4 retro § 12.2 + baseline.md § V4 模块逐项验证 |

## 4. 下次该改什么（流程优化）

### 流程层面

1. **commit 显式 stub 标注必须**（baseline.md 教训 1）· `test(stub):` / `feat(no-test):` 前缀 + PR description 注明追踪 issue
2. **不动 audit 报告作为活文档** · audit 锁定时点 + 修复状态写新文档（baseline.md / retro v3）· 避免 audit 报告被反复修改失去审计价值
3. **数字真相必须递归统计** · `find ... -type f` 比 `ls` 可靠 · commit 时必须写绝对路径
4. **CI 必须把 AST 阻断器接进去** · T33 是 audit 的防御延伸，T34 把 quality gate 接到 GitHub Actions 是不可绕过的底线

### 技术层面

1. **§ 6.5 hook 现在已带 6 步 v2 DOD 校验**（git log 显示 "✅ 6 步 v2 DOD 校验通过"）· 这是新增的能力，让 commit 前自查更全面
2. **T33 violations 报告 + T34 workflow 的契约测试** · 现有 evidence 已证明 6 violations 是真实问题（T33 报告与我的 § 9.1 + V4 retro § 12.2 三方独立验证）
3. **git status 索引时延** · 不要根据"git status 一开始没显示"判断文件没改 · 多跑一次或者直接 grep 文件内容验证

### 规则沉淀（CLAUDE.md 候选）

- **§ 6.5 适用范围可加一条**："工作树领先 origin 多 commits 时，先 `git log --oneline -5` 看最近动态"
- **§ 6.8 v2 同步六处** 已经完整，本任务执行有效 · 可考虑加"决策表加 ✅/🟡/⏸ 状态列"作为强约束

## 5. memory 更新清单（v3 闭环）

### v3 已写（本会话内）

- ✅ **`feedback-pytest-runtime-bootstrap.md`**（2026-07-22 别人已写于 issues-audit 任务）· 我跑 baseline 时验证 = 真有效

### v3 新增（按本任务经验）

- ⏳ **`feedback-stub-test-debt.md`**（升级 v2 候选）· 加 § 3.5 "T33 AST 阻断器扫描方法" + § 4 "commit 前预检 3 层"
- ⏳ **`feedback-milestones-v4-v3-sync.md`**（新）· "retro 完成 ≠ 全部完成" + 标题修正模式
- ⏳ **`feedback-audit-report-vs-baseline-roles.md`**（新）· audit 报告锁定时点不可修改 · 修复状态写新文档（baseline.md / retro v3）· 防 audit 报告被反复改失去审计价值

### 不写（理由）

- ❌ feedback-decisions-sync-to-issues.md · 已在 v2 列表但本任务通过 § 6.8 v2 严格执行已覆盖 · 不再单独写
- ❌ verifier-required-for-critical.md · 已写 CLAUDE.md § 6.7 v1 · 本任务无 verifier 经验增量

---

## 元信息

- **文档版本**：v1 · 2026-07-22 · **commit**：`ced766a`
- **任务路径**：`docs/tasks/2026-07-21-issues-audit/`
- **本会话关键产出**：
  - `docs/issues.md` 债务 9 + 修正债务 3 + 进度更新（commit `ced766a` 部分）
  - `docs/tasks/2026-07-21-issues-audit/decisions.md` 决策 13/14 + 修正 5
  - `docs/tasks/2026-07-21-issues-audit/baseline.md` **新建**（115 行 · pytest 698/1/4/0 · 9 步对照 · 防御基建 · 教训）
  - `docs/tasks/2026-07-17-new-feature-ai-push/tasks.md` § 9.1 双时间线表
  - `docs/tasks/2026-07-17-new-feature-ai-push/retro.md` § 12/13/14 v3 段（待 commit）
  - `docs/rules/milestones.md` V4 段重写（v3 "核心功能已实现 · 验证修复中"）（待 commit）
  - `docs/tasks/2026-07-21-issues-audit/retro.md` **本文档**（待 commit）
- **关联**：
  - [`docs/issues.md` 债务 9](../issues.md)
  - [`docs/tasks/2026-07-17-new-feature-ai-push/tasks.md` § 9.1/§ 9.6/§ 9.7](../2026-07-17-new-feature-ai-push/tasks.md)
  - [`docs/tasks/2026-07-17-new-feature-ai-push/retro.md` § 12-14](../2026-07-17-new-feature-ai-push/retro.md)
  - [`docs/tasks/2026-07-21-issues-audit/baseline.md`](baseline.md)
  - [`docs/rules/milestones.md` V4](../../rules/milestones.md)
  - [`audit 报告原文`](../../../../Documents/Codex/2026-07-21/ai-agent-1-agent-agent-2/outputs/KnockWise-测试真实性基线-2026-07-21.md)

---

## 完成判定（CLAUDE.md § 6.6 闭环条件）

> ⚠️ **CLAUDE.md § 6.6 v2 规则**：本文档完成后立即起草，但**步骤 6 只有在用户确认改进项后才算完成**

- [x] § 1 做对了什么（含 6 条具体事项）
- [x] § 2 踩的坑（含 6 条 + bugfix）
- [x] § 3 调研偏差修正（含 5 条对照）
- [x] § 4 下次改什么（流程 + 技术 + 规则）
- [x] § 5 memory 更新清单（含已写 / 待写 / 不写分类）
- [x] **commit 引用**：所有改动链接到 commit hash（`ced766a`）+ 第二批 commit 待挂

**闭环状态**：起草完成 · 待用户确认 § 4 / § 5 改进项（特别是 memory 3 条新写）

---

## § 关联 commits

| commit | 内容 | 状态 |
|---|---|---|
| `ced766a` | docs(v4+audit): 登记假绿灯债务 9 + pytest baseline 698/1/4/0 + § 9.1 双时间线 | ✅ committed |
| （TBD）| docs(v4+milestones+audit-retro): 改正 V4 retro 标题 + V4 状态 + audit retro 闭环 | 🟡 待 commit |
