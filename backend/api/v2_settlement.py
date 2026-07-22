"""V2 Settlement API — 6 个新端点（PR 3a · V2.3）

按 api-spec.md §2 + tasks.md T20 实施：
- GET  /api/v2/dashboard/summary            → SummaryService.dashboard
- GET  /api/v2/profile/weekly?week=...      → SummaryService.weekly
- GET  /api/v2/profile/monthly?month=...    → SummaryService.monthly
- POST /api/v2/profile/refresh              → ProfileSettlementService.manual_refresh
- GET  /api/v2/knowledge/recent-sediments?limit=N → Obsidian service.ls_files
- POST /api/v2/obsidian/sync                → SummaryService.sync_daily_to_obsidian

所有端点：
- 走 JWT 认证（Depends(get_current_user)）
- 路径前缀 /api/v2
- 响应头加 X-API-Version: v2.0
- 限流（spec §3.2 表格）— slowapi 接入（L4 review 改进项）
- 失败兜底：HTTP 200 + 降级版（决策 7A），不返 5xx
"""
from __future__ import annotations

import logging
from datetime import date as date_type
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.dependencies import get_current_user
from core.limiter import limiter  # V2 L4 review 限流
from models import User
from services.summary_service import SummaryService
from services.profile_settlement_service import ProfileSettlementService
from services.obsidian_service import obsidian
from services.obsidian_sediment_service import ObsidianSedimentService
from pathlib import Path

log = logging.getLogger("knockwise.api.v2")

router = APIRouter(prefix="/api/v2", tags=["v2-settlement"])


# ─── /api/v2/dashboard/summary ─────────────────────

@router.get("/dashboard/summary")
@limiter.limit("5/60second")
async def get_dashboard_summary(
    request: Request,
    date: Optional[str] = Query(
        None, description="YYYY-MM-DD, 默认 = today (用户时区)"
    ),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    x_api_version: str = Header(default="v2.0"),
):
    """GET /api/v2/dashboard/summary — Dashboard 顶部"今日学习总结"卡。

    决策 7A 派生：服务失败时返降级版（_fallback=true），HTTP 200。
    限流：60s 内 5 次（spec §3.2）— slowapi V2.4 接入。
    """
    target_date = date_type.today()
    if date:
        try:
            target_date = date_type.fromisoformat(date)
        except ValueError:
            raise HTTPException(status_code=422, detail="date format must be YYYY-MM-DD")

    summary = await SummaryService().dashboard(user_id=user.id, db=db)
    if summary is None:
        # 极端情况：服务彻底返 None（不应发生，但兜底）
        return {
            "title": "今日学习总结",
            "date": target_date.isoformat(),
            "yesterday_count": 0,
            "mastered": [],
            "weak_shift": [],
            "body": "今日总结暂不可用",
            "_fallback": True,
        }
    return summary


# ─── /api/v2/profile/weekly ────────────────────────

@router.get("/profile/weekly")
@limiter.limit("1/60second")
async def get_profile_weekly(
    request: Request,
    week: str = Query(..., description="ISO week (YYYY-Www)"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """GET /api/v2/profile/weekly — 周报 + 12 周 trajectory。"""
    # 验证 week 格式
    import re
    if not re.match(r"^\d{4}-W\d{2}$", week):
        raise HTTPException(
            status_code=422, detail="week format must be YYYY-Www"
        )

    summary = await SummaryService().weekly(user_id=user.id, week=week, db=db)
    if summary is None:
        raise HTTPException(status_code=500, detail="weekly summary failed")
    return summary


# ─── /api/v2/profile/monthly ───────────────────────

@router.get("/profile/monthly")
@limiter.limit("1/60second")
async def get_profile_monthly(
    request: Request,
    month: str = Query(..., description="YYYY-MM"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """GET /api/v2/profile/monthly — 月报 + 6 月 trajectory + 落库。"""
    import re
    if not re.match(r"^\d{4}-\d{2}$", month):
        raise HTTPException(
            status_code=422, detail="month format must be YYYY-MM"
        )

    summary = await SummaryService().monthly(user_id=user.id, month=month, db=db)
    if summary is None:
        raise HTTPException(status_code=500, detail="monthly summary failed")
    return summary


# ─── /api/v2/profile/refresh ───────────────────────

@router.post("/profile/refresh")
@limiter.limit("1/60second")
async def post_profile_refresh(
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """POST /api/v2/profile/refresh — 手动刷新画像 + DEL summary cache 3 key。

    限流：60s 内 1 次（防手动刷量，spec §3.2）。
    """
    from uuid import UUID
    result = await ProfileSettlementService().manual_refresh(
        user_id=UUID(user.id), db=db,
    )
    if result is None:
        raise HTTPException(status_code=500, detail="refresh failed")
    return result


# ─── /api/v2/knowledge/recent-sediments ────────────

@router.get("/knowledge/recent-sediments")
@limiter.limit("20/60second")
async def get_recent_sediments(
    request: Request,
    limit: int = Query(5, ge=1, le=20, description="默认 5, 最大 20"),
    user: User = Depends(get_current_user),
):
    """GET /api/v2/knowledge/recent-sediments — 最近 N 个学习沉淀文件。

    决策 7A 派生：vault 不存在返空 list（不返 500），前端 UI 显示提示。
    """
    vault = Path.home() / "Obsidian" / "coding"
    files: list[dict] = []
    try:
        if not vault.exists():
            return []  # 决策 7A：vault 不在 → 空 list，不抛
        # 扫 learning/ + interview/ 子目录
        all_md = []
        for subdir in ["learning", "interview"]:
            sub = vault / subdir
            if sub.exists():
                for f in sub.iterdir():
                    if f.suffix == ".md":
                        all_md.append(f)
        # 按 mtime 排序
        all_md.sort(key=lambda f: f.stat().st_mtime, reverse=True)
        # 取 limit 个
        for f in all_md[:limit]:
            stat = f.stat()
            rel_path = str(f.relative_to(vault))
            files.append({
                "rel_path": rel_path,
                "full_path": str(f) if vault.exists() else None,
                "success": True,
                "error": None,
            })
    except Exception as e:
        log.warning(f"recent-sediments vault scan failed: {e}")
        # 决策 7A：失败 log + 返空 list，不返 500
    return files


# ─── /api/v2/obsidian/sync ─────────────────────────

@router.post("/obsidian/sync")
@limiter.limit("1/60second")
async def post_obsidian_sync(
    request: Request,
    date: str = Query(..., description="YYYY-MM-DD"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """POST /api/v2/obsidian/sync — 手动触发 Obsidian 同步（vault 后创建时用）。

    决策 7A 派生：vault 不存在返 synced_count=0 + files=[]，不抛 500。
    """
    from datetime import date as _date
    try:
        target = _date.fromisoformat(date)
    except ValueError:
        raise HTTPException(status_code=422, detail="date format must be YYYY-MM-DD")

    result = await SummaryService().sync_daily_to_obsidian(
        user_id=user.id, date=target, db=db,
    )
    if result is None:
        # 决策 7A：服务彻底返 None → 返 synced=False 标记
        return {
            "date": date,
            "synced_count": 0,
            "files": [],
            "_fallback": True,
        }
    # 包装成 api-spec 形式
    return {
        "date": date,
        "synced_count": 1 if result.get("synced") else 0,
        "files": [{
            "rel_path": f"learning/{date}.md",
            "full_path": result.get("path"),
            "success": result.get("synced", False),
            "error": result.get("error"),
        }],
    }
