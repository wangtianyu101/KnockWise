"""Cross-module AI recommendation engine.

Connects interview analytics (weak spots, scores), knowledge base (notes, links),
and news (daily reports, stats) to generate personalized recommendations.
"""

from collections import Counter
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import User, Interview, QuestionRecord
from services.obsidian_service import obsidian
from services.news_service import news_service


async def get_recommendations(user: User, db: AsyncSession) -> list[dict]:
    """Generate cross-module recommendations for this user."""
    recs = []

    # 1. Interview weak spots → suggest knowledge base notes
    weak_spots = await _get_weak_spots(user, db)
    knowledge_recs = _match_knowledge(weak_spots)
    recs.extend(knowledge_recs)

    # 2. Interview gap → suggest practice
    interview_recs = await _interview_recs(user, db)
    recs.extend(interview_recs)

    # 3. Stats context
    stats_recs = _stats_context()
    recs.extend(stats_recs)

    # Sort by priority and deduplicate
    seen = set()
    unique = []
    for r in recs:
        key = r["title"]
        if key not in seen:
            seen.add(key)
            unique.append(r)
    return unique[:6]


async def _get_weak_spots(user: User, db: AsyncSession) -> list[str]:
    """Extract weak topics from interview records."""
    result = await db.execute(
        select(Interview).where(
            Interview.user_id == user.id,
            Interview.status == "completed",
        )
    )
    interviews = result.scalars().all()
    blind_counts = Counter()
    for iv in interviews:
        qresult = await db.execute(
            select(QuestionRecord).where(QuestionRecord.interview_id == iv.id)
        )
        for r in qresult.scalars().all():
            for spot in (r.blind_spots or []):
                blind_counts[spot] += 1
    return [spot for spot, _ in blind_counts.most_common(5)]


def _match_knowledge(weak_spots: list[str]) -> list[dict]:
    """Match weak spots against knowledge base notes."""
    if not weak_spots:
        return []
    recs = []
    notes = []
    for spot in weak_spots[:3]:
        results = obsidian.search(spot, limit=3)
        notes.extend(results)
    seen = set()
    for n in notes[:4]:
        if n["path"] not in seen:
            seen.add(n["path"])
            recs.append({
                "type": "knowledge",
                "title": f"复习笔记「{n['name'].replace('.md','')}」",
                "detail": f"你的薄弱点「{weak_spots[0]}」在这篇笔记中有涉及",
                "link": f"/knowledge?note={n['path']}",
                "priority": "high",
            })
    if not recs and weak_spots:
        recs.append({
            "type": "knowledge",
            "title": f"补充学习「{weak_spots[0]}」",
            "detail": "知识库中暂无相关笔记，建议添加",
            "priority": "medium",
        })
    return recs


async def _interview_recs(user: User, db: AsyncSession) -> list[dict]:
    """Generate interview practice recommendations."""
    result = await db.execute(
        select(Interview).where(Interview.user_id == user.id).order_by(Interview.started_at.desc())
    )
    interviews = result.scalars().all()
    completed = [i for i in interviews if i.status == "completed"]

    if not completed:
        return [{
            "type": "interview",
            "title": "开始第一次面试",
            "detail": "选择 AI Agent 方向，体验追问引擎",
            "link": "/interview/setup",
            "priority": "high",
        }]
    if len(completed) < 3:
        return [{
            "type": "interview",
            "title": f"继续练习（已完成 {len(completed)} 次）",
            "detail": "建议完成至少 3 次面试以获得趋势分析",
            "link": "/interview/setup",
            "priority": "medium",
        }]
    return []


def _stats_context() -> list[dict]:
    """Provide stats-based context recommendations."""
    try:
        stats = news_service.get_code_stats(days=7)
    except Exception:
        return []
    s = stats.get("summary", {})
    if s.get("total_tokens", 0) > 500_000:
        return [{
            "type": "stats",
            "title": f"本周 Token 消耗 {s['total_tokens']/1000:.0f}K",
            "detail": "编码强度较高，注意休息",
            "priority": "low",
        }]
    return [{
        "type": "stats",
        "title": "代码统计已就绪",
        "detail": f"累计 {s.get('total_days',0)} 天 · {s.get('total_tokens',0)/1000:.0f}K tokens",
        "priority": "low",
    }]
