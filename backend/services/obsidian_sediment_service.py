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
        """写每日学习笔记：learning/YYYY-MM-DD.md（包含 YAML frontmatter）。"""
        # T10 实施：生成 frontmatter + content
        log.debug(f"write_daily placeholder: date={date}")
        return None

    def write_weekly(self, week: str, content: str) -> Optional[str]:
        """写周报：weekly/YYYY-Www.md。"""
        # T11 实施
        log.debug(f"write_weekly placeholder: week={week}")
        return None

    def write_monthly(self, month: str, content: str) -> Optional[str]:
        """写月报：monthly/YYYY-MM.md。"""
        # T11 实施
        log.debug(f"write_monthly placeholder: month={month}")
        return None

    def write_mastered_dump(
        self, user_id: UUID, topics: List[dict]
    ) -> Optional[str]:
        """写已掌握 topic dump：mastered/<user_id>.md。"""
        # T11 实施
        log.debug(f"write_mastered_dump placeholder: user={user_id}")
        return None

    def write_practice_log(
        self, session_id: UUID, content: str
    ) -> Optional[str]:
        """写面试日志：interview/YYYY-MM-DD-<session_id>.md。

        session_id 实际是 interview_id（UUID）；路径里用前 8 字符避免太长。
        """
        # T12 实施
        log.debug(f"write_practice_log placeholder: session={session_id}")
        return None
