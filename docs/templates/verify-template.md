---
title: 验证文档模板（verify）
date: 2026-06-30
updated: 2026-07-21
status: v2
tags: [verify, 5步, L3, L5, 模板]
related:
  - [test-cases-template.md](test-cases-template.md)
  - [tasks-template.md](tasks-template.md)
---

# 验证文档模板（verify.md）

> **一句话**：步骤 5 只完成 L3 整合测试和 L5 staging；L1/L2/L4 已在步骤 4 分布式完成。
>
> **作者**：AI 主导证据收集，人确认运行结果。
>
> **对应 DOD**：`docs/DOD.md` §七。

## 0. 上游证据（必填）

| 分布式活动 | 证据位置 | 结果 |
|---|---|---|
| L1 类型检查 | `<command / log / commit>` | ✅ / ❌ |
| L2 单元测试 | `<command / test-cases.md>` | `<N passed / coverage>` |
| L4 review / verifier | `<review / verifier result>` | PASS / FAIL |

> 本段只引用步骤 4 已产生的证据，不在步骤 5 重新制造五层 gate。

## L3 整合测试（必填）

- **范围**：<API contract / 数据库事务 / 跨模块 / E2E>
- **命令**：`<可复现命令>`
- **环境**：<local integration / test>
- **结果**：PASSED / FAILED
- **耗时**：<X 秒>

### 场景

| 场景 | 期望 | 实际 | 证据 | 结论 |
|---|---|---|---|---|
| <场景 1> | <期望> | <实际> | `<log / response>` | ✅ / ❌ |
| <场景 2> | <期望> | <实际> | `<log / response>` | ✅ / ❌ |

## L5 staging 运行时验证（必填）

- **环境**：<staging / 本机完整服务；不得只写单元测试环境>
- **启动方式**：`./scripts/start.sh`
- **验证人**：<姓名>
- **日期**：YYYY-MM-DD
- **结果**：PASSED / FAILED

### 真实路径

| 用户路径 | 操作步骤 | 期望 | 实际 | 截图/日志 | 结论 |
|---|---|---|---|---|---|
| <路径 1> | <1...2...> | <期望> | <实际> | `<path>` | ✅ / ❌ |

## 失败与残留风险（必填）

- **失败项**：<无 / 具体项>
- **未覆盖项**：<无 / 具体项及原因>
- **残留风险**：<风险 + owner + 后续动作>

> 无法运行、依赖缺失或没有证据时必须写 FAILED/BLOCKED，不得写成通过。

## 用户验收（必填）

- **结论**：✅ 验证完成 / ❌ 退回步骤 4
- **确认人**：<name>
- **确认日期**：YYYY-MM-DD

## 🎯 硬性 DOD

- [ ] 已引用步骤 4 的 L1/L2/L4 证据
- [ ] L3 整合测试通过且有可复现命令
- [ ] L5 staging 真实路径通过且有日志/截图/浏览器证据
- [ ] 期望与实际逐项记录，失败没有被隐藏
- [ ] 用户明确确认验证完成

> 任一项未满足，verify.md 不算完成，不能进入步骤 6 复盘。

## 相关文档

- [test-cases-template.md](test-cases-template.md)
- [tasks-template.md](tasks-template.md)
- `docs/DOD.md` §七
