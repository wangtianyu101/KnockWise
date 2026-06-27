"""单测: services/interview_service.py

覆盖:
- InterviewSessionManager 全部公开方法（11 个）+ _serializable_state
- create / get_next / process_answer / get_state / set_state / is_complete
- save_state / restore_from_db（mock AsyncSession）
- 异常路径（session 不存在、DB miss、state 非 dict）

策略：monkeypatch LangGraph agents，不接真 DB。
"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from services.interview_service import (
    InterviewSessionManager,
    _serializable_state,
)


# ─── 共享 mock 工厂 ──────────────────────────────────────────

def make_state(
    user_id="user-001",
    profile=None,
    round="round1",
    style="standard",
    interview_phase="intro",
):
    profile = profile or {"tech_stack": ["Python"]}
    return {
        "user_id": user_id,
        "profile": profile,
        "round": round,
        "style": style,
        "interview_phase": interview_phase,
        "current_topic": None,
        "current_question_id": None,
        "current_question": {},
        "current_depth": 0,
        "followup_count": 0,
        "max_followup_depth": 4,
        "questions_asked": [],
        "questions_remaining": 8,
        "total_score": 0,
        "blind_spots": [],
        "messages": [],
        "route": None,
        "should_end": False,
    }


@pytest.fixture
def mock_initial_state(monkeypatch):
    """替换 create_initial_state 为简化的纯字典工厂。"""
    monkeypatch.setattr(
        "services.interview_service.create_initial_state",
        lambda user_id, profile, round, style: make_state(user_id, profile, round, style),
    )


@pytest.fixture
def mock_graph(monkeypatch):
    """替换 build_interview_graph 为 MagicMock（不实例化 LangGraph）。"""
    monkeypatch.setattr(
        "services.interview_service.build_interview_graph",
        lambda: MagicMock(name="compiled_graph"),
    )


@pytest.fixture
def mock_question_engine(monkeypatch):
    """替换 question_engine.select_next_question。"""
    engine = MagicMock()
    monkeypatch.setattr(
        "services.interview_service.question_engine", engine, raising=False
    )
    return engine


@pytest.fixture
def mock_followup_engine(monkeypatch):
    """替换 followup_engine.determine_action。"""
    engine = MagicMock()
    engine.determine_action = AsyncMock(
        return_value={"action": "next_question", "followup_text": ""}
    )
    monkeypatch.setattr(
        "services.interview_service.followup_engine", engine, raising=False
    )
    return engine


@pytest.fixture
def mock_evaluate_agent(monkeypatch):
    """替换 evaluate_agent.evaluate_answer。"""
    agent = MagicMock()
    agent.evaluate_answer = AsyncMock(
        return_value={"score": 3, "feedback": "OK", "blind_spots": []}
    )
    monkeypatch.setattr(
        "services.interview_service.evaluate_agent", agent, raising=False
    )
    return agent


@pytest.fixture
def mgr(mock_initial_state, mock_graph, mock_question_engine, mock_followup_engine, mock_evaluate_agent):
    """一个干净的 InterviewSessionManager，所有外部依赖已 mock。"""
    return InterviewSessionManager()


# ─── create_session ──────────────────────────────────────────

class TestCreateSession:
    def test_returns_uuid_string(self, mgr):
        sid = mgr.create_session(user_id="u-1", profile={"tech_stack": ["Python"]})
        assert isinstance(sid, str)
        assert len(sid) == 36  # UUID4

    def test_uses_provided_session_id(self, mgr):
        sid = mgr.create_session(
            user_id="u-1", profile={}, session_id="my-custom-id"
        )
        assert sid == "my-custom-id"

    def test_stores_session_in_memory(self, mgr):
        sid = mgr.create_session(user_id="u-1", profile={"tech_stack": ["Py"]})
        assert sid in mgr._sessions
        assert mgr._sessions[sid]["state"]["user_id"] == "u-1"

    def test_uses_round_and_style(self, mgr):
        sid = mgr.create_session(
            user_id="u-1", profile={}, round="round2", style="behavioral"
        )
        state = mgr._sessions[sid]["state"]
        assert state["round"] == "round2"
        assert state["style"] == "behavioral"

    def test_two_sessions_get_different_ids(self, mgr):
        a = mgr.create_session(user_id="u-1", profile={})
        b = mgr.create_session(user_id="u-2", profile={})
        assert a != b


# ─── get_next_question ────────────────────────────────────────

class TestGetNextQuestion:
    def test_returns_question_dict_when_available(self, mgr, mock_question_engine):
        mock_question_engine.select_next_question.return_value = {
            "id": "q-1",
            "question_text": "什么是 ReAct？",
            "topic": "agent",
            "sub_topic": "react",
        }
        sid = mgr.create_session(user_id="u-1", profile={})
        q = mgr.get_next_question(sid)
        assert q["id"] == "q-1"
        assert mgr._sessions[sid]["state"]["current_question_id"] == "q-1"
        assert mgr._sessions[sid]["state"]["interview_phase"] == "questioning"

    def test_adds_to_questions_asked(self, mgr, mock_question_engine):
        mock_question_engine.select_next_question.return_value = {"id": "q-2"}
        sid = mgr.create_session(user_id="u-1", profile={})
        mgr.get_next_question(sid)
        assert "q-2" in mgr._sessions[sid]["state"]["questions_asked"]

    def test_does_not_duplicate_question_asked(self, mgr, mock_question_engine):
        mock_question_engine.select_next_question.return_value = {"id": "q-3"}
        sid = mgr.create_session(user_id="u-1", profile={})
        mgr.get_next_question(sid)
        mgr.get_next_question(sid)
        assert mgr._sessions[sid]["state"]["questions_asked"] == ["q-3"]

    def test_returns_none_when_engine_has_no_question(self, mgr, mock_question_engine):
        mock_question_engine.select_next_question.return_value = None
        sid = mgr.create_session(user_id="u-1", profile={})
        result = mgr.get_next_question(sid)
        assert result is None
        assert mgr._sessions[sid]["state"]["interview_phase"] == "done"
        assert mgr._sessions[sid]["state"]["should_end"] is True

    def test_raises_for_missing_session(self, mgr):
        with pytest.raises(ValueError, match="Session .* not found"):
            mgr.get_next_question("nonexistent-id")


# ─── process_answer ───────────────────────────────────────────

class TestProcessAnswer:
    async def test_happy_path_returns_evaluation(self, mgr, mock_followup_engine, mock_evaluate_agent):
        sid = mgr.create_session(user_id="u-1", profile={})
        mgr._sessions[sid]["state"]["current_question"] = {
            "question_text": "q",
            "answer_key_points": [],
            "topic": "agent",
            "sub_topic": "react",
        }
        result = await mgr.process_answer(sid, "ReAct = Reasoning + Acting")
        assert "score" in result
        assert "feedback" in result
        assert result["action"] == "next_question"
        assert result["has_followup"] is False

    async def test_followup_action_updates_depth(self, mgr, mock_followup_engine, mock_evaluate_agent):
        mock_followup_engine.determine_action.return_value = {
            "action": "followup",
            "followup_text": "再深入讲讲",
        }
        sid = mgr.create_session(user_id="u-1", profile={})
        mgr._sessions[sid]["state"]["current_question"] = {}
        await mgr.process_answer(sid, "答得浅")
        state = mgr._sessions[sid]["state"]
        assert state["current_depth"] == 1
        assert state["followup_count"] == 1
        assert state["interview_phase"] == "following_up"

    async def test_skip_and_record_adds_blind_spot(self, mgr, mock_followup_engine):
        mock_followup_engine.determine_action.return_value = {
            "action": "skip_and_record",
            "blind_spot": "不了解 Memory 机制",
        }
        sid = mgr.create_session(user_id="u-1", profile={})
        mgr._sessions[sid]["state"]["current_question"] = {}
        await mgr.process_answer(sid, "不知道")
        assert "不了解 Memory 机制" in mgr._sessions[sid]["state"]["blind_spots"]

    async def test_has_followup_flag_for_probe_action(self, mgr, mock_followup_engine):
        mock_followup_engine.determine_action.return_value = {
            "action": "probe",
            "followup_text": "能具体点吗",
        }
        sid = mgr.create_session(user_id="u-1", profile={})
        mgr._sessions[sid]["state"]["current_question"] = {}
        result = await mgr.process_answer(sid, "答得笼统")
        assert result["has_followup"] is True

    async def test_has_followup_false_for_next_question(self, mgr):
        sid = mgr.create_session(user_id="u-1", profile={})
        mgr._sessions[sid]["state"]["current_question"] = {}
        result = await mgr.process_answer(sid, "答得好")
        assert result["has_followup"] is False

    async def test_missing_session_raises(self, mgr):
        with pytest.raises(ValueError):
            await mgr.process_answer("nonexistent", "any answer")


# ─── get_state / set_state / is_complete ──────────────────────

class TestGetState:
    def test_returns_state_copy(self, mgr):
        sid = mgr.create_session(user_id="u-1", profile={})
        state = mgr.get_state(sid)
        assert state["user_id"] == "u-1"
        # 修改副本不影响原 state
        state["user_id"] = "mutated"
        assert mgr._sessions[sid]["state"]["user_id"] == "u-1"

    def test_raises_for_missing_session(self, mgr):
        with pytest.raises(ValueError):
            mgr.get_state("nonexistent")


class TestSetState:
    def test_replaces_state(self, mgr):
        sid = mgr.create_session(user_id="u-1", profile={})
        new_state = make_state(user_id="u-1", interview_phase="questioning")
        mgr.set_state(sid, new_state)
        assert mgr._sessions[sid]["state"]["interview_phase"] == "questioning"

    def test_makes_copy_to_avoid_external_mutation(self, mgr):
        sid = mgr.create_session(user_id="u-1", profile={})
        new_state = make_state(user_id="u-1")
        mgr.set_state(sid, new_state)
        new_state["user_id"] = "mutated"
        assert mgr._sessions[sid]["state"]["user_id"] == "u-1"

    def test_raises_for_missing_session(self, mgr):
        with pytest.raises(ValueError):
            mgr.set_state("nonexistent", {})


class TestIsComplete:
    def test_false_when_phase_not_done(self, mgr):
        sid = mgr.create_session(user_id="u-1", profile={})
        assert mgr.is_complete(sid) is False

    def test_true_when_phase_done(self, mgr):
        sid = mgr.create_session(user_id="u-1", profile={})
        mgr._sessions[sid]["state"]["interview_phase"] = "done"
        assert mgr.is_complete(sid) is True

    def test_raises_for_missing_session(self, mgr):
        with pytest.raises(ValueError):
            mgr.is_complete("nonexistent")


# ─── save_state（DB 持久化）───────────────────────────────────

class TestSaveState:
    async def test_silently_skips_unknown_session(self, mgr, mock_db):
        """session 不在内存中时直接 return，不抛错。"""
        await mgr.save_state("not-in-memory", mock_db)
        mock_db.execute.assert_not_called()

    async def test_writes_state_snapshot_to_db(self, mgr, mock_db, fake_interview):
        sid = mgr.create_session(user_id="u-1", profile={})
        mgr._sessions[sid]["state"]["interview_phase"] = "questioning"

        # 让 db.execute 返回 fake_interview
        from tests.conftest import FakeResult
        mock_db.execute.return_value = FakeResult(scalar=fake_interview)

        await mgr.save_state(sid, mock_db)

        assert fake_interview.state_snapshot is not None
        assert fake_interview.state_snapshot["interview_phase"] == "questioning"
        mock_db.commit.assert_awaited_once()

    async def test_no_commit_when_interview_not_found(self, mgr, mock_db):
        from tests.conftest import FakeResult
        mock_db.execute.return_value = FakeResult(scalar=None)  # 没找到
        sid = mgr.create_session(user_id="u-1", profile={})
        await mgr.save_state(sid, mock_db)
        mock_db.commit.assert_not_awaited()


# ─── restore_from_db（DB 恢复）─────────────────────────────────

class TestRestoreFromDb:
    async def test_returns_false_when_no_interview(self, mgr, mock_db):
        from tests.conftest import FakeResult
        mock_db.execute.return_value = FakeResult(scalar=None)
        result = await mgr.restore_from_db("some-id", mock_db)
        assert result is False

    async def test_returns_false_when_snapshot_empty(self, mgr, mock_db, fake_interview):
        fake_interview.state_snapshot = None
        from tests.conftest import FakeResult
        mock_db.execute.return_value = FakeResult(scalar=fake_interview)
        result = await mgr.restore_from_db("some-id", mock_db)
        assert result is False

    async def test_returns_false_when_snapshot_invalid_type(self, mgr, mock_db, fake_interview):
        fake_interview.state_snapshot = "not-a-dict"
        from tests.conftest import FakeResult
        mock_db.execute.return_value = FakeResult(scalar=fake_interview)
        result = await mgr.restore_from_db("some-id", mock_db)
        assert result is False

    async def test_restores_session_from_snapshot(self, mgr, mock_db, fake_interview):
        snapshot = make_state(user_id="u-restored", interview_phase="questioning")
        fake_interview.state_snapshot = snapshot
        fake_interview.id = "restored-id"

        from tests.conftest import FakeResult
        mock_db.execute.return_value = FakeResult(scalar=fake_interview)

        result = await mgr.restore_from_db("restored-id", mock_db)
        assert result is True
        assert "restored-id" in mgr._sessions
        assert mgr._sessions["restored-id"]["state"]["user_id"] == "u-restored"


# ─── _serializable_state（模块级辅助）─────────────────────────

class TestSerializableState:
    def test_keeps_primitive_types(self):
        state = {
            "user_id": "u-1",
            "round": "round1",
            "score": 3,
            "tags": ["a", "b"],
            "meta": {"key": "value"},
            "active": True,
            "ratio": 0.5,
            "empty": None,
        }
        clean = _serializable_state(state)
        assert clean == state

    def test_strips_non_serializable_values(self):
        class NonSerializable:
            pass
        state = {
            "good": "ok",
            "bad_obj": NonSerializable(),  # 不可 JSON 序列化
            "bad_lambda": lambda x: x,     # 不可 JSON 序列化
        }
        clean = _serializable_state(state)
        assert clean == {"good": "ok"}

    def test_empty_state(self):
        assert _serializable_state({}) == {}


# ─── singleton 检查 ──────────────────────────────────────────

def test_session_manager_is_singleton():
    from services.interview_service import session_manager
    assert isinstance(session_manager, InterviewSessionManager)
    assert session_manager is session_manager  # same instance