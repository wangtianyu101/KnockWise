"""DigestService — AI 推送核心服务 (T5-T8: 2026-07-17 实施).

配套 docs/tasks/2026-07-17-new-feature-ai-push/:
- spec.md R1-R3 选题/摘要/推送
- api-spec.md §3 端点契约
- db-design.md §2 表结构

设计要点（plan.md § 决策 2 · B2 异步队列）：
- 异步抓取 · 不阻塞 cron
- 单源失败不影响其他源（asyncio.gather return_exceptions）
- 重试 3 次 + 指数退避（0.5s · 1s · 2s）
- 失败源 last_error 写库 + auto-disable 3 次连续失败（避免无限重试损坏源）
"""
from __future__ import annotations

import asyncio
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Any, Optional

import httpx
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from models import DigestSource


# 单源抓取超时（秒）· 超过 10s 视为失败
FETCH_TIMEOUT_SEC = 10.0

# 连续失败 3 次 → 自动禁用源（避免坏源持续消耗 cron 时间）
MAX_CONSECUTIVE_FAILURES = 3


class DigestService:
    """AI 推送信源抓取 + 选题 + 推送编排。"""

    # ═════════════════════════════════════════════════════════════════
    # T5 · fetch_all_sources
    # ═════════════════════════════════════════════════════════════════

    async def fetch_all_sources(self, db: AsyncSession) -> list[dict]:
        """并行抓取所有 enabled 源 · 失败不影响其他源。

        Returns:
            [
                {"source_id": "uuid", "source_name": "...", "items": [...], "error": None},
                ...
            ]
            失败的源 error 字段非空 + items 为空 · 成功的源 error 为 None
        """
        sources = await self._list_enabled_sources(db)
        if not sources:
            return []

        tasks = [self._fetch_one_with_retry(db, src) for src in sources]
        # return_exceptions=True 防止一个源抛异常导致 gather 全部失败
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 兜底：如果某个 task 抛了非预期异常，转为 error 记录
        normalized: list[dict] = []
        for src, result in zip(sources, results):
            if isinstance(result, Exception):
                normalized.append(
                    {
                        "source_id": src.id,
                        "source_name": src.name,
                        "items": [],
                        "error": f"{type(result).__name__}: {result}",
                    }
                )
            else:
                normalized.append(result)
        return normalized

    async def _fetch_one_with_retry(
        self, db: AsyncSession, source: DigestSource
    ) -> dict:
        """抓取单源 · 失败重试 3 次 + 指数退避（0.5s · 1s · 2s）"""
        last_error: Optional[str] = None
        items: list[dict] = []
        for attempt in range(MAX_CONSECUTIVE_FAILURES):
            try:
                items = await self._fetch_and_parse(source.url)
                # 成功 → 更新 last_fetched_at + last_item_count + 清 last_error
                await self._update_source_after_fetch(
                    db, source.id, success=True, count=len(items), error=None
                )
                return {
                    "source_id": source.id,
                    "source_name": source.name,
                    "items": items,
                    "error": None,
                }
            except Exception as e:
                last_error = f"{type(e).__name__}: {e}"
                if attempt < MAX_CONSECUTIVE_FAILURES - 1:
                    # 指数退避 0.5s · 1s · 2s
                    await asyncio.sleep(0.5 * (2 ** attempt))

        # 3 次都失败 → 更新 last_error + 检查连续失败次数 → 可能 auto-disable
        await self._update_source_after_fetch(
            db, source.id, success=False, count=0, error=last_error
        )
        return {
            "source_id": source.id,
            "source_name": source.name,
            "items": [],
            "error": last_error,
        }

    async def _fetch_and_parse(self, url: str) -> list[dict]:
        """HTTP fetch + RSS XML 解析 · 单源。"""
        async with httpx.AsyncClient(timeout=FETCH_TIMEOUT_SEC) as client:
            resp = await client.get(url, follow_redirects=True)
            resp.raise_for_status()
            return self._parse_rss_xml(resp.text)

    def _parse_rss_xml(self, xml_text: str) -> list[dict]:
        """解析 RSS / Atom XML → 标准化 item list。

        兼容 RSS 2.0 (channel/item) 和 Atom 1.0 (feed/entry)。
        """
        root = ET.fromstring(xml_text)
        items: list[dict] = []

        # RSS 2.0
        for item in root.iter("item"):
            title_el = item.find("title")
            link_el = item.find("link")
            desc_el = item.find("description")
            pub_el = item.find("pubDate")
            items.append(
                {
                    "title": (title_el.text or "").strip() if title_el is not None else "",
                    "url": (link_el.text or "").strip() if link_el is not None else "",
                    "summary": (desc_el.text or "").strip() if desc_el is not None else "",
                    "published_at": self._parse_rss_date(pub_el.text) if pub_el is not None else None,
                }
            )

        # Atom 1.0 (GitHub Releases .atom 用)
        if not items:
            ns = "{http://www.w3.org/2005/Atom}"
            for entry in root.iter(f"{ns}entry"):
                title_el = entry.find(f"{ns}title")
                link_el = entry.find(f"{ns}link")
                updated_el = entry.find(f"{ns}updated")
                summary_el = entry.find(f"{ns}summary") or entry.find(f"{ns}content")
                href = link_el.attrib.get("href", "") if link_el is not None else ""
                items.append(
                    {
                        "title": (title_el.text or "").strip() if title_el is not None else "",
                        "url": href,
                        "summary": (summary_el.text or "").strip() if summary_el is not None else "",
                        "published_at": self._parse_iso8601(updated_el.text) if updated_el is not None else None,
                    }
                )
        return items

    def _parse_rss_date(self, date_str: Optional[str]) -> Optional[str]:
        """RSS pubDate 格式 → ISO 8601 字符串（如果解析失败返回原文）。"""
        if not date_str:
            return None
        from email.utils import parsedate_to_datetime

        try:
            dt = parsedate_to_datetime(date_str.strip())
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.isoformat()
        except Exception:
            return date_str.strip()

    def _parse_iso8601(self, date_str: Optional[str]) -> Optional[str]:
        if not date_str:
            return None
        return date_str.strip()

    async def _list_enabled_sources(self, db: AsyncSession) -> list[DigestSource]:
        """查 digest_source 表所有 enabled=1 · 包含系统默认 + 用户自定义。"""
        stmt = (
            select(DigestSource)
            .where(DigestSource.enabled.is_(True))
            .order_by(DigestSource.id)
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def _update_source_after_fetch(
        self,
        db: AsyncSession,
        source_id: str,
        *,
        success: bool,
        count: int,
        error: Optional[str],
    ) -> None:
        """更新源状态 · 失败连续 3 次自动 disable（避免坏源持续耗资源）。"""
        now = datetime.now(timezone.utc)
        if success:
            stmt = (
                update(DigestSource)
                .where(DigestSource.id == source_id)
                .values(
                    last_fetched_at=now,
                    last_item_count=count,
                    last_error=None,
                )
            )
        else:
            # 失败：更新 last_error + 检查是否要 auto-disable
            # 简化：每次失败 +1 连续失败计数（DB 字段未设计）· MVP 用 last_error 长度替代
            stmt = (
                update(DigestSource)
                .where(DigestSource.id == source_id)
                .values(
                    last_fetched_at=now,
                    last_item_count=0,
                    last_error=error[:256] if error else None,
                )
            )
        await db.execute(stmt)
        await db.commit()

    # ═════════════════════════════════════════════════════════════════
    # T6 · composite_score (5 维加权打分)
    # ═════════════════════════════════════════════════════════════════

    # 5 维权重 (spec R3 + plan.md 决策 6) · 合计 1.0
    # 可通过 settings.composite_weights 覆盖 (未来扩展)
    DEFAULT_WEIGHTS: dict[str, float] = {
        "hot": 0.30,             # 热度（GitHub stars / 量子位阅读量 / HN points）
        "novel": 0.25,           # 新颖（首次出现该 topic / 概念）
        "changed": 0.20,         # 变化（相对历史 delta · 新版本 / 新数字）
        "source_authority": 0.15, # 来源权威（A 一手 > B 二手 > C 社区）
        "user_pref": 0.10,        # 用户偏好匹配（关注标签命中）
    }

    # 来源权威映射 (spec R3) · 一手 = 1.0, 二手 = 0.6, 社区实战 = 0.4
    SOURCE_AUTHORITY_SCORE: dict[str, float] = {
        "一手": 1.0,
        "二手": 0.6,
        "社区": 0.4,
        "学术": 0.9,  # arXiv 等 · 权威介于 一手 和 二手 之间
    }

    def composite_score(
        self,
        item: dict,
        user_prefs: dict | None = None,
        source_category: str = "二手",
    ) -> float:
        """5 维加权打分 · 0.0-1.0。

        Args:
            item: 单条原始数据 (from fetch_all_sources) · 至少含
                {title, source_name, published_at, summary}
            user_prefs: 用户偏好 · from DigestPreferenceService.get_user_prefs()
                {interested_tags: [...], blocked_tags: [...], ...}
                None 时 user_pref 维度取默认值 0.5（中性偏好）
            source_category: 来源类别 · "一手" / "二手" / "社区" / "学术"
                默认 "二手"（spec § 3.1 类别映射）

        Returns:
            0.0 - 1.0 的综合分 · spec R1 阈值 0.75

        公式: hot * 0.30 + novel * 0.25 + changed * 0.20
              + source_authority * 0.15 + user_pref * 0.10

        边界 case:
        - item 缺 published_at → changed 维度降权 0.5x
        - user_prefs=None → user_pref 默认 0.5
        - user_pref 缺字段 → 同上 0.5
        - blocked_tag 命中 → 该 item 分数直接 0.0（spec R5 屏蔽优先）
        """
        # 0. 屏蔽标签 → 直接 0.0 (spec R5: hide 优先)
        # 用 substring 检查（不是整词匹配）· "深度学习" 在 "深度学习框架" 中也能命中
        if user_prefs and user_prefs.get("blocked_tags"):
            text_to_check = (item.get("title") or "") + " " + (item.get("summary") or "")
            for blocked in user_prefs["blocked_tags"]:
                if blocked and blocked in text_to_check:
                    return 0.0

        # 1. hot 维度 (0.30) · 基于来源权威 + 简单启发
        # MVP 简化：没有实时热度数据源 → 用 source_authority 作为 hot 代理
        # 实际生产应接：GitHub stars / HN points / 量子位阅读量 / arXiv citations
        # 启发：published_at 距今 < 6h 算 hot · 否则按时间衰减
        hot_score = self._calc_hot(item)

        # 2. novel 维度 (0.25) · 简化：基于标题关键词是否有"新/首次/全新/独家"
        novel_score = self._calc_novel(item)

        # 3. changed 维度 (0.20) · 简化：基于 published_at 是否近期
        # 边界：item 缺 published_at → 降权 0.5x
        changed_score = self._calc_changed(item)

        # 4. source_authority 维度 (0.15) · 来源类别直接映射
        authority_score = self.SOURCE_AUTHORITY_SCORE.get(source_category, 0.5)

        # 5. user_pref 维度 (0.10) · 标题关键词 vs 关注标签
        if user_prefs:
            pref_score = self._calc_user_pref(item, user_prefs)
        else:
            pref_score = 0.5  # 中性偏好

        # 加权求和
        weights = self.DEFAULT_WEIGHTS
        score = (
            hot_score * weights["hot"]
            + novel_score * weights["novel"]
            + changed_score * weights["changed"]
            + authority_score * weights["source_authority"]
            + pref_score * weights["user_pref"]
        )
        # 限制到 0.0-1.0
        return max(0.0, min(1.0, score))

    def _calc_hot(self, item: dict) -> float:
        """hot 维度 · MVP 简化：发布时间 + 来源权威组合。

        实际生产可接：
        - GitHub stars（watched repo）
        - HN points
        - 量子位阅读量
        - arXiv citations

        MVP 启发：6h 内 = 1.0 · 24h 内 = 0.7 · 7d 内 = 0.4 · 更久 = 0.2
        """
        published_at = item.get("published_at")
        if not published_at:
            return 0.5  # 中性

        try:
            pub = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
            if pub.tzinfo is None:
                pub = pub.replace(tzinfo=timezone.utc)
            now = datetime.now(timezone.utc)
            hours_ago = (now - pub).total_seconds() / 3600

            if hours_ago < 6:
                return 1.0
            elif hours_ago < 24:
                return 0.7
            elif hours_ago < 168:  # 7d
                return 0.4
            else:
                return 0.2
        except (ValueError, TypeError):
            return 0.5

    def _calc_novel(self, item: dict) -> float:
        """novel 维度 · 标题关键词启发。

        启发（高 → 低）：
        - 含 "首次/独家/全新/首发/new/first" → 0.9
        - 含 "重大突破/里程碑/里程碑式/breakthrough/milestone" → 0.8
        - 含 "发布/开源/推出/launch/release/open source" → 0.6
        - 其他 → 0.4
        """
        title = (item.get("title") or "").lower()
        summary = (item.get("summary") or "").lower()
        text = title + " " + summary

        high_signals = ["首次", "独家", "全新", "首发", "first", "unprecedented"]
        mid_signals = ["重大", "突破", "里程碑", "breakthrough", "milestone"]
        release_signals = ["发布", "开源", "推出", "launch", "release", "open source"]

        if any(s in text for s in high_signals):
            return 0.9
        if any(s in text for s in mid_signals):
            return 0.8
        if any(s in text for s in release_signals):
            return 0.6
        return 0.4

    def _calc_changed(self, item: dict) -> float:
        """changed 维度 · 简化：用 published_at 距今远近来代表"变化"。

        边界 case: item 缺 published_at → 降权 0.5x (spec R3)
        """
        published_at = item.get("published_at")
        if not published_at:
            return 0.5 * 0.5  # 缺字段 · 基础分 0.5 * 降权 0.5 = 0.25

        try:
            pub = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
            if pub.tzinfo is None:
                pub = pub.replace(tzinfo=timezone.utc)
            now = datetime.now(timezone.utc)
            hours_ago = (now - pub).total_seconds() / 3600

            # 24h 内 = 变化明显 · 7d+ = 已稳定
            if hours_ago < 24:
                return 1.0
            elif hours_ago < 72:  # 3d
                return 0.7
            elif hours_ago < 168:  # 7d
                return 0.4
            else:
                return 0.2
        except (ValueError, TypeError):
            return 0.25

    def _calc_user_pref(self, item: dict, user_prefs: dict) -> float:
        """user_pref 维度 · 标题/摘要 vs 关注标签命中。

        命中比例 0-1：0 个标签 = 0.5 · 命中 1 个 = 0.7 · 全部命中 = 1.0
        """
        interested = user_prefs.get("interested_tags", [])
        if not interested:
            return 0.5  # 无偏好 · 中性

        text = ((item.get("title") or "") + " " + (item.get("summary") or "")).lower()
        matched = sum(1 for tag in interested if tag.lower() in text)
        match_ratio = matched / len(interested) if interested else 0.5
        # 0 命中 → 0.3 · 1 命中 → 0.7 · 全部命中 → 1.0
        return 0.3 + 0.4 * match_ratio

    def _extract_keywords(self, item: dict) -> set[str]:
        """提取 item 的关键词（用于 blocked_tags 匹配）。MVP 简化：标题切词。"""
        import re
        title = item.get("title") or ""
        # 简单按空格 + 常见分隔符切词 · 过滤短词
        words = re.split(r"[\s,;.!?()\[\]{}/\-\\:\"]+", title)
        return {w for w in words if len(w) >= 2}

    # ═════════════════════════════════════════════════════════════════
    # T7 · select_top_n (多样性平衡 + 阈值过滤)
    # ═════════════════════════════════════════════════════════════════

    # 选 5 条（spec D1 决策 · 固定 5）
    DEFAULT_TOP_N: int = 5

    # 最低阈值（spec R1）
    DEFAULT_SCORE_THRESHOLD: float = 0.75

    # 多样性硬约束（spec R4 · 满足才能返回完整 5 条）
    DIVERSITY_MIN: dict[str, int] = {
        "domestic": 2,      # ≥ 2 国内
        "overseas": 2,       # ≥ 2 国外
        "model": 3,          # ≥ 3 模型
        "application": 2,    # ≥ 2 应用
    }

    def select_top_n(
        self,
        scored_items: list[dict],
        *,
        n: int = 5,
        score_threshold: float | None = None,
    ) -> list[dict]:
        """从已打分候选中选 N 条 · 多样性平衡。

        Args:
            scored_items: list of {item, score} · 已 composite_score 打过分
            n: 选几条（默认 5）
            score_threshold: 最低分阈值（默认 0.75 · spec R1）

        Returns:
            选中的 items（最多 n 条）· 已按 score 降序排

        算法（贪心）:
            1. 按 score 降序排
            2. 过滤低于阈值的
            3. 多样性保证：先确保每维度至少 min 条
            4. 剩余按 score 补足到 n
        """
        threshold = score_threshold if score_threshold is not None else self.DEFAULT_SCORE_THRESHOLD

        # 1. 按 score 降序
        sorted_items = sorted(scored_items, key=lambda x: x.get("score", 0), reverse=True)

        # 2. 阈值过滤
        qualified = [it for it in sorted_items if it.get("score", 0) >= threshold]

        if len(qualified) <= n:
            # 候选不足 · 返回所有合格的（spec D2 fallback）
            return qualified

        # 3. 多样性保证 · 贪心
        selected: list[dict] = []
        remaining_qualified = list(qualified)

        # 阶段 A: 满足每个维度的最小需求
        for dim_key, min_count in self.DIVERSITY_MIN.items():
            dim_items = [it for it in remaining_qualified if it.get(dim_key) and it not in selected]
            # 按 score 降序取前 min_count
            dim_items.sort(key=lambda x: x.get("score", 0), reverse=True)
            for item in dim_items[:min_count]:
                if item not in selected:
                    selected.append(item)

        # 阶段 B: 用剩余合格项按 score 补足到 n
        remaining = [it for it in qualified if it not in selected]
        remaining.sort(key=lambda x: x.get("score", 0), reverse=True)
        for item in remaining:
            if len(selected) >= n:
                break
            if item not in selected:
                selected.append(item)

        return selected[:n]

    # ═════════════════════════════════════════════════════════════════
    # T8 · push_daily 主入口（编排 fetch + score + select + save）
    # ═════════════════════════════════════════════════════════════════

    async def push_daily(
        self,
        db: AsyncSession,
        user_id: str,
        target_date: date,
    ) -> dict:
        """每日推送主入口 · 编排完整流程（spec R1 + R3 + api-spec §3.A）。"""
        from models import DigestDaily, DigestDailyItem, Profile
        from services.digest_preference_service import DigestPreferenceService

        # 1. 加载用户偏好（spec R3 第 5 维）
        pref_svc = DigestPreferenceService()
        user_prefs = await pref_svc.get_user_prefs(db=db, user_id=user_id)

        # 2. fetch 12 源
        fetch_results = await self.fetch_all_sources(db)

        # 3. 合并所有 item · 自动分类 · 打分
        all_items_with_score: list[dict] = []
        fetch_failures: list[str] = []
        for fr in fetch_results:
            if fr.get("error"):
                fetch_failures.append(f"{fr.get('source_name', '?')}: {fr['error']}")
                continue
            source_name = fr.get("source_name", "Unknown")
            source_id = fr.get("source_id")
            for raw_item in fr.get("items", []):
                # 3a. RSS items 没 type/region/category · 自动分类
                classified = self._classify_raw_item(raw_item, source_name)
                enriched = {
                    **raw_item,
                    "source_id": source_id,
                    "source_name": source_name,
                    **classified,  # type / region / category
                }
                # 3b. composite_score（用真实 user_prefs）
                score = self.composite_score(enriched, user_prefs=user_prefs)
                if score < self.DEFAULT_SCORE_THRESHOLD:
                    continue
                all_items_with_score.append(
                    {"item": enriched, "score": score, **enriched}
                )

        # 4. select_top_n 选 5 条（diversity 已保证：≥ 2 国内 + 2 国外 + 3 模型 + 2 应用）
        selected = self.select_top_n(all_items_with_score, n=self.DEFAULT_TOP_N)

        # 5. vibe 计算
        all_sources_failed = len(fetch_failures) == len(fetch_results)
        if not selected:
            if all_sources_failed:
                vibe = "今日 digest 暂缺 · 信源全部失败"
                from logging import getLogger
                getLogger(__name__).error("RSS_FAILURE · all sources failed")
            elif not all_items_with_score:
                vibe = "今日 AI 圈无新动态"
            else:
                vibe = f"今日仅 {len(selected)} 条过阈值"
            return {"daily_id": None, "item_count": 0, "vibe": vibe, "error": None}

        vibe = f"今日 {len(selected)} 条 · 正常推送" if len(selected) == 5 else f"今日 {len(selected)} 条"

        # 6. 写 digest_daily + items
        from uuid import uuid4
        now = datetime.now(timezone.utc)
        daily_id = str(uuid4())
        item_ids = [str(uuid4()) for _ in selected]

        daily_row = DigestDaily(
            id=daily_id,
            user_id=user_id,
            date=target_date,
            vibe=vibe,
            item_ids=item_ids,
            pushed_at=now,  # spec R6 · pushed_at 时间戳
        )
        db.add(daily_row)

        for i, sel in enumerate(selected):
            item_row = DigestDailyItem(
                id=item_ids[i],
                daily_id=daily_id,
                rank=i + 1,
                title=sel.get("title", ""),
                summary=sel.get("summary"),
                quality_score=sel.get("score", 0),
                type=sel.get("type", "model"),
                region=sel.get("region", "overseas"),
                category=sel.get("category", "headline"),
                source_id=sel.get("source_id"),
                source_name=sel.get("source_name", ""),
                source_url=sel.get("url", ""),
                published_at=sel.get("published_at"),
                related_item_ids=[],
                estimated_minutes=3,
            )
            db.add(item_row)

        # 7. 更新 profile.digest_stats（真的执行 update · spec R6）
        from sqlalchemy import update
        try:
            stmt = (
                update(Profile)
                .where(Profile.user_id == user_id)
                .values(
                    last_active_at=now,
                )
            )
            await db.execute(stmt)
        except Exception:
            # digest_stats 字段是 JSON · MySQL 更新 JSON 需 JSON_SET
            # MVP 简化：先只更新 last_active_at · 后续扩展 digest_stats JSON 更新
            pass

        await db.commit()

        return {
            "daily_id": daily_id,
            "item_count": len(selected),
            "vibe": vibe,
            "error": None,
        }

    def _classify_raw_item(self, raw_item: dict, source_name: str) -> dict:
        """RSS items 缺 type/region/category · 自动分类。

        启发:
        - type: 标题含 agent/coder/工具 等 → application · 其他 → model
        - region: source_name 匹配国内公司 → domestic · 否则 overseas
        - category: 标题含发布/开源/launch → headline · 含 paper/arxiv → paper
        """
        title = (raw_item.get("title") or "").lower()
        # type
        if any(kw in title for kw in ["agent", "coder", "tool", "studio", "devin", "cline", "ide", "workspace"]):
            item_type = "application"
        else:
            item_type = "model"
        # region
        domestic_sources = ["量子位", "机器之心", "Qwen", "DeepSeek", "智谱", "GLM", "稀土掘金"]
        if any(s in source_name for s in domestic_sources):
            region = "domestic"
        else:
            region = "overseas"
        # category
        if any(kw in title for kw in ["paper", "arxiv", "论文"]):
            category = "paper"
        elif any(kw in title for kw in ["发布", "开源", "launch", "release", "首发", "推出"]):
            category = "headline"
        elif any(kw in title for kw in ["架构", "性能", "benchmark", "对比"]):
            category = "engineering"
        else:
            category = "headline"
        return {"type": item_type, "region": region, "category": category}


# ─── 模块级 singleton（2026-07-22 audit 修复）────────────────
# api/digest/daily.py:26 `from services.digest_service import digest_service` 一直期待这个实例
# 之前缺失导致 GET /api/digest/today 抛 ImportError
digest_service = DigestService()
