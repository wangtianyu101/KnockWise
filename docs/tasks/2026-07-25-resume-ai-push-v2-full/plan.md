# Plan · AI 推送 v2 完整实施

> 日期：2026-07-25 · 作者：Claude · 版本：v1
> 配套：[research.md](research.md) · [tasks.md](tasks.md)

---

## 1 · 方案

**分 6 阶段渐进实施** · 当前会话执行 Phase A · 后续 session 接力 B-F。

### Phase A · 即时可做（不依赖外部服务）

| A# | Requirement | 工作 |
|---|---|---|
| A1 | R6 | push_timezone 字段完整化（DB + schema + UI 5 选项下拉）|
| A2 | R7+R10 | 30s 阅读时长上报 + 主区域标已读 |
| A3 | R5 | URL HttpUrl 强校验 + tags 上限拦截 |
| A4 | spec § 5 | 34 TCs pytest 化（按 R 分文件）|

### Phase B · RSS 真集成（待 RSSHub）

需要用户先部署 RSSHub（Docker 国内拉不动 → 备选 mock 8 XML）。

### Phase C · 行为反馈

R10 反馈到 scoring · 需要 LLM 接通。

### Phase D · 多渠道

R8 邮件 · 需要 Resend API key。

### Phase E · 可观测性

metrics + 性能预算 · 不依赖外部。

### Phase F · UX 完整化

mockup 全部对齐 + i18n · 不依赖外部。

## 2 · 本会话做（Phase A）

见 [tasks.md § Phase A](tasks.md)

## 3 · DOD

### 3.1 必跑

- [ ] pytest tests/services/test_digest_settings_timezone.py 绿
- [ ] pytest tests/api/test_digest_read.py 绿
- [ ] pytest tests/api/test_digest_sources_validation.py 绿
- [ ] e2e/digest.spec.ts 场景 8（30s 阅读后标已读）✅
- [ ] e2e/digest.spec.ts 场景 9（settings 时区切换）✅
- [ ] typecheck 无新 error

### 3.2 验证

- [ ] /push/settings UI 显示时区下拉 · 保存生效
- [ ] /push/daily/[item-id] 停留 30s 后该条标"已读"
- [ ] /api/digest/sources POST 拒绝 invalid URL → 400

## 4 · 风险 + 缓解

| 风险 | 等级 | 缓解 |
|---|---|---|
| DB migration 失败 | 🟡 | _MIGRATIONS 表已 pattern · 同款 ALTER |
| pytest fixture 与本地 DB 冲突 | 🟢 | 沿用 conftest.py |
| Phase A 完成后 LLM/RSSHub 仍未接通 → 真 push_daily 仍 0 items | 🟡 | dev fallback 保留 · spec v2 字段先齐 |

## 元信息

- **路径模式**：full-6（分阶段 · 当前 Phase A · 后续 B-F 由后续 session 接力）
- **范围**：🔴 完整实施（Phase A 当前会话 · 后续阶段 follow-up）
- **估时**：Phase A ~8h · 全部 ~35h