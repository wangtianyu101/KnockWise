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
from datetime import date as date_type, datetime, timezone
from typing import Any, List, Optional

from core.cache import cache

log = logging.getLogger("codemock.summary")

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
        """生成今日学习总结（Dashboard 顶部卡用，T18 实施）。"""
        # T16 骨架占位；T18 实施：DB 聚合 + LLM narrative + Redis 缓存
        log.debug(f"daily placeholder: user={user_id} date={date}")
        return None

    async def weekly(
        self, user_id: str, week: str, db: Any = None
    ) -> Optional[dict]:
        """生成周报，12 周 trajectory（T19 实施）。"""
        log.debug(f"weekly placeholder: user={user_id} week={week}")
        return None

    async def monthly(
        self, user_id: str, month: str, db: Any = None
    ) -> Optional[dict]:
        """生成月报，落库 monthly_reports.summary_stats（T19 实施）。"""
        log.debug(f"monthly placeholder: user={user_id} month={month}")
        return None

    async def sync_daily_to_obsidian(
        self, user_id: str, date: date_type, db: Any = None
    ) -> Optional[dict]:
        """落库 Obsidian 月报（T19 实施）。"""
        log.debug(f"sync_daily_to_obsidian placeholder: user={user_id}")
        return None

    async def dashboard(
        self, user_id: str, db: Any = None
    ) -> Optional[dict]:
        """Dashboard 顶部 summary，Redis 缓存命中快速返回（T18 实施）。"""
        log.debug(f"dashboard placeholder: user={user_id}")
        return None

    def _generate_narrative(self, stats: dict, template: str) -> str:
        """LLM 生成自然语言叙述（T17 实施）。

        Returns:
            str: LLM 生成或规则降级的叙述（**绝不抛异常**）
        """
        # T16 骨架占位；T17 实施：LLM 调 + JSON prompt + strip markdown + 降级
        log.debug(f"_generate_narrative placeholder: template={template[:30]}")
        return f"（骨架占位）叙述 based on {len(stats)} stats"
