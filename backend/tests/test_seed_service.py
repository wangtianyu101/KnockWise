"""单测: services/seed_service.py

策略：monkeypatch SEED_DIR 到 tmp_path（不能动 backend/seed_data/）。
覆盖：seed_questions / load_questions_from_files / get_question_by_id / get_questions_by_topic
目标：≥ 70%
"""
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from services import seed_service as svc
from services.seed_service import (
    seed_questions,
    load_questions_from_files,
    get_question_by_id,
    get_questions_by_topic,
    SEED_FILES,
)


SAMPLE_QUESTIONS = [
    {
        "id": "q-1",
        "topic": "agent",
        "sub_topic": "react",
        "difficulty": 3,
        "round": "round1",
        "question_text": "什么是 ReAct？",
        "answer_key_points": ["Reasoning", "Acting"],
        "followup_tree": {},
    },
    {
        "id": "q-2",
        "topic": "rag",
        "sub_topic": "chunking",
        "difficulty": 2,
        "round": "round2",
        "question_text": "如何切分文档？",
        "answer_key_points": ["按段", "按句"],
    },
]


@pytest.fixture
def fake_seed_dir(tmp_path, monkeypatch):
    """monkeypatch SEED_DIR 到 tmp_path，并写假 seed JSON 文件"""
    monkeypatch.setattr(svc, "SEED_DIR", tmp_path)
    # 写 SEED_FILES 里对应的文件
    for filename, _ in SEED_FILES:
        (tmp_path / filename).write_text(
            json.dumps(SAMPLE_QUESTIONS, ensure_ascii=False),
            encoding="utf-8",
        )
    return tmp_path


# ─── seed_questions ───────────────────────────────────────────

class TestSeedQuestions:
    async def test_skips_when_already_seeded(self, mock_db, fake_seed_dir):
        """库里已有数据且 force=False 时直接 return"""
        from tests.conftest import FakeResult
        # limit(1) query 返回一个 Question
        mock_db.execute = AsyncMock(return_value=FakeResult(scalar="existing"))

        await seed_questions(mock_db)
        # 不应 add 任何 Question
        mock_db.add.assert_not_called()
        mock_db.commit.assert_not_awaited()

    async def test_force_reseeds_even_when_existing(self, mock_db, fake_seed_dir, capsys):
        from tests.conftest import FakeResult
        # 4 个文件 × 2 题 = 8 个 id 查询 + 1 个 limit(1) check = 9 个 result
        side_effects = [FakeResult(scalar="existing")]  # limit(1)
        side_effects += [FakeResult(scalar=None)] * 8   # 8 个 id 查询（都不存在）
        mock_db.execute = AsyncMock(side_effect=side_effects)

        await seed_questions(mock_db, force=True)
        # 4 文件 × 2 题 = 8 题 add
        assert mock_db.add.call_count == 8
        mock_db.commit.assert_awaited()

    async def test_imports_all_seed_questions(self, mock_db, fake_seed_dir, capsys):
        from tests.conftest import FakeResult
        # 1 个 limit(1) + 8 个 id 查询
        side_effects = [FakeResult(scalar=None)]  # limit(1)
        side_effects += [FakeResult(scalar=None)] * 8
        mock_db.execute = AsyncMock(side_effect=side_effects)

        await seed_questions(mock_db)
        assert mock_db.add.call_count == 8
        first_q = mock_db.add.call_args_list[0].args[0]
        assert first_q.id == "q-1"
        assert first_q.topic == "agent"
        assert first_q.difficulty == 3

    async def test_skips_existing_question_ids(self, mock_db, fake_seed_dir, capsys):
        from tests.conftest import FakeResult
        # limit(1) None；8 个 id 查询，其中 q-1 存在
        side_effects = [FakeResult(scalar=None)]  # limit(1)
        side_effects += [FakeResult(scalar="existing_q-1")]  # q-1 存在
        side_effects += [FakeResult(scalar=None)] * 7  # 其他 7 个 id 不存在
        mock_db.execute = AsyncMock(side_effect=side_effects)

        await seed_questions(mock_db)
        # q-1 跳过；其他 7 个 add
        assert mock_db.add.call_count == 7

    async def test_skips_missing_seed_files(self, mock_db, tmp_path, monkeypatch, capsys):
        """seed file 不存在时跳过（不抛错）"""
        monkeypatch.setattr(svc, "SEED_DIR", tmp_path)  # 空目录
        from tests.conftest import FakeResult
        # 1 个 limit(1)，但没文件 → 没后续 id 查询
        mock_db.execute = AsyncMock(side_effect=[
            FakeResult(scalar=None),  # limit(1)
        ])

        await seed_questions(mock_db)
        mock_db.add.assert_not_called()  # 没文件 → 没题可加
        # commit 仍会被调（即使 0 题），但应不抛错

    async def test_uses_default_topic_from_filename(self, mock_db, tmp_path, monkeypatch, capsys):
        """item 没 topic 时用 SEED_FILES tuple 的 default"""
        monkeypatch.setattr(svc, "SEED_DIR", tmp_path)
        (tmp_path / "rag_tech.json").write_text(json.dumps([
            {
                "id": "q-rag",
                # 故意不写 topic，应 fallback 到 "rag"
                "sub_topic": "chunking",
                "difficulty": 2,
                "round": "round1",
                "question_text": "Q?",
            }
        ]), encoding="utf-8")

        from tests.conftest import FakeResult
        # 1 个 limit(1) + 1 个 id 查询（q-rag）
        mock_db.execute = AsyncMock(side_effect=[
            FakeResult(scalar=None),
            FakeResult(scalar=None),
        ])

        await seed_questions(mock_db)
        # 验证 add 的 topic 是 "rag"（default from SEED_FILES）
        added = mock_db.add.call_args.args[0]
        assert added.topic == "rag"


# ─── load_questions_from_files ────────────────────────────────

class TestLoadQuestionsFromFiles:
    def test_loads_all_files(self, fake_seed_dir):
        questions = load_questions_from_files()
        # 4 个文件 × 2 题 = 8（但因为写同一个 dict 引用，内容相同）
        # 实际：每个文件读自己的 SAMPLE_QUESTIONS（虽然 dict 一样）
        # 验证至少 q-1 和 q-2 都在
        ids = {q["id"] for q in questions}
        assert "q-1" in ids
        assert "q-2" in ids

    def test_skips_missing_files(self, tmp_path, monkeypatch):
        """seed file 缺失时跳过该文件"""
        monkeypatch.setattr(svc, "SEED_DIR", tmp_path)
        # 只写一个文件，且只放 agent topic
        (tmp_path / "agent_core.json").write_text(json.dumps([
            {"id": "agent-only", "topic": "agent", "sub_topic": "react",
             "difficulty": 3, "round": "round1", "question_text": "Q?"}
        ]), encoding="utf-8")
        # 其他 3 个文件不存在
        questions = load_questions_from_files()
        # 只有 agent_core.json 的内容
        assert all(q["topic"] == "agent" for q in questions)
        assert len(questions) == 1

    def test_returns_empty_when_no_files(self, tmp_path, monkeypatch):
        monkeypatch.setattr(svc, "SEED_DIR", tmp_path)
        assert load_questions_from_files() == []


# ─── get_question_by_id ───────────────────────────────────────

class TestGetQuestionById:
    def test_finds_question(self, fake_seed_dir):
        q = get_question_by_id("q-1")
        assert q is not None
        assert q["id"] == "q-1"
        assert q["topic"] == "agent"

    def test_returns_none_when_not_found(self, fake_seed_dir):
        assert get_question_by_id("q-nonexistent") is None

    def test_handles_missing_seed_files(self, tmp_path, monkeypatch):
        monkeypatch.setattr(svc, "SEED_DIR", tmp_path)
        assert get_question_by_id("any") is None


# ─── get_questions_by_topic ───────────────────────────────────

class TestGetQuestionsByTopic:
    def test_filters_by_topic(self, fake_seed_dir):
        # 我们 SAMPLE_QUESTIONS 里既有 agent 也有 rag
        agents = get_questions_by_topic("agent")
        assert all(q["topic"] == "agent" for q in agents)
        assert len(agents) >= 1

        rags = get_questions_by_topic("rag")
        assert all(q["topic"] == "rag" for q in rags)

    def test_returns_empty_for_unknown_topic(self, fake_seed_dir):
        assert get_questions_by_topic("nonexistent_topic") == []

    def test_handles_missing_files(self, tmp_path, monkeypatch):
        monkeypatch.setattr(svc, "SEED_DIR", tmp_path)
        assert get_questions_by_topic("any") == []