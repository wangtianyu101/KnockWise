"""ObsidianSedimentService (V2.2 PR 2 — V2 智能沉淀层 · Obsidian 写回)

职责（spec.md §4.4）：
- write_daily(date, content)         → 写 learning/YYYY-MM-DD.md
- write_weekly(week, content)         → 写 weekly/YYYY-Www.md
- write_monthly(month, content)       → 写 monthly/YYYY-MM.md
- write_mastered_dump(user_id, topics) → 写 mastered/<user_id>.md
- write_practice_log(session_id, content) → 写 interview/YYYY-MM-DD-<id>.md

容错核心（决策 7A）：
- _write() 失败返回 None，log warning，**不抛**异常
- vault 不存在 → log warning 一次，return None
- 写文件失败 → log warning，return None

实施任务（tasks.md § V2.2）：
- T9: 骨架 + _write 容错（本文件）
- T10: write_daily 实现（含 YAML frontmatter）
- T11: write_weekly/monthly/mastered_dump 实现
- T12: write_practice_log 实现（interview log 路径）
- T13: settle_after_practice 末尾调 write_daily
- T14: settle_after_interview 末尾调 write_practice_log
- T15: test 凑齐 ≥ 80% 覆盖

参考：V1 services/obsidian_service.py VAULT_ROOT = Path.home() / "Obsidian" / "coding"
"""
from __future__ import annotations

import logging
from datetime import date, datetime, timezone
from pathlib import Path
from typing import List, Optional
from uuid import UUID

log = logging.getLogger("codemock.obsidian_sediment")

VAULT_ROOT = Path.home() / "Obsidian" / "coding"
DAILY_DIR = "learning"
INTERVIEW_DIR = "interview"
WEEKLY_DIR = "weekly"
MONTHLY_DIR = "monthly"
MASTERED_DIR = "mastered"


# ════════════════════════════════════════════════════════════
#  ObsidianSedimentService — 沉淀写回核心
# ════════════════════════════════════════════════════════════


class ObsidianSedimentService:
    """V2 沉淀写回 Obsidian vault。

    所有方法**不抛异常**（决策 7A）：失败 log warning + return None。
    调用方（settle_after_practice/interview）业务不感知。
    """

    def __init__(self, vault_path: Path = VAULT_ROOT):
        self.vault = vault_path

    def _write(self, rel_path: str, content: str) -> Optional[str]:
        """容错核心：vault 不存在/写失败 → log warning + return None（**不抛**）。

        Returns:
            成功: 绝对路径 (str)
            失败: None
        """
        try:
            if not self.vault.exists():
                log.warning(
                    f"ObsidianSedimentService._write: vault not found at {self.vault}"
                )
                return None
            full = self.vault / rel_path
            full.parent.mkdir(parents=True, exist_ok=True)
            full.write_text(content, encoding="utf-8")
            return str(full)
        except Exception as e:
            log.warning(
                f"ObsidianSedimentService._write failed: {rel_path} → {e}"
            )
            return None

    def write_daily(self, date: date, content: str) -> Optional[str]:
        """写每日学习笔记：learning/YYYY-MM-DD.md（包含 YAML frontmatter）。

        T10 实施：
        - YAML frontmatter：date / generated_at
        - body：调用方传入的 content
        - 调用 _write 写文件
        - 失败 log + return None（决策 7A）
        """
        try:
            rel_path = f"{DAILY_DIR}/{date.isoformat()}.md"
            frontmatter = "\n".join([
                "---",
                f"date: {date.isoformat()}",
                f"generated_at: {datetime.now(timezone.utc).isoformat()}",
                "---",
                "",
            ])
            full_content = frontmatter + (content or "")
            return self._write(rel_path, full_content)
        except Exception as e:
            log.warning(f"write_daily failed: date={date} error={e}")
            return None

    def write_weekly(self, week: str, content: str) -> Optional[str]:
        """写周报：weekly/YYYY-Www.md。"""
        try:
            rel_path = f"{WEEKLY_DIR}/{week}.md"
            frontmatter = "\n".join([
                "---",
                f"week: {week}",
                f"generated_at: {datetime.now(timezone.utc).isoformat()}",
                "---",
                "",
            ])
            return self._write(rel_path, frontmatter + (content or ""))
        except Exception as e:
            log.warning(f"write_weekly failed: week={week} error={e}")
            return None

    def write_monthly(self, month: str, content: str) -> Optional[str]:
        """写月报：monthly/YYYY-MM.md。"""
        try:
            rel_path = f"{MONTHLY_DIR}/{month}.md"
            frontmatter = "\n".join([
                "---",
                f"month: {month}",
                f"generated_at: {datetime.now(timezone.utc).isoformat()}",
                "---",
                "",
            ])
            return self._write(rel_path, frontmatter + (content or ""))
        except Exception as e:
            log.warning(f"write_monthly failed: month={month} error={e}")
            return None

    def write_mastered_dump(
        self, user_id: UUID, topics: List[dict]
    ) -> Optional[str]:
        """写已掌握 topic dump：mastered/<user_id>.md。"""
        try:
            rel_path = f"{MASTERED_DIR}/{user_id}.md"
            body_lines = [f"- {t.get('topic', '?')}" for t in topics]
            frontmatter = "\n".join([
                "---",
                f"user_id: {user_id}",
                f"count: {len(topics)}",
                f"generated_at: {datetime.now(timezone.utc).isoformat()}",
                "---",
                "",
                "# Mastered Topics\n\n",
            ])
            return self._write(rel_path, frontmatter + "\n".join(body_lines))
        except Exception as e:
            log.warning(
                f"write_mastered_dump failed: user={user_id} error={e}"
            )
            return None

    def write_practice_log(
        self, session_id: UUID, content: str
    ) -> Optional[str]:
        """写面试日志：interview/YYYY-MM-DD-<id8>.md。

        session_id 实际是 interview_id（UUID）；路径里用前 8 字符避免太长。
        """
        try:
            today = datetime.now(timezone.utc).date()
            id_short = str(session_id)[:8]
            rel_path = f"{INTERVIEW_DIR}/{today.isoformat()}-{id_short}.md"
            frontmatter = "\n".join([
                "---",
                f"session_id: {session_id}",
                f"date: {today.isoformat()}",
                f"generated_at: {datetime.now(timezone.utc).isoformat()}",
                "---",
                "",
            ])
            return self._write(rel_path, frontmatter + (content or ""))
        except Exception as e:
            log.warning(
                f"write_practice_log failed: session={session_id} error={e}"
            )
            return None
