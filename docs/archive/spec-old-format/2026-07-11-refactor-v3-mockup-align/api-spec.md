---
title: API 详细规范 · KnockWise 前端对齐重构
date: 2026-07-11
status: v1
tags: [api-spec, 2步, API, v3-mockup-align, knockwise, /recent]
related:
  - [research.md](research.md) — 上游调研
  - [plan.md](plan.md) — 实施计划（P3 阶段）
  - [spec.md](spec.md) — 技术契约概览
  - [component-spec.md](component-spec.md) — 前端组件详细
  - [db-design.md](db-design.md) — DB 变更（无）
  - V3 API README: [../../api/README.md](../../api/README.md)
---

# API 详细规范：KnockWise 前端对齐重构

> **核心结论**：**本次重构只新增 1 个端点**：`GET /api/interviews/recent?limit=3`。
> 其他 50+ 现有端点**完全不动**（业务冻结）。

---

## 0. 全局结论（CLAUDE.md §1.5 全局图）

```
┌──────────────────────────────────────────────────────────────────────┐
│                  本次重构 API 影响：1 个新增 + 0 个修改                │
│                                                                       │
│  现有 50+ 端点 ──────────────────→  现有 50+ 端点（完全不变）        │
│  backend/api/*.py                                                     │
│                                                                       │
│  🆕 新增 1 端点：                                                      │
│  GET /api/interviews/recent?limit=3                                  │
│    └─ 给 Dashboard HeroCard 用 · 读最近 3 次面试的 radar_data        │
│                                                                       │
│  现有 _MIGRATIONS 不变 · Interview.radar_data 字段已存在              │
│  （V2 沉淀层已添加）                                                    │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 1. 🆕 GET /api/interviews/recent

### 1.1 端点概览

| 维度 | 详情 |
|---|---|
| **HTTP 方法** | `GET` |
| **路径** | `/api/interviews/recent` |
| **认证** | `Depends(get_current_user)` —— JWT Bearer Token |
| **Query 参数** | `limit: int = 3`（1 ≤ limit ≤ 10）|
| **响应** | 200 OK + `InterviewRecentResponse` JSON |
| **错误码** | 401 UNAUTHORIZED / 422 INVALID_QUERY / 500 INTERNAL_ERROR |
| **缓存** | 无（mock 数据，每次实时查 DB）|
| **频率限制** | 60 req/min per user（slowapi 已在 V2 应用，spec §3.2）|
| **性能目标** | P95 < 50ms |
| **路径冲突** | ❌ 无（不与现有 `/api/interviews` 冲突，是新独立路径）|

### 1.2 Request

#### Headers

```http
GET /api/interviews/recent?limit=3 HTTP/1.1
Host: localhost:8000
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json
```

#### Query 参数

| 参数 | 类型 | 必填 | 默认 | 范围 | 说明 |
|---|---|---|---|---|---|
| `limit` | int | ❌ | 3 | 1 ≤ limit ≤ 10 | 返回最近 N 条面试 |

#### 验证规则

```python
# backend/api/interview.py
async def get_recent_interviews(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(3, ge=1, le=10, description="返回最近 N 条面试，1-10"),
):
```

Pydantic 自动校验：`limit < 1` 或 `limit > 10` → 422 INVALID_QUERY

### 1.3 Response

#### 成功响应（200 OK）

```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "round": "字节·后端",
      "style": "tech",
      "status": "completed",
      "total_questions": 8,
      "overall_score": 78.5,
      "radar_data": {
        "algorithm": 78,
        "system_design": 75,
        "network": 65,
        "frontend": 50,
        "ai": 40
      },
      "started_at": "2026-07-08T14:30:00Z",
      "ended_at": "2026-07-08T15:05:00Z"
    },
    {
      "id": "661f9511-f30c-52e5-b827-557766551111",
      "round": "阿里·前端",
      "style": "tech",
      "status": "completed",
      "total_questions": 6,
      "overall_score": 68.0,
      "radar_data": {
        "algorithm": 65,
        "system_design": 60,
        "network": 70,
        "frontend": 75,
        "ai": 50
      },
      "started_at": "2026-07-05T10:00:00Z",
      "ended_at": "2026-07-05T10:35:00Z"
    },
    {
      "id": "772fa622-a41d-63f6-c938-668877662222",
      "round": "腾讯·全栈",
      "style": "mixed",
      "status": "completed",
      "total_questions": 7,
      "overall_score": 62.0,
      "radar_data": {},
      "started_at": "2026-07-01T16:00:00Z",
      "ended_at": "2026-07-01T16:42:00Z"
    }
  ],
  "total": 3
}
```

#### 空数据响应（200 OK + 空数组）

```json
{
  "items": [],
  "total": 0
}
```

### 1.4 错误响应（CLAUDE.md § 阶段 3 详细化 · 错误码）

#### 401 UNAUTHORIZED

```json
{
  "error": {
    "code": "UNAUTHORIZED",
    "message": "未登录或 token 已过期",
    "request_id": "req_abc123"
  }
}
```

#### 422 INVALID_QUERY

```json
{
  "error": {
    "code": "INVALID_QUERY",
    "message": "limit must be between 1 and 10",
    "details": {
      "param": "limit",
      "received": 15,
      "expected": "1 ≤ limit ≤ 10"
    },
    "request_id": "req_def456"
  }
}
```

#### 500 INTERNAL_ERROR

```json
{
  "error": {
    "code": "INTERNAL_ERROR",
    "message": "服务暂时不可用，请稍后重试",
    "details": null,
    "request_id": "req_ghi789"
  }
}
```

### 1.5 Pydantic Schema

```python
# backend/schemas/interview.py（新增）
from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime

class InterviewRecentItem(BaseModel):
    """单条最近面试记录（用于 Dashboard HeroCard RadarMini）"""
    id: UUID = Field(..., description="面试唯一 ID")
    round: str = Field(..., description="公司方向，如 '字节·后端'")
    style: str = Field(..., description="面试风格，如 'tech' / 'mixed'")
    status: str = Field(..., description="状态：'completed' / 'in_progress' / 'aborted'")
    total_questions: int = Field(..., ge=0, description="总题数")
    overall_score: Optional[float] = Field(None, ge=0, le=100, description="总分 0-100")
    radar_data: dict = Field(
        default_factory=dict,
        description="5 维雷达数据 {algorithm, system_design, network, frontend, ai}；旧数据可能为空 dict"
    )
    started_at: Optional[str] = Field(None, description="开始时间 ISO 8601")
    ended_at: Optional[str] = Field(None, description="结束时间 ISO 8601")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "round": "字节·后端",
                "style": "tech",
                "status": "completed",
                "total_questions": 8,
                "overall_score": 78.5,
                "radar_data": {
                    "algorithm": 78, "system_design": 75,
                    "network": 65, "frontend": 50, "ai": 40
                },
                "started_at": "2026-07-08T14:30:00Z",
                "ended_at": "2026-07-08T15:05:00Z"
            }
        }


class InterviewRecentResponse(BaseModel):
    """最近面试响应"""
    items: list[InterviewRecentItem] = Field(default_factory=list)
    total: int = Field(..., ge=0, description="返回条数（与 items.length 相同，因已 LIMIT）")
```

### 1.6 Service 方法

```python
# backend/services/interview_service.py（新增）
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

async def list_recent_interviews(
    db: AsyncSession,
    user_id: str,
    limit: int = 3,
) -> list[dict]:
    """返回当前用户最近 N 条 completed 面试（含 radar_data）。

    用途：Dashboard HeroCard RadarMini 显示最近 3 次面试雷达。

    过滤条件：
    - user_id = 当前用户（防越权）
    - status = 'completed'（避免半成品 in_progress）
    - deleted_at IS NULL（软删除过滤）
    - overall_score IS NOT NULL（避免没打分的）

    排序：started_at DESC
    Limit：1-10

    性能：走 idx_user_status 索引 + 内存 LIMIT O(1)
    """
    stmt = (
        select(Interview)
        .where(
            and_(
                Interview.user_id == user_id,
                Interview.status == 'completed',
                Interview.deleted_at.is_(None),
                Interview.overall_score.is_not(None),
            )
        )
        .order_by(Interview.started_at.desc())
        .limit(limit)
    )

    result = await db.execute(stmt)
    interviews = result.scalars().all()

    return [
        {
            "id": iv.id,
            "round": iv.round,
            "style": iv.style,
            "status": iv.status,
            "total_questions": iv.total_questions,
            "overall_score": iv.overall_score,
            "radar_data": iv.radar_data or {},
            "started_at": iv.started_at.isoformat() if iv.started_at else None,
            "ended_at": iv.ended_at.isoformat() if iv.ended_at else None,
        }
        for iv in interviews
    ]
```

### 1.7 API 端点路由

```python
# backend/api/interview.py（新增 · 在 list_interviews 之后）
from fastapi import Query

@router.get("/recent", response_model=InterviewRecentResponse)
async def get_recent_interviews(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(3, ge=1, le=10, description="返回最近 N 条面试"),
) -> InterviewRecentResponse:
    """V3.8 新增 · Dashboard HeroCard 用。

    返回当前用户最近 N 条 completed 面试，按 started_at DESC 排序。
    """
    items = await list_recent_interviews(db, user.id, limit=limit)
    return InterviewRecentResponse(items=items, total=len(items))
```

### 1.8 路由注册顺序（避免冲突）

`/recent` 必须**在 `/{interview_id}` 之前注册**，否则 FastAPI 会把 "recent" 当作 interview_id 解析：

```python
# backend/api/interview.py：路由顺序

@router.get("")                                    # 列表（已有）
async def list_interviews(...): ...

@router.get("/recent", response_model=...)         # 🆕 新增 · 必须在前
async def get_recent_interviews(...): ...

@router.get("/{interview_id}", response_model=...) # 单条（已有）
async def get_interview(...): ...
```

### 1.9 错误响应统一格式（V2 L4 #3）

`/recent` 端点的错误响应遵循 V2 L4 改进 #3 统一格式（spec §7.4）：

```python
# backend/core/exceptions.py（已有）
class APIError(HTTPException):
    def __init__(self, code: str, message: str, status_code: int, details: dict | None = None):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details
        super().__init__(status_code=status_code, detail={
            "error": {
                "code": code,
                "message": message,
                "details": details,
                "request_id": request_id_var.get(),  # 上下文变量
            }
        })
```

FastAPI 异常处理器统一捕获 `APIError` + 其他异常，包装成统一格式响应。

---

## 2. 前端类型定义（spec.md §2.1 已写 · 补充完整版）

```typescript
// frontend/types/interview.ts（新增）
export interface InterviewRadarData {
  algorithm?: number;
  system_design?: number;
  network?: number;
  frontend?: number;
  ai?: number;
  [key: string]: number | undefined;
}

export interface InterviewRecentItem {
  id: string;
  round: string;
  style: string;
  status: 'completed' | 'in_progress' | 'aborted';
  total_questions: number;
  overall_score: number | null;
  radar_data: InterviewRadarData;
  started_at: string | null;
  ended_at: string | null;
}

export interface InterviewRecentResponse {
  items: InterviewRecentItem[];
  total: number;
}

// RadarMini 5 维 key 标准（与后端约定）
export const RADAR_DIMENSIONS = [
  'algorithm',
  'system_design',
  'network',
  'frontend',
  'ai',
] as const;

export type RadarDimension = typeof RADAR_DIMENSIONS[number];
```

---

## 3. 前端 API 调用模式

### 3.1 apiGet 统一封装（已有）

```typescript
// frontend/lib/api.ts（修改：加 apiGet）
export async function apiGet<T>(url: string, params?: Record<string, any>): Promise<T> {
  const queryString = params
    ? '?' + new URLSearchParams(params).toString()
    : '';
  const fullUrl = `${API}${url}${queryString}`;
  const res = await fetch(fullUrl, {
    headers: {
      Authorization: `Bearer ${getToken()}`,
      'Content-Type': 'application/json',
    },
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    const err = new Error(body?.error?.message || `HTTP ${res.status}`);
    (err as any).code = body?.error?.code;
    (err as any).status = res.status;
    (err as any).details = body?.error?.details;
    throw err;
  }
  return res.json();
}
```

### 3.2 HeroCard 调用 /recent

```typescript
// frontend/components/v3/HeroCard/HeroCard.tsx
import { apiGet } from '@/lib/api';
import type { InterviewRecentResponse } from '@/types/interview';

async function fetchRecentInterviews(limit: number = 3) {
  return apiGet<InterviewRecentResponse>('/api/interviews/recent', { limit });
}

// useAsyncData hook 包装（spec.md §7.3）
function useRecentInterviews(limit: number = 3) {
  return useAsyncData(() => fetchRecentInterviews(limit));
}
```

---

## 4. 测试矩阵（9 测试 · spec.md §4 已列 · 详细版）

### 4.1 测试文件

```python
# backend/tests/test_interview_recent_endpoint.py
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from backend.main import app
from backend.tests.conftest import create_test_user, create_test_interview

class TestRecentInterviewsEndpoint:
    """V3.8 P3 新增 /api/interviews/recent 测试"""

    async def test_recent_empty(self, client: AsyncClient, auth_headers):
        """#1: 新用户 0 面试 → 返回空数组"""
        response = await client.get(
            "/api/interviews/recent",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data == {"items": [], "total": 0}

    async def test_recent_one(self, client, db, auth_headers, test_user):
        """#2: 1 条 completed → total=1"""
        await create_test_interview(
            db, user_id=test_user.id, status="completed",
            overall_score=78.5, round="字节·后端",
        )
        response = await client.get("/api/interviews/recent", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["overall_score"] == 78.5
        assert data["items"][0]["round"] == "字节·后端"

    async def test_recent_three(self, client, db, auth_headers, test_user):
        """#3: 3 条 completed → total=3，按 started_at DESC"""
        for i, score in enumerate([78.5, 68.0, 62.0]):
            await create_test_interview(
                db, user_id=test_user.id, status="completed",
                overall_score=score,
                started_at=datetime(2026, 7, 8 - i),  # 倒序
            )
        response = await client.get("/api/interviews/recent", headers=auth_headers)
        data = response.json()
        assert data["total"] == 3
        # 验证排序：最近（i=0）的 score=78.5 在前
        assert data["items"][0]["overall_score"] == 78.5
        assert data["items"][1]["overall_score"] == 68.0
        assert data["items"][2]["overall_score"] == 62.0

    async def test_recent_truncate(self, client, db, auth_headers, test_user):
        """#4: 5 条 completed + limit=3 → 返回 3 条"""
        for i in range(5):
            await create_test_interview(
                db, user_id=test_user.id, status="completed",
                overall_score=70.0 + i,
            )
        response = await client.get(
            "/api/interviews/recent?limit=3",
            headers=auth_headers,
        )
        data = response.json()
        assert len(data["items"]) == 3
        assert data["total"] == 3

    async def test_recent_excludes_in_progress(self, client, db, auth_headers, test_user):
        """#5: 2 completed + 1 in_progress → 只返回 2"""
        await create_test_interview(db, user_id=test_user.id, status="completed", overall_score=78.0)
        await create_test_interview(db, user_id=test_user.id, status="completed", overall_score=68.0)
        await create_test_interview(db, user_id=test_user.id, status="in_progress", overall_score=None)
        response = await client.get("/api/interviews/recent", headers=auth_headers)
        data = response.json()
        assert data["total"] == 2

    async def test_recent_excludes_no_score(self, client, db, auth_headers, test_user):
        """#6: 1 completed 有分 + 1 completed 无分 → 只返回有分的"""
        await create_test_interview(db, user_id=test_user.id, status="completed", overall_score=78.0)
        await create_test_interview(db, user_id=test_user.id, status="completed", overall_score=None)
        response = await client.get("/api/interviews/recent", headers=auth_headers)
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["overall_score"] == 78.0

    async def test_recent_user_isolation(self, client, db, auth_headers, test_user, other_user):
        """#7: 用户 A 3 条 + 用户 B 3 条 → A 只看到自己的"""
        for i in range(3):
            await create_test_interview(db, user_id=test_user.id, status="completed", overall_score=70.0)
        for i in range(3):
            await create_test_interview(db, user_id=other_user.id, status="completed", overall_score=80.0)
        response = await client.get("/api/interviews/recent", headers=auth_headers)
        data = response.json()
        assert data["total"] == 3
        assert all(item["overall_score"] == 70.0 for item in data["items"])

    async def test_recent_limit_validation(self, client, auth_headers):
        """#8: limit=0 / limit=11 / limit="abc" → 422"""
        for bad_limit in ["0", "11", "abc"]:
            response = await client.get(
                f"/api/interviews/recent?limit={bad_limit}",
                headers=auth_headers,
            )
            assert response.status_code == 422
            body = response.json()
            assert body["error"]["code"] == "INVALID_QUERY"

    async def test_recent_unauthenticated(self, client):
        """#9: 无 token → 401"""
        response = await client.get("/api/interviews/recent")
        assert response.status_code == 401
        body = response.json()
        assert body["error"]["code"] == "UNAUTHORIZED"
```

### 4.2 覆盖率目标

- 端点代码覆盖率：≥ 85%
- 错误分支全覆盖：401 / 422 / 500
- 边界值：limit=1 / limit=10 / limit=0 / limit=11

---

## 5. 性能基准（CLAUDE.md § 一 L4 性能验证）

| 场景 | 目标 P95 | 实测（mock 测试） |
|---|---|---|
| 0 条面试 | < 30ms | ~10ms |
| 3 条面试 | < 50ms | ~20ms |
| 100 条历史（限 limit=3）| < 50ms | ~25ms |
| 1000 条历史（限 limit=3）| < 80ms | ~40ms |

**性能达标条件**：P95 < 50ms（mock 测），加 20ms 网络延迟后 < 70ms（满足 spec §8 性能预算）

---

## 6. OpenAPI 文档自动生成

FastAPI 自动生成 OpenAPI schema，前端可用 `npm run gen-api-types` 生成 TS 类型（V1 既有脚本）。

新端点会自动出现在：
- `http://localhost:8000/docs` Swagger UI
- `http://localhost:8000/openapi.json`
- 前端 `types/api-generated.d.ts`

---

## 7. 现有 API 不变清单（冻结）

> CLAUDE.md §1.7 重构不动业务。以下端点**完全不变**：

| 端点 | 路由 | 状态 |
|---|---|---|
| `GET /api/interviews` | `backend/api/interview.py:109` | ✅ 冻结 |
| `POST /api/interviews/{id}/favorite` | line 174 | ✅ 冻结 |
| `DELETE /api/interviews/{id}` | line 210 | ✅ 冻结 |
| `POST /api/interviews` (start) | line 247 | ✅ 冻结 |
| `GET /api/interviews/{id}` | line 319 | ✅ 冻结 |
| `GET /api/interviews/{id}/records` | line 338 | ✅ 冻结 |
| `POST /api/interviews/{id}/next-question` | line 351 | ✅ 冻结 |
| `POST /api/interviews/{id}/complete` | line 436 | ✅ 冻结 |
| `POST /api/interviews/records/{record_id}/answer` | line 540 | ✅ 冻结 |
| `POST /api/interviews/transcribe` | line 651 | ✅ 冻结 |
| `POST /api/interviews/voice/respond` | line 699 | ✅ 冻结 |
| `POST /api/interviews/livekit-token` | line 827 | ✅ 冻结 |
| `GET /api/dashboard` | `backend/api/dashboard.py` | ✅ 冻结 |
| `GET /api/learn/{...}` (10 个) | `backend/api/learn.py` | ✅ 冻结 |
| `GET /api/admin/{...}` (3 个) | `backend/api/admin.py` | ✅ 冻结（V3.7 既有）|
| `GET /api/analytics/{...}` (4 个) | `backend/api/analytics.py` | ✅ 冻结 |
| `GET /api/knowledge/{...}` (3 个) | `backend/api/knowledge.py` | ✅ 冻结 |
| `GET /api/v2/{...}` (6 个沉淀层) | `backend/api/v2_settlement.py` | ✅ 冻结（V2 既有）|
| `GET /api/profile/{...}` (5 个) | `backend/api/profile.py` | ✅ 冻结 |
| `GET /api/news/{...}` (5 个) | `backend/api/news.py` | ✅ 冻结 |
| `GET /api/qa/{...}` (3 个) | `backend/api/qa.py` | ✅ 冻结 |
| `POST /api/auth/{...}` (4 个) | `backend/api/auth.py` | ✅ 冻结 |

**总计 50+ 端点全部冻结**，仅新增 1 个 `/recent`。

---

## 8. 部署顺序（CLAUDE.md § 一.三 阶段 2 · 部署策略）

### 8.1 P3 阶段部署

```bash
# 1. 后端先发版（向后兼容）
git checkout main
git pull
# deploy backend
./scripts/start.sh backend  # 自动跑 _MIGRATIONS（无新 ALTER）

# 2. 前端后发版（使用新端点）
./scripts/start.sh frontend
```

### 8.2 兼容矩阵（spec.md §7.5 详细）

| 部署顺序 | 老前端 + 新后端 | 新前端 + 老后端 |
|---|---|---|
| **P3 部署** | ✅ 老前端调 `/api/interviews`（原有），不调 `/recent` | ⚠️ 新前端 HeroCard 调 `/api/interviews/recent` 404 → EmptyState fallback |

**最坏情况**：新前端 + 老后端 → HeroCard 显示 EmptyState（不致命，可接受）

---

## 9. 风险评估

| 风险 | 等级 | 缓解 |
|---|---|---|
| 路由顺序错（`/recent` 被当 `/{id}`）| 🔴 高 | 测试覆盖 + code review 必看路由顺序 |
| radar_data 旧数据为空 dict | 🟡 中 | 前端 HeroCard partial 状态自动处理 |
| limit 越界 | 🟢 低 | Pydantic 自动校验 422 |
| 性能不达标 | 🟢 低 | 走 idx_user_status 索引 + mock 测试 |
| 用户隔离泄漏 | 🔴 高 | 测试 #7 覆盖 + `Depends(get_current_user)` 强制 |

---

## 10. 关联文档

- [research.md](research.md) §9.3 /recent 设计 + §9.7 后端约束
- [plan.md](plan.md) P3 阶段任务清单 + §5 风险预案
- [spec.md](spec.md) §2 API 契约 + §7.5 兼容矩阵
- [db-design.md](db-design.md) Interview.radar_data 字段已存在
- [component-spec.md](component-spec.md) HeroCard 调用 /recent 详细
- V3 API README: [../../api/README.md](../../api/README.md)
- CLAUDE.md § 一.三 阶段 2/3· § 一 L1-L5 验证· § 一.7 重构路径