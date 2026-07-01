# 项目开发工作流（强制约束）

> 本文件是项目级的 hook 准则，约束本仓库所有开发活动的执行顺序。
> 任何 AI 助手 / Claude Code 在本项目工作时必须遵守。

---

## 0 步：调研前置（不可跳）

| 步 | 名称 | 谁触发 | 触发命令 |
|---|---|---|---|
| **0** | **调研** | 我说"调研" | 按"任务类型"自动选模板（见下表） |

**核心原则**：新功能 / 重构 / 议題关闭 / 大型 bug 修复 / P0 紧急，**开工前必先调研**。直接跳到第 1 步 = 流程违规。

### 0.1 任务类型 → 模板选择

| 触发词包含 | 类型 | 模板 | 时间预算 |
|---|---|---|---|
| `新功能` / `设计` / `feature` / `加` | 新功能 | [`research-new-feature.md`](docs/templates/research-new-feature.md) | 30-60 min |
| `bug` / `修复` / `失败` / `报错` / `fix` | Bug 修复 | [`research-bug.md`](docs/templates/research-bug.md) | 10-30 min |
| `重构` / `refactor` / `拆分` / `优化` | 重构 | [`research-refactor.md`](docs/templates/research-refactor.md) | 20-40 min |
| `关闭` / `议題` / `issue` | 议題关闭 | [`research-issue.md`](docs/templates/research-issue.md) | 10-20 min |
| `P0` / `紧急` / `线上` / `故障` | P0 紧急 | [`research-p0.md`](docs/templates/research-p0.md) | 5-10 min |

> ⚠️ **任务理解段必填**：AI 必须用自己的话复述"用户要做什么"。**复述不对 → 立刻停下等用户确认**，不要继续调研。

### 0.2 通用调研清单（所有类型必做）

- [ ] 任务理解：用自己的话复述（用户确认对）
- [ ] 读 `docs/issues.md`
- [ ] 跑 `git log -10`（最近相关改动）
- [ ] 跑 `git status`（看 unstaged / 多 agent 冲突）
- [ ] 找到 ≥ 3 个相关文件
- [ ] 列出依赖影响（改 A 会影响 B/C）
- [ ] 风险点带等级（🔴/🟡/🟢）+ 缓解方案
- [ ] 给完整 7 步路径建议

### 0.3 产物落地

- **长期调研**（推荐）：写到 `docs/tasks/YYYY-MM-DD-<类型>-<topic>/research.md`
- **临时调研**：直接在 chat 输出，下次开工重做
- **不落地 = 不算完成**

### 0.4 防御对象

- AI 接到"做设计"指令后不看现状 → 重复造轮 / 忽略沉积议題
- AI 不知道哪个任务类型用哪个模板 → 输出格式混乱
- AI 调研 5 分钟就交差 → 用通用清单的 ≥ 3 文件 / ≥ 2 风险点强约束

---

## 一、6 步强制流程（不可跳级）

| 步 | 名称 | 谁触发 | 触发命令 |
|---|---|---|---|
| **1** | **设计文档** | 我让"做设计" | 把想法落到 `docs/`，讲清楚"做什么、为什么" |
| **2** | **设计文档验证** | 我说"验证" | 自查：完整性 / 可行性 / 一致性 / 冲突点 |
| **3** | **设计文档详细化** | 我说"细化" | 加实现细节、边界情况、错误处理、配置、迁移 |
| **4** | **页面规划** | 我说"出页面" | UI 草图、流程图、交互细节、组件清单 |
| **5** | **统一通过** | 我说"通过" | 上面 1-4 都完成并经我明确批准 |
| **6** | **开始实施** | 我说"开始实施" | 才能改代码、装依赖、跑服务 |

**核心原则**：每一步必须等我的明确指令才能进下一步。没收到指令前只做当前阶段该做的事。

---

## 二、绝对不能动的东西（在设计阶段）

| 对象 | 状态 |
|---|---|
| `backend/seed_data/*.json`（50 道种子题） | ❌ 禁止改、扩、删、动任何字段 |
| `backend/seed_data/expanded/`（如果创建过） | ❌ 禁止创建 |
| `backend/.venv/` | ❌ 禁止改 |
| `backend/.env.local` | ❌ 禁止改 |
| `frontend/node_modules/` | ❌ 禁止改 |
| `livekit.yaml` | ❌ 禁止改 |
| MySQL 真实数据 | ❌ 禁止改、删、清空 |

例外：
- **修复 bug**：如果发现现有代码有明确 bug，可以即时修，但要报告
- **查问题 / 跑测试 / 调命令**：可以即时跑
- **文档整理 / 改名 / 去重**：可以即时做（不算"实施"）
- **读 / 搜索 / 分析代码**：可以即时做

---

## 三、各阶段交付物清单

### 阶段 1：设计文档
- 写在 `docs/`，中文文件名
- 包含：目标、范围、**全局架构图**、模块边界、用户旅程、业务规则
- **不做**：具体代码、库选型最后一步、页面 mockup、SQL、API 详细

### 阶段 1.5：架构图规则（强制）

**所有设计类 / 技术类文档必须先画全局图**，再写细节。

1. 文档开头（第一节内）必须有 **全局架构图**（ASCII / mermaid），让读者 30 秒内 get 整体
2. 每个大功能 / 子系统章节开头有 **局部架构图** + **用户流图** / **状态机** / **决策树**
3. 图要清晰可读（box-drawing 字符 + 标签）
4. 出现顺序：**全局 → 子模块 → 细节**

> 反例：上来就贴 SQL 表结构 / endpoint 列表 → ❌
> 正例：先画系统怎么连、用户怎么走 → ✅

### 阶段 1.6：产品 vs 技术分文件（强制）

**设计文档只放产品内容**。技术细节分流到对应文件：

| 内容 | 放哪 |
|---|---|
| 功能架构 / 用户旅程 / 业务规则 / 边缘场景 | 设计文档（产品） |
| 数据库表 / SQL / 索引 / 迁移 | `技术文档.md` 或 `xxx-技术设计.md` |
| API endpoint / Request/Response | `接口文档.md`（增量加） |
| Service 方法签名 / 错误码 | `技术文档.md` 或 `xxx-技术设计.md` |
| UI 草图 / 流程图 / 组件清单 | 阶段 4 单独出 |

**判断标准**：如果一段内容是"程序员看的"（SQL、API、代码签名）→ 移出设计文档。

### 1.7 非新功能分支（必走路径）

| 类型 | 路径 | 关键约束 |
|---|---|---|
| **新功能** | 0 → 1 → 2 → 3 → 4 → 5 → 6 | 完整流程 |
| **Bug 修复** | 登记 `docs/issues.md` → fix commit → 回归测试 | 必须有测试（见第六节） |
| **重构** | 登记议題 → 引用议題编号 commit → 测试通过 | 不改业务行为 |
| **议題关闭** | 直接执行调研结论 | commit 标题含议題编号（如 `fix(A)`） |
| **P0 紧急修复** | 例外：即时修 + 24h 内补登记 | 必须补回归测试 + `docs/issues.md` |

> **关闭例外面口子**：第二节"绝对不能动"原"修复 bug"例外太宽，本节明确化分类。

### 1.8 阶段 6 完成定义（DOD · 实施完毕必过）

- [ ] 所有 phase 的设计文档 / 技术文档 / 页面文档都已 commit
- [ ] `目前缺陷.md` 相关议題状态已更新（📋 → 🚧 → ✅）
- [ ] pre-commit hook 通过（tsc + pytest 全绿）
- [ ] **核心 service 测试覆盖率 ≥ 80%**（见下方清单）
- [ ] 没有"未通过就实施"（git log 应能溯源到阶段 5"通过" commit）
- [ ] 用户口头确认（或明确说"通过"）

**不满足 DOD = 阶段 6 未完成**，不得进入下一个需求。

#### 核心 service 清单（必须 ≥ 80% 覆盖率）

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

### 阶段 2：设计文档验证
- 自查清单（见 `docs/面试题库设计.md` 内的"验证清单"小节）
- 输出：✅ 通过 / ⚠️ 需修改 / ❌ 推翻

### 阶段 3：设计文档详细化
- 补：每个 API 的 Request/Response 样例
- 补：每个数据表的字段类型 + 索引 + 约束
- 补：每个 service 的方法签名
- 补：错误码、异常分支
- 补：数据迁移 SQL

### 阶段 4：页面规划
- ASCII 草图（每个页面一张）
- 用户操作流程
- 组件清单
- 状态机（如适用）
- 不写代码

### 阶段 5：统一通过
- 等我说"通过"
- 我可能要求改某一步，回到对应阶段重做

### 阶段 6：开始实施
- 我说"开始实施" 才动
- 按阶段 3 详细化的设计落地
- 实施中如发现设计有误，**先停下报我**，再决定改设计还是改代码

---

## 四、命名规范（已确认）

- 模块名：**面试题库**
- 设计文档：`docs/tasks/2026-06-22-new-feature-question-bank/spec.md`
- 文档目录索引：`docs/README.md`
- 相关文档（已存在，可引用）：
  - `docs/tasks/2026-06-22-new-feature-question-bank/` （面试题库全套）
  - `docs/tasks/2026-06-22-new-feature-ai-push/` （AI 推送全套）
  - `docs/tasks/2026-06-22-realtime-voice/` （实时语音）
  - `docs/api/README.md` （全局接口文档）
  - `docs/issues.md` （议題追踪）
  - `docs/archive/2026-06-27-docs-old-structure/` （4 层分类的旧结构）
  - `docs/archive/三层记忆与学习闭环.md`（v1 旧设计，已废弃）

### 4.1 docs/ 目录结构（按任务组织 + 全局汇总）

```
docs/
├── README.md                       # 文档地图
├── issues.md                       # 议題追踪（动态）
├── tasks/                          # ⭐ 按任务组织
│   ├── 2026-06-22-new-feature-question-bank/
│   │   ├── spec.md                 # 1 规格
│   │   ├── technical-spec.md       # 1 技术设计
│   │   ├── design-spec.md          # 1 页面规划
│   │   └── plan.md                 # 实施计划
│   ├── 2026-06-22-new-feature-ai-push/
│   │   ├── product-doc.md
│   │   ├── spec.md
│   │   └── design-spec.md
│   └── 2026-06-22-realtime-voice/
│       ├── plan.md
│       └── upgrade-plan.md
├── api/                            # 全局 API 索引
│   └── README.md
├── designs/                        # HTML 设计稿
├── templates/                      # 调研模板（基础设施）
│   ├── research-new-feature.md
│   ├── research-bug.md
│   ├── research-refactor.md
│   └── research-p0.md
└── archive/                        # 归档旧文档
    └── 2026-06-27-docs-old-structure/   # 4 层分类的旧结构
```

**命名约定**：任务目录 = `YYYY-MM-DD-<类型>-<topic>/`，文件 = 固定英文名。

---

## 五、违反流程的处置

如果我（AI）违反上面的流程：
1. 你会立刻打断
2. 我会停下，回退已做的实施工作（如有）
3. 回到正确的当前阶段
4. 在回复里写"自我复盘"，承认错误

---

## 六、单测强制规则（2026-06-25 新增 · 核心规则）

> **所有写代码的 commit 必须配套单测**。这是硬性要求，不是建议。

### 6.1 适用范围

| 类型 | 必须测 | 说明 |
|---|---|---|
| **新 service 函数** | ✅ | 至少 1 个 happy path + 边界条件 |
| **新 endpoint** | ✅ | schema 校验 + happy path + 失败路径 |
| **新 schema (Pydantic)** | ✅ | 必填字段 + Literal 校验 + 边界值 |
| **新组件 (UI)** | 🟡 推荐 | 测核心交互逻辑（不用 mount 整个页面） |
| **类型定义 (`types/`)** | 🟡 推荐 | 字段对齐校验（防 schema drift） |
| **Bug 修复** | ✅ | 加回归测试防止复发 |
| **配置/常量** | ❌ 不需要 | — |

### 6.2 测试基础设施

| 端 | 框架 | 命令 | 位置 |
|---|---|---|---|
| 后端 | **pytest** | `cd backend && ./.venv/bin/python -m pytest tests/ -v` | `backend/tests/test_*.py` |
| 前端 | **vitest** + RTL + happy-dom | `cd frontend && npm test` | `frontend/**/*.test.{ts,tsx}` |

### 6.3 自检清单（每个代码 commit 前必须过）

- [ ] 新加函数有 happy path 测试
- [ ] 边界值 / 异常输入有测试
- [ ] Pydantic schema 的 Literal/Range 校验有测试
- [ ] Bug 修复有回归测试
- [ ] `pytest` / `vitest` 全绿才 commit

### 6.4 违反处置

- 没单测的 commit 不算完成 → 我（AI）会停下来补测
- 你可以拒绝 merge 没单测的代码

---

## 七、本地启动（强制）

> 2026-06-27 实测确认：Docker 模式**走不通**，必须用本机模式。
> AI 开工前**必须**先 `./scripts/start.sh` 把基础设施起起来。

### 8.1 为什么不用 Docker

| 阻塞 | 详情 |
|---|---|
| `registry-1.docker.io`（Docker Hub） | 在国内网络下 timeout / 无法访问 |
| `ghcr.io` 匿名访问 | 仅 `livekit/*` 等极少数公开仓库可匿名 pull；`collabora/whisperlive` 需 auth |
| `daocloud.io` mirror | 仅代理 `library/`（Docker 官方镜像），第三方仓库不代理 |
| `livekit/livekit-server` | 无 macOS 原生二进制（仅 linux/windows），必须 Docker |
| WhisperLive | **不需要**！代码里 `WhisperLiveClient` 类定义了但**无任何调用**；主路径走 `SimpleSTT`（本地 openai-whisper） |

**结论**：Docker 路径会卡在第一步（pull 镜像），本机模式用 brew 装的 livekit-server + 本地 MySQL/Redis 替代。

### 8.2 本机模式 5 个服务

| 服务 | 端口 | 提供方 | 启动命令 |
|---|---|---|---|
| MySQL 8.x | 3306 | brew services | `brew services start mysql` |
| Redis 7.x | 6379 | brew services | `brew services start redis` |
| **LiveKit 1.13.1** | 7880/7881/7882 | brew 二进制 | `livekit-server --config ./livekit.yaml --node-ip 127.0.0.1` |
| FastAPI 后端 | 8000 | .venv/bin/uvicorn | `cd backend && ./.venv/bin/uvicorn main:app --port 8000 --env-file .env.local` |
| Next.js 前端 | 3000 | npm | `cd frontend && npm run dev` |

### 8.3 一键启停（推荐）

```bash
./scripts/start.sh           # 幂等起全部（已在跑就跳过）
./scripts/stop.sh            # 优雅停 livekit + backend + frontend（不动 MySQL/Redis）
./scripts/stop.sh all        # + 关 MySQL/Redis
./scripts/start.sh backend   # 单起某个服务
```

**特性**：
- 幂等：端口被占就记录已有 PID，不重复起
- 优雅关闭：SIGTERM → 等 5s → 还在就 SIGKILL
- PID 文件：`/tmp/intervue-pids.txt`
- 日志：`/tmp/intervue-{livekit,backend,frontend}.log`

### 8.4 已知坑（避雷）

| 坑 | 解决 |
|---|---|
| `livekit.yaml` 里 `node_ip: 192.168.1.20` 硬编码 | 启动时加 `--node-ip 127.0.0.1`（脚本已处理） |
| LiveKit 二进制命令名是 `livekit-server` 不是 `livekit` | `brew install livekit` 后用 `livekit-server` |
| 后端 init_db/cache 失败**不阻塞**启动 | 是设计如此（不让 DB 挂掉拖死服务），看日志 `Database unavailable` 警告 |
| 端到端业务（dashboard/dev-login）走 JWT | 拿 token: `curl 'http://localhost:8000/api/auth/dev-login?user_id=1'` |

### 8.5 端到端验证脚本

起完后跑一遍（任选其一）：

```bash
# A. 浏览器打开
open http://localhost:3000

# B. Swagger
open http://localhost:8000/docs

# C. 命令行验证
curl -s http://localhost:8000/api/health
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:3000/

# D. 真实业务（dev-login + dashboard）
TOKEN=$(curl -s 'http://localhost:8000/api/auth/dev-login?user_id=1' | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
curl -s -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/dashboard
```

### 8.6 故障排查速查

| 症状 | 排查 |
|---|---|
| `Failed to fetch`（前端） | 后端没起？`curl http://localhost:8000/api/health` |
| `Unknown column 'xxx'` | DB 旧表缺列 → `core/database.py:_MIGRATIONS` 应自动 ALTER，看启动日志 |
| LiveKit 连不上 | `node_ip` 没改？用 `lsof -i :7880` 看进程是否在 |
| 知识库空 | `~/Obsidian/coding/` 不存在？改 `services/obsidian_service.py:VAULT_ROOT` |

---

## 八、当前状态

### 8.1 阶段追踪（设计流程）

- [x] 阶段 1：设计文档初版（`docs/tasks/2026-06-22-new-feature-question-bank/spec.md`）
- [x] 阶段 1.0：docs 目录 4 层分类整理（2026-06-18）
- [x] 阶段 2：设计文档验证（2026-06-18，⚠️ 通过条件性，3 项 P3 已并入阶段 3）
- [x] 阶段 3：设计文档详细化（2026-06-18，1535 行 / 14 章节 / 24 API / 5 新表 / 1 改表 / 迁移 SQL / 错误码 / 议题 D 引用）
- [x] 阶段 3.6：产品/技术拆分 + 架构图重画（2026-06-18）
- [x] 阶段 4：页面规划（2026-06-18，843 行 / 10 章节 / 4 新页 + 3 改页 / 23 新组件）
- [x] 阶段 4.1：**4 大独立模块重构**（2026-06-18）
- [x] 阶段 4.2：**AI 推送独立成单独模块**（2026-06-22）

### 8.2 实施状态（2026-06-27 更新）

- [x] **V1 骨架完成** — 19 张表 + 60+ API + 19 前端页面 + 5 service（question_bank / learning_progress / qa / study_plan / recommendations）
  - 详见 [`docs/tasks/2026-06-27-v1-closure/closure.md`](docs/tasks/2026-06-27-v1-closure/closure.md)
  - plan.md 69 项已完成 51%（✅ 35 项 + 🟡 15 项）+ ⚪ 26% 已合理化（设计已变）+ ➖ 1%
- [x] **测试覆盖** — 367 个测试 / 82% 覆盖 / 核心 6 service 99%（远超 DOD ≥ 80%）
- [x] **本地启动** — 6/7 服务在线（MySQL / Redis / LiveKit / Backend / Frontend + WhisperLive 证实不需要）
- [x] **一键脚本** — `scripts/start.sh` / `stop.sh` 幂等 + 优雅关闭
- [ ] **V2 智能沉淀层** — 3 个 service 缺失（spec 写过但 V1 没做）：
  - [ ] `SummaryService`（AI 自动摘要）— 🟡 中优先
  - [ ] `ProfileSettlementService`（画像自动沉淀）— 🔴 高优先
  - [ ] `ObsidianSedimentService`（Obsidian 自动写回）— 🔴 高优先

### 8.3 git 状态

- 8 个 commit 已落地（本地，**未 push** 到 origin/main）
  - docs: 4 层分类重构为按任务
  - infra: 一键启停脚本 + CLAUDE.md § 七
  - fix(services): study_plan_service.py 缺 Question import
  - test(infra): conftest.py + pytest-asyncio + pre-commit 升级
  - test(services): 6 核心 service 测试覆盖 12% → 99%
  - test(services): obsidian/news/seed/archive 测试覆盖 70% → 100%
  - docs: 补测试调研报告 + 复盘
  - docs+infra: 补遗漏文件（README / DOD / 4 个新模板 / check-step.py）

### 8.4 待用户决策

- **是否启动 V2**（补 3 个智能 service）？
- **是否 git push**（8 个 commit 在本地）？
- **是否补 15 个 🟡 部分项**（筛选参数 / 共享组件 / 移动端等）？
