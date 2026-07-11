"""
V3.1 精选题单 CollectionService 单元测试（PR 2 · 重定义后）
策略：用 mock_db 模拟（V1 风格），避免 aiomysql + pytest-asyncio event loop 问题
"""
from unittest.mock import AsyncMock, MagicMock
import pytest
from datetime import datetime


@pytest.fixture
def mock_db():
    """Mock AsyncSession：execute / commit / refresh / get 用 AsyncMock（await）· 链式值用 MagicMock。"""
    db = MagicMock()
    # async 方法：await db.execute(...) / await db.commit() 等
    db.execute = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.get = AsyncMock(return_value=None)
    db.delete = AsyncMock()
    db.add = MagicMock()
    # execute 链式结果：execute(...).scalars().all() / .scalar_one_or_none() / .first()
    execute_result = MagicMock()
    scalars = execute_result.scalars.return_value
    scalars.all.return_value = []
    scalars.first.return_value = None
    execute_result.scalar_one_or_none.return_value = None
    execute_result.rowcount = 0
    db.execute.return_value = execute_result
    return db


@pytest.mark.asyncio
async def test_list_collections_returns_empty_when_no_collections(mock_db):
    """T8: 空数据库 → 列表返回空。"""
    from services.collection_service import list_collections
    items = await list_collections(mock_db, user_id=None)
    assert items == []


@pytest.mark.asyncio
async def test_subscribe_collection_with_existing_collection(mock_db):
    """T8: 订阅存在的题单 → 返回 progress + subscribed_at。"""
    from services.collection_service import subscribe_collection

    existing = MagicMock(id='agent_foundation', name='Agent 基础到进阶',
                        cover_color='#6366f1', icon_emoji='🤖', question_count=0,
                        is_system=True, sort_order=10,
                        description='', created_at=datetime(2026, 7, 9),
                        updated_at=datetime(2026, 7, 9))
    mock_db.get.return_value = existing

    result = await subscribe_collection(mock_db, 'user-x', 'agent_foundation')

    assert result is not None
    assert result['collection_id'] == 'agent_foundation'
    assert result['progress']['done_count'] == 0
    assert result['progress']['total_count'] == 0  # 占位 0 题
    mock_db.execute.assert_called()


@pytest.mark.asyncio
async def test_subscribe_collection_returns_none_for_missing(mock_db):
    """T8: 订阅不存在的题单 → 返回 None。"""
    from services.collection_service import subscribe_collection
    mock_db.get.return_value = None
    result = await subscribe_collection(mock_db, 'user-x', 'nonexistent')
    assert result is None


@pytest.mark.asyncio
async def test_unsubscribe_returns_true_when_exists(mock_db):
    """T8: 取消订阅存在的题单 → 返回 True。"""
    from services.collection_service import unsubscribe_collection

    existing_sub = MagicMock(collection_id='agent_foundation')
    mock_db.execute.return_value.scalar_one_or_none.return_value = existing_sub

    ok = await unsubscribe_collection(mock_db, 'user-x', 'agent_foundation')
    assert ok is True
    mock_db.delete.assert_called_once_with(existing_sub)


@pytest.mark.asyncio
async def test_unsubscribe_returns_false_when_missing(mock_db):
    """T8: 取消订阅不存在的题单 → 返回 False。"""
    from services.collection_service import unsubscribe_collection

    mock_db.execute.return_value.scalar_one_or_none.return_value = None

    ok = await unsubscribe_collection(mock_db, 'user-y', 'nonexistent')
    assert ok is False
    mock_db.delete.assert_not_called()


@pytest.mark.asyncio
async def test_get_collection_returns_none_for_missing(mock_db):
    """T8: 获取不存在的题单 → 返回 None。"""
    from services.collection_service import get_collection
    mock_db.get.return_value = None
    result = await get_collection(mock_db, 'nonexistent')
    assert result is None


@pytest.mark.asyncio
async def test_seed_collections_creates_1_placeholder(mock_db):
    """T10: seed 1 个 agent_foundation 占位题单（数据解耦）。"""
    from services.collection_service import seed_collections_system, SYSTEM_COLLECTIONS

    # 验证 SYSTEM_COLLECTIONS 配置（用户 2026-07-10 重定义后）
    assert len(SYSTEM_COLLECTIONS) == 1
    cfg = SYSTEM_COLLECTIONS[0]
    assert cfg['id'] == 'agent_foundation'
    assert cfg['name'] == 'Agent 基础到进阶'
    # is_system 是 service 硬编码 True（不在 cfg 里）
    assert cfg['topic_filter'] == 'agent_architecture'

    # 验证 seed 调用
    mock_db.execute.return_value.scalar_one_or_none.return_value = None
    cnt = await seed_collections_system(mock_db)
    assert cnt == 1
    assert mock_db.execute.called


@pytest.mark.asyncio
async def test_seed_collections_keeps_question_count_zero(mock_db):
    """T10 重定义：seed 不自动关联题目 · question_count 保持 0。"""
    from services.collection_service import seed_collections_system

    mock_db.execute.return_value.scalar_one_or_none.return_value = None

    cnt = await seed_collections_system(mock_db)
    assert cnt == 1

    # 检查 execute 调用：最后一个 UPDATE 应该是 question_count=0
    execute_calls = mock_db.execute.call_args_list
    found_zero = False
    for call in execute_calls:
        sql = str(call.args[0]) if call.args else ''
        if 'UPDATE question_collections' in sql and 'question_count = 0' in sql:
            found_zero = True
    assert found_zero, 'seed 应设置 question_count=0（占位 · 不自动关联题目）'
