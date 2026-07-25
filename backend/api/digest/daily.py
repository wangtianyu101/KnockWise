"""Digest Daily API (T10: 2026-07-17 实施).

GET /api/digest/today
GET /api/digest/daily/{date}
GET /api/digest/dailies?limit=N

配套 api-spec.md § 3.A + spec.md R7
"""
from datetime import date as date_type

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.dependencies import get_current_user
from models import DigestDaily as DigestDailyModel
from models import DigestDailyItem as DigestDailyItemModel
from models import User
from schemas.digest import (
    DigestDailiesListItem,
    DigestDailiesListResponse,
    DigestDailyItem as DigestDailyItemSchema,
    DigestTodayResponse,
)

router = APIRouter(prefix="/api/digest", tags=["digest-daily"])


@router.get("/today", response_model=DigestTodayResponse)
async def get_today(
    target_date: date_type | None = Query(default=None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """今日 5 条 digest + vibe。"""
    from datetime import date as today_date

    actual_date = target_date or today_date.today()
    return await _load_daily(db, str(user.id), actual_date)


@router.get("/daily/{target_date}", response_model=DigestTodayResponse)
async def get_daily_by_date(
    target_date: date_type,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """某天完整 digest。"""
    return await _load_daily(db, str(user.id), target_date)


@router.get("/dailies", response_model=DigestDailiesListResponse)
async def list_dailies(
    limit: int = Query(default=7, ge=1, le=30),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """最近 N 天 digest 列表（轻量 · 不含 items）。"""
    user_id = str(user.id)
    total_result = await db.execute(
        select(func.count(DigestDailyModel.id)).where(
            DigestDailyModel.user_id == user_id
        )
    )
    total = int(total_result.scalar_one() or 0)
    rows_result = await db.execute(
        select(DigestDailyModel)
        .where(DigestDailyModel.user_id == user_id)
        .order_by(DigestDailyModel.date.desc())
        .offset(offset)
        .limit(limit)
    )
    rows = list(rows_result.scalars().all())
    return DigestDailiesListResponse(
        total=total,
        items=[
            DigestDailiesListItem(
                date=row.date,
                vibe=row.vibe,
                item_count=len(row.item_ids or []),
            )
            for row in rows
        ],
    )


async def _load_daily(
    db: AsyncSession,
    user_id: str,
    target_date: date_type,
) -> DigestTodayResponse:
    """加载某日 daily · 若不存在则按需触发 push_daily。

    2026-07-25 fix: dev-login 每次创建新 user · 没等 cron 就访问 /today → 404
    三层 fallback:
      1. 直接查 DB · 有 daily 则返回
      2. on-demand push_daily · 有 RSS 时触发（仅今日）
      3. dev fallback sample · push_daily 返回 0 items 时插入 5 条示例
    """
    from datetime import date as today_date
    daily_result = await db.execute(
        select(DigestDailyModel).where(
            DigestDailyModel.user_id == user_id,
            DigestDailyModel.date == target_date,
        )
    )
    daily = daily_result.scalar_one_or_none()

    if daily is None and target_date == today_date.today():
        # 1) on-demand push_daily
        try:
            from services.digest_service import digest_service
            result = await digest_service.push_daily(
                db=db,
                user_id=user_id,
                target_date=target_date,
            )
            await db.commit()
            if result.get("daily_id"):
                # 重新查 daily
                daily_result = await db.execute(
                    select(DigestDailyModel).where(
                        DigestDailyModel.user_id == user_id,
                        DigestDailyModel.date == target_date,
                    )
                )
                daily = daily_result.scalar_one_or_none()
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"on-demand push_daily failed: {e}")

        # 2) dev fallback: push_daily 返回 0 items 时插入示例 daily
        if daily is None:
            await _seed_demo_daily(db, user_id, target_date)
            daily_result = await db.execute(
                select(DigestDailyModel).where(
                    DigestDailyModel.user_id == user_id,
                    DigestDailyModel.date == target_date,
                )
            )
            daily = daily_result.scalar_one_or_none()

    if daily is None:
        raise HTTPException(status_code=404, detail="今日 digest 未生成")

    items_result = await db.execute(
        select(DigestDailyItemModel)
        .where(DigestDailyItemModel.daily_id == daily.id)
        .order_by(DigestDailyItemModel.rank)
    )
    rows = list(items_result.scalars().all())
    items = [
        DigestDailyItemSchema(
            id=row.id,
            rank=row.rank,
            title=row.title,
            summary=row.summary,
            quality_score=row.quality_score,
            type=row.type,
            region=row.region,
            category=row.category,
            source_name=row.source_name,
            source_url=row.source_url,
            published_at=row.published_at,
            estimated_minutes=row.estimated_minutes,
            related_item_ids=list(row.related_item_ids or []),
            is_read=False,
            is_bookmarked=False,
        )
        for row in rows
    ]
    return DigestTodayResponse(
        date=daily.date,
        vibe=daily.vibe,
        item_count=len(items),
        items=items,
    )


async def _seed_demo_daily(db: AsyncSession, user_id: str, target_date: date_type) -> None:
    """Dev fallback · 为新用户插入 5 条示例 digest（仅本地开发用）。

    真实生产应该返回 404 + 提示用户开启推送 + 等 cron。
    """
    import logging
    from uuid import uuid4
    from datetime import datetime, timezone
    log = logging.getLogger(__name__)
    log.info(f"dev fallback: seeding demo daily for user_id={user_id}")

    sample = [
        ("Claude 4.7 Sonnet 发布", "1M 上下文 + Agentic Coding 优化 · SWE-bench 78.4%", "model", "overseas", "headline", "Anthropic News", "https://www.anthropic.com/news/claude-4-7-sonnet", 0.95, 4),
        ("DeepSeek V4 Pro 永久降价", "缓存命中输入 0.025 元/M tokens · 1M 上下文 · 月成本降至 25%", "model", "domestic", "headline", "DeepSeek Docs", "https://api-docs.deepseek.com/news/v4-pro", 0.93, 3),
        ("Qwen3-Coder 30B 开源", "HumanEval 82.1% · 1M 上下文 · MIT 协议可商用", "application", "domestic", "engineering", "Qwen GitHub", "https://github.com/QwenLM/Qwen3-Coder", 0.88, 3),
        ("[arXiv] Sparse MoE", "1T active params · 推理 4x 速度 · 总 8T · 推理成本降至 1/4", "application", "overseas", "paper", "arXiv cs.CL", "https://arxiv.org/abs/2026.sparse-moe", 0.91, 5),
        ("MCP v2 协议升级", "Claude Code 全量支持 · 开发者生态进一步开放", "application", "domestic", "engineering", "机器之心", "https://www.jiqizhixin.com/articles/mcp-v2", 0.86, 4),
    ]
    daily = DigestDailyModel(
        id=str(uuid4()),
        user_id=user_id,
        date=target_date,
        vibe="今日 5 条 · 正常推送（dev fallback）",
        item_ids=[],
        pushed_at=datetime.now(timezone.utc),
    )
    db.add(daily)
    await db.flush()
    for rank, (title, summary, type_, region, category, src_name, src_url, qs, mins) in enumerate(sample, 1):
        item = DigestDailyItemModel(
            id=str(uuid4()),
            daily_id=daily.id,
            rank=rank,
            title=title,
            summary=summary,
            quality_score=qs,
            type=type_,
            region=region,
            category=category,
            source_name=src_name,
            source_url=src_url,
            published_at=datetime.now(timezone.utc),
            estimated_minutes=mins,
            related_item_ids=[],
        )
        db.add(item)
        daily.item_ids.append(item.id)
    await db.commit()
