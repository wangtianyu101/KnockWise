"""NewsService — reads AI daily/weekly reports and code stats from Obsidian vault."""

import os
import re
import json
import sqlite3
from collections import defaultdict
from datetime import date, datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

TZ = timezone(timedelta(hours=8))
OBSIDIAN_AI = Path.home() / "Obsidian" / "coding" / "ai"
STATS_DB = Path.home() / "IdeaProjects" / "agent-memory" / "scripts" / ".stats.db"

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


class NewsService:
    """Read AI daily reports, weekly reports, and code stats from Obsidian."""

    # ── Daily Reports ────────────────────────────────────────────

    def list_dailies(self) -> list[dict]:
        """List all AI daily report files."""
        if not OBSIDIAN_AI.exists():
            return []
        items = []
        for f in sorted(OBSIDIAN_AI.glob("AI 日报 *.md"), reverse=True):
            items.append({
                "name": f.name,
                "date": f.name.replace("AI 日报 ", "").replace(".md", ""),
                "size": f.stat().st_size,
            })
        return items

    def get_daily(self, day: str | None = None) -> Optional[dict]:
        """Get daily report for a specific day (defaults to latest)."""
        if day:
            fpath = OBSIDIAN_AI / f"AI 日报 {day}.md"
        else:
            files = sorted(OBSIDIAN_AI.glob("AI 日报 *.md"), reverse=True)
            if not files: return None
            fpath = files[0]
        if not fpath.exists(): return None
        content = fpath.read_text(encoding="utf-8")
        return {
            "name": fpath.name,
            "date": fpath.name.replace("AI 日报 ", "").replace(".md", ""),
            "content": content,
            "size": fpath.stat().st_size,
        }

    # ── Weekly Reports ───────────────────────────────────────────

    def list_weeklies(self) -> list[dict]:
        if not OBSIDIAN_AI.exists(): return []
        items = []
        for f in sorted(OBSIDIAN_AI.glob("AI 周报 *.md"), reverse=True):
            items.append({"name": f.name, "week": f.name.replace("AI 周报 ", "").replace(".md", ""), "size": f.stat().st_size})
        return items

    def get_weekly(self, week: str | None = None) -> Optional[dict]:
        if week:
            fpath = OBSIDIAN_AI / f"AI 周报 {week}.md"
        else:
            files = sorted(OBSIDIAN_AI.glob("AI 周报 *.md"), reverse=True)
            if not files: return None
            fpath = files[0]
        if not fpath.exists(): return None
        content = fpath.read_text(encoding="utf-8")
        return {"name": fpath.name, "week": fpath.name.replace("AI 周报 ", "").replace(".md", ""), "content": content}

    # ── Code Stats ────────────────────────────────────────────────

    def get_code_stats(self, days: int = 7) -> dict:
        """Read token + code stats from SQLite DB (populated by stats.py)."""
        if not STATS_DB.exists():
            return self._fallback_stats()
        try:
            conn = sqlite3.connect(str(STATS_DB))
            conn.row_factory = sqlite3.Row
            rows = conn.execute("""
                SELECT s.date, COALESCE(tok.total_input,0) as ti, COALESCE(tok.total_output,0) as t_o,
                       COALESCE(cod.lines_added,0) as ca, COALESCE(cod.lines_deleted,0) as cd,
                       COALESCE(cod.commits,0) as cc
                FROM daily_summary s
                LEFT JOIN (SELECT date, SUM(input_tokens) as total_input, SUM(output_tokens) as total_output FROM daily_tokens GROUP BY date) tok ON s.date = tok.date
                LEFT JOIN (SELECT date, SUM(lines_added) as lines_added, SUM(lines_deleted) as lines_deleted, SUM(commits) as commits FROM daily_code GROUP BY date) cod ON s.date = cod.date
                WHERE s.date >= date('now', ? || ' days')
                ORDER BY s.date DESC
            """, (f"-{days}",)).fetchall()

            # Totals
            agg = conn.execute("""
                SELECT COUNT(*) as days, COALESCE(SUM(input_tokens),0) as ti, COALESCE(SUM(output_tokens),0) as t_o,
                       COALESCE(SUM(lines_added),0)+COALESCE(SUM(lines_deleted),0) as lines,
                       COALESCE(SUM(commits),0) as cms
                FROM daily_tokens LEFT JOIN daily_code ON daily_tokens.date = daily_code.date
            """).fetchone()
            conn.close()

            daily = [{"date": r["date"], "tokens_in": r["ti"], "tokens_out": r["t_o"],
                       "code_added": r["ca"], "code_deleted": r["cd"], "commits": r["cc"]} for r in rows]
            return {
                "daily": daily,
                "summary": {"total_days": agg["days"] or 0, "total_tokens": (agg["ti"] or 0) + (agg["t_o"] or 0),
                            "total_code": agg["lines"] or 0, "total_commits": agg["cms"] or 0},
            }
        except Exception:
            return self._fallback_stats()

    def _fallback_stats(self) -> dict:
        """Return empty stats when DB unavailable."""
        return {"daily": [], "summary": {"total_days": 0, "total_tokens": 0, "total_code": 0, "total_commits": 0}}

    # ── Sources ───────────────────────────────────────────────────

    def get_sources(self) -> list[dict]:
        return [
            {"name": "量子位", "url": "https://www.qbitai.com/feed", "category": "大模型", "enabled": True},
            {"name": "36氪", "url": "https://36kr.com/feed", "category": "应用", "enabled": True, "ai_filter": True},
            {"name": "HuggingFace Papers", "url": "https://huggingface.co/api/daily_papers", "category": "论文", "enabled": True},
            {"name": "arXiv cs.AI", "url": "https://rss.arxiv.org/rss/cs.AI", "category": "论文", "enabled": True},
        ]


news_service = NewsService()
