# 🇨🇳 AI 推送 × 微信公众号 集成方案

> **配套**：[`research.md`](research.md) § 5 差距 #1（微信公众号模板消息）
> **调研时间**：2026-07-17
> **状态**：🟡 设计稿 · 数字未现场实测

---

## § 0 · ⚠️ 置信度声明

本方案里**任何具体数字**（限流 / 审核天数 / errcode）都**未经腾讯官方文档现场验证**。

| 数字 | 来源 | 置信 | 建议核验 |
|---|---|---|---|
| 500K 服务号 / 100K 订阅号 日上限 | web search 二手 | 🟡 | 后台"开发 → 接口权限"实测 |
| 200 calls/min | 同上 | 🟡 | 同上 |
| 1/30s, 100/hr 单用户 | 同上 | 🟡 | 同上 |
| 3-5 天审核 | 行业经验 | 🟡 | 申请一个模板实测 |
| 1 次/月行业切换 | 同上 | 🟡 | 后台操作时确认 |

**实测方法**：申请一个个人订阅号 → 服务号（要企业资质），填一个测试模板，从技术角度看到真实数字。

---

## § 1 · 决策矩阵 · 该不该做

### 1.1 数字匹配（500K / 天）

| KnockWise 用户规模 | 是否够 | 说明 |
|---|---|---|
| 0 - 1K 用户 | ✅ 远超 | 用 0.2% 配额 |
| 1K - 50K 用户 | ✅ 够 | 用 10% 配额 · 每日推送全覆盖 |
| 50K - 200K 用户 | 🟡 接近 | 需要优化推送频率（不每天推） |
| > 200K 用户 | ❌ 不够 | 转向 WeCom（企业微信）|

**KnockWise 现实**：用户规模大概率在 1K-10K 量级 · 500K 完全够。

### 1.2 真正的卡点 · 行业分类

模板消息**一个行业只能选一个分类**，且自定义路由不能跨分类。

**AI 推送是跨行业**：
- "📚 教育" → 适合学习内容
- "💻 科技" → 适合 AI 资讯
- "💼 商业" → 适合商业动态
- 用户偏好不同 → 单一分类**约束内容多样性**

🟡 验证：你推给用户的 AI 推送 = "**科技 + 商业 + 教育** 三类的混合" → 模板分类**只选一个**会损失其他类的视觉规范。

**解决方案**：
- **方案 A**:选最大类（"科技"）· 内容里跨类用 emoji 区分 · **推荐**（最简单）
- **方案 B**:申请多个模板（每个分类一个）· 但需要切行业 · 1 次/月限制 · **不推荐**
- **方案 C**:放弃模板消息 · 改用**客服消息**（48 小时窗口）· 用户交互后才能发 · 不适合日常推送

### 1.3 频率限制 vs 推送频率

| 用户偏好 | 公众号限制 | 冲突？ |
|---|---|---|
| 每日 1 推（默认）| 1/30s · 100/hr | 无冲突 |
| 每周 1 推 | 同上 | 无冲突 |
| 实时通知（如题目答错即时推）| 1/30s 是约束 | 🟡 如果你以后做实时 push 会卡 |

**KnockWise AI 推送目前是日/周/月** → **无冲突**。

---

## § 2 · 集成架构

### 2.1 用户视角流程

```
┌────────────────────────────────────────────────────┐
│ KnockWise AI 推送·微信渠道                          │
│                                                     │
│ ① 用户在 KnockWise 设置页                          │
│    点"绑定微信" → 跳到微信 OAuth                    │
│    ↓                                               │
│ ② 微信回调 /api/wechat/callback，拿到 openid       │
│    ↓                                               │
│ ③ 存 profiles.wechat_openid                          │
│    ↓                                               │
│ ④ 用户在 AI 推送设置里勾"启用微信推送"              │
│    ↓                                               │
│ ⑤ 每天 8:00 cron                                    │
│    ├ 现有邮件链路（保持）                           │
│    └ 新增微信链路：                                 │
│       - 通过 OpenAPI 调模板消息                      │
│       - 按用户 openid 单发                          │
│                                                     │
│ ⑥ 用户微信收到模板消息                              │
│    ├ 标题："AI 日报 2026-07-17 · 10 条精选"          │
│    ├ 摘要：日报第 1 条 + LLM 摘要                   │
│    ├ 点击 → H5 页（公网可访问的 /push/daily/[date]）│
│    └ 或点击小程序跳转（如果有的话）                  │
└────────────────────────────────────────────────────┘
```

### 2.2 现有架构如何扩展

```
┌─ 当前 DigestService.push_daily() ────────────────┐
│   1. fetch_all_sources()                          │
│   2. select_top10()                              │
│   3. generate_summary()                          │
│   4. save_to_db()                                │
│   5. send_email()      ← 已有                    │
│   6. send_macos_notification() ← 已有            │
│   7. update_profile_stats()                      │
└──────────────────────────────────────────────────┘

扩展：
   8. send_wechat_template()  ← 新增（本期目标）
```

### 2.3 新增的 Service

```python
# backend/services/wechat_push_service.py

class WeChatPushService:
    """微信公众号模板消息推送服务。

    依赖:
    - WECHAT_APP_ID / WECHAT_APP_SECRET  (环境变量)
    - 用户表 wechat_openid 字段（profiles 加列）
    - 已审核通过的模板 ID (WECHAT_AI_DIGEST_TEMPLATE_ID)
    """

    async def send_daily_digest(
        self, user: User, daily: DigestDaily
    ) -> bool:
        """主入口：发 AI 日报到用户微信。"""
        access_token = await self._get_access_token()
        template_data = self._render_template(daily)
        result = await self._call_template_send_api(
            access_token,
            user.wechat_openid,
            template_id=settings.WECHAT_AI_DIGEST_TEMPLATE_ID,
            data=template_data,
            client_msg_id=self._gen_msg_id(user, daily),
        )
        return self._handle_result(user, result)
```

### 2.4 新增的数据字段

```sql
-- profiles 加 1 个字段
ALTER TABLE profiles
    ADD COLUMN wechat_openid VARCHAR(64) NULL,
    ADD COLUMN wechat_bound_at DATETIME(6) NULL,
    ADD COLUMN wechat_enabled BOOLEAN NOT NULL DEFAULT FALSE;

-- digest_settings 加 1 个字段（或独立 settings 表，看现有设计）
-- wechat_enabled BOOLEAN
```

### 2.5 新增的 API

| Method | Path | 用途 |
|---|---|---|
| GET | `/api/wechat/oauth-url` | 生成绑定二维码 URL |
| GET | `/api/wechat/callback` | OAuth 回调，存 openid |
| POST | `/api/wechat/unbind` | 解绑 |
| GET | `/api/wechat/status` | 当前绑定状态 |

---

## § 3 · 模板设计 · 建议草稿

### 3.1 模板分类选择（决策）

🟡 选"**科技 - IT 科技**"，理由：
- AI 资讯是核心定位 · 最契合
- 审核通过率最高
- 用户心智匹配

### 3.2 模板 ID 注册时填的内容

| 字段 | 内容 |
|---|---|
| 模板名称 | AI 日报精选通知 |
| 行业 | IT 科技 |
| 模板内容 | `{{first.DATA}} 标题：{{keyword1.DATA}} 共 {{keyword2.DATA}} 条 {{remark.DATA}}` |
| 关键词 | first / keyword1 / keyword2 / remark |
| 跳转 | H5 链接或小程序（推荐 H5，降低用户进入门槛）|

### 3.3 渲染示例

用户收到：

```
┌──────────────────────────────────────┐
│  🔥 AI 日报 2026-07-17                │
│                                       │
│  今日 10 条精选 · 5 分钟读完          │
│                                       │
│  头条：OpenAI 发布 GPT-5 多模态版      │
│  共 10 条                             │
│                                       │
│  [查看完整日报 →]                      │
│                                       │
│  KnockWise · AI 日报                   │
└──────────────────────────────────────┘
```

---

## § 4 · 关键工程问题

### 4.1 Access Token 管理

- **有效期**：2 小时 · 不刷新会过期
- **频率**：200 calls/min 全局配额 · access_token endpoint 也算
- **建议**：
  - Redis 缓存 access_token（key = `wechat:access_token` · TTL = 7000s）
  - 异步刷新（cron 每 1.5 小时刷一次 · 避免用时再去拿）

### 4.2 消息队列（避免突发 429）

🟡 推荐：
- Redis Sorted Set（score = unix timestamp）做待发队列
- 一个消费者线程 · 每 1-2 秒 poll 一次 · 每次批量 50-100 条
- 配合 sliding window log（每个 openid 一小时内发送时间列表）· 避免 1/30s 限流

### 4.3 错误处理（errcode 码表）

| errcode | 含义 | 处理 |
|---|---|---|
| 0 | 成功 | 标记 done |
| 40001 / 42001 | access_token 过期 | 刷新 token 重试 |
| 43004 | 用户黑名单 | 标记用户取消订阅 |
| 45009 | 频率超限 | exponential backoff · 5/15/60 分钟 |
| 其他 | 未知错误 | 记录日志 · 不重试 |

### 4.4 幂等性

🟡 推荐：
- 客户端生成 `client_msg_id = uuid(user_id, digest_id)` · 32 字符
- Redis 锁：`SET wechat:msg:{client_msg_id} 1 NX EX 120` · 2 分钟 TTL
- 防止 at-least-once 投递的重复

---

## § 5 · 实施路径（建议 4 步走）

| 步骤 | 工作量 | 价值 | 风险 |
|---|---|---|---|
| **Step 1 · 服务号注册** | 1-2 周（资质）| 🟡 必需 | 资质（需要企业 / 个体工商户）|
| **Step 2 · 模板审核** | 1 周（3-5 天）| 🟡 必需 | 审核可能拒 · 行业分类卡 |
| **Step 3 · 后端集成** | 3-5 天 | 高 | 限流逻辑可能踩坑 |
| **Step 4 · 前端 UI** | 2-3 天 | 中 | OAuth 跳转体验 |

**总周期**：4-6 周（含服务号资质）。

### 备选：如果不想申请服务号

- **微信小程序**订阅消息：替代方案 · 限制更严但不需要服务号
- **微信客服消息**：48h 窗口 · 用户交互后才能发
- **第三方推送**（个推 / 极光 + 微信通道）：集成微信通道 · 走 SDK

---

## § 6 · 给 KnockWise 的具体推荐

### 6.1 优先级判断

| 选项 | 工作量 | 价值 | 推荐度 |
|---|---|---|---|
| **A. 上 微信公众号 模板消息** | 4-6 周 | 🟢 国内分发天花板 | ⭐⭐⭐ 高 |
| **B. 上 飞书机器人** | 2 天 | 🟡 B 端拓展 | ⭐⭐ 中 |
| **C. 上 邮件 + in-app（已有）** | 已完成 | 通用但不够国内 | ⭐ 低 |

### 6.2 决策触发

| 你的回答 | 该选项 |
|---|---|
| "我有企业资质，且想国内爆发" | **A 微信公众号** |
| "我想先做轻量级 B 端拓展" | **B 飞书机器人** |
| "我没有企业资质，订阅号够用" | **A 但用订阅号（100K 配额也够 1K 用户）** |
| "我不急，先把 AI 推送 RSS + LLM 自身打磨好" | **C 等产品稳定再说** |

### 6.3 建议 · 短期 / 中期

**短期（本周）**：
- 把 `digest_hide.duration_sec` 字段塞进 LLM 选题 prompt（项目差距 #3 · 见 research.md § 5）· 2 小时工作量
- 价值：直接提升个性化 · 无外部依赖

**中期（4-6 周）**：
- 上微信公众号模板消息 · 按本方案实施
- 价值：国内分发天花板

---

## § 7 · 风险清单

| 风险 | 概率 | 影响 | 缓解 |
|---|---|---|---|
| 服务号申请被拒（资质不全）| 🟡 中 | 阻塞上线 | 备选订阅号（100K 配额也够）|
| 模板审核拒（行业分类错误）| 🟡 中 | 阻塞 | 选"IT 科技" · 重新提交 1 次/月限制 |
| 500K 不够用（用户 > 200K）| 🔴 低 | 阻塞 | 转 WeCom |
| 单用户 1/30s 限制 · 实时 push 卡 | 🟡 中 | 实时 push 不能做 | 保持日/周/月推送 · 不做实时 |
| 用户举报骚扰被封号 | 🟡 中 | 全局 | 严控推送频率 + 提供"不再接收" |

---

## § 8 · 元 · 验证

应用刚加的 § 6.7 verify-loop rule 检查本文档：

| 校验 | 状态 |
|---|---|
| 对照 research.md § 5 差距 #1 | ✅ 本文档就是差距 #1 的展开 |
| 对照 spec.md § 七 推送渠道实现 | ✅ 邮件实现有 · 微信是补充 |
| 对照 § 六 单测强制 | ❌ 未含测试设计（不在本文档 scope）|
| 数字有置信度标注 | ✅ 每条都标 🟡/🔴 |
| Pre-commit hook | 🟡 不进 git 暂 commit |

**自我验证**：本方案**不应直接落地**——所有 🟡 数字必须先实测。落地前**最小可行验证清单**：

- [ ] 注册服务号（或订阅号）拿到 app_id + secret
- [ ] 申请 1 个测试模板 · 看审核几天
- [ ] 用 1 个测试 openid 手动 curl 模板消息 API · 看 errcode 实际响应
- [ ] 用 Redis 跑 200 calls/min 压测 · 看 429 触发

完成 4 条 → 数字才有 🟢 置信 → 才能进代码开发。

---

## 元信息

- **文档版本**：v1 · 2026-07-17
- **路径**：`docs/tasks/2026-07-17-investigate-ai-push-survey/wechat-integration-plan.md`
- **配套**：[`research.md`](research.md) § 5 #1 · [原 spec.md § 七](../../tasks/2026-06-22-new-feature-ai-push/spec.md)
- **下一步**：**做不做** 由用户决策 · 不进 6 步流程