"""ProfileSettlementService (V2.1 PR 1 — V2 智能沉淀层 · 画像沉淀)

职责：
- settle_after_practice 答题后触发：更新 weak_topics / mastered_topics / last_active_at
- settle_after_interview 面试后触发：聚合本场盲点 → 更新 last_active_at
- weekly_full_refresh 深度重算 learning_trajectory 12 周趋势
- manual_refresh 手动触发（"刷新画像"按钮用）+ DEL summary cache 3 key

实现要点（决策 7A 派生 — 不抛 + log）：
- 整套 try/except 兜底 → 失败 log warning → 返回失败标记 SettlementResult
- 乐观锁（updated_at 比对，决策 §3.2）→ 冲突重试 1 次
- 写入失败时 **不** 阻塞上游业务（答题 / 面试照样返结果）

实施任务：
- T1: 骨架（本文件，4 方法占位 pass）
- T2: settle_after_practice 实现
- T3: settle_after_interview 实现
- T4: weekly_full_refresh 实现
- T5: manual_refresh 实现
- T6: 改 learning_progress_service.upsert_progress 末尾触发
- T7: 改 interview.py:complete 触发 + 拆 interview_settlement.py
- T8: test_profile_settlement_service.py ≥ 80% 覆盖

参考：V1 services/learning_progress_service.py 风格（module docstring + codemock logger + section dividers）
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from core.cache import cache

log = logging.getLogger("codemock.profile_settlement")


# ════════════════════════════════════════════════════════════
#  ProfileSettlementService — 画像沉淀核心
# ════════════════════════════════════════════════════════════


class ProfileSettlementService:
    """用户画像沉淀 service。

    所有方法**不抛异常**（决策 7A）：失败 log warning + 返回标记失败的结果。
    调用方（V1 learning_progress_service.upsert_progress / interview.py:complete）业务不感知。
    """

    async def settle_after_practice(
        self, user_id: UUID, qid: str, score: int, db: AsyncSession
    ) -> Optional["SettlementResult"]:
        """答题后触发：更新 Profile.weak_topics / mastered_topics / last_active_at。

        业务规则（T2 实施）：
        - 读 Question.topic + QuestionProgress → 算 error_rate = 1 - correct/practice
        - error_rate ≥ 0.5 → topic 入 weak_topics（更新或新增）
        - 同一 topic 答对第 2 次且 score ≥ 4 → 从 weak_topics 移到 mastered_topics
        - 更新 Profile.last_active_at = now

        容错（决策 7A）：
        - 乐观锁：commit 失败重试 1 次（spec GWT-3）
        - 整套 try/except → 失败 log warning + return None（**不抛**，spec GWT-9）
        """
        # 局部 import 避免循环依赖（spec.md §3.3 安全）
        from sqlalchemy import and_, select
        from models import Profile, Question, QuestionProgress
        from schemas.settlement import SettlementResult, TopicSettlement

        try:
            # 1. 读 Question.topic
            topic_res = await db.execute(
                select(Question.topic).where(Question.id == qid)
            )
            topic = topic_res.scalar_one_or_none()
            if not topic:
                log.warning(f"settle_after_practice: question not found qid={qid}")
                return None

            # 2. 读 QuestionProgress（practice_count + correct_count → error_rate）
            prog_res = await db.execute(
                select(QuestionProgress).where(
                    and_(
                        QuestionProgress.user_id == str(user_id),
                        QuestionProgress.question_id == qid,
                    )
                )
            )
            progress = prog_res.scalar_one_or_none()
            if not progress:
                log.warning(
                    f"settle_after_practice: no progress yet user={user_id} qid={qid}"
                )
                return None

            # 3. 算 error_rate
            if progress.practice_count > 0:
                error_rate = 1.0 - (
                    progress.correct_count / progress.practice_count
                )
            else:
                error_rate = 0.0

            # 4. 读 Profile with FOR UPDATE（行锁防并发覆盖，spec GWT-3）
            prof_res = await db.execute(
                select(Profile)
                .where(Profile.user_id == str(user_id))
                .with_for_update()
            )
            profile = prof_res.scalar_one_or_none()
            if not profile:
                log.warning(
                    f"settle_after_practice: profile not found user={user_id}"
                )
                return None

            # 5. 算 weak / mastered 列表
            weak = list(profile.weak_topics or [])
            mastered = list(profile.mastered_topics or [])
            now = datetime.now(timezone.utc)

            existing_weak_idx = next(
                (i for i, t in enumerate(weak) if t.get("topic") == topic), None
            )
            existing_mastered_idx = next(
                (i for i, t in enumerate(mastered) if t.get("topic") == topic), None
            )

            topic_entry = {
                "topic": topic,
                "error_rate": round(error_rate, 2),
                "practice_count": progress.practice_count,
                "last_practiced_at": now.isoformat(),
                "related_question_ids": [qid],
            }

            # 6. 决策：进 weak / 移到 mastered / 跳过
            if existing_mastered_idx is not None:
                # 已经在 mastered → 不动
                pass
            elif error_rate >= 0.5:
                # error_rate 高 → 进 weak
                if existing_weak_idx is not None:
                    weak[existing_weak_idx] = topic_entry
                else:
                    weak.append(topic_entry)
            elif (
                score >= 4
                and progress.practice_count >= 2
                and existing_weak_idx is not None
            ):
                # 同一 topic 答对第 2 次且 score 高 → 移到 mastered
                weak = [t for t in weak if t.get("topic") != topic]
                mastered_entry = {**topic_entry, "error_rate": 0.0}
                if existing_mastered_idx is not None:
                    mastered[existing_mastered_idx] = mastered_entry
                else:
                    mastered.append(mastered_entry)
            # else: 维持现状

            # 7. 写回 Profile（乐观锁：commit 失败重试 1 次）
            profile.weak_topics = weak
            profile.mastered_topics = mastered
            profile.last_active_at = now
            profile.updated_at = now

            committed = False
            for attempt in range(2):
                try:
                    await db.commit()
                    committed = True
                    break
                except Exception as e:
                    log.debug(
                        f"settle_after_practice commit attempt {attempt + 1} failed: {e}"
                    )
                    try:
                        await db.rollback()
                    except Exception:
                        pass
            if not committed:
                log.warning(
                    f"settle_after_practice: commit failed after retry user={user_id} qid={qid}"
                )
                return None

            # 8. 失效 summary cache（best-effort，不阻塞）
            try:
                await cache.delete(f"summary:dashboard:{user_id}")
                await cache.delete(f"summary:profile:{user_id}")
            except Exception as e:
                log.debug(
                    f"settle_after_practice: cache delete best-effort failed: {e}"
                )

            # 9. 返回 SettlementResult
            return SettlementResult(
                user_id=user_id,
                settled_at=now,
                weak_topics=[TopicSettlement(**t) for t in weak],
                mastered_topics=[TopicSettlement(**t) for t in mastered],
                triggered_by="practice",
                cache_invalidated=True,
            )
        except Exception as e:
            # 决策 7A：整套兜底 → log + return None，**不抛异常**
            log.warning(
                f"settle_after_practice failed: user={user_id} qid={qid} score={score} error={e}"
            )
            try:
                await db.rollback()
            except Exception:
                pass
            return None

    async def settle_after_interview(
        self, user_id: UUID, interview_id: UUID, db: AsyncSession
    ) -> Optional["SettlementResult"]:
        """面试后触发：聚合本场盲点 → 更新 last_active_at。

        业务规则（T3 实施）：
        - 读 Report（per interview）→ top_blind_spots（list of {topic, error_rate, ...}）
        - 合并 top_blind_spots 进 Profile.weak_topics（去重，保留原值）
        - 更新 Profile.last_active_at = now

        容错（决策 7A）：整套 try/except → 失败 log + return None（**不抛**）
        乐观锁：commit 失败重试 1 次
        """
        # 局部 import 避免循环依赖
        from sqlalchemy import select
        from models import Profile, Report
        from schemas.settlement import SettlementResult, TopicSettlement

        try:
            # 1. 读 Report（per interview）
            report_res = await db.execute(
                select(Report).where(Report.interview_id == str(interview_id))
            )
            report = report_res.scalar_one_or_none()
            if not report:
                log.warning(
                    f"settle_after_interview: report not found interview={interview_id}"
                )
                return None

            top_blind_spots = list(report.top_blind_spots or [])

            # 2. 读 Profile with FOR UPDATE（行锁防并发覆盖）
            prof_res = await db.execute(
                select(Profile)
                .where(Profile.user_id == str(user_id))
                .with_for_update()
            )
            profile = prof_res.scalar_one_or_none()
            if not profile:
                log.warning(
                    f"settle_after_interview: profile not found user={user_id}"
                )
                return None

            # 3. 合并 top_blind_spots → weak_topics（去重，保留原值）
            weak = list(profile.weak_topics or [])
            existing_topics = {t.get("topic") for t in weak}
            now = datetime.now(timezone.utc)

            for spot in top_blind_spots:
                topic = spot.get("topic") or spot.get("name")
                if not topic or topic in existing_topics:
                    continue
                weak.append({
                    "topic": topic,
                    "error_rate": float(spot.get("error_rate", 0.5)),
                    "practice_count": int(spot.get("practice_count", 1)),
                    "last_practiced_at": now.isoformat(),
                    "related_question_ids": list(spot.get("related_question_ids", [])),
                })
                existing_topics.add(topic)

            # 4. 写回 Profile（乐观锁重试 1 次）
            profile.weak_topics = weak
            profile.last_active_at = now
            profile.updated_at = now

            committed = False
            for attempt in range(2):
                try:
                    await db.commit()
                    committed = True
                    break
                except Exception as e:
                    log.debug(
                        f"settle_after_interview commit attempt {attempt + 1} failed: {e}"
                    )
                    try:
                        await db.rollback()
                    except Exception:
                        pass
            if not committed:
                log.warning(
                    f"settle_after_interview: commit failed after retry user={user_id} interview={interview_id}"
                )
                return None

            # 5. 失效 summary cache（best-effort）
            try:
                await cache.delete(f"summary:dashboard:{user_id}")
                await cache.delete(f"summary:profile:{user_id}")
            except Exception as e:
                log.debug(
                    f"settle_after_interview: cache delete best-effort failed: {e}"
                )

            # 6. 返回 SettlementResult
            return SettlementResult(
                user_id=user_id,
                settled_at=now,
                weak_topics=[TopicSettlement(**t) for t in weak],
                mastered_topics=[
                    TopicSettlement(**t) for t in (profile.mastered_topics or [])
                ],
                triggered_by="interview",
                cache_invalidated=True,
            )
        except Exception as e:
            # 决策 7A：整套兜底 → log + return None，**不抛异常**
            log.warning(
                f"settle_after_interview failed: user={user_id} interview={interview_id} error={e}"
            )
            try:
                await db.rollback()
            except Exception:
                pass
            return None

    async def weekly_full_refresh(
        self, user_id: UUID, db: AsyncSession
    ) -> Optional["SettlementResult"]:
        """深度重算 12 周 learning_trajectory。

        业务规则（T4 实施）：
        - 读 question_progress 12 周
        - 按 ISO week 聚合 mastered_count
        - 写入 Profile.learning_trajectory = {week: mastered_count}

        容错（决策 7A）：失败 log → return None（不抛）
        """
        # T1 骨架占位；T4 实施
        log.debug(f"weekly_full_refresh placeholder: user={user_id}")
        return None

    async def manual_refresh(
        self, user_id: UUID, db: AsyncSession
    ) -> Optional["SettlementResult"]:
        """手动触发（"刷新画像"按钮）。

        业务规则（T5 实施）：
        - 调 weekly_full_refresh 重算
        - DEL Redis 3 个 key：
          * summary:dashboard:{user_id}
          * summary:profile:{user_id}
          * profile:{user_id}

        容错（决策 7A）：失败 log → return None（不抛）
        """
        # T1 骨架占位；T5 实施
        log.debug(f"manual_refresh placeholder: user={user_id}")
        return None
