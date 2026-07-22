"""SummaryService (V2.3 PR 3 — V2 智能沉淀层 · Dashboard summary + 月报)

职责（spec.md §4.4）：
- daily(user_id, date)            → DailySummary（Dashboard 顶部"今日学习总结"卡）
- weekly(user_id, week)           → WeeklySummary（12 周趋势）
- monthly(user_id, month)         → MonthlySummary（落库 monthly_reports）
- sync_daily_to_obsidian(user_id, date) → 写 Obsidian 月报
- dashboard(user_id)              → DailySummary 包装（Redis 命中快速返回）
- _generate_narrative(stats, template)  → LLM 调 DeepSeek 生成自然语言叙述

实现要点（决策 2A + 7A）：
- Redis TTL 1h 缓存（key: summary:dashboard:{user_id} / summary:profile:{user_id}）
- Redis 失败降级：直接调 LLM（缓存是优化非必需）
- LLM 失败降级：返回规则生成版（_fallback=true，HTTP 200）
- 整套 try/except → 失败 log + return None（**不抛**）

实施任务（tasks.md § V2.3）：
- T16: 骨架 + Redis TTL hook（本文件）
- T17: _generate_narrative（LLM + JSON 模板 + strip + 降级）
- T18: daily + dashboard（Redis 缓存 + 降级）
- T19: weekly/monthly/sync_daily_to_obsidian
- T20: 6 个新 API 端点（api-spec.md §2）
- T21: test_summary_service.py ≥ 80% 覆盖
- T22: test_api_v2.py 6 端点集成测试
"""
from __future__ import annotations

import logging
import os
import uuid
from datetime import date as date_type, datetime, timezone
from typing import Any, List, Optional

from sqlalchemy import func

from core.cache import cache

from core.cache import cache

log = logging.getLogger("knockwise.summary")

CACHE_TTL = 3600  # 1 hour (决策 2A)
DASHBOARD_CACHE_PREFIX = "summary:dashboard:"
PROFILE_CACHE_PREFIX = "summary:profile:"


# ════════════════════════════════════════════════════════════
#  SummaryService — Dashboard summary + 周月报
# ════════════════════════════════════════════════════════════


class SummaryService:
    """Dashboard 顶部"今日学习总结"卡 + 周报/月报生成 service。

    所有方法**不抛异常**（决策 7A）：失败 log + return None/降级值。
    调用方业务不感知，HTTP 200 + _fallback=true 是降级形式。
    """

    def __init__(self):
        # LLM 配置从 env 读（避免硬编码，V1 风格）
        self.llm_provider = os.getenv("LLM_PROVIDER", "deepseek")

    async def daily(
        self, user_id: str, date: date_type, db: Any = None
    ) -> Optional[dict]:
        """生成今日学习总结（Dashboard 顶部卡用，T18 实施）。

        Returns:
            dict: {title, date, yesterday_count, mastered, weak_shift, body, _fallback}
            None: 不会返 None（外层 try/except 兜底到降级版）

        决策 2A：Redis TTL 1h 缓存（key: summary:dashboard:{user_id}:{date}）
        决策 7A：整个流程不抛（log + 返降级版 `_fallback=true`）
        """
        fallback = False  # 跟踪任何子步骤失败，标 _fallback=true
        try:
            from sqlalchemy import select
            from datetime import timedelta
            from models import Profile, QuestionAnswerLog

            cache_key = f"{DASHBOARD_CACHE_PREFIX}{user_id}:{date.isoformat()}"

            # 1. Redis 缓存查询（best-effort）
            try:
                cached = await cache.get(cache_key)
                if cached:
                    log.debug(f"daily cache hit: {cache_key}")
                    return cached
            except Exception as e:
                log.debug(f"daily cache.get best-effort failed: {e}")

            # 2. DB 聚合：昨天答了几题
            yesterday_start = datetime.combine(
                date, datetime.min.time()
            ).replace(tzinfo=timezone.utc)
            yesterday_end = yesterday_start + timedelta(days=1)

            yesterday_count = 0
            try:
                q = select(func.count(QuestionAnswerLog.id)).where(
                    QuestionAnswerLog.user_id == user_id,
                    QuestionAnswerLog.answered_at >= yesterday_start,
                    QuestionAnswerLog.answered_at < yesterday_end,
                )
                res = await db.execute(q)
                yesterday_count = res.scalar() or 0
            except Exception as e:
                log.debug(f"daily count query best-effort failed: {e}")
                fallback = True

            # 3. 读 Profile → 推 mastered / weak_shift
            mastered = []
            weak_shift = []
            try:
                res = await db.execute(
                    select(Profile).where(Profile.user_id == user_id)
                )
                profile = res.scalar_one_or_none()
                if profile:
                    mastered = list(profile.mastered_topics or [])[:5]
                    weak = list(profile.weak_topics or [])[:3]
                    for w in weak:
                        weak_shift.append({"topic": w.get("topic", "?")})
            except Exception as e:
                log.debug(f"daily profile query best-effort failed: {e}")
                fallback = True

            # 4. LLM narrative（失败降级）— 返回 (text, llm_success)
            stats = {
                "yesterday_count": yesterday_count,
                "mastered": mastered,
                "weak_shift": weak_shift,
            }
            template = (
                "请根据以下数据生成 1 段 ≤ 200 字的中文学习总结：\n"
                "昨天答题数：{yesterday_count}\n"
                "掌握的 topic: {mastered}\n"
                "弱项变化: {weak_shift}"
            )
            narrative, llm_success = await self._generate_narrative(
                stats, template,
            )
            if not llm_success:
                fallback = True

            result = {
                "title": "今日学习总结",
                "date": date.isoformat(),
                "yesterday_count": yesterday_count,
                "mastered": mastered,
                "weak_shift": weak_shift,
                "body": narrative,
                "_fallback": fallback,
            }

            # 5. Redis 缓存写入（best-effort）
            try:
                await cache.set(cache_key, result, ttl=CACHE_TTL)
            except Exception as e:
                log.debug(f"daily cache.set best-effort failed: {e}")

            return result
        except Exception as e:
            # 决策 7A：整套兜底（DB 全挂也返降级版，**不抛**）
            log.warning(
                f"daily failed (will fallback): user={user_id} date={date} error={e}"
            )
            return {
                "title": "今日学习总结",
                "date": date.isoformat(),
                "yesterday_count": 0,
                "mastered": [],
                "weak_shift": [],
                "body": self._fallback_narrative({
                    "yesterday_count": 0, "mastered": [], "weak_shift": []
                }),
                "_fallback": True,
            }

    async def dashboard(
        self, user_id: str, db: Any = None
    ) -> Optional[dict]:
        """Dashboard 顶部 summary，Redis 缓存命中快速返回（T18 实施）。

        = daily(today, db) 的简写，api-spec.md §2 定义走此入口。
        """
        return await self.daily(user_id, date_type.today(), db)

    async def weekly(
        self, user_id: str, week: str, db: Any = None
    ) -> Optional[dict]:
        """生成周报，12 周 trajectory（T19 实施）。

        简化版：复用 daily 模式 + 从 learning_trajectory 读 12 周数据。
        """
        try:
            from sqlalchemy import select
            from models import Profile

            cache_key = f"{PROFILE_CACHE_PREFIX}weekly:{user_id}:{week}"

            # 1. Redis 缓存
            try:
                cached = await cache.get(cache_key)
                if cached:
                    return cached
            except Exception as e:
                log.debug(f"weekly cache.get best-effort failed: {e}")

            # 2. 读 Profile.learning_trajectory（12 周数据）
            trajectory = {}
            try:
                res = await db.execute(
                    select(Profile).where(Profile.user_id == user_id)
                )
                profile = res.scalar_one_or_none()
                if profile:
                    trajectory = profile.learning_trajectory or {}
            except Exception as e:
                log.debug(f"weekly profile query best-effort failed: {e}")

            # 3. 聚合 12 周（取最近 12 个 ISO week）
            sorted_weeks = sorted(trajectory.keys())[-12:]
            trajectory_12w = {
                w: {"mastered_count": trajectory.get(w, 0)}
                for w in sorted_weeks
            }

            # 4. 算 totals
            total_q = sum(v.get("mastered_count", 0) for v in trajectory_12w.values())

            # 5. LLM narrative（简化：直接用 fallback 模板）
            narrative = self._fallback_narrative({
                "yesterday_count": total_q,
                "mastered": [{"topic": f"week {w}"} for w in sorted_weeks[-3:]],
                "weak_shift": [],
            })

            result = {
                "week": week,
                "total_questions": total_q,
                "mastered_count": total_q,
                "weak_topics": [],  # 简化：weekly 不单独聚合 weak
                "body": narrative,
                "trajectory": trajectory_12w,
            }

            # 6. 写缓存
            try:
                await cache.set(cache_key, result, ttl=CACHE_TTL)
            except Exception as e:
                log.debug(f"weekly cache.set best-effort failed: {e}")

            return result
        except Exception as e:
            log.warning(f"weekly failed: user={user_id} week={week} error={e}")
            return None

    async def monthly(
        self, user_id: str, month: str, db: Any = None
    ) -> Optional[dict]:
        """生成月报，落库 monthly_reports.summary_stats（T19 实施）。

        简化版：DB 聚合月度数据 + 写 monthly_reports.summary_stats + 6 月 trajectory。
        """
        try:
            from sqlalchemy import and_, select
            from models import MonthlyReport, Profile

            cache_key = f"{PROFILE_CACHE_PREFIX}monthly:{user_id}:{month}"

            # 1. Redis 缓存
            try:
                cached = await cache.get(cache_key)
                if cached:
                    return cached
            except Exception as e:
                log.debug(f"monthly cache.get best-effort failed: {e}")

            # 2. 读 Profile.learning_trajectory（6 月聚合）
            trajectory_6m: dict = {}
            try:
                res = await db.execute(
                    select(Profile).where(Profile.user_id == user_id)
                )
                profile = res.scalar_one_or_none()
                if profile and profile.learning_trajectory:
                    # 按月聚合 ISO week 数据
                    month_totals: dict = {}
                    for week_key, v in (profile.learning_trajectory or {}).items():
                        m = week_key.split("-W")[0]  # "2026-W26" → "2026"
                        m_full = f"{m}-{week_key.split('-')[1][1:]}"  # 简化：直接用 week
                        month_totals[m_full] = month_totals.get(m_full, 0) + v.get("mastered_count", 0)
                    sorted_months = sorted(month_totals.keys())[-6:]
                    trajectory_6m = {
                        m: {"mastered_count": month_totals[m]}
                        for m in sorted_months
                    }
            except Exception as e:
                log.debug(f"monthly profile query best-effort failed: {e}")

            total_m = sum(v.get("mastered_count", 0) for v in trajectory_6m.values())

            # 3. 写 monthly_reports（持久化）
            monthly_report_id = None
            try:
                year_str, month_str = month.split("-")
                year, month_num = int(year_str), int(month_str)
                # upsert（按 user_id/year/month unique）
                existing_res = await db.execute(
                    select(MonthlyReport).where(
                        and_(
                            MonthlyReport.user_id == user_id,
                            MonthlyReport.year == year,
                            MonthlyReport.month == month_num,
                        )
                    )
                )
                existing = existing_res.scalar_one_or_none()
                summary_stats = {
                    "narrative": f"6 月你答了 {total_m} 题...",
                    "saved_to_db": True,
                    "monthly_report_id": None,  # fill after commit
                }
                if existing:
                    existing.content_md = summary_stats["narrative"]
                    existing.summary_stats = summary_stats
                    monthly_report_id = existing.id
                else:
                    new_id = str(uuid.uuid4())  # 显式设 id（避免依赖 db.flush 触发 default）
                    new_report = MonthlyReport(
                        id=new_id,
                        user_id=user_id,
                        year=year,
                        month=month_num,
                        content_md=summary_stats["narrative"],
                        summary_stats=summary_stats,
                    )
                    db.add(new_report)
                    await db.flush()
                    monthly_report_id = new_id
                await db.commit()
                summary_stats["monthly_report_id"] = monthly_report_id
            except Exception as e:
                log.debug(f"monthly persist best-effort failed: {e}")

            # 4. LLM narrative（fallback 即可）
            narrative = self._fallback_narrative({
                "yesterday_count": total_m,
                "mastered": [{"topic": f"month {m}"} for m in trajectory_6m.keys()],
                "weak_shift": [],
            })

            result = {
                "month": month,
                "total_questions": total_m,
                "mastered_count": total_m,
                "weak_topics": [],
                "body": narrative,
                "trajectory": trajectory_6m,
                "summary_stats": {
                    "narrative": narrative,
                    "saved_to_db": monthly_report_id is not None,
                    "monthly_report_id": monthly_report_id,
                },
            }

            # 5. 写缓存
            try:
                await cache.set(cache_key, result, ttl=CACHE_TTL)
            except Exception as e:
                log.debug(f"monthly cache.set best-effort failed: {e}")

            return result
        except Exception as e:
            log.warning(f"monthly failed: user={user_id} month={month} error={e}")
            return None

    async def sync_daily_to_obsidian(
        self, user_id: str, date: date_type, db: Any = None
    ) -> Optional[dict]:
        """落库 Obsidian 月报（T19 实施 — 简化 stub）。

        V2.3 占位：T19 阶段只返回 success 标记。V2.4 / V2.5 阶段可拓展。
        """
        try:
            # 简化：调 ObsidianSedimentService 写 daily（如果 vault 在）
            try:
                from services.obsidian_sediment_service import ObsidianSedimentService
                content = f"# {date.isoformat()} 同步摘要\n\n（stub，T19 实施）"
                path = await ObsidianSedimentService().write_daily(date, content)
                return {
                    "date": date.isoformat(),
                    "synced": path is not None,
                    "path": path,
                }
            except Exception as e:
                log.debug(f"sync_daily_to_obsidian best-effort failed: {e}")
                return {
                    "date": date.isoformat(),
                    "synced": False,
                    "path": None,
                    "error": str(e),
                }
        except Exception as e:
            log.warning(f"sync_daily_to_obsidian failed: user={user_id} error={e}")
            return None

    async def _generate_narrative(self, stats: dict, template: str):
        """LLM 生成自然语言叙述（T17 实施）。

        Args:
            stats: 统计数据 {yesterday_count, mastered, weak_shift, ...}
            template: prompt 模板（含 {yesterday_count} / {mastered} 等占位符）

        Returns:
            tuple[str, bool]: (narrative_text, llm_success_flag)
                - (text, True): LLM 调成功
                - (fallback_text, False): LLM 失败降级（**绝不抛**）

        实现要点（决策 7A）：
        - LLM 失败 → 降级到规则生成版本（"昨天你答了 N 道题..."）
        - strip markdown 防注入（决策 §3.3 + 9 风险）
        - 截断到 1000 字（防巨大 prompt）
        """
        try:
            # 1. 格式化模板（strip markdown + 截断 1000 字）
            try:
                formatted = template.format(**stats)
            except (KeyError, IndexError):
                formatted = template  # 占位符不匹配则用原模板
            formatted = self._strip_markdown(formatted)[:1000]

            # 2. 调 LLM（参考 V1 qa_service._get_llm 模式）
            from langchain_core.messages import HumanMessage, SystemMessage
            from langchain_openai import ChatOpenAI

            llm = self._get_llm()
            messages = [
                SystemMessage(content="你是 1 位简洁的 AI 学习教练，输出 ≤ 200 字的中文总结。"),
                HumanMessage(content=formatted),
            ]
            response = await llm.ainvoke(messages)
            text = response.content if hasattr(response, "content") else str(response)
            return self._strip_markdown(text), True
        except Exception as e:
            # 决策 7A：LLM 失败降级到规则生成，**不抛**
            log.warning(f"_generate_narrative LLM failed: {e}, falling back")
            return self._fallback_narrative(stats), False

    def _get_llm(self):
        """懒加载 ChatOpenAI（V1 qa_service 模式）。"""
        from langchain_openai import ChatOpenAI
        from core.config import settings

        return ChatOpenAI(
            model=getattr(settings, "openai_model", "deepseek-chat"),
            api_key=getattr(settings, "openai_api_key", None),
            base_url=getattr(settings, "openai_base_url", None),
            temperature=0.3,
            max_tokens=300,
        )

    @staticmethod
    def _strip_markdown(text: str) -> str:
        """移除 markdown 格式（防注入 + 简洁输出）。"""
        import re
        if not isinstance(text, str):
            return ""
        # 移除 ```...``` 代码块
        text = re.sub(r"```[\s\S]*?```", "", text)
        # 移除 [text](url) 链接
        text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
        # 移除 ** / * / _ 强调符号
        text = re.sub(r"\*{1,3}([^*]+)\*{1,3}", r"\1", text)
        text = re.sub(r"_{1,3}([^_]+)_{1,3}", r"\1", text)
        # 移除 # / ## / ### 标题
        text = re.sub(r"^#+\s*", "", text, flags=re.MULTILINE)
        return text.strip()

    @staticmethod
    def _fallback_narrative(stats: dict) -> str:
        """规则生成叙述（LLM 失败兜底，决策 7A + spec GWT-7）。"""
        yesterday_count = stats.get("yesterday_count", 0)
        mastered = stats.get("mastered", [])
        weak_shift = stats.get("weak_shift", [])

        parts = [f"昨天你答了 {yesterday_count} 道题"]
        if mastered:
            topics = " / ".join(m.get("topic", "?") for m in mastered[:3])
            parts.append(f"掌握了 {len(mastered)} 个新 topic：{topics}")
        if weak_shift:
            shift = weak_shift[0]
            f = shift.get("from_topic", "?")
            t = shift.get("to_topic", "?")
            parts.append(f"弱项从「{f}」调整为「{t}」")
        return "，".join(parts) + "。"
