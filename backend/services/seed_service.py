from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import Question


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
