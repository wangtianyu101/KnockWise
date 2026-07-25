from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models import DigestSource, Question

logger = logging.getLogger(__name__)


SEED_DIR = Path(__file__).parent.parent / "seed_data"

SEED_FILES = [
    ("agent_core.json", "agent_architecture"),
    ("rag_tech.json", "rag"),
    ("langgraph.json", "langgraph"),
    ("java_backend.json", "java"),
]


async def seed_questions(db: AsyncSession, force: bool = False):
    """Import all seed questions into the database."""
    existing = await db.execute(select(Question).limit(1))
    if existing.scalar_one_or_none() and not force:
        print("Questions already seeded. Use force=True to re-seed.")
        return

    total = 0
    for filename, default_topic in SEED_FILES:
        filepath = SEED_DIR / filename
        if not filepath.exists():
            print(f"Warning: {filepath} not found, skipping.")
            continue

        data = json.loads(filepath.read_text(encoding="utf-8"))
        for item in data:
            existing_q = await db.execute(
                select(Question).where(Question.id == item["id"])
            )
            if existing_q.scalar_one_or_none():
                continue

            q = Question(
                id=item["id"],
                topic=item.get("topic", default_topic),
                sub_topic=item["sub_topic"],
                difficulty=item["difficulty"],
                round=item["round"],
                question_text=item["question_text"],
                answer_key_points=item.get("answer_key_points", []),
                followup_tree=item.get("followup_tree", {}),
            )
            db.add(q)
            total += 1

    await db.commit()
    print(f"Seeded {total} questions.")


def load_questions_from_files() -> list[dict]:
    """Load all seed questions as a list of dicts (for in-memory use)."""
    questions = []
    for filename, _ in SEED_FILES:
        filepath = SEED_DIR / filename
        if filepath.exists():
            data = json.loads(filepath.read_text(encoding="utf-8"))
            questions.extend(data)
    return questions


def get_question_by_id(question_id: str) -> Optional[dict]:
    """Get a single question by its ID from seed files."""
    for filename, _ in SEED_FILES:
        filepath = SEED_DIR / filename
        if filepath.exists():
            data = json.loads(filepath.read_text(encoding="utf-8"))
            for q in data:
                if q["id"] == question_id:
                    return q
    return None


def get_questions_by_topic(topic: str) -> list[dict]:
    """Get questions filtered by topic from seed files."""
    result = []
    for filename, _ in SEED_FILES:
        filepath = SEED_DIR / filename
        if filepath.exists():
            data = json.loads(filepath.read_text(encoding="utf-8"))
            for q in data:
                if q.get("topic") == topic:
                    result.append(q)
    return result


# ═══════════════════════════════════════════════════════════════════
# Digest Sources (V2 AI 推送 · 2026-07-25 修复 stub)
# ═══════════════════════════════════════════════════════════════════

DIGEST_SOURCES_SEED_FILE = "digest_sources.json"
DEFAULT_DIGEST_SOURCE_COUNT = 8


async def seed_default_digest_sources(db: AsyncSession) -> int:
    """Seed 8 系统默认 digest_sources（幂等）。

    Returns:
        实际新插入的行数（已存在则返回 0）。

    说明：
        - 系统默认源 user_id IS NULL · 所有用户共享
        - enabled=True（默认启用）· spec R5 独立性
        - 重复调用安全：若 DB 已有 is_default=True 的 8 行 · 跳过
    """
    # 1. 幂等检查
    existing_count = await db.scalar(
        select(func.count(DigestSource.id)).where(
            DigestSource.is_default.is_(True),
            DigestSource.user_id.is_(None),
        )
    )
    if existing_count and existing_count >= DEFAULT_DIGEST_SOURCE_COUNT:
        logger.info(f"digest default sources already seeded: {existing_count} rows")
        return 0

    # 2. 读 seed JSON
    seed_path = SEED_DIR / DIGEST_SOURCES_SEED_FILE
    if not seed_path.exists():
        logger.warning(f"digest seed file not found: {seed_path}")
        return 0

    seed_data = json.loads(seed_path.read_text(encoding="utf-8"))

    # 3. 插入（去重 by URL）
    inserted = 0
    for item in seed_data:
        # 已存在同名同 URL · 跳过
        existing = await db.scalar(
            select(DigestSource.id).where(
                DigestSource.url == item["url"],
                DigestSource.user_id.is_(None),
            )
        )
        if existing:
            continue

        db.add(DigestSource(
            name=item["name"],
            url=item["url"],
            category=item["category"],
            type=item["type"],
            region=item["region"],
            enabled=True,
            is_default=True,
            last_item_count=0,
        ))
        inserted += 1

    if inserted > 0:
        await db.commit()
        logger.info(f"seeded {inserted} default digest sources")

    return inserted
