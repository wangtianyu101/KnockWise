"""
V3.1 · 精选题单 CollectionService（PR 2）

5 方法：
- list_collections：列表查询（JOIN subscribes 算 subscribed + progress）
- get_collection：详情查询（含 position 排序的题目列表）
- subscribe_collection：订阅（INSERT IGNORE 防 409）
- unsubscribe_collection：取消订阅
- seed_collections_system：seed 5 官方题单 + 关联题目
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import and_, select, text
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy.ext.asyncio import AsyncSession

from models import (
    Question,
    QuestionCollection,
    QuestionCollectionMap,
    CollectionSubscribe,
    UserQuestion,
)

log = logging.getLogger("codemock.collection")


# V3.1 官方题单（用户 2026-07-10 拍 agent 方向 + 数据解耦 · 只建 1 个 agent 题单）
# 题目后续手动加 / 定时任务拉（不在 V3.1 范围）
SYSTEM_COLLECTIONS = [
    {
        "id": "agent_foundation",
        "name": "Agent 基础到进阶",
        "description": "Agent 架构 / LangGraph / RAG · 持续更新中（题目后续入库）",
        "cover_color": "#6366f1",
        "icon_emoji": "🤖",
        "sort_order": 10,
        "topic_filter": "agent_architecture",  # 关联 V1 agent_core.json
    },
]


async def list_collections(
    db: AsyncSession, *, user_id: Optional[str] = None, subscribed_only: bool = False
) -> list[dict]:
    """题单列表（含订阅状态 + 进度）。"""
    stmt = select(QuestionCollection).where(QuestionCollection.is_system == True).order_by(QuestionCollection.sort_order)
    rows = (await db.execute(stmt)).scalars().all()

    # 用户订阅 map
    sub_map: dict[str, CollectionSubscribe] = {}
    if user_id:
        sub_stmt = select(CollectionSubscribe).where(CollectionSubscribe.user_id == user_id)
        for s in (await db.execute(sub_stmt)).scalars().all():
            sub_map[s.collection_id] = s

    items = []
    for c in rows:
        sub = sub_map.get(c.id)
        subscribed = sub is not None
        if subscribed_only and not subscribed:
            continue
        items.append({
            "id": c.id,
            "name": c.name,
            "description": c.description,
            "cover_color": c.cover_color,
            "icon_emoji": c.icon_emoji,
            "question_count": c.question_count,
            "is_system": c.is_system,
            "subscribed": subscribed,
            "progress": sub.progress_json if sub else None,
        })
    return items


async def get_collection(
    db: AsyncSession, collection_id: str, user_id: Optional[str] = None
) -> Optional[dict]:
    """题单详情（含题目列表）。"""
    c = await db.get(QuestionCollection, collection_id)
    if c is None:
        return None

    # 关联题目（按 position 排序）
    qstmt = (
        select(Question, QuestionCollectionMap.position)
        .join(QuestionCollectionMap, QuestionCollectionMap.question_id == Question.id)
        .where(QuestionCollectionMap.collection_id == collection_id)
        .order_by(QuestionCollectionMap.position)
    )
    rows = (await db.execute(qstmt)).all()

    # 用户订阅
    sub = None
    if user_id:
        sub = (await db.execute(
            select(CollectionSubscribe).where(
                CollectionSubscribe.user_id == user_id,
                CollectionSubscribe.collection_id == collection_id,
            )
        )).scalar_one_or_none()

    questions = [
        {
            "id": q.id,
            "topic": q.topic,
            "sub_topic": q.sub_topic,
            "difficulty": q.difficulty,
            "position": pos,
            "completed": False,  # TODO: 接入 question_progress
        }
        for q, pos in rows
    ]

    return {
        "id": c.id,
        "name": c.name,
        "description": c.description,
        "cover_color": c.cover_color,
        "icon_emoji": c.icon_emoji,
        "question_count": c.question_count,
        "is_system": c.is_system,
        "subscribed": sub is not None,
        "progress": sub.progress_json if sub else None,
        "questions": questions,
    }


async def subscribe_collection(db: AsyncSession, user_id: str, collection_id: str) -> dict:
    """订阅题单（INSERT IGNORE 防 409）。"""
    # 先校验题单存在
    c = await db.get(QuestionCollection, collection_id)
    if c is None:
        return None

    now = datetime.now(timezone.utc)
    initial_progress = {
        "done_count": 0,
        "total_count": c.question_count,
        "completion_rate": 0.0,
        "last_question_id": None,
    }

    # MySQL INSERT IGNORE 语法
    stmt = mysql_insert(CollectionSubscribe).values(
        id=_gen_uuid(),
        user_id=user_id,
        collection_id=collection_id,
        progress_json=initial_progress,
        subscribed_at=now,
        last_active_at=now,
    )
    stmt = stmt.on_duplicate_key_update(
        last_active_at=now,  # 重复订阅只更新时间
    )
    await db.execute(stmt)
    await db.commit()

    return {
        "collection_id": collection_id,
        "user_id": user_id,
        "subscribed_at": now.isoformat(),
        "progress": initial_progress,
    }


async def unsubscribe_collection(db: AsyncSession, user_id: str, collection_id: str) -> bool:
    """取消订阅。"""
    stmt = select(CollectionSubscribe).where(
        CollectionSubscribe.user_id == user_id,
        CollectionSubscribe.collection_id == collection_id,
    )
    row = (await db.execute(stmt)).scalar_one_or_none()
    if row is None:
        return False
    await db.delete(row)
    await db.commit()
    return True


async def seed_collections_system(db: AsyncSession) -> int:
    """预填 5 官方题单 + 关联题目。返回创建/更新的题单数。"""
    created = 0
    for cfg in SYSTEM_COLLECTIONS:
        # 1. upsert 题单
        stmt = mysql_insert(QuestionCollection).values(
            id=cfg["id"],
            name=cfg["name"],
            description=cfg["description"],
            cover_color=cfg["cover_color"],
            icon_emoji=cfg["icon_emoji"],
            is_system=True,
            question_count=0,
            sort_order=cfg["sort_order"],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        stmt = stmt.on_duplicate_key_update(
            name=cfg["name"],
            description=cfg["description"],
            cover_color=cfg["cover_color"],
            icon_emoji=cfg["icon_emoji"],
            sort_order=cfg["sort_order"],
            updated_at=datetime.now(timezone.utc),
        )
        await db.execute(stmt)

        # 2. 关联题目（按 topic_filter 找 Question.topic）
        topic = cfg["topic_filter"]
        qstmt = select(Question.id).where(Question.topic == topic).order_by(Question.id)
        q_rows = (await db.execute(qstmt)).scalars().all()

        # 3. upsert 关联（先删旧关联，再加新关联 · 幂等）
        await db.execute(
            text("DELETE FROM question_collection_maps WHERE collection_id = :cid"),
            {"cid": cfg["id"]},
        )
        # V3.1 数据解耦（用户 2026-07-10 决定）：不自动关联题目
        # 题目后续手动加 / 定时任务拉（不在 V3 范围）
        # 保留 q_rows 查询作为参考（决定不写库）
        _ = q_rows  # noqa

        # 4. question_count 保持 0（题目后续填）
        await db.execute(
            text("UPDATE question_collections SET question_count = 0 WHERE id = :cid"),
            {"cid": cfg["id"]},
        )
        created += 1
        log.info(f"seed collection {cfg['id']} as placeholder (题目后续手动添加)")

    await db.commit()
    return created


def _gen_uuid() -> str:
    import uuid
    return str(uuid.uuid4())
