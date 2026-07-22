"""
PR 3 · V3.7 admin API 端点（手动触发题目同步）

POST /api/admin/sync-questions
  - 鉴权：需要 admin 权限（V1 admin 表 · 如无则要求 is_admin 字段）
  - 简化：当前 V1 无 admin 角色，临时复用 get_current_user（无 admin 校验）
  - body: { "dry_run": false, "collection_id": "agent_foundation" }
"""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.dependencies import get_current_user
from models import User, Question
from services.question_sync_service import build_default_sources, sync_questions
from services.question_quality_service import get_sync_history

log = logging.getLogger("knockwise.api.admin")

router = APIRouter(prefix="/api/admin", tags=["admin"])


class SyncQuestionsRequest(BaseModel):
    """手动触发题目同步请求。"""
    dry_run: bool = Field(default=False, description="True = 只统计不入库")
    collection_id: Optional[str] = Field(default=None, description="关联到精选题单 ID")


class SyncQuestionsResponse(BaseModel):
    """手动触发题目同步响应。"""
    fetched: int = Field(..., description="从数据源拉取的题目数")
    created: int = Field(..., description="新入库的题目数")
    skipped: int = Field(..., description="去重跳过的题目数")
    errors: int = Field(..., description="错误数")


@router.post("/sync-questions", response_model=SyncQuestionsResponse)
async def sync_questions_endpoint(
    req: SyncQuestionsRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> SyncQuestionsResponse:
    """手动触发题目同步（admin 端点 · PR 3）。

    注意：V1 暂无 admin 角色，临时任何登录用户都可调用。
    TODO(V4): 加 admin 权限校验（V1 加 is_admin 字段）。
    """
    log.info(f"admin sync triggered by user={user.id} dry_run={req.dry_run} collection={req.collection_id}")

    sources = build_default_sources()
    if not sources:
        return SyncQuestionsResponse(fetched=0, created=0, skipped=0, errors=0)

    stats = await sync_questions(
        db,
        sources,
        collection_id=req.collection_id,
        dry_run=req.dry_run,
    )
    return SyncQuestionsResponse(**stats)


# ════════════════════════════════════════════════════════════
# PR 4 · sync-history 端点（admin 看同步历史）
# ════════════════════════════════════════════════════════════


class SyncHistoryItem(BaseModel):
    id: int
    source: str
    fetched: int
    created: int
    skipped: int
    errors: int
    duration_sec: float
    status: str
    error_msg: Optional[str]
    started_at: str


@router.get("/sync-history", response_model=list[SyncHistoryItem])
async def get_sync_history_endpoint(
    limit: int = Query(default=10, ge=1, le=100),
    user: User = Depends(get_current_user),
) -> list[SyncHistoryItem]:
    """拉最近 N 条同步历史（PR 4 · admin 端点）。"""
    history = get_sync_history(limit=limit)
    return [SyncHistoryItem(**item) for item in history]


# ════════════════════════════════════════════════════════════
# PR 5 · admin 题库管理 API（列表 + PATCH）
# ════════════════════════════════════════════════════════════


class QuestionListItem(BaseModel):
    id: str
    topic: str
    sub_topic: str
    difficulty: int
    round: str
    question_text: str


class QuestionListResponse(BaseModel):
    items: list[QuestionListItem]
    total: int


class QuestionPatchRequest(BaseModel):
    """PR 5: admin 修改题目元数据（部分更新）。"""
    topic: Optional[str] = Field(default=None, max_length=64)
    sub_topic: Optional[str] = Field(default=None, max_length=64)
    difficulty: Optional[int] = Field(default=None, ge=1, le=5)
    round: Optional[str] = Field(default=None, max_length=32)

    @field_validator("round")
    @classmethod
    def _validate_round(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if v not in {"round1", "round2"}:
            raise ValueError("round 必须为 'round1' 或 'round2'")
        return v


@router.get("/questions", response_model=QuestionListResponse)
async def list_questions_admin(
    topic: Optional[str] = Query(default=None),
    difficulty: Optional[int] = Query(default=None, ge=1, le=5),
    keyword: Optional[str] = Query(default=None, description="按 question_text contains 过滤"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> QuestionListResponse:
    """admin 列表题库（PR 5）。"""
    stmt = select(Question)
    count_stmt = select(func.count(Question.id))

    if topic:
        stmt = stmt.where(Question.topic == topic)
        count_stmt = count_stmt.where(Question.topic == topic)
    if difficulty is not None:
        stmt = stmt.where(Question.difficulty == difficulty)
        count_stmt = count_stmt.where(Question.difficulty == difficulty)
    if keyword:
        like = f"%{keyword}%"
        stmt = stmt.where(Question.question_text.like(like))
        count_stmt = count_stmt.where(Question.question_text.like(like))

    stmt = stmt.order_by(Question.id).offset(skip).limit(limit)
    rows = (await db.execute(stmt)).scalars().all()
    total = (await db.execute(count_stmt)).scalar_one()

    items = [
        QuestionListItem(
            id=q.id,
            topic=q.topic,
            sub_topic=q.sub_topic,
            difficulty=q.difficulty,
            round=q.round or "round1",
            question_text=q.question_text[:200] + ("..." if len(q.question_text) > 200 else ""),
        )
        for q in rows
    ]
    return QuestionListResponse(items=items, total=total)


@router.patch("/questions/{question_id}", response_model=QuestionListItem)
async def patch_question_admin(
    question_id: str,
    req: QuestionPatchRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> QuestionListItem:
    """admin PATCH 题目（PR 5）。"""
    q = await db.get(Question, question_id)
    if q is None:
        raise HTTPException(status_code=404, detail=f"题目 {question_id} 不存在")

    updates = req.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(status_code=422, detail="至少提供一个字段")

    for field, value in updates.items():
        setattr(q, field, value)

    await db.commit()
    await db.refresh(q)

    log.info(f"admin PATCH question {question_id} by user={user.id}: {updates}")

    return QuestionListItem(
        id=q.id,
        topic=q.topic,
        sub_topic=q.sub_topic,
        difficulty=q.difficulty,
        round=q.round or "round1",
        question_text=q.question_text[:200],
    )
