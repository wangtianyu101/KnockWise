"""Settlement 数据契约 (V2.1 PR 1 — ProfileSettlementService)

来源：spec.md §4.1
- TopicSettlement: 单个 topic 沉淀数据
- SettlementResult: settlement 执行结果（API 返回 + 内部 service 返回）
"""
from __future__ import annotations

from datetime import datetime
from typing import List
from uuid import UUID

from pydantic import BaseModel, Field


class TopicSettlement(BaseModel):
    """单个 topic 的沉淀数据（写入 weak_topics / mastered_topics）"""

    topic: str = Field(min_length=1, max_length=50)  # 业务：topic 名
    error_rate: float = Field(ge=0.0, le=1.0)  # 业务：错题率 0-1
    practice_count: int = Field(ge=0)  # 业务：练习次数
    last_practiced_at: datetime
    related_question_ids: List[str] = Field(default_factory=list, max_length=50)


class SettlementResult(BaseModel):
    """settlement 执行结果（API 返回 + 内部 service 返回）"""

    user_id: UUID
    settled_at: datetime
    weak_topics: List[TopicSettlement]  # 业务：当前 weak_topics 快照
    mastered_topics: List[TopicSettlement]  # 业务：当前 mastered_topics 快照
    triggered_by: str = Field(
        pattern=r"^(interview|practice|manual_refresh|weekly_refresh)$"
    )  # 业务：触发源
    cache_invalidated: bool = True  # 业务：是否让 summary 缓存失效
