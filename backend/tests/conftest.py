"""共享 pytest fixtures.

约定：
- mock_db    → Mock AsyncSession；模拟链式调用 db.execute(...) → result.scalars().all() 等
- mock_cache → Mock Redis 单例（替换 core.cache.cache）
- mock_llm   → Mock ChatOpenAI（给 qa_service 等 LLM 依赖用）

使用：
    async def test_x(mock_db, mock_cache):
        mock_db.execute.return_value.scalars.return_value.all.return_value = [...]
        result = await service.some_func(mock_db, ...)
        assert result == ...
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest


# ─── DB Mock ──────────────────────────────────────────

class FakeResult:
    """模拟 sqlalchemy Result 对象，支持链式调用。

    用法：
        result = FakeResult(items=[...], scalar=42)
        mock_db.execute.return_value = result

        # 然后 service 里：
        items = result.scalars().all()         # → items
        one = result.scalar_one_or_none()      # → scalar
        first = result.scalars().first()       # → items[0]
    """
    def __init__(self, items=None, scalar=None, row=None):
        self._items = items if items is not None else []
        self._scalar = scalar
        self._row = row

    def scalars(self):
        return self

    def first(self):
        return self._items[0] if self._items else None

    def all(self):
        return list(self._items)

    def scalar(self):
        """SQLAlchemy Result.scalar() — 返回第一行第一列（通常是 ._scalar 或 ._items[0]）"""
        if self._scalar is not None:
            return self._scalar
        if self._items:
            # 让 row/tuple 的第一列返回
            first = self._items[0]
            if isinstance(first, tuple):
                return first[0]
            return first
        return None

    def scalar_one_or_none(self):
        return self._scalar

    def one_or_none(self):
        return self._row

    def rows(self):
        return [self._row] if self._row else []


@pytest.fixture
def mock_db() -> AsyncMock:
    """Mock AsyncSession。直接赋值给 service 函数 db 参数。

    默认行为：
    - db.execute(...) → FakeResult(items=[])  （空结果）
    - db.add(obj)    → MagicMock              （不报错）
    - db.commit()    → AsyncMock              （awaitable）
    - db.refresh()   → AsyncMock
    - db.delete()    → AsyncMock
    """
    db = AsyncMock()
    db.execute = AsyncMock(return_value=FakeResult(items=[]))
    db.get = AsyncMock(return_value=None)
    db.add = MagicMock()
    db.delete = AsyncMock()
    db.commit = AsyncMock()
    db.flush = AsyncMock()
    db.refresh = AsyncMock()
    db.close = AsyncMock()
    return db


# ─── Cache Mock ────────────────────────────────────────

@pytest.fixture
def mock_cache(monkeypatch):
    """Mock Redis cache 单例。替换 core.cache.cache。

    默认行为：
    - cache.get(key)    → None（cache miss）
    - cache.set(key, v) → True
    - cache.delete(key) → True
    """
    cache = MagicMock()
    cache.get = AsyncMock(return_value=None)
    cache.set = AsyncMock(return_value=True)
    cache.delete = AsyncMock(return_value=True)
    cache.delete_pattern = AsyncMock(return_value=True)
    cache.healthy = True
    monkeypatch.setattr("core.cache.cache", cache)
    # 兼容 services 里可能直接 import 的情况
    monkeypatch.setattr("services.question_bank_service.cache", cache, raising=False)
    monkeypatch.setattr("services.learning_progress_service.cache", cache, raising=False)
    monkeypatch.setattr("services.profile_settlement_service.cache", cache, raising=False)
    monkeypatch.setattr("services.summary_service.cache", cache, raising=False)
    return cache


# ─── LLM Mock ──────────────────────────────────────────

@pytest.fixture
def mock_llm(monkeypatch):
    """Mock ChatOpenAI 实例。给需要 LLM 调用的 service 用。

    默认行为：
    - llm.ainvoke(messages) → MagicMock(content="mocked LLM response")
    """
    from langchain_core.messages import AIMessage

    llm = MagicMock()
    llm.ainvoke = AsyncMock(return_value=AIMessage(content="mocked LLM response"))
    monkeypatch.setattr("services.qa_service._get_llm", lambda: llm)
    return llm


# ─── 通用辅助 ──────────────────────────────────────────

@pytest.fixture
def fake_user():
    """Mock User 对象（id / email / display_name）"""
    user = MagicMock()
    user.id = "user-uuid-001"
    user.email = "test@example.com"
    user.display_name = "test_user"
    return user


@pytest.fixture
def fake_interview():
    """Mock Interview ORM 对象"""
    interview = MagicMock()
    interview.id = "interview-uuid-001"
    interview.user_id = "user-uuid-001"
    interview.profile_id = "profile-uuid-001"
    interview.round = "round1"
    interview.style = "standard"
    interview.status = "in_progress"
    interview.state_snapshot = None
    interview.started_at = None
    interview.ended_at = None
    interview.total_questions = 0
    interview.overall_score = None
    interview.is_favorite = False
    return interview


@pytest.fixture
def fake_question():
    """Mock Question ORM 对象"""
    q = MagicMock()
    q.id = "q-uuid-001"
    q.topic = "agent_architecture"
    q.sub_topic = "streaming"
    q.difficulty = 3
    q.text = "Agent 流式输出和普通 LLM 有什么不同？"
    q.followup_tree = {"type": "answer_router", "branches": []}
    q.tags = "[]"
    q.source = "seed"
    q.created_by = None
    return q

# ─── 限流 fixture（slowapi 在测试中禁用）───────────────────────

import pytest
from slowapi import Limiter
from slowapi.util import get_remote_address


@pytest.fixture(autouse=True)
def reset_limiter():
    """每个测试前清空 slowapi 限流状态，避免串行测试触发限流。"""
    from core.limiter import limiter
    limiter.reset()
    yield
    limiter.reset()
