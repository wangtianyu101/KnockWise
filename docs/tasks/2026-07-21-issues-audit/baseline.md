# Pytest Baseline · KnockWise 后端（2026-07-22）

> **目的**：记录 audit 触发的紧急修复链反应后的 pytest 真实可跑状态 · 解决 audit 报告 § 7 阻塞项「建立后端 pytest 运行基线」
> **触发**：用户「先跑 pytest baseline」（2026-07-22）
> **关联**：
> - [`research.md`](research.md) § 7（基线）
> - [`decisions.md` 决策 11/12/13/14](decisions.md)（决策记录）
> - [`docs/issues.md` 债务 3 + 债务 9](../issues.md)（主账）
> - [`docs/tasks/2026-07-17-new-feature-ai-push/tasks.md` § 9.6 / § 9.7](../2026-07-17-new-feature-ai-push/tasks.md)（实施证据）
> - [audit 报告原文](../../../../Documents/Codex/2026-07-21/ai-agent-1-agent-agent-2/outputs/KnockWise-测试真实性基线-2026-07-21.md)（审计源数据）

---

## 📊 总体数字

| 指标 | 数值 | 备注 |
|---|---:|---|
| `pytest --collect-only -q` | **703 tests collected** | audit 时 674 → 现 +29（代码库演进过程中新增） |
| `pytest --tb=no -q` | **698 passed, 1 skipped, 4 xfailed, 0 failed** | 1.66s 跑完 · 零 failed |
| 后端覆盖率（全量） | **行 61.55%** | 详见 § 9.7 T34 实施证据 |
| Digest 核心覆盖率 | **行 85.61% / 分支 82.00%** | 高于 T34 80% / 70% gate |
| V4 模块 9 步修复 | **8/9 已完成 · T29 待实跑** | 详见 § 历史时间线 |
| T33 AST 阻断器 violations | **6**（T20 占位标记） | exit 1 · 真实阻断（audit 时未存在此阻断器） |
| T34 GitHub Actions 三 Gate | **3 job up · 1 required policy pending** | quality + typecheck + build |

---

## 🔬 V4 模块逐项验证（audit 41 个空壳 → 现状对照）

| 文件 | audit 状态 | 行数 audit→现状 | 现实状态 | audit → 现状偏差 |
|---|---|---|---|---|
| `backend/tests/api/test_digest_api.py` (T20) | 16 全 `pass` | 54 → 292 行 | ✅ 重写（16 测试 + 18 行/测试真实密度 + AsyncMock + 断言） | **-16 空壳** |
| `backend/tests/e2e/test_digest_push.py` (T24) | 4 全 `pass` | 11 → 208 行 | ✅ 重写（注释「T24 重写 · 2026-07-22」+ 5 scenario） | **-4 空壳** |
| `backend/tests/services/test_digest_llm.py` (T22) | 4 全 `pass` | 14 → 已删 | ✅ 删/重写/转移（被 T33 阻断器后续清理） | **-4 空壳** |
| `backend/tests/services/test_rss_fetch.py` (T23) | 5 全 `pass` | 12 → 214 行 | ✅ 重写（5 测试 + 43 行/测试真实密度） | **-5 空壳** |
| `backend/tests/services/test_digest_service_unit.py` (T21) | 12 全 `pass` | 31 → 已删 | ✅ 删（重复空壳） | **-12 空壳** |
| `frontend/tests/visual/digest.spec.ts` (T28) | **文件不存在** | — | ✅ 创建 | **从无到有** |
| `frontend/tests/e2e/digest.spec.ts` (T29) | 5 scenario 已 collect 未实跑 | — | 🟡 文件已实化 · 5 scenario 待实跑（需 dev server 启 3000/8000） | **未实跑** |
| `scripts/deploy-rsshub.sh` (T30) | **不存在** | — | ✅ 创建 + `docker-compose.yml` 有 RSSHub service | **从无到有** |
| `backend/utils/metrics.py` (T31) | **不存在** | — | ✅ 创建（logger.py 仅保留 trace/logger 工具） | **从无到有** |

**净空壳减少**：audit 41 → **T20 6 个 violations = 真实 stub 残留**（T33 阻断器已显形报告）

---

## 🛡️ 防御性基建（audit 触发的连锁修复）

| 组件 | 落地状态 | 价值 |
|---|---|---|
| **T33 · AST 空测试阻断器** | ✅ `scripts/check_test_quality.py` + 24 回归测试 + 6 violations 实时阻断 | **根本性防御**：未来 stub 测试无法混入 |
| **T34 · 三 Gate CI** | ✅ `.github/workflows/ci.yml` 3 job（quality / typecheck / build）· exit 1 | CI 层阻断，让质量门不可绕过 |
| 债务 5（密码哈希注释） | ⏸ 暂缓（已与决策 4 关联） | 生产前实施 |

---

## ⏱️ 历史时间线（audit 触发 → baseline 闭环）

| 日期 | 事件 | commit / 文档 |
|---|---|---|
| 2026-07-21 | Codex 双 agent 完成 AST 静态审计 | [`KnockWise-测试真实性基线-2026-07-21.md`](../../../../Documents/Codex/2026-07-21/ai-agent-1-agent-agent-2/outputs/KnockWise-测试真实性基线-2026-07-21.md) |
| 2026-07-21 ~22 | 用户/agent 紧急修复 T20/T22/T23/T24 + T28 + T30 + T31 | V4 tasks.md § 9.2 / git history |
| 2026-07-22 早 | 决策 A 实施：service 真调 graph.ainvoke + with_structured_output | decisions.md 决策 1（议题 A+E） |
| 2026-07-22 早 | 决策 5 实施：issues.md 5 处偏差修正 | decisions.md 决策 5 |
| 2026-07-22 早 | 决策 15 实施：HTML mockup 回归 | decisions.md 决策 15 |
| 2026-07-22 | T33 + T34 落地（Harness 治理阶段 3+4） | V4 tasks.md § 9.6 / § 9.7 |
| 2026-07-22 | **本 agent**：登记债务 9（P0-1） + 校正 T20-T31 状态（P0-2） | docs/issues.md / V4 tasks.md § 9 |
| 2026-07-22 | **本 agent**：跑 pytest baseline 698/1/4/0 + 写本文件 | 本文档 |

---

## 🚧 剩余事项（不阻断 baseline，但需跟进）

### T29 Playwright 实跑
- **现状**：`frontend/tests/e2e/digest.spec.ts` 文件已实化（5 scenario），但**未实跑**
- **阻塞**：需要 dev server 启动 3000 + 8000
- **建议**：单独会话跑（不依赖本 baseline）

### T20 6 个 violations（T33 阻断器显形）
- **现状**：T20 重写后大部分真实，但仍有 6 处占位标记
- **定位**：T33 的 `scripts/check_test_quality.py` 已实时报告（exit 1），等下一次 commit 时自动阻断
- **建议**：下周实施 T33 收尾时一并清理

### GitHub branch protection
- **现状**：T34 workflow 已部署，但分支保护规则尚未标 3 个 checks 为 required
- **建议**：需用户在 GitHub UI 配置（不能 agent 自动化）

### 债务 5 注释修正（生产前）
- **现状**：`backend/models/__init__.py:49` 注释写 `# bcrypt hash` 实际是 pbkdf2
- **建议**：下次涉及 models 时一并改

---

## 📝 验证命令清单（复现本 baseline）

```bash
cd backend
./.venv/bin/python -m pytest --collect-only -q   # 应输出 703 tests collected
./.venv/bin/python -m pytest --tb=no -q          # 应输出 698 passed, 1 skipped, 4 xfailed
./.venv/bin/python -m pytest tests/test_check_coverage.py tests/test_ci_workflow.py tests/test_network_policy.py -q  # 13 passed
./.venv/bin/python -m pytest tests/test_check_test_quality.py -q  # 24 passed (T33 回归)
python3 scripts/check_test_quality.py backend/tests   # exit 1 + 6 violations (T20)
```

---

## 🎯 教训（写入下个 audit 模板）

1. **commit message 用 "stub" 显式标注**：commit `9251fd6` 用了 "stub" 一词，被 audit 抓到。**未来 commit 涉及 stub 必须**：
   - title 显式 `test(stub):` 或 `feat(no-test):`
   - PR description 明确写"暂未实装测试"
   - 关联追踪 issue（如本债务 9）
2. **T33 类型 AST 阻断器是必须基建**：audit 发现任何空壳都太晚，预防胜过修复
3. **T34 CI 三 Gate 是 audit 的延伸**：不被 CI 拦截的"质量门"等于没门
4. **数字真相必须递归统计**：`ls` 顶层漏算子目录，让 audit 第一次写"29"错；必须 `find ... -type f`
5. **不动 audit 报告作为活文档**：原报告就锁定 2026-07-21 时点，修复状态写在新文档（如本 baseline.md），避免冲突
