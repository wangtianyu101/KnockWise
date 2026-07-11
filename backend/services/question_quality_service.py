"""
PR 4 · V3.7 题库质量监控服务（meta · 用户 2026-07-10 拍）

4 方法：
- check_field_completeness：字段缺失统计
- detect_duplicates：按 question_text 哈希找重复
- record_sync_history：每次 sync 落库一条记录
- get_sync_history：拉最近 N 条同步历史
"""
from __future__ import annotations

import logging
from collections import Counter
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from models import Question

log = logging.getLogger("codemock.question_quality")


# ════════════════════════════════════════════════════════════
# T19.1: 字段完整性检查
# ════════════════════════════════════════════════════════════

async def check_field_completeness(db: AsyncSession) -> dict:
    """统计题库字段缺失情况。

    Returns:
        {
            "total": int,           # 题总数
            "missing_answer_key_points": int,
            "missing_followup_tree": int,
            "missing_sub_topic": int,
            "completeness_rate": float,  # 0-1
            "by_topic": {topic: {...}},  # 按 topic 统计
        }
    """
    stmt = select(Question.id, Question.topic, Question.answer_key_points, Question.followup_tree, Question.sub_topic)
    rows = (await db.execute(stmt)).all()

    total = len(rows)
    missing_akp = 0
    missing_ft = 0
    missing_sub = 0
    by_topic: dict[str, dict] = {}

    for row in rows:
        qid, topic, akp, ft, sub = row
        topic_stats = by_topic.setdefault(topic or "unknown", {"total": 0, "missing_akp": 0, "missing_ft": 0})
        topic_stats["total"] += 1

        if not akp or len(akp) == 0:
            missing_akp += 1
            topic_stats["missing_akp"] += 1
        if not ft or len(ft) == 0:
            missing_ft += 1
            topic_stats["missing_ft"] += 1
        if not sub:
            missing_sub += 1

    # 完整率：3 个字段全填 = 1
    completeness_rate = 1.0
    if total > 0:
        complete = total - sum(1 for r in rows if (not r[2] or len(r[2]) == 0) or (not r[3] or len(r[3]) == 0) or not r[4])
        completeness_rate = round(complete / total, 4)

    return {
        "total": total,
        "missing_answer_key_points": missing_akp,
        "missing_followup_tree": missing_ft,
        "missing_sub_topic": missing_sub,
        "completeness_rate": completeness_rate,
        "by_topic": by_topic,
    }


# ════════════════════════════════════════════════════════════
# T19.2: 重复题检测
# ════════════════════════════════════════════════════════════

async def detect_duplicates(db: AsyncSession) -> list[dict]:
    """按 question_text 哈希找重复题。

    Returns:
        [{"hash": str, "ids": [str], "count": int, "sample_text": str}, ...]
        仅返回 count > 1 的重复组。
    """
    import hashlib

    stmt = select(Question.id, Question.question_text)
    rows = (await db.execute(stmt)).all()

    hash_to_ids: dict[str, list[str]] = {}
    hash_to_sample: dict[str, str] = {}

    for qid, text in rows:
        if not text:
            continue
        h = hashlib.md5(text.strip().encode("utf-8")).hexdigest()
        hash_to_ids.setdefault(h, []).append(qid)
        hash_to_sample.setdefault(h, text[:100])

    duplicates = []
    for h, ids in hash_to_ids.items():
        if len(ids) > 1:
            duplicates.append({
                "hash": h,
                "ids": ids,
                "count": len(ids),
                "sample_text": hash_to_sample[h],
            })
    duplicates.sort(key=lambda d: d["count"], reverse=True)
    return duplicates


# ════════════════════════════════════════════════════════════
# T19.3/T19.4: 同步历史（in-memory 实现 · 不入 DB 简化版）
# ════════════════════════════════════════════════════════════

# 模块级 in-memory 历史（单进程 · V1 模式 · 不入 DB）
# 实际生产应该落 DB · 但 PR 4 简化版用内存
_sync_history: list[dict] = []
_MAX_HISTORY = 100


def record_sync_history(
    *,
    source: str,
    fetched: int,
    created: int,
    skipped: int,
    errors: int,
    duration_sec: float = 0.0,
    status: str = "success",
    error_msg: Optional[str] = None,
) -> dict:
    """记录一次同步结果（in-memory · V1 简化版）。"""
    record = {
        "id": len(_sync_history) + 1,
        "source": source,
        "fetched": fetched,
        "created": created,
        "skipped": skipped,
        "errors": errors,
        "duration_sec": round(duration_sec, 2),
        "status": status,  # success / partial / failed
        "error_msg": error_msg,
        "started_at": datetime.now(timezone.utc).isoformat(),
    }
    _sync_history.append(record)
    # 保留最近 N 条
    if len(_sync_history) > _MAX_HISTORY:
        _sync_history.pop(0)

    # 错误告警：连续 3 次失败
    recent = _sync_history[-3:]
    if len(recent) >= 3 and all(r["status"] == "failed" for r in recent):
        log.error(f"question_sync ALERT: 3 consecutive failures · last_error={recent[-1].get('error_msg')}")

    log.info(f"sync history recorded: source={source} status={status} created={created}")
    return record


def get_sync_history(limit: int = 10) -> list[dict]:
    """拉最近 N 条同步历史。"""
    return _sync_history[-limit:][::-1]  # 倒序返回


def reset_sync_history() -> None:
    """清空历史（测试用）。"""
    _sync_history.clear()