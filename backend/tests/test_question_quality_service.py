"""
PR 4 · V3.7 题库质量监控测试（5 测试点）
策略：mock_db（V1 风格）+ in-memory history
"""
from unittest.mock import AsyncMock, MagicMock
import pytest


# ════════════════════════════════════════════════════════════
# T19.1: 字段完整性检查
# ════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_check_field_completeness_counts_missing():
    """T21.1: 字段缺失统计（无 answer_key_points → 计数 +1）。"""
    from services.question_quality_service import check_field_completeness

    db = MagicMock()
    db.execute = AsyncMock()

    # Mock 3 题：1 题完整，2 题缺字段
    rows = [
        ("q1", "agent", ["kp1"], {"tree": "x"}, "sub1"),  # 完整
        ("q2", "agent", [], {}, "sub2"),                    # 缺 akp + ft
        ("q3", "rag", None, None, ""),                       # 全缺
    ]
    execute_result = MagicMock()
    execute_result.all.return_value = rows
    db.execute.return_value = execute_result

    stats = await check_field_completeness(db)

    assert stats["total"] == 3
    assert stats["missing_answer_key_points"] == 2  # q2 + q3
    assert stats["missing_followup_tree"] == 2      # q2 + q3
    assert stats["missing_sub_topic"] == 1           # q3
    # 完整率：1/3 ≈ 0.3333
    assert stats["completeness_rate"] < 0.5
    assert "agent" in stats["by_topic"]
    assert stats["by_topic"]["agent"]["total"] == 2


# ════════════════════════════════════════════════════════════
# T19.2: 重复题检测
# ════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_detect_duplicates_finds_groups():
    """T21.2: 重复题检测（2 题同 text → 标记）。"""
    from services.question_quality_service import detect_duplicates

    db = MagicMock()
    db.execute = AsyncMock()

    rows = [
        ("q1", "什么是 ReAct？"),
        ("q2", "什么是 ReAct？"),         # 与 q1 重复
        ("q3", "ReAct 怎么用？"),          # 不重复
        ("q4", "什么是 ReAct？"),         # 与 q1/q2 重复
    ]
    execute_result = MagicMock()
    execute_result.all.return_value = rows
    db.execute.return_value = execute_result

    duplicates = await detect_duplicates(db)

    assert len(duplicates) == 1
    assert duplicates[0]["count"] == 3  # q1/q2/q4 同一 text
    assert set(duplicates[0]["ids"]) == {"q1", "q2", "q4"}
    assert duplicates[0]["sample_text"] == "什么是 ReAct？"


# ════════════════════════════════════════════════════════════
# T19.3: sync_history 写入 + 读取
# ════════════════════════════════════════════════════════════


def test_sync_history_record_and_retrieve():
    """T21.3: sync_history 写入 + 读取。"""
    from services.question_quality_service import record_sync_history, get_sync_history, reset_sync_history

    reset_sync_history()  # 清空

    # 写 3 条
    record_sync_history(source="local", fetched=10, created=5, skipped=3, errors=2, status="partial")
    record_sync_history(source="github", fetched=20, created=8, skipped=0, errors=0, status="success")
    record_sync_history(source="http", fetched=0, created=0, skipped=0, errors=1, status="failed", error_msg="timeout")

    # 读
    history = get_sync_history(limit=10)
    assert len(history) == 3
    # 最新在前
    assert history[0]["source"] == "http"
    assert history[0]["status"] == "failed"
    assert history[1]["source"] == "github"
    assert history[2]["source"] == "local"


# ════════════════════════════════════════════════════════════
# T19.4: 错误告警（连续 3 次失败 → 触发 log error）
# ════════════════════════════════════════════════════════════


def test_sync_history_consecutive_failure_alerts(caplog):
    """T21.4: 错误告警（连续 3 次失败 → log error）。"""
    import logging
    from services.question_quality_service import record_sync_history, reset_sync_history

    reset_sync_history()

    # 连续 3 次失败
    with caplog.at_level(logging.ERROR, logger="codemock.question_quality"):
        record_sync_history(source="x", fetched=0, created=0, skipped=0, errors=1, status="failed")
        record_sync_history(source="x", fetched=0, created=0, skipped=0, errors=1, status="failed")
        record_sync_history(source="x", fetched=0, created=0, skipped=0, errors=1, status="failed")

    # 检查 log 包含 ALERT
    alert_logs = [r for r in caplog.records if "ALERT" in r.message]
    assert len(alert_logs) == 1
    assert "3 consecutive failures" in alert_logs[0].message


def test_sync_history_no_alert_with_success_interruption(caplog):
    """T21.4 边界：成功中断 → 不告警。"""
    import logging
    from services.question_quality_service import record_sync_history, reset_sync_history

    reset_sync_history()

    with caplog.at_level(logging.ERROR, logger="codemock.question_quality"):
        record_sync_history(source="x", fetched=0, created=0, skipped=0, errors=1, status="failed")
        record_sync_history(source="x", fetched=10, created=5, skipped=0, errors=0, status="success")  # 中断
        record_sync_history(source="x", fetched=0, created=0, skipped=0, errors=1, status="failed")
        record_sync_history(source="x", fetched=0, created=0, skipped=0, errors=1, status="failed")

    # 不应触发 ALERT（最近 3 不是连续 failed）
    alert_logs = [r for r in caplog.records if "ALERT" in r.message]
    assert len(alert_logs) == 0


# ════════════════════════════════════════════════════════════
# T19.5: 端到端 sync + 落库（简化 · 不连真 DB）
# ════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_end_to_end_sync_with_history_record():
    """T21.5: 端到端 sync → record history。"""
    from services.question_sync_service import sync_questions
    from services.question_quality_service import record_sync_history, get_sync_history, reset_sync_history

    reset_sync_history()

    db = MagicMock()
    db.commit = AsyncMock()
    db.add = MagicMock()
    db.execute = AsyncMock()
    execute_result = MagicMock()
    execute_result.all.return_value = []
    execute_result.scalar_one_or_none.return_value = None
    db.execute.return_value = execute_result

    source = MagicMock()
    source.fetch_questions = AsyncMock(return_value=[
        {"id": "agent_e2e_001", "topic": "agent", "sub_topic": "test", "question_text": "e2e 测试题"}
    ])

    stats = await sync_questions(db, [source], dry_run=False)
    assert stats["created"] == 1

    # record history
    record_sync_history(source="e2e", fetched=stats["fetched"], created=stats["created"],
                      skipped=stats["skipped"], errors=stats["errors"])

    history = get_sync_history(limit=1)
    assert len(history) == 1
    assert history[0]["created"] == 1