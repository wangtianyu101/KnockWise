"""Knowledge API — Obsidian vault integration."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.dependencies import get_current_user
from models import User
from services.obsidian_service import obsidian

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])


@router.get("/tree")
async def get_tree(user: User = Depends(get_current_user)):
    return obsidian.tree()


@router.get("/browse")
async def browse(subdir: str = "", user: User = Depends(get_current_user)):
    return obsidian.list_files(subdir)


@router.get("/search")
async def search(q: str = Query(...), limit: int = 20, user: User = Depends(get_current_user)):
    if not q.strip():
        return []
    return obsidian.search(q.strip(), limit)


@router.get("/note")
async def read_note(path: str = Query(...), user: User = Depends(get_current_user)):
    note = obsidian.read_note(path)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return note


@router.put("/note")
async def write_note(path: str = Query(...), content: str = "", user: User = Depends(get_current_user)):
    return obsidian.write_note(path, content)


@router.get("/graph")
async def get_graph(user: User = Depends(get_current_user)):
    return obsidian.build_graph()


@router.get("/stats")
async def get_stats(user: User = Depends(get_current_user)):
    return obsidian.get_stats()


@router.get("/backlinks")
async def backlinks(path: str = Query(...), user: User = Depends(get_current_user)):
    return obsidian.get_backlinks(path)


@router.get("/daily")
async def daily_note(date: str | None = None, user: User = Depends(get_current_user)):
    note = obsidian.get_daily_note(date)
    if not note:
        raise HTTPException(status_code=404, detail="Daily note not found")
    return note
