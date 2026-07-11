"""学习复习模块 Router (Phase 1c)。

路由前缀: /api/learn
对应 docs/10-架构/面试题库-页面规划.md · 4.2 学 tab · /learn /review /qa

注意: 实际路由统一走 /api/learn 前缀 (前端 api.ts 学习复习 endpoint 都用这个)。
tab 是前端 UI 概念, 后端一个 namespace 即可。
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.dependencies import get_current_user
from models import User
from schemas.learn import (
    CreateQASessionInput,
    CreateStudyPlanInput,
    CreateTagInput,
    CreateUserQuestionInput,
    EndSessionInput,
    EndSessionResponse,
    LearnStatsResponse,
    MasteryStatus,
    ProgressListResponse,
    QAChatInput,
    QAChatResponse,
    QASession as QASessionSchema,
    QASessionDetail,
    QASessionListResponse,
    QuestionDetail,
    QuestionListResponse,
    RecommendResponse,
    RecentSessionsResponse,
    ReviewQueueResponse,
    StartSessionInput,
    StartSessionResponse,
    StudyPlan,
    StudyPlanProgressResponse,
    SubmitAnswerInput,
    SubmitAnswerResponse,
    TagOut,
    UpdateProgressInput,
    UpdateProgressResponse,
    UpdateStudyPlanInput,
    UpdateUserQuestionInput,
    UpsertUserNoteInput,
    UserNoteOut,
)
from services import (
    collection_service,
    learning_progress_service,
    qa_service,
    question_bank_service,
    study_plan_service,
)

log = logging.getLogger("codemock.api.learn")
router = APIRouter(prefix="/api/learn", tags=["learn"])


def _uid(user: User = Depends(get_current_user)) -> str:
    """current_user.id 提取 (DRY)。"""
    return user.id


# ════════════════════════════════════════════════════════════
#  题目查询
# ════════════════════════════════════════════════════════════


@router.get("/questions", response_model=QuestionListResponse)
async def list_questions(
    topic: Optional[str] = None,
    difficulty: Optional[int] = Query(default=None, ge=1, le=5),
    source: Optional[str] = None,
    bookmarked: Optional[bool] = None,
    q: Optional[str] = None,
    sort: str = Query(default="id", pattern="^(id|difficulty|last_practiced|random)$"),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await question_bank_service.list_questions(
        db, user.id,
        topic=topic, difficulty=difficulty, source=source,
        bookmarked=bookmarked, q=q, sort=sort, page=page, size=size,
    )


@router.get("/questions/{qid}", response_model=QuestionDetail)
async def get_question_detail(
    qid: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    detail = await question_bank_service.get_question_detail(db, user.id, qid)
    if detail is None:
        raise HTTPException(status_code=404, detail="题目不存在")
    return detail


# ════════════════════════════════════════════════════════════
#  答题 / 进度
# ════════════════════════════════════════════════════════════


@router.post("/questions/{qid}/answer", response_model=SubmitAnswerResponse)
async def submit_answer(
    qid: str,
    data: SubmitAnswerInput,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    p = await learning_progress_service.upsert_progress(
        db, user.id, qid,
        score=data.score,
        blind_spots=data.blind_spots,
        user_answer=data.user_answer,
        duration_sec=data.duration_sec,
        source=data.source,
    )
    # review_queue 剩余数 (粗估, 不要求精确)
    queue = await learning_progress_service.get_review_queue(db, user.id, limit=9999)
    return SubmitAnswerResponse(
        progress=_prog_to_dict(p),
        review_queue_remaining=len(queue),
    )


def _prog_to_dict(p) -> dict:
    return {
        "id": p.id,
        "status": p.status,
        "practice_count": p.practice_count,
        "correct_count": p.correct_count,
        "bookmarked": p.bookmarked,
        "ease_factor": p.ease_factor,
        "interval_days": p.interval_days,
        "next_review_at": p.next_review_at.isoformat() if p.next_review_at else None,
        "last_practiced_at": p.last_practiced_at.isoformat() if p.last_practiced_at else None,
        "user_answer": p.user_answer,
        "notes_path": p.notes_path,
    }


@router.patch("/progress/{qid}", response_model=UpdateProgressResponse)
async def update_progress(
    qid: str,
    data: UpdateProgressInput,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    p = await learning_progress_service.get_user_progress(db, user.id, qid)
    if p is None:
        raise HTTPException(status_code=404, detail="进度不存在 (请先答一题)")
    if data.bookmarked is not None:
        p.bookmarked = data.bookmarked
    if data.status is not None:
        p.status = data.status
    if data.notes_path is not None:
        p.notes_path = data.notes_path
    await db.commit()
    await db.refresh(p)
    learning_progress_service.invalidate_review_queue(user.id)
    return UpdateProgressResponse(progress=_prog_to_dict(p))


@router.get("/progress", response_model=ProgressListResponse)
async def list_my_progress(
    status: Optional[MasteryStatus] = None,
    bookmarked: Optional[bool] = None,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await learning_progress_service.list_my_progress(
        db, user.id, status=status, bookmarked=bookmarked, page=page, size=size,
    )


# ════════════════════════════════════════════════════════════
#  推荐 / 复习队列
# ════════════════════════════════════════════════════════════


@router.get("/recommend", response_model=RecommendResponse)
async def get_recommend(
    n: int = Query(default=3, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    items = await learning_progress_service.get_recommend(db, user.id, n=n)
    return RecommendResponse(items=items)


@router.get("/review-queue", response_model=ReviewQueueResponse)
async def get_review_queue(
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    items = await learning_progress_service.get_review_queue(db, user.id, limit=limit)
    return ReviewQueueResponse(items=items, total=len(items))


# ════════════════════════════════════════════════════════════
#  Session
# ════════════════════════════════════════════════════════════


@router.post("/sessions", response_model=StartSessionResponse)
async def start_session(
    data: StartSessionInput,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    s = await learning_progress_service.start_session(db, user.id, session_type=data.type)
    return StartSessionResponse(
        session_id=s.id,
        type=s.type,
        started_at=s.started_at.isoformat() if s.started_at else None,
    )


@router.patch("/sessions/{session_id}/end", response_model=EndSessionResponse)
async def end_session(
    session_id: str,
    data: EndSessionInput,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    items = [item.model_dump() for item in data.items]
    s = await learning_progress_service.end_session(db, user.id, session_id, items)
    if s is None:
        raise HTTPException(status_code=404, detail="Session 不存在或无权限")
    return EndSessionResponse(
        session_id=s.id,
        duration_sec=s.duration_sec,
        item_count=len(s.items or []),
    )


@router.get("/sessions/recent", response_model=RecentSessionsResponse)
async def get_recent_sessions(
    days: int = Query(default=7, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await learning_progress_service.get_recent_sessions(db, user.id, days=days)


# ════════════════════════════════════════════════════════════
#  学习计划
# ════════════════════════════════════════════════════════════


@router.get("/plans")
async def list_plans(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await study_plan_service.list_plans(db, user.id)


@router.post("/plans", response_model=StudyPlan)
async def create_plan(
    data: CreateStudyPlanInput,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    p = await study_plan_service.create_plan(db, user.id, data.model_dump())
    return StudyPlan(
        id=p.id, name=p.name, description=p.description, goal=p.goal,
        start_date=p.start_date.isoformat(), end_date=p.end_date.isoformat(),
        status=p.status, weekly_target=p.weekly_target or [], progress=p.progress or {},
    )


@router.patch("/plans/{plan_id}", response_model=StudyPlan)
async def update_plan(
    plan_id: str,
    data: UpdateStudyPlanInput,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # Pydantic v2 model_dump 已经把嵌套 Pydantic 转成 dict 了, 直接传
    payload = {k: v for k, v in data.model_dump().items() if v is not None}
    p = await study_plan_service.update_plan(db, user.id, plan_id, payload)
    if p is None:
        raise HTTPException(status_code=404, detail="计划不存在或无权限")
    return StudyPlan(
        id=p.id, name=p.name, description=p.description, goal=p.goal,
        start_date=p.start_date.isoformat(), end_date=p.end_date.isoformat(),
        status=p.status, weekly_target=p.weekly_target or [], progress=p.progress or {},
    )


@router.delete("/plans/{plan_id}")
async def delete_plan(
    plan_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    ok = await study_plan_service.delete_plan(db, user.id, plan_id)
    if not ok:
        raise HTTPException(status_code=404, detail="计划不存在或无权限")
    return {"ok": True}


@router.get("/plans/{plan_id}/progress", response_model=StudyPlanProgressResponse)
async def get_plan_progress(
    plan_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await study_plan_service.get_plan_progress(db, user.id, plan_id)
    if result is None:
        raise HTTPException(status_code=404, detail="计划不存在或无权限")
    return StudyPlanProgressResponse(**result)


# ════════════════════════════════════════════════════════════
#  QA session (LLM 问答)
# ════════════════════════════════════════════════════════════


@router.get("/qa", response_model=QASessionListResponse)
async def list_qa_sessions(
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await qa_service.list_qa_sessions(db, user.id, limit=limit)


@router.post("/qa", response_model=QASessionDetail)
async def create_qa_session(
    data: CreateQASessionInput,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    s = await qa_service.create_qa_session(db, user.id, data.question_id)
    return QASessionDetail(
        id=s.id, question_id=s.question_id,
        created_at=s.created_at.isoformat() if s.created_at else None,
        messages=[],
    )


@router.get("/qa/{session_id}", response_model=QASessionDetail)
async def get_qa_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    s = await qa_service.get_qa_session(db, user.id, session_id)
    if s is None:
        raise HTTPException(status_code=404, detail="Session 不存在")
    return QASessionDetail(
        id=s.id, question_id=s.question_id,
        created_at=s.created_at.isoformat() if s.created_at else None,
        messages=s.messages or [],
    )


@router.delete("/qa/{session_id}")
async def delete_qa_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    ok = await qa_service.delete_qa_session(db, user.id, session_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Session 不存在")
    return {"ok": True}


@router.post("/qa/chat", response_model=QAChatResponse)
async def chat_qa(
    data: QAChatInput,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await qa_service.chat_qa(
        db, user.id, data.question_id,
        message=data.message, session_id=data.session_id,
    )


# ════════════════════════════════════════════════════════════
#  Tags / Notes / UserQuestion / Stats
# ════════════════════════════════════════════════════════════


@router.get("/tags")
async def list_tags(
    include_system: bool = True,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[TagOut]:
    return await question_bank_service.list_tags(db, user.id, include_system=include_system)


@router.post("/tags", response_model=TagOut)
async def create_tag(
    data: CreateTagInput,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    t = await question_bank_service.create_tag(
        db, user.id, name=data.name, color=data.color, is_system=data.is_system,
    )
    return TagOut(
        id=t.id, name=t.name, color=t.color,
        is_system=t.is_system, user_id=t.user_id,
    )


@router.post("/questions/{qid}/tags/{tag_id}")
async def add_tag_to_question(
    qid: str, tag_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    await question_bank_service.add_tag_to_question(db, qid, tag_id)
    return {"ok": True}


@router.delete("/questions/{qid}/tags/{tag_id}")
async def remove_tag_from_question(
    qid: str, tag_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    await question_bank_service.remove_tag_from_question(db, qid, tag_id)
    return {"ok": True}


@router.get("/questions/{qid}/note", response_model=Optional[UserNoteOut])
async def get_user_note(
    qid: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await question_bank_service.get_user_note(db, user.id, qid)


@router.put("/questions/{qid}/note", response_model=UserNoteOut)
async def upsert_user_note(
    qid: str,
    data: UpsertUserNoteInput,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    n = await question_bank_service.upsert_user_note(db, user.id, qid, data.content_md)
    return UserNoteOut(
        id=n.id, content_md=n.content_md,
        updated_at=n.updated_at.isoformat() if n.updated_at else None,
    )


@router.post("/user-questions")
async def create_user_question(
    data: CreateUserQuestionInput,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    uq = await question_bank_service.create_user_question(db, user.id, data.model_dump())
    return {"id": uq.id}


@router.put("/user-questions/{qid}")
async def update_user_question(
    qid: str,
    data: UpdateUserQuestionInput,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    payload = {k: v for k, v in data.model_dump().items() if v is not None}
    uq = await question_bank_service.update_user_question(db, user.id, qid, payload)
    if uq is None:
        raise HTTPException(status_code=404, detail="用户题不存在")
    return {"id": uq.id}


@router.delete("/user-questions/{qid}")
async def delete_user_question(
    qid: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    ok = await question_bank_service.delete_user_question(db, user.id, qid)
    if not ok:
        raise HTTPException(status_code=404, detail="用户题不存在")
    return {"ok": True}


@router.get("/stats", response_model=LearnStatsResponse)
async def get_learn_stats(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await learning_progress_service.get_learn_stats(db, user.id)


# ════════════════════════════════════════════════════════════
# V3.1 · 精选题单端点（PR 2 · 4 端点）
# ════════════════════════════════════════════════════════════


@router.get("/collections")
async def list_collections(
    subscribed_only: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """题单列表（V3.1）"""
    items = await collection_service.list_collections(
        db, user_id=user.id, subscribed_only=subscribed_only
    )
    return {"items": items, "total": len(items)}


@router.get("/collections/{collection_id}")
async def get_collection(
    collection_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """题单详情（V3.1）"""
    data = await collection_service.get_collection(db, collection_id, user_id=user.id)
    if data is None:
        raise HTTPException(status_code=404, detail=f"题单 {collection_id} 不存在")
    return data


@router.post("/collections/{collection_id}/subscribe")
async def subscribe_collection(
    collection_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """订阅题单（V3.1 · 幂等）"""
    result = await collection_service.subscribe_collection(db, user.id, collection_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"题单 {collection_id} 不存在")
    return result


@router.delete("/collections/{collection_id}/subscribe")
async def unsubscribe_collection(
    collection_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """取消订阅（V3.1）"""
    ok = await collection_service.unsubscribe_collection(db, user.id, collection_id)
    if not ok:
        raise HTTPException(status_code=404, detail=f"未订阅题单 {collection_id}")
    return {"collection_id": collection_id, "deleted": True}