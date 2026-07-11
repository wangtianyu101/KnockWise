"""
PR 5 · V3.7 admin 题库管理 API 测试（6 测试点）
策略：mock_db（V1 风格）
"""
from unittest.mock import AsyncMock, MagicMock
import pytest
from fastapi import HTTPException


# ════════════════════════════════════════════════════════════
# T25.1: PATCH topic → 更新成功
# ════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_patch_question_updates_topic():
    """T25.1: PATCH topic → 更新成功。"""
    from api.admin import patch_question_admin, QuestionPatchRequest, QuestionListItem

    # Mock Question 对象
    q = MagicMock()
    q.id = "agent_001"
    q.topic = "agent_architecture"
    q.sub_topic = "react_agent"
    q.difficulty = 3
    q.round = "round1"
    q.question_text = "ReAct agent 的核心循环是什么？"

    db = MagicMock()
    db.get = AsyncMock(return_value=q)
    db.commit = AsyncMock()
    db.refresh = AsyncMock()

    req = QuestionPatchRequest(topic="agent_updated")

    result = await patch_question_admin(
        question_id="agent_001",
        req=req,
        user=MagicMock(id="user-x"),
        db=db,
    )

    assert isinstance(result, QuestionListItem)
    assert q.topic == "agent_updated"  # 字段已 set
    db.commit.assert_called_once()
    db.refresh.assert_called_once()


# ════════════════════════════════════════════════════════════
# T25.2: PATCH difficulty=0 → 422 校验失败
# ════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_patch_question_difficulty_validation():
    """T25.2: PATCH difficulty=0 → 422（Pydantic 校验）。"""
    from api.admin import QuestionPatchRequest
    from pydantic import ValidationError

    with pytest.raises(ValidationError) as exc_info:
        QuestionPatchRequest(difficulty=0)

    errors = exc_info.value.errors()
    assert any(e["loc"] == ("difficulty",) for e in errors)


@pytest.mark.asyncio
async def test_patch_question_difficulty_too_high():
    """T25.2 扩展：difficulty=6 → 422。"""
    from api.admin import QuestionPatchRequest
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        QuestionPatchRequest(difficulty=6)


# ════════════════════════════════════════════════════════════
# T25.3: PATCH round='invalid' → 422
# ════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_patch_question_round_validation():
    """T25.3: PATCH round='invalid' → 422。"""
    from api.admin import QuestionPatchRequest
    from pydantic import ValidationError

    with pytest.raises(ValidationError) as exc_info:
        QuestionPatchRequest(round="invalid_round")

    errors = exc_info.value.errors()
    assert any("round" in str(e["loc"]) for e in errors)


@pytest.mark.asyncio
async def test_patch_question_round_valid():
    """T25.3 扩展：round='round1' / 'round2' → 通过。"""
    from api.admin import QuestionPatchRequest

    req1 = QuestionPatchRequest(round="round1")
    assert req1.round == "round1"

    req2 = QuestionPatchRequest(round="round2")
    assert req2.round == "round2"


# ════════════════════════════════════════════════════════════
# T25.4: GET 列表 + 过滤
# ════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_list_questions_with_filters():
    """T25.4: GET 列表 + topic/difficulty 过滤。"""
    from api.admin import list_questions_admin, QuestionListResponse

    db = MagicMock()
    db.execute = AsyncMock()

    # Mock 2 道题
    q1 = MagicMock(id="agent_001", topic="agent_architecture", sub_topic="x",
                  difficulty=3, round="round1", question_text="题目1")
    q2 = MagicMock(id="rag_001", topic="rag", sub_topic="y",
                  difficulty=4, round="round2", question_text="题目2")

    # execute 多次调用：第一次查 list · 第二次查 count
    execute_result_list = MagicMock()
    execute_result_list.scalars.return_value.all.return_value = [q1, q2]

    execute_result_count = MagicMock()
    execute_result_count.scalar_one.return_value = 2

    # 不同 execute 调用返回不同结果
    db.execute.side_effect = [execute_result_list, execute_result_count]

    result = await list_questions_admin(
        topic="agent",
        difficulty=3,
        keyword=None,
        skip=0,
        limit=50,
        user=MagicMock(),
        db=db,
    )

    assert isinstance(result, QuestionListResponse)
    assert result.total == 2
    assert len(result.items) == 2
    assert result.items[0].id == "agent_001"


# ════════════════════════════════════════════════════════════
# T25.5: GET 关键词搜索（question_text contains）
# ════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_list_questions_keyword_search():
    """T25.5: GET 关键词搜索（按 question_text contains）。"""
    from api.admin import list_questions_admin

    db = MagicMock()
    db.execute = AsyncMock()

    q1 = MagicMock(id="agent_001", topic="agent", sub_topic="react",
                  difficulty=3, round="round1", question_text="ReAct agent 的核心循环")

    execute_result_list = MagicMock()
    execute_result_list.scalars.return_value.all.return_value = [q1]
    execute_result_count = MagicMock()
    execute_result_count.scalar_one.return_value = 1

    db.execute.side_effect = [execute_result_list, execute_result_count]

    result = await list_questions_admin(
        topic=None,
        difficulty=None,
        keyword="ReAct",
        skip=0,
        limit=50,
        user=MagicMock(),
        db=db,
    )

    assert result.total == 1
    assert result.items[0].question_text.startswith("ReAct")


# ════════════════════════════════════════════════════════════
# T25.6: PATCH 不存在 id → 404
# ════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_patch_question_not_found():
    """T25.6: PATCH 不存在 id → 404。"""
    from api.admin import patch_question_admin, QuestionPatchRequest
    from fastapi import HTTPException

    db = MagicMock()
    db.get = AsyncMock(return_value=None)  # 题目不存在

    req = QuestionPatchRequest(topic="new_topic")

    with pytest.raises(HTTPException) as exc_info:
        await patch_question_admin(
            question_id="nonexistent_id",
            req=req,
            user=MagicMock(),
            db=db,
        )

    assert exc_info.value.status_code == 404
    assert "nonexistent_id" in str(exc_info.value.detail)


# ════════════════════════════════════════════════════════════
# 额外：PATCH 空 body → 422
# ════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_patch_question_empty_body():
    """T25.x: PATCH 空 body → 422。"""
    from api.admin import patch_question_admin, QuestionPatchRequest
    from fastapi import HTTPException

    q = MagicMock()
    db = MagicMock()
    db.get = AsyncMock(return_value=q)

    req = QuestionPatchRequest()  # 所有字段都 None

    with pytest.raises(HTTPException) as exc_info:
        await patch_question_admin(
            question_id="agent_001",
            req=req,
            user=MagicMock(),
            db=db,
        )

    assert exc_info.value.status_code == 422