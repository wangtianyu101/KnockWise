"""
V3.7 题目同步服务测试（PR 3 · 5 测试点）
策略：mock 数据源（不连真 GitHub / HTTP）+ 单元测试
"""
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from datetime import datetime


# ════════════════════════════════════════════════════════════
# T1: 拉取 3 题 → 写入 DB
# ════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_sync_questions_creates_new():
    """T1: 从数据源拉 3 题 → 入库 3 题。"""
    from services.question_sync_service import sync_questions

    db = MagicMock()
    db.commit = AsyncMock()
    db.add = MagicMock()
    db.execute = AsyncMock()
    # execute().scalars().all() 返回空（无已存在 id）
    execute_result = MagicMock()
    execute_result.scalars.return_value.all.return_value = []
    execute_result.scalar_one_or_none.return_value = None
    db.execute.return_value = execute_result

    # Mock 数据源：返回 3 题
    source = MagicMock()
    source.fetch_questions = AsyncMock(return_value=[
        {
            "id": "agent_ext_001",
            "topic": "agent_architecture",
            "sub_topic": "react_agent",
            "difficulty": 3,
            "round": "round1",
            "question_text": "ReAct agent 的核心循环是什么？",
            "answer_key_points": ["Reasoning", "Acting", "Observation"],
            "followup_tree": {},
        },
        {
            "id": "agent_ext_002",
            "topic": "agent_architecture",
            "sub_topic": "plan_execute",
            "difficulty": 4,
            "round": "round1",
            "question_text": "Plan-and-Execute 与 ReAct 的区别？",
            "answer_key_points": ["Plan 阶段", "Execute 阶段", "Replan"],
            "followup_tree": {},
        },
        {
            "id": "agent_ext_003",
            "topic": "agent_architecture",
            "sub_topic": "multi_agent",
            "difficulty": 5,
            "round": "round2",
            "question_text": "多 agent 协作的通信模式有哪些？",
            "answer_key_points": ["黑板模型", "消息传递", "共享内存"],
            "followup_tree": {},
        },
    ])

    stats = await sync_questions(db, [source], dry_run=False)

    assert stats["fetched"] == 3
    assert stats["created"] == 3
    assert stats["skipped"] == 0
    assert stats["errors"] == 0
    assert db.add.call_count == 3
    db.commit.assert_called()


# ════════════════════════════════════════════════════════════
# T2: 字段映射（外部 schema → V1 Question）
# ════════════════════════════════════════════════════════════


def test_map_external_to_question_required_fields():
    """T2: 字段映射 — 必填字段缺失返回 None。"""
    from services.question_sync_service import map_external_to_question

    # 必填字段缺失
    result = map_external_to_question({"id": "x", "topic": "y"})  # 缺 sub_topic / question_text
    assert result is None


def test_map_external_to_question_optional_defaults():
    """T2: 字段映射 — 可选字段默认值（difficulty=3, round='round1'）。"""
    from services.question_sync_service import map_external_to_question

    raw = {
        "id": "agent_ext_004",
        "topic": "agent_architecture",
        "sub_topic": "tool_use",
        "question_text": "如何设计 tool 调用的错误重试？",
        # 没 difficulty / round / answer_key_points / followup_tree
    }
    result = map_external_to_question(raw)

    assert result is not None
    assert result["id"] == "agent_ext_004"
    assert result["topic"] == "agent_architecture"
    assert result["difficulty"] == 3  # 默认
    assert result["round"] == "round1"  # 默认
    assert result["answer_key_points"] == []  # 默认
    assert result["followup_tree"] == {}  # 默认


def test_map_external_to_question_full():
    """T2: 字段映射 — 完整字段都映射。"""
    from services.question_sync_service import map_external_to_question

    raw = {
        "id": "agent_ext_005",
        "topic": "agent_architecture",
        "sub_topic": "memory",
        "difficulty": 4,
        "round": "round2",
        "question_text": "长期记忆如何存储？",
        "answer_key_points": ["向量数据库", "摘要", "实体"],
        "followup_tree": {"q1": "answer1"},
    }
    result = map_external_to_question(raw)

    assert result["difficulty"] == 4
    assert result["round"] == "round2"
    assert result["answer_key_points"] == ["向量数据库", "摘要", "实体"]
    assert result["followup_tree"] == {"q1": "answer1"}


# ════════════════════════════════════════════════════════════
# T3: 去重（重复 id 不写）
# ════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_sync_questions_dedup_existing():
    """T3: 已存在的 id 跳过，不重复入库。"""
    from services.question_sync_service import sync_questions

    db = MagicMock()
    db.commit = AsyncMock()
    db.add = MagicMock()
    db.execute = AsyncMock()
    # execute() 第一次：SELECT 已有 id → 返回 2 个已存在
    # 注意：service 用 result.all()（不是 scalars().all()）· mock 路径要对齐
    existing_ids = ["agent_ext_001", "agent_ext_002"]
    execute_result = MagicMock()
    execute_result.all.return_value = [(x,) for x in existing_ids]
    execute_result.scalars.return_value.all.return_value = []
    execute_result.scalar_one_or_none.return_value = None
    db.execute.return_value = execute_result

    # Mock 数据源：返回 3 题，其中 2 个已存在
    source = MagicMock()
    source.fetch_questions = AsyncMock(return_value=[
        {"id": "agent_ext_001", "topic": "agent", "sub_topic": "x", "question_text": "已存在1"},
        {"id": "agent_ext_002", "topic": "agent", "sub_topic": "x", "question_text": "已存在2"},
        {"id": "agent_ext_003", "topic": "agent", "sub_topic": "x", "question_text": "新题"},
    ])

    stats = await sync_questions(db, [source], dry_run=False)

    assert stats["fetched"] == 3
    assert stats["created"] == 1  # 只 003 新写
    assert stats["skipped"] == 2  # 001/002 跳过
    assert db.add.call_count == 1


# ════════════════════════════════════════════════════════════
# T4: CLI 调用（mock subprocess）
# ════════════════════════════════════════════════════════════


def test_cli_module_imports():
    """T4: CLI 模块可正常 import。"""
    from cli import sync_questions
    assert hasattr(sync_questions, "main")
    assert hasattr(sync_questions, "build_default_sources")


# ════════════════════════════════════════════════════════════
# T5: API 端点
# ════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_api_admin_sync_questions_endpoint():
    """T5: API 端点 POST /api/admin/sync-questions → 返回 stats。"""
    from api.admin import SyncQuestionsRequest, SyncQuestionsResponse

    req = SyncQuestionsRequest(dry_run=True, collection_id="agent_foundation")
    assert req.dry_run is True
    assert req.collection_id == "agent_foundation"

    resp = SyncQuestionsResponse(fetched=5, created=3, skipped=2, errors=0)
    assert resp.fetched == 5
    assert resp.created == 3


def test_build_default_sources_constructs():
    """T5: 默认数据源工厂（按 env 构造）。"""
    from services.question_sync_service import (
        build_default_sources,
        LocalDataSource,
        GitHubDataSource,
        HTTPAPIDataSource,
    )
    import os

    # 清理
    for k in ["QUESTION_SYNC_GITHUB_REPO", "QUESTION_SYNC_HTTP_API"]:
        os.environ.pop(k, None)

    # 只 local
    sources = build_default_sources()
    assert len(sources) == 1
    assert isinstance(sources[0], LocalDataSource)

    # + GitHub
    os.environ["QUESTION_SYNC_GITHUB_REPO"] = "owner/repo"
    sources = build_default_sources()
    assert len(sources) == 2
    assert any(isinstance(s, GitHubDataSource) for s in sources)

    # + HTTP
    os.environ["QUESTION_SYNC_HTTP_API"] = "https://api.example.com"
    sources = build_default_sources()
    assert len(sources) == 3
    assert any(isinstance(s, HTTPAPIDataSource) for s in sources)

    # 清理
    os.environ.pop("QUESTION_SYNC_GITHUB_REPO", None)
    os.environ.pop("QUESTION_SYNC_HTTP_API", None)


def test_compute_question_hash():
    """T2 辅助：题目 hash 计算（去重验证用）。"""
    from services.question_sync_service import compute_question_hash

    q1 = {"id": "agent_001", "question_text": "什么是 ReAct？"}
    q2 = {"id": "agent_001", "question_text": "什么是 ReAct？"}  # 相同
    q3 = {"id": "agent_001", "question_text": "什么是 ReAct agent？"}  # 不同文本

    assert compute_question_hash(q1) == compute_question_hash(q2)
    assert compute_question_hash(q1) != compute_question_hash(q3)
