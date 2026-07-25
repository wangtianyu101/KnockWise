# 设计 Mockup 工作流

> **触发条件**：任务涉及用户可见的 UI / 页面 / UX；不依赖用户说出某句固定口令
>
> **触发时机**：步骤 1 `design-spec.md` 完成页面地图后、用户验收规格前产出；步骤 2 `component-spec.md` 只引用已验收设计并定义实现契约
>
> **路径位置**：
> - 实际 HTML mockup：`docs/tasks/<date>-<type>-<topic>/mockups/*.html`
> - 设计索引：`docs/designs/<topic>/index.md`（仅链接 · 不存内容）

---

## 1. 三层产物（ASCII + HTML + index）

设计 spec 阶段必须产出的三层产物，缺一不可：

| 层 | 位置 | 用途 | 谁能看到 |
|---|---|---|---|
| **页面 ASCII Wireframe** | design-spec.md §3 · 5-10 行/页 | 在 chat 里直接展示 · 用户不需要打开文件 | chat / doc |
| **HTML Mockup** | `task/mockups/01-today.html` 等 | 在浏览器打开 · 看真实交互 + 真内容 | 浏览器 |
| **设计索引** | `docs/designs/<topic>/index.md` | 从全局入口跳转 · 不存内容 · 仅链接 | markdown |

> **Why 三层**：ASCII 是 sketch · HTML 是产品 · index 是导航 · 三者互相不可替代

---

## 2. HTML Mockup 风格规范

### 必做

| 维度 | 规范 |
|---|---|
| **CSS 框架** | ❌ 不引外部依赖 · **纯 inline CSS + CSS variables** · 单文件 standalone |
| **样式方法** | `:root { --bg: #f9fafb; ... }` 定义主题变量 · 不引 Tailwind CDN（重 3MB+）|
| **内容真实感** | ✅ 真实 AI 内容（如 Claude 4.7 Sonnet / DeepSeek V4 / Qwen3-Coder）· ❌ Lorem ipsum |
| **交互** | 至少 1-2 个 modal（HideDialog / AddSource）· `onclick` 即可关闭（纯 HTML）|
| **响应式** | 移动端 padding 自动调整 · nav 间距缩小 · `@media (max-width: 640px)` |
| **页面互链** | nav 链接互相跳转 · 用户能完整 click through |
| **行数** | 150-300 行/页 · 不堆 CSS 进 1000 行 |
| **自查** | 产出后必须 `open 文件` 至少自查 1 次 · 不能有 typo / 死链 |

### 双轴标签色彩（KnockWise 已认可）

```css
:root {
  /* type 标签 */
  --accent-blue:   #1e40af; --accent-blue-bg:   #dbeafe;  /* 模型 */
  --accent-purple: #5b21b6; --accent-purple-bg: #ede9fe;  /* 应用 */
  /* region 标签 */
  --accent-orange: #9a3412; --accent-orange-bg: #fed7aa;  /* 国内 */
  --accent-green:  #065f46; --accent-green-bg:  #d1fae5;  /* 国外 */
}
```

### 反例（不要做）

- ❌ 产出 React 组件代码 · 用户要的是**视觉稿**不是代码
- ❌ 产出 Figma link · 用户没装 Figma
- ❌ ASCII mockup 用太多字符 · 5-10 行/页够用
- ❌ Tailwind CDN · 单文件 3MB+ 不 portable
- ❌ Placeholder 内容（"Lorem ipsum 1"）· 用真实内容
- ❌ 跨页面不互链 · nav 链接断开 · 用户体验差

---

## 3. design-spec.md § 3 ASCII Wireframe 规范

### 位置

```
design-spec.md
├── § 1 用户旅程
├── § 2 页面地图
├── § 3 页面线框  ← 每个页面 1 张 ASCII wireframe
├── § 4 交互细节
└── § 5 视觉规范
```

### 字符与尺寸

| 维度 | 规范 |
|---|---|
| **字符** | `┌─┐│└┘├─┤`（box drawing）· 不用 ASCII `+-` 拼接 |
| **宽度** | 统一 65 字符宽（便于跨页对齐）|
| **高度** | 5-10 行/页（详情页可到 15-20 行）· 不塞满所有交互 |
| **数量** | 每个 page 1 个 · 含 modal 的页面 · modal 单独画框 |
| **标注** | 关键元素用 `[...]` 标注 · 如 `[🔖 收藏]` `[模型][国外]` badge |

### 标准 5 行布局模式

```
┌─────────────────────────────────────────┐
│ Header (logo + nav links)               │
├─────────────────────────────────────────┤
│ Vibe/Status 徽章                         │
├─────────────────────────────────────────┤
│ Page Title + Subtitle                    │
├─────────────────────────────────────────┤
│ [Content Card 1]                         │
│ [Content Card 2]                         │
├─────────────────────────────────────────┤
│ Footer (status / pagination)            │
└─────────────────────────────────────────┘
```

### 含 Modal 的页面（如详情页）

```
┌─────────────────────────────────────────┐
│ ← 返回 + Page Title                      │
├─────────────────────────────────────────┤
│ [Badges] · Source · Time                │
│                                         │
│ # H1 Title                              │
│ Summary paragraph (3-5 lines)           │
│ ┌─ Source Box ──────────────────────┐  │
│ │ Original URL + timestamp           │  │
│ └────────────────────────────────────┘  │
│ [Action buttons row]                    │
│ 📚 Related items list                   │
└─────────────────────────────────────────┘

[点击按钮弹 Modal]
┌──────────────────┐
│ Modal title      │
│ ◉ Radio option   │
│ ○ Radio option   │
│ [keyword chips]  │
│ [Cancel] [OK]    │
└──────────────────┘
```

---

## 4. 路径约定（task/mockups/ + designs/index.md）

### 路径结构

```
docs/
├── tasks/
│   └── YYYY-MM-DD-<type>-<topic>/
│       ├── spec.md
│       ├── design-spec.md           # 页面 ASCII + 引用 mockups/
│       ├── db-design.md
│       ├── component-spec.md        # 步骤 2 引用已验收设计
│       ├── plan.md
│       └── mockups/                  # ✅ 实际 HTML mockup
│           ├── 01-today.html
│           ├── 02-daily-detail.html
│           └── ...
│
└── designs/
    └── <topic>/                       # e.g. ai-push-v2/
        └── index.md                   # ✅ 仅链接 · 不存内容
```

### 路径原则

| 类型 | 位置 |
|---|---|
| HTML mockup 实文件 | `docs/tasks/<date>-<type>-<topic>/mockups/*.html` |
| 设计索引（仅链接）| `docs/designs/<topic>/index.md` |
| 旧版设计（archive）| `docs/designs/<topic>/archive/*.html` |

### index.md 模板

```markdown
# <Topic> 设计索引

> 本目录仅存链接 · 不存实际设计文件

## HTML 页面 mockup
| # | 路径 | 页面 |
|---|---|---|
| 1 | `../../tasks/<task>/mockups/01-today.html` | /push 今日 |

## 相关规格文档
- `../../tasks/<task>/spec.md`
- `../../tasks/<task>/design-spec.md`
- `../../tasks/<task>/component-spec.md`
```

### Git 处理

- ✅ 真实 HTML mockup **必须进 git**；否则 index.md 在其他机器、CI 和后续会话中会成为死链
- ✅ index.md **进 git**（链接是文档的一部分）
- ✅ 旧版设计保留在 `archive/` · 做对比参考

---

## 5. 完整产物清单（self-check）

每次 design-spec 提交用户验收前确认：

- [ ] design-spec.md § 2 有完整页面 routes 表格
- [ ] design-spec.md § 3 每个页面有 1 个 ASCII wireframe（涉及 modal 时单独画框）
- [ ] `docs/tasks/<task>/mockups/` 有 N 个 HTML 文件（N = 页面数）
- [ ] 每个 HTML 都能 `open` 成功打开 · 无 typo · nav 互链
- [ ] 需要 modal 的交互在 HTML 中可操作；不需要 modal 的页面不强行添加
- [ ] HTML 内容是真实 placeholder（不是 Lorem ipsum）
- [ ] `docs/designs/<topic>/index.md` 存在 · 链接到 mockups/ 和 spec
- [ ] index.md 仅含链接 · 不复制内容

---

## 6. 反例（历史踩坑 · 不要再犯）

- ❌ 在 docs/designs/ 下存 *.html **同时**在 task/mockups/ 存同一文件 · 双重维护
- ❌ 用 `../AI推送-页面设计.html` 这种含中文路径的 mockup · **URL 编码不一致**会断链
- ❌ HTML 文件用 Lorem ipsum · 用户无法识别"是不是对的"
- ❌ 5 个 HTML 互不互链 · 用户在浏览器里无法"切换页面"
- ❌ Tailwind CDN（3MB+）· 单文件 standalone 应该 inline CSS
- ❌ ASCII wireframe 太长（30+ 行）· 失去"扫一眼"价值
- ❌ HTML mockup 不自查 · 有 typo 用户看不到
- ❌ 删 task 时把 mockup 也删了 · mockup 是设计资产独立于 task 状态

---

## 7. 相关文档

- [`docs/templates/design-spec-template.md`](../templates/design-spec-template.md) — 步骤 1 页面与视觉规格
- [`docs/templates/component-spec-template.md`](../templates/component-spec-template.md) — 步骤 2 引用已验收设计并定义组件契约
- [`docs/templates/spec-template.md`](../templates/spec-template.md) — spec 写作模板
- [`CLAUDE.md` § 一](../../CLAUDE.md) — 6 步主流程
- [`checklist.md`](checklist.md) — 阶段交付物清单

---

## 元信息

- **版本**：v3 · 2026-07-21（明确步骤 1/2 边界 + mockup 入 git）
- **来源**：AI 推送模块 component-spec 写作实践 · 5 个 HTML mockup + 5 个 ASCII wireframe 全部通过用户审阅
- **下次 review**：下一个 UI/页面设计任务完成后 · 验证本规则适用性
---

## 8. ⚠️ 必须继承项目视觉系统（KnockWise V3 案例）

**2026-07-17 教训**：AI 推送模块首次 5 个 mockup 全部用了 **light mode + Linear/Notion 简洁风**，与 KnockWise V3 已建立的 **dark glassmorphism + 渐变光晕** 体系完全不同。用户指出"AI 推送还是其中一个模块呀" · 强制重做。

**Why**：
- KnockWise V3.x 已建立完整视觉系统（CSS variables · glass-card · gradient · glow）
- AI 推送是 KnockWise **子模块**，必须继承父视觉，不能自创一套
- **一致性比"我喜欢另一种风格"更重要** · 否则用户打开模块感觉"跳到另一个 app"

**How to apply**：

### 设计 mockup 第一步：导出项目视觉 token

```bash
# 找项目里最新的 mockup（通常是上一个任务 / 主页）
ls docs/tasks/*/mockups/
# 或 docs/designs/

# 复制 :root CSS variables 段
# 关键 token：颜色 / 阴影 / 圆角 / 字体 / 动效曲线 / spacing

# 复制基础 component 类
# 如 .glass-card / .btn-primary / .tag-default / .sidebar / .app-nav
```

### 必备继承清单（mockup 之前检查）

- [ ] **主题色** · 调出项目的 `--color-primary` + 辅助色 · 不自创
- [ ] **glass-card / card 类** · 用项目定义的卡片样式 · 不用 box-shadow 重写
- [ ] **按钮体系** · btn-primary / btn-secondary / btn-ghost / btn-danger
- [ ] **tag / badge 体系** · tag-default / tag-direction / tag-active · 不自创 flat 实底色 badge
- [ ] **导航结构** · sidebar + app-nav（如果项目有）· 不是裸 top nav
- [ ] **shadow 系统** · glow / shadow-sm / shadow-md · 不用单层 box-shadow
- [ ] **动效曲线** · 用项目 `--ease-spring` / `--ease-out`
- [ ] **字体** · 用项目的 font-family · 不用默认 system
- [ ] **图标** · 用项目的 icon 系统 · 如 SVG inline + 项目色

### KnockWise V3 视觉 token（截至 2026-07-17 · 复用）

```css
:root {
  /* 主题色 */
  --color-primary: #6366f1;
  --color-primary-hover: #4f46e5;
  --color-cyan: #06b6d4;
  --color-emerald: #10b981;
  --color-amber: #f59e0b;
  --color-violet: #a78bfa;
  --color-pink: #ec4899;

  /* 背景（dark mode） */
  --color-bg-page: #050914;
  --color-bg-card: rgba(15, 20, 40, 0.7);
  --color-bg-card-hover: rgba(20, 26, 50, 0.85);

  /* 文字 */
  --color-text-primary: #f8fafc;
  --color-text-secondary: #94a3b8;
  --color-text-tertiary: #64748b;

  /* 状态 */
  --color-success: #34d399;
  --color-warning: #fbbf24;
  --color-error: #f87171;
  --color-info: #60a5fa;

  /* 边框 + 阴影 */
  --color-border: rgba(148, 163, 184, 0.08);
  --color-border-hover: rgba(99, 102, 241, 0.25);
  --shadow-glow-primary: 0 0 0 1px rgba(99, 102, 241, 0.15), 0 4px 16px rgba(99, 102, 241, 0.2);
  --shadow-glow-emerald: 0 0 0 1px rgba(16, 185, 129, 0.15), 0 4px 16px rgba(16, 185, 129, 0.2);
  --shadow-glow-amber: 0 0 0 1px rgba(245, 158, 11, 0.15), 0 4px 16px rgba(245, 158, 11, 0.2);
  --shadow-md: 0 4px 12px rgba(0, 0, 0, 0.25);
  --shadow-lg: 0 8px 24px rgba(0, 0, 0, 0.3);

  /* 动效 */
  --ease-spring: cubic-bezier(0.34, 1.56, 0.64, 1);
  --ease-out: cubic-bezier(0.16, 1, 0.3, 1);

  /* 字体 */
  font-family: -apple-system, BlinkMacSystemFont, "Inter", "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
  font-feature-settings: "cv02", "cv03", "cv04", "cv11";
  letter-spacing: -0.011em;
}
```

### 基础 component 类（mockup 必复用）

| 类名 | 用途 |
|---|---|
| `.glass-card` | 主卡片 · backdrop-blur + rgba bg + border |
| `.glass-card-static` | 静态卡（无 hover）|
| `.btn` `.btn-primary` `.btn-secondary` `.btn-ghost` `.btn-danger` | 按钮体系 |
| `.tag` `.tag-default` `.tag-direction` `.tag-active` `.tag-info` `.tag-topic` `.tag-difficulty-*` | 徽章体系 |
| `.app-nav` | 顶部 nav（56px sticky）|
| `.sidebar` | 左侧 sidebar（240px）|
| `.sidebar-item` `.sidebar-group` `.sidebar-search` | sidebar 内部 |
| `.modal-overlay` `.modal-content` | 模态框 |
| `.toast` | Vercel 风格顶部 toast |
| `.stat-num` | 等宽数字 |
| `.recommendation-item` `.module-quick-link` | 推荐条目 |

**所有 mockup 必须复用这些类**。需要新增类时，加到 V3 mockup 文档头部 · 不要在 mockup 里私造类。

### 反例（不要再犯）

- ❌ **自创 light theme**（项目是 dark）· 除非项目明确是 light theme
- ❌ **自创颜色 token**（如 `#3b82f6`）· 改用 `--color-primary`
- ❌ **自创 button class**（如 `.my-btn`）· 用 `.btn-primary` 等
- ❌ **裸 top nav**（项目有 sidebar）· 用 `<aside class="sidebar">`
- ❌ **box-shadow 单层** · 用 `--shadow-glow-primary`
- ❌ **default transition** · 用 `--ease-spring` / `--ease-out`
- ❌ **Lorem ipsum 占位** · 真实内容 + 项目 tag 名
- ❌ **flat 实底色 badge** · V3 用 transparent bg + 边框 + rgba 文字 · 不用纯色背景

---

## 元信息

- **版本**：v2 · 2026-07-17（加 § 8 视觉一致性教训 · 案例）
- **来源**：AI 推送模块 component-spec 写作实践 · 5 个 HTML mockup + 5 个 ASCII wireframe 全部通过用户审阅 · **但 V3 视觉一致性发现需重做**
- **下次 review**：5 个 mockup 重做后 · 用户视觉审阅通过才算 v3 stable
