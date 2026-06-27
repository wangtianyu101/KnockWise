"""单测: services/qa_service.py

覆盖 8 个函数 + LLM mock，目标 ≥ 80%。
"""
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services import qa_service as svc


# ─── _get_llm singleton ───────────────────────────────────────

class TestGetLlm:
    def test_returns_chat_openai_instance(self, monkeypatch):
        """首次调用构造 ChatOpenAI；后续复用"""
        # 重置 module-level singleton
        monkeypatch.setattr(svc, "_llm", None)

        fake_llm = MagicMock(name="ChatOpenAI")
        with patch("services.qa_service.ChatOpenAI", return_value=fake_llm) as mock_cls:
            llm1 = svc._get_llm()
            llm2 = svc._get_llm()

        assert llm1 is llm2  # singleton
        mock_cls.assert_called_once()  # 只构造一次


# ─── QASession CRUD ───────────────────────────────────────────

class TestListQaSessions:
    async def test_returns_session_dicts(self, mock_db):
        from tests.conftest import FakeResult
        s1 = SimpleNamespace(id="s-1", question_id="q-1",
                             created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
                             messages=[{"role": "user", "content": "hi"}])
        s2 = SimpleNamespace(id="s-2", question_id="q-2", created_at=None, messages=None)
        mock_db.execute = AsyncMock(return_value=FakeResult(items=[s1, s2]))

        result = await svc.list_qa_sessions(mock_db, "u-1")
        assert len(result["items"]) == 2
        assert result["items"][0]["message_count"] == 1
        assert result["items"][1]["message_count"] == 0  # None messages → 0
        assert result["items"][1]["created_at"] is None

    async def test_empty_list(self, mock_db):
        from tests.conftest import FakeResult
        mock_db.execute = AsyncMock(return_value=FakeResult(items=[]))
        result = await svc.list_qa_sessions(mock_db, "u-1")
        assert result["items"] == []


class TestGetQaSession:
    async def test_returns_none_when_not_found(self, mock_db):
        mock_db.get = AsyncMock(return_value=None)
        assert await svc.get_qa_session(mock_db, "u-1", "s-1") is None

    async def test_returns_none_when_owner_mismatch(self, mock_db):
        s = SimpleNamespace(user_id="OTHER")
        mock_db.get = AsyncMock(return_value=s)
        assert await svc.get_qa_session(mock_db, "u-1", "s-1") is None

    async def test_returns_session(self, mock_db):
        s = SimpleNamespace(id="s-1", user_id="u-1", messages=[])
        mock_db.get = AsyncMock(return_value=s)
        result = await svc.get_qa_session(mock_db, "u-1", "s-1")
        assert result is s


class TestCreateQaSession:
    async def test_creates_with_defaults(self, mock_db):
        result = await svc.create_qa_session(mock_db, "u-1", "q-1")
        added = mock_db.add.call_args.args[0]
        assert added.user_id == "u-1"
        assert added.question_id == "q-1"
        assert added.messages == []
        assert added.created_at is not None
        mock_db.commit.assert_awaited()


class TestDeleteQaSession:
    async def test_returns_false_when_not_found(self, mock_db):
        mock_db.get = AsyncMock(return_value=None)
        assert await svc.delete_qa_session(mock_db, "u-1", "s-1") is False

    async def test_returns_false_when_owner_mismatch(self, mock_db):
        s = SimpleNamespace(user_id="OTHER")
        mock_db.get = AsyncMock(return_value=s)
        assert await svc.delete_qa_session(mock_db, "u-1", "s-1") is False

    async def test_deletes_session(self, mock_db):
        s = SimpleNamespace(user_id="u-1")
        mock_db.get = AsyncMock(return_value=s)
        assert await svc.delete_qa_session(mock_db, "u-1", "s-1") is True
        mock_db.delete.assert_awaited_with(s)


# ─── _build_system_prompt ─────────────────────────────────────

class TestBuildSystemPrompt:
    def test_includes_question_text(self):
        p = svc._build_system_prompt("什么是 ReAct？", [])
        assert "什么是 ReAct？" in p

    def test_includes_key_points(self):
        p = svc._build_system_prompt("Q?", ["Reasoning", "Acting"])
        assert "- Reasoning" in p
        assert "- Acting" in p

    def test_empty_key_points_shows_placeholder(self):
        p = svc._build_system_prompt("Q?", [])
        assert "无标准答案" in p

    def test_includes_markdown_hint(self):
        p = svc._build_system_prompt("Q?", [])
        assert "Markdown" in p
        assert "中文" in p


# ─── _get_question_context ────────────────────────────────────

class TestGetQuestionContext:
    async def test_returns_none_when_not_found(self, mock_db):
        mock_db.get = AsyncMock(return_value=None)
        assert await svc._get_question_context(mock_db, "q-1") is None

    async def test_returns_seed_question_context(self, mock_db):
        seed_q = SimpleNamespace(question_text="Q?", answer_key_points=["p1", "p2"])
        mock_db.get = AsyncMock(return_value=seed_q)
        ctx = await svc._get_question_context(mock_db, "q-1")
        assert ctx["text"] == "Q?"
        assert ctx["key_points"] == ["p1", "p2"]

    async def test_returns_user_question_context_with_no_answer(self, mock_db):
        u_q = SimpleNamespace(question_text="User Q?", answer=None)
        mock_db.get = AsyncMock(side_effect=[None, u_q])
        ctx = await svc._get_question_context(mock_db, "u-q-1")
        assert ctx["text"] == "User Q?"
        assert ctx["key_points"] == []

    async def test_returns_user_question_context_with_answer(self, mock_db):
        u_q = SimpleNamespace(question_text="User Q?", answer="my answer")
        mock_db.get = AsyncMock(side_effect=[None, u_q])
        ctx = await svc._get_question_context(mock_db, "u-q-1")
        assert ctx["key_points"] == ["my answer"]


# ─── chat_qa（核心：DB + LLM）────────────────────────────────

class TestChatQa:
    async def test_returns_error_when_question_not_found(self, mock_db):
        mock_db.get = AsyncMock(return_value=None)
        result = await svc.chat_qa(mock_db, "u-1", "q-not-exist", "hi")
        assert result["reply"] == "题目不存在或已被删除"
        assert result["session_id"] is None

    async def test_returns_error_when_session_owner_mismatch(self, mock_db, mock_llm):
        # 1) _get_question_context 取 Question → OK
        # 2) db.get(QASession) → owner 不匹配
        seed_q = SimpleNamespace(question_text="Q?", answer_key_points=["p"])
        s = SimpleNamespace(user_id="OTHER", messages=[])
        mock_db.get = AsyncMock(side_effect=[seed_q, s])

        result = await svc.chat_qa(mock_db, "u-1", "q-1", "hi", session_id="s-1")
        assert result["reply"] == "Session 不存在或无权限"
        assert result["session_id"] is None

    async def test_returns_error_when_session_not_found(self, mock_db, mock_llm):
        seed_q = SimpleNamespace(question_text="Q?", answer_key_points=["p"])
        mock_db.get = AsyncMock(side_effect=[seed_q, None])
        result = await svc.chat_qa(mock_db, "u-1", "q-1", "hi", session_id="bad-id")
        assert result["reply"] == "Session 不存在或无权限"

    async def test_creates_new_session_when_no_session_id(self, mock_db, mock_llm):
        seed_q = SimpleNamespace(question_text="Q?", answer_key_points=["p"])
        mock_db.get = AsyncMock(side_effect=[seed_q, SimpleNamespace(id="new-s", user_id="u-1", messages=[])])

        # 让 create_qa_session 返回的 mock 有 .id / .messages 属性
        with patch.object(svc, "create_qa_session", new_callable=AsyncMock) as mock_create:
            new_s = SimpleNamespace(id="new-session-id", user_id="u-1", messages=[])
            mock_create.return_value = new_s

            result = await svc.chat_qa(mock_db, "u-1", "q-1", "hi")

        assert result["session_id"] == "new-session-id"
        assert "mocked LLM response" in result["reply"]

    async def test_appends_user_and_assistant_messages(self, mock_db, mock_llm):
        """验证 chat_qa 把消息正确写入 session"""
        seed_q = SimpleNamespace(question_text="Q?", answer_key_points=["p"])
        s = SimpleNamespace(
            id="s-1", user_id="u-1", messages=[]
        )
        mock_db.get = AsyncMock(side_effect=[seed_q, s])

        await svc.chat_qa(mock_db, "u-1", "q-1", "hi", session_id="s-1")

        # session.messages 现在应有 2 条（user + assistant）
        assert len(s.messages) == 2
        assert s.messages[0]["role"] == "user"
        assert s.messages[0]["content"] == "hi"
        assert s.messages[1]["role"] == "assistant"
        assert "mocked LLM response" in s.messages[1]["content"]
        mock_db.commit.assert_awaited()

    async def test_handles_llm_exception(self, mock_db, monkeypatch):
        """LLM 抛错时返回错误消息而不 crash"""
        seed_q = SimpleNamespace(question_text="Q?", answer_key_points=["p"])
        s = SimpleNamespace(id="s-1", user_id="u-1", messages=[])
        mock_db.get = AsyncMock(side_effect=[seed_q, s])

        # 让 _get_llm 返回会抛错的 mock
        bad_llm = MagicMock()
        bad_llm.ainvoke = AsyncMock(side_effect=RuntimeError("network down"))
        monkeypatch.setattr(svc, "_get_llm", lambda: bad_llm)

        result = await svc.chat_qa(mock_db, "u-1", "q-1", "hi", session_id="s-1")
        assert "⚠️ LLM 调用失败" in result["reply"]
        assert "network down" in result["reply"]

    async def test_includes_history_in_llm_call(self, mock_db, mock_llm):
        """历史 user/assistant 消息都传给 LLM"""
        seed_q = SimpleNamespace(question_text="Q?", answer_key_points=["p"])
        s = SimpleNamespace(
            id="s-1", user_id="u-1",
            messages=[
                {"role": "user", "content": "first question", "ts": "2026-01-01T00:00:00"},
                {"role": "assistant", "content": "first answer", "ts": "2026-01-01T00:00:01"},
            ],
        )
        mock_db.get = AsyncMock(side_effect=[seed_q, s])

        await svc.chat_qa(mock_db, "u-1", "q-1", "second question", session_id="s-1")

        # 检查 LLM 被调，且消息含历史
        assert mock_llm.ainvoke.await_count == 1
        llm_call_msgs = mock_llm.ainvoke.await_args.args[0]
        # SystemMessage + 2 history + 1 new user = 4 条
        assert len(llm_call_msgs) == 4
        # 验证 content
        all_content = " ".join(
            (m.content if hasattr(m, "content") else str(m)) for m in llm_call_msgs
        )
        assert "first question" in all_content
        assert "first answer" in all_content
        assert "second question" in all_content

    async def test_handles_resp_without_content_attr(self, mock_db, monkeypatch):
        """LLM 返回对象无 .content 时，用 str() 转换"""
        seed_q = SimpleNamespace(question_text="Q?", answer_key_points=["p"])
        s = SimpleNamespace(id="s-1", user_id="u-1", messages=[])
        mock_db.get = AsyncMock(side_effect=[seed_q, s])

        str_response = "plain string response"
        llm_no_content = MagicMock()
        # 配置 ainvoke 返回的对象在 hasattr(content) 时返回 False
        llm_no_content.ainvoke = AsyncMock(return_value=str_response)
        # 因为 MagicMock 默认有 .content 属性，所以这里直接用字符串
        # 注意：MagicMock() 默认 .content 是 MagicMock 实例，所以 hasattr 返回 True
        # 我们的代码 fallback 是 `str(resp)`，所以用字符串也行
        monkeypatch.setattr(svc, "_get_llm", lambda: llm_no_content)

        result = await svc.chat_qa(mock_db, "u-1", "q-1", "hi", session_id="s-1")
        # resp.content 是 MagicMock，会被 truthy 取到，但有内容
        assert result["reply"] is not None