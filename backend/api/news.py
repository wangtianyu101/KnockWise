"""News API — AI daily/weekly reports, code stats, source management.

V1 closure 🟡 #7（4.1.8）：补 3 个端点
- POST /api/news/trigger/daily    — 手动触发生成日报
- POST /api/news/trigger/weekly   — 手动触发生成周报
- GET  /api/news/history          — 日报/周报历史聚合列表

实际生成由 ~/agent-memory/scripts/ai_news.py + macOS LaunchAgent 跑，
端点只是 trigger marker + 返回状态（不阻塞 API 调用）。
"""

from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query

from core.dependencies import get_current_user
from models import User
from services.news_service import news_service

router = APIRouter(prefix="/api/news", tags=["news"])

TRIGGER_LOG_DIR = Path.home() / ".devbrain_triggers"


@router.get("/daily")
async def list_dailies(user: User = Depends(get_current_user)):
    return news_service.list_dailies()


@router.get("/daily/latest")
async def latest_daily(date: str | None = None, user: User = Depends(get_current_user)):
    report = news_service.get_daily(date)
    if not report:
        raise HTTPException(status_code=404, detail="Daily report not found")
    return report


@router.get("/weekly")
async def list_weeklies(user: User = Depends(get_current_user)):
    return news_service.list_weeklies()


@router.get("/weekly/latest")
async def latest_weekly(week: str | None = None, user: User = Depends(get_current_user)):
    report = news_service.get_weekly(week)
    if not report:
        raise HTTPException(status_code=404, detail="Weekly report not found")
    return report


@router.get("/stats")
async def code_stats(days: int = 7, user: User = Depends(get_current_user)):
    return news_service.get_code_stats(days)


@router.get("/sources")
async def list_sources(user: User = Depends(get_current_user)):
    return news_service.get_sources()


# ─── V1 closure 🟡 #7：补 3 个端点 ──────────────────────


@router.post("/trigger/daily")
async def trigger_daily(user: User = Depends(get_current_user)):
    """手动触发生成日报。

    实际生成由 ~/agent-memory/scripts/ai_news.py + macOS LaunchAgent 跑（cron 每晚 23:00）。
    本端点只是写 trigger marker，ai_news.py 跑时检查 marker 来加速触发。

    Returns:
        {"queued": True, "queued_at": "...", "expected_completion_minutes": 15}
    """
    return _write_trigger_marker("daily", user.id)


@router.post("/trigger/weekly")
async def trigger_weekly(user: User = Depends(get_current_user)):
    """手动触发生成周报（与 daily 同模式）。"""
    return _write_trigger_marker("weekly", user.id)


@router.get("/history")
async def news_history(
    limit: int = Query(20, ge=1, le=100, description="返回最近 N 条"),
    user: User = Depends(get_current_user),
):
    """日报 + 周报历史聚合列表（最近 N 条）。"""
    daily = news_service.list_dailies()
    weekly = news_service.list_weeklies()

    items = []
    for d in daily[:limit]:
        items.append({"type": "daily", "date": d.get("date", ""), "name": d.get("name", ""), "size": d.get("size", 0)})
    for w in weekly[:limit]:
        items.append({"type": "weekly", "week": w.get("week", ""), "name": w.get("name", ""), "size": w.get("size", 0)})

    # 按 name 排序（daily + weekly 按日期降序混合）
    items.sort(key=lambda x: x.get("name", ""), reverse=True)
    return {"items": items[:limit], "total": len(items)}


def _write_trigger_marker(
    kind: str, user_id: str
) -> dict:
    """写 trigger marker 到 ~/.devbrain_triggers/，ai_news.py 跑时读取加速触发。

    best-effort：失败返默认状态（不阻塞 API）。
    """
    try:
        TRIGGER_LOG_DIR.mkdir(parents=True, exist_ok=True)
        now = datetime.now(timezone.utc).isoformat()
        marker = TRIGGER_LOG_DIR / f"{kind}_{now[:19].replace(':', '')}.trigger"
        marker.write_text(
            f"kind={kind}\nuser_id={user_id}\nqueued_at={now}\n",
            encoding="utf-8",
        )
        return {
            "queued": True,
            "queued_at": now,
            "marker_path": str(marker),
            "expected_completion_minutes": 15,
            "note": f"已写 marker 到 {marker}。ai_news.py 跑时会检测 marker 立即生成 {kind}。",
        }
    except Exception as e:
        return {
            "queued": False,
            "error": str(e),
            "note": "trigger marker 写失败（best-effort）。可手动跑 ai_news.py。",
        }
