# Product Doc · AI 推送模块（v2 · scope 收窄）

> 日期：2026-07-17 · 作者：Claude（与用户 2026-07-17 对话沉淀）
> 配套：[spec.md](spec.md) · [research.md](research.md) · [sources-investigation.md](sources-investigation.md) · [dual-agent-synthesis.md](dual-agent-synthesis.md)
> 上游：[原 spec 2026-06-22](../2026-06-22-new-feature-ai-push/product-doc.md) — 较宽 scope · 本版 supersede

---

## 一、目标用户（角色）

| 角色 | 痛点 | 频率 |
|---|---|---|
| **AI 应用开发者**（核心）| 信息过载 · 没时间筛选 · 想跟进 AI 圈但被淹没 | 每日 5 分钟 |
| **Agent 开发者** | 想看框架迭代 · GitHub trending 噪音大 · 找高质量信号难 | 每日 5 分钟 |
| **大模型技术关注者**（研究者/工程师）| 模型发布频繁 · 国内外对比耗时 · 想集中看一手源 | 每日 5 分钟 |

**不服务**：投资人 / PM / 创业方向关注者（scope 收窄已剔除）

---

## 二、核心价值主张

**"每日 2-3 分钟，让你看完 AI 圈今天的 5 件重要事"**

| 之前（行业现状） | 之后（AI 推送） |
|---|---|
| 30+ RSS 源自己刷 · 半小时看不完 | 5 条精选 · 2-3 分钟读完 |
| 摘要质量参差 · LLM 一刀切 | 5 维综合打分 · quality ≥ 0.75 才入选 |
| 看完不记得 · 没上下文 | 引用溯源 · 历史 digest 关联 |
| 国内渠道邮件打开率 < 10% | 主体验在 KnockWise 内 · 邮件/微信只作通知 |
| 散在 Twitter/HN/Discord | 一站式 + 国内外对比 |

---

## 三、关键决策（从 research/synthesis 聚合）

| # | 决策 | 理由 |
|---|---|---|
| D1 | **5 条固定 / 每日** · 不再 1-5 可变 | C1 共识：可变损害习惯 · Morning Brew/TLDR 都是固定 |
| D2 | **主体验在 KnockWise 内**（pull-based）· 邮件/微信作通知 | N1 洞察：减少反感知 · 推送退化为通知 |
| D3 | **8 核心源 + 用户可加自选** | C4 共识：30+ 太宽 · 8 默认最稳 |
| D4 | **每条 digest 含引用溯源** | C3 共识：反 LLM 幻觉 · 信任基础 |
| D5 | **国内/国外 + 模型/应用 双轴标签** | 用户原话 · 是用户思考框架 |
| D6 | **公众号资质立即申请**（4-6 周流程） | C5 共识：国内护城河 · 不阻塞 P0 |
| D7 | **MVP 不做对比 / watchlist / Obsidian** | Phase 2 后做 · 先把 digest 做稳 |
| D8 | **peer-attention signal 不做** | Q2 默认 · MVP 范围控制 |
| D9 | **MVP 完成后 6-8 周不评估** | X2 共识：让用户形成习惯 |

---

## 四、用户旅程（5 个核心场景）

### 4.1 早晨通勤（pull-based 主路径）
```
用户打开 KnockWise（mock interview 工具日常入口）
        ↓
主页面"今日 5 条"card 自动展示（vibe 标注："今日 5 条 · 偏安静"）
        ↓
扫 5 条标题 + 摘要（30 秒/条 = 2.5 分钟）
        ↓
感兴趣的 2 条 → [收藏] / 点击详情深读
        ↓
不感兴趣的 → [🔇 屏蔽]
```

### 4.2 邮件 fallback（用户没打开 KnockWise）
```
每天 8:00（用户配置时区）· 用户已开邮件通知
        ↓
收到邮件"今日 AI 推送已就绪 · 5 条"
        ↓
点邮件 → 跳 KnockWise /push 页面看完整 5 条
```

### 4.3 微信通知（中国用户 · Phase 1 后期）
```
公众号模板消息："KnockWise · 今日 5 条"
        ↓
点击 → 跳 KnockWise /push 页面
```

### 4.4 用户调偏好
```
设置页 → 信源管理（启停 + 加自选 RSS）
        ↓
关注标签 + 屏蔽标签
        ↓
推送时间（默认 8:00 可改）
        ↓
渠道开关（邮件 / macOS notification）
```

### 4.5 深读某条
```
点某条 digest → 详情页
        ↓
看完整 LLM 摘要 + source_url 跳转原文
        ↓
看 related_digest_ids（同主题历史）
        ↓
[收藏] [分享] [🔇 屏蔽]
```

---

## 五、成功指标（DOD）

### 5.1 用户行为指标

| 指标 | 目标 | 测量 |
|---|---|---|
| **日打开率** | > 40% | 收到推送用户 / 总订阅用户 |
| **读完率**（5/5 已读）| > 60% | 读完整 5 条用户 / 打开用户 |
| **收藏率** | > 10% | 收藏条数 / 阅读条数 |
| **屏蔽率** | < 5% | 屏蔽条数 / 推送条数 |
| **30 天留存** | > 30% | 30 天后仍订阅用户 |

> ⚠️ 红队提醒（X2）：**MVP 完成后 6-8 周不评估** · 让习惯形成 · day-14 retention < 20% 才考虑终止

### 5.2 工程质量指标

| 指标 | 目标 |
|---|---|
| 单测覆盖率 | ≥ 80% 核心 service |
| P95 推送延迟 | < 30s（从 cron 触发到邮件发出）|
| LLM 成本 / 用户 / 日 | < ¥0.05 |
| RSSHub / 爬虫稳定性 | ≥ 99% 月度可用 |

---

## 六、不在本期 MVP 范围（Phase 2+）

| 功能 | 阶段 | 备注 |
|---|---|---|
| 微信公众号模板消息发送 | P2 | 资质需 4-6 周 · D6 启动申请 |
| 飞书 / 钉钉 webhook | P2 | 1 周可上 · 公众号上线前替代 |
| 对比周报（"上周模型对比"）| P2 | 机会 O3 · 用户分享触发器 |
| Watchlist 关注追踪 | P2 | 机会 O2 + N3 · 个人数据起点 |
| Obsidian 双向同步 | P2 | V2.3 单向写回已有 · 加反向读 |
| 用户 embedding 个性化 | P3 | 1000 用户行为后才有意义 |
| 对话式 digest（可追问 AI 编辑）| P3 | 机会 O1 · worktree 高 |
| Open API / MCP endpoint | P3 | 机会 O13 · 给 agent 生态 |
| macOS notification | 不做 | spec 原 P1 暂缓 · 维持 |
| 微信小程序 | 不做 | 公众号够用 |

---

## 七、相关文档

- [research.md](research.md) — 0 步调研报告
- [sources-investigation.md](sources-investigation.md) — 信源清单 v2（30+ → 8 核心）
- [dual-agent-synthesis.md](dual-agent-synthesis.md) — 双 agent 调研聚合
- [spec.md](spec.md) — 技术契约
- [CLAUDE.md § 6.7 verify-loop](../../../../CLAUDE.md) — 实施自校验规则

---

## 八、签字

**产品意图已确认**：✅ 用户 2026-07-17

**已知偏差**：
- MVP 不做对比 / watchlist / Obsidian（Phase 2）· 用户已知
- peer-attention signal 不做（Phase 3）· 用户已知
- 国内公众号资质本周申请 · 不阻塞 MVP 编码
