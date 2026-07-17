# 各阶段交付物清单

> **来源**：原 CLAUDE.md § 三（2026-07-17 拆出）
> **触发**：进入 1 步设计 / 4 步实施 / 5 步验证 阶段时读

## 阶段 1：设计文档
- 写在 `docs/`，中文文件名
- 包含：目标、范围、**全局架构图**、模块边界、用户旅程、业务规则
- **不做**：具体代码、库选型最后一步、页面 mockup、SQL、API 详细

## 阶段 1.5：架构图规则（强制）

**所有设计类 / 技术类文档必须先画全局图**，再写细节。

1. 文档开头（第一节内）必须有 **全局架构图**（ASCII / mermaid），让读者 30 秒内 get 整体
2. 每个大功能 / 子系统章节开头有 **局部架构图** + **用户流图** / **状态机** / **决策树**
3. 图要清晰可读（box-drawing 字符 + 标签）
4. 出现顺序：**全局 → 子模块 → 细节**

> 反例：上来就贴 SQL 表结构 / endpoint 列表 → ❌
> 正例：先画系统怎么连、用户怎么走 → ✅

## 阶段 1.6：产品 vs 技术分文件（强制）

**设计文档只放产品内容**。技术细节分流到对应文件：

| 内容 | 放哪 |
|---|---|
| 功能架构 / 用户旅程 / 业务规则 / 边缘场景 | 设计文档（产品） |
| 数据库表 / SQL / 索引 / 迁移 | `技术文档.md` 或 `xxx-技术设计.md` |
| API endpoint / Request/Response | `接口文档.md`（增量加） |
| Service 方法签名 / 错误码 | `技术文档.md` 或 `xxx-技术设计.md` |
| UI 草图 / 流程图 / 组件清单 | 阶段 4 单独出 |

**判断标准**：如果一段内容是"程序员看的"（SQL、API、代码签名）→ 移出设计文档。

## 1.7 非新功能分支（必走路径）

| 类型 | 路径 | 关键约束 |
|---|---|---|
| **新功能** | 0 → 1 → 2 → 3 → 4 → 5 → 6 | 完整流程 |
| **Bug 修复** | 登记 [`docs/issues.md`](../issues.md) → fix commit → 回归测试 | 必须有测试（见 [`testing-rules.md`](testing-rules.md)） |
| **重构** | 登记议題 → 引用议題编号 commit → 测试通过 | 不改业务行为 |
| **议題关闭** | 直接执行调研结论 | commit 标题含议題编号（如 `fix(A)`） |
| **P0 紧急修复** | 例外：即时修 + 24h 内补登记 | 必须补回归测试 + `docs/issues.md` |

> **关闭例外面口子**：第二节"绝对不能动"原"修复 bug"例外太宽，本节明确化分类。

## 1.8 阶段 4 完成定义（DOD · 实施完毕必过）

> ⚠️ v2 重命名：原"阶段 6 完成定义"在新框架中改为"阶段 4 完成定义"（实施在新框架是步骤 4）。

- [ ] 所有 phase 的设计文档 / 技术文档 / 页面文档都已 commit
- [ ] [`docs/issues.md`](../issues.md) 相关议題状态已更新（📋 → 🚧 → ✅）
- [ ] pre-commit hook 通过（tsc + pytest 全绿）
- [ ] **核心 service 测试覆盖率 ≥ 80%**（见下方清单）
- [ ] 5 验证通过（verify.md L3 整合 + L5 staging 跑通）
- [ ] 用户口头确认（或明确说"verify 完成"）

**不满足 DOD = 阶段 4 未完成**，不得进入下一个需求。

### 核心 service 清单（必须 ≥ 80% 覆盖率）

| service | 路径 | 重要性 |
|---|---|---|
| `interview_service` | `backend/services/interview_service.py` | 🔥 核心（面试生命周期） |
| `learning_progress_service` | `backend/services/learning_progress_service.py` | 🔥 核心（SM-2 算法） |
| `question_bank_service` | `backend/services/question_bank_service.py` | 🔥 核心（题库） |
| `qa_service` | `backend/services/qa_service.py` | 🔥 核心（问答） |
| `recommendations_service` | `backend/services/recommendations_service.py` | 🔥 核心（推荐） |
| `study_plan_service` | `backend/services/study_plan_service.py` | 🔥 核心（学习计划） |

**非核心 service**（不强制 80%）：`obsidian_service` / `news_service` / `resume_parser` / `archive_service` / `seed_service` / `asr_tts` / `agora`

**测量命令**：
```bash
cd backend && ./.venv/bin/python -m pytest tests/ \
  --cov=services --cov-report=term-missing
```

## 阶段 2：设计文档验证
- 自查清单（见 `docs/面试题库设计.md` 内的"验证清单"小节）
- 输出：✅ 通过 / ⚠️ 需修改 / ❌ 推翻

## 阶段 3：设计文档详细化
- 补：每个 API 的 Request/Response 样例
- 补：每个数据表的字段类型 + 索引 + 约束
- 补：每个 service 的方法签名
- 补：错误码、异常分支
- 补：数据迁移 SQL

## 阶段 4：页面规划
- ASCII 草图（每个页面一张）
- 用户操作流程
- 组件清单
- 状态机（如适用）
- 不写代码

## 阶段 5：统一通过
- 等用户说"通过"
- 用户可能要求改某一步，回到对应阶段重做

## 阶段 6：开始实施
- 用户说"开始实施" 才动
- 按阶段 3 详细化的设计落地
- 实施中如发现设计有误，**先停下报用户**，再决定改设计还是改代码
