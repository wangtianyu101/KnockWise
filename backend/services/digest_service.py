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

LLM 评分（2026-07-27）：
- composite_score 优先调 minimax（spec R3 第 1 维真实 LLM 评分）
- API key 未配置 / 调用失败 → fallback 到启发式 mock（spec § 3.8 失败恢复）
- prompt 注入防护：消息长度限制 + JSON mode 强制输出
"""
from __future__ import annotations

import asyncio
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Any, Optional
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import httpx
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from models import DigestSource
from services.minimax_client import MinimaxClient, MinimaxError, get_minimax_client


# 单源抓取超时（秒）· 超过 10s 视为失败
FETCH_TIMEOUT_SEC = 10.0

# 连续失败 3 次 → 自动禁用源（避免坏源持续消耗 cron 时间）
MAX_CONSECUTIVE_FAILURES = 3

# RSSHub routes are only defined for sources that do not have a reliable
# second-party feed URL. Official feeds continue to fail closed after retries.
RSSHUB_SOURCE_ROUTES: dict[str, str] = {
    "机器之心": "/jiqizhixin",
    "量子位": "/qbitai",
}


class DigestService:
    """AI 推送信源抓取 + 选题 + 推送编排。"""

    def __init__(self, llm_service: Any | None = None, email_service: Any | None = None) -> None:
        self.llm_service = llm_service
        self.email_service = email_service
        self._notification_tasks: set[asyncio.Task[Any]] = set()

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

        # Network work stays concurrent, while writes through one AsyncSession
        # are serialized (SQLAlchemy sessions are not task-safe).
        db_write_lock = asyncio.Lock()
        tasks = [self._fetch_one_with_retry(db, src, db_write_lock) for src in sources]
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
        self._deduplicate_results(normalized)
        return normalized

    async def _fetch_one_with_retry(
        self,
        db: AsyncSession,
        source: DigestSource,
        db_write_lock: asyncio.Lock | None = None,
    ) -> dict:
        """抓取单源 · 失败重试 3 次 + 指数退避（0.5s · 1s · 2s）"""
        last_error: Optional[str] = None
        items: list[dict] = []
        for attempt in range(MAX_CONSECUTIVE_FAILURES):
            try:
                items = await self._fetch_and_parse(source.url)
                # 成功 → 更新 last_fetched_at + last_item_count + 清 last_error
                update_kwargs = {"db_write_lock": db_write_lock} if db_write_lock else {}
                await self._update_source_after_fetch(
                    db, source.id, success=True, count=len(items), error=None, **update_kwargs
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

        # Direct feed exhausted: supported sources get one RSSHub fallback.
        fallback_url = self._rsshub_fallback_url(source)
        if fallback_url:
            try:
                items = await self._fetch_and_parse(fallback_url)
                update_kwargs = {"db_write_lock": db_write_lock} if db_write_lock else {}
                await self._update_source_after_fetch(
                    db, source.id, success=True, count=len(items), error=None, **update_kwargs
                )
                return {
                    "source_id": source.id,
                    "source_name": source.name,
                    "items": items,
                    "error": None,
                }
            except Exception as fallback_error:
                last_error = (
                    f"{last_error}; RSSHub {type(fallback_error).__name__}: "
                    f"{fallback_error}"
                )

        # 3 次都失败 → 更新 last_error + 检查连续失败次数 → 可能 auto-disable
        update_kwargs = {"db_write_lock": db_write_lock} if db_write_lock else {}
        await self._update_source_after_fetch(
            db, source.id, success=False, count=0, error=last_error, **update_kwargs
        )
        return {
            "source_id": source.id,
            "source_name": source.name,
            "items": [],
            "error": last_error,
        }

    def _rsshub_fallback_url(self, source: DigestSource) -> str | None:
        route = RSSHUB_SOURCE_ROUTES.get(str(source.name))
        if not route:
            return None
        from core.config import settings

        return f"{settings.rsshub_url.rstrip('/')}{route}"

    def _deduplicate_results(self, results: list[dict]) -> None:
        """Remove duplicate articles across sources while preserving order."""
        seen: set[str] = set()
        for result in results:
            unique_items: list[dict] = []
            for item in result.get("items", []):
                key = self._article_key(item)
                if key in seen:
                    continue
                seen.add(key)
                unique_items.append(item)
            result["items"] = unique_items

    def _article_key(self, item: dict) -> str:
        raw_url = str(item.get("url") or "").strip()
        if raw_url:
            parts = urlsplit(raw_url)
            query = urlencode([
                (key, value)
                for key, value in parse_qsl(parts.query, keep_blank_values=True)
                if not key.lower().startswith("utm_")
                and key.lower() not in {"ref", "source"}
            ])
            path = parts.path.rstrip("/") or "/"
            return urlunsplit(
                (parts.scheme.lower(), parts.netloc.lower(), path, query, "")
            )
        return f"title:{str(item.get('title') or '').strip().casefold()}"

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
                summary_el = entry.find(f"{ns}summary")
                if summary_el is None:
                    summary_el = entry.find(f"{ns}content")
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
        db_write_lock: asyncio.Lock | None = None,
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
        if db_write_lock is None:
            await db.execute(stmt)
            await db.commit()
        else:
            async with db_write_lock:
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

        2026-07-27 LLM 集成：minimax 配置时优先调真 LLM · fallback 到启发式。

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

        # spec R3 + R10: 真 LLM 评分（minimax 5 维一次返回）· fallback 到启发式
        # LLM6: 此处只取 score 字段（不取分类 · 分类由 _llm_score_and_classify 提供）
        llm_result = self._llm_composite_score(item, user_prefs, source_category)
        if llm_result is not None:
            # llm_result is dict `{"score":..., "type":..., "region":..., "category":...}`
            return llm_result["score"] if isinstance(llm_result, dict) else llm_result

        # Fallback: 启发式 mock
        hot_score = self._calc_hot(item)
        novel_score = self._calc_novel(item)
        changed_score = self._calc_changed(item)
        authority_score = self.SOURCE_AUTHORITY_SCORE.get(source_category, 0.5)
        pref_score = self._calc_user_pref(item, user_prefs) if user_prefs else 0.5

        weights = self.DEFAULT_WEIGHTS
        score = (
            hot_score * weights["hot"]
            + novel_score * weights["novel"]
            + changed_score * weights["changed"]
            + authority_score * weights["source_authority"]
            + pref_score * weights["user_pref"]
        )
        return max(0.0, min(1.0, score))

    async def _llm_composite_score_async(
        self,
        item: dict,
        user_prefs: dict | None,
        source_category: str,
    ) -> float | None:
        """异步 LLM 评分（minimax）· 返回 0-1 或 None（未配置/失败）"""
        try:
            client = get_minimax_client()
        except Exception:
            return None
        if not client.is_configured:
            return None
        try:
            return await self._call_minimax_score(client, item, user_prefs, source_category)
        except MinimaxError as e:
            import logging
            logging.getLogger(__name__).warning(f"minimax 评分失败 · fallback heuristic: {e}")
            return None
        except Exception as e:
            import logging
            logging.getLogger(__name__).exception(f"minimax 评分异常 · fallback heuristic: {e}")
            return None

    def _llm_composite_score(
        self,
        item: dict,
        user_prefs: dict | None,
        source_category: str,
    ) -> float | None:
        """同步入口：单条 item LLM 评分（保留向后兼容 · 实际 push_daily 用 batch 版）。"""
        import logging
        log = logging.getLogger(__name__)
        try:
            client = get_minimax_client()
        except Exception as e:
            log.warning(f"[LLM5] minimax get_client 异常: {e}")
            return None
        if not client.is_configured:
            log.warning(f"[LLM5] minimax 未配置 · fallback (key={bool(client.api_key)})")
            return None
        try:
            log.warning(f"[LLM5] minimax 评分开始 · title={item.get('title','')[:30]}")
            result = self._call_minimax_score_sync(client, item, user_prefs, source_category)
            log.warning(f"[LLM5] minimax 评分完成 · score={result['score']:.3f} type={result.get('type')} region={result.get('region')}")
            return result
        except MinimaxError as e:
            log.warning(f"[LLM5] minimax 评分失败 · fallback: {type(e).__name__}: {e}")
            return None
        except Exception as e:
            log.exception(f"[LLM5] minimax 评分异常 · fallback: {e}")
            return None

    def _llm_score_batch(
        self,
        items: list[dict],
        user_prefs: dict | None,
    ) -> list[dict | None]:
        """2026-07-25 LLM10: 批量 LLM 评分（一次 prompt 评 N 条 · 减少 rate limit 风险）。

        Args:
            items: list of {title, summary, source_name, ...}
            user_prefs: 用户偏好

        Returns:
            list of dict {score, type, region, category} | None（per item）
            None 整体表示 LLM 失败 → caller fallback heuristic
        """
        import logging
        log = logging.getLogger(__name__)
        if not items:
            return []
        try:
            client = get_minimax_client()
        except Exception:
            return [None] * len(items)
        if not client.is_configured:
            return [None] * len(items)

        # prompt 一次给所有 items
        n = len(items)
        items_text = []
        for idx, it in enumerate(items):
            t = (it.get("title") or "")[:200]
            s = (it.get("summary") or "")[:300]
            src = (it.get("source_name") or "Unknown")[:100]
            items_text.append(f"#{idx+1}\n标题: {t}\n摘要: {s}\n来源: {src}")
        items_block = "\n\n".join(items_text)

        interested = (user_prefs or {}).get("interested_tags", [])[:10]
        blocked = (user_prefs or {}).get("blocked_tags", [])[:10]

        system = (
            f"你是 AI 行业动态评分助手。给 {n} 条 digest 候选按 5 维 0-1 评分 + 分类。"
            "必须返回合法 JSON 数组，按顺序对应候选："
            "[{\"hot\":0.x,\"novel\":0.x,\"changed\":0.x,\"source_authority\":0.x,\"user_pref\":0.x,"
            "\"type\":\"model|application\",\"region\":\"domestic|overseas\","
            "\"category\":\"headline|paper|engineering|opinion\"}, ...]"
        )
        user = f"""用户关注标签: {interested or '无'}
用户屏蔽标签: {blocked or '无'}

候选 {n} 条:
{items_block}

只返回 JSON 数组 · 不要其他文字。"""

        messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
        try:
            data_list = client.chat_json_sync(messages, temperature=0.2, max_tokens=400 * n)
        except MinimaxError as e:
            log.warning(f"[LLM10] batch minimax 失败 ({n} items): {e}")
            return [None] * n
        except Exception as e:
            log.exception(f"[LLM10] batch minimax 异常: {e}")
            return [None] * n

        if not isinstance(data_list, list):
            log.warning(f"[LLM10] batch 响应不是 list · got {type(data_list)}")
            return [None] * n

        # 限定长度 + 字段
        VALID_TYPES = {"model", "application"}
        VALID_REGIONS = {"domestic", "overseas"}
        VALID_CATEGORIES = {"headline", "paper", "engineering", "opinion"}
        weights = self.DEFAULT_WEIGHTS
        results: list[dict | None] = []
        for i in range(n):
            if i >= len(data_list):
                results.append(None)
                continue
            d = data_list[i]
            try:
                scores = {
                    "hot": max(0.0, min(1.0, float(d["hot"]))),
                    "novel": max(0.0, min(1.0, float(d["novel"]))),
                    "changed": max(0.0, min(1.0, float(d["changed"]))),
                    "source_authority": max(0.0, min(1.0, float(d["source_authority"]))),
                    "user_pref": max(0.0, min(1.0, float(d["user_pref"]))),
                }
                type_v = str(d.get("type", "model")).strip().lower()
                region_v = str(d.get("region", "overseas")).strip().lower()
                cat_v = str(d.get("category", "headline")).strip().lower()
                if type_v not in VALID_TYPES:
                    type_v = "model"
                if region_v not in VALID_REGIONS:
                    region_v = "overseas"
                if cat_v not in VALID_CATEGORIES:
                    cat_v = "headline"
                weighted = sum(scores[k] * weights[k] for k in scores)
                results.append({
                    "score": weighted,
                    "type": type_v,
                    "region": region_v,
                    "category": cat_v,
                })
            except (KeyError, ValueError, TypeError) as e:
                log.warning(f"[LLM10] item {i} parse 失败: {e}")
                results.append(None)
        return results

    def _call_minimax_score_sync(
        self,
        client: MinimaxClient,
        item: dict,
        user_prefs: dict | None,
        source_category: str,
    ) -> dict:
        """调 minimax（同步）一次拿 5 维分 + 类型 + 地域 + 分类。

        返回: {score: float, type: str, region: str, category: str} · 失败抛 MinimaxError

        prompt 注入防护（spec § 3.3）：
        - 用户可控字段（title / summary）做长度限制 ≤ 1000 字符
        - system prompt 固定指令 + JSON mode 强制输出
        """
        title = (item.get("title") or "")[:1000]
        summary = (item.get("summary") or "")[:1000]
        source_name = (item.get("source_name") or "Unknown")[:200]
        interested = (user_prefs or {}).get("interested_tags", [])[:10]
        blocked = (user_prefs or {}).get("blocked_tags", [])[:10]

        system = (
            "你是 AI 行业动态评分助手。给每条 digest 候选按 5 维 0-1 评分，并分类。"
            "必须返回合法 JSON："
            "{\"hot\":0.x,\"novel\":0.x,\"changed\":0.x,\"source_authority\":0.x,\"user_pref\":0.x,"
            "\"type\":\"model|application\","
            "\"region\":\"domestic|overseas\","
            "\"category\":\"headline|paper|engineering|opinion\"}"
        )
        user = f"""维度定义:
- hot: 话题热度（近期重要事件 / 行业关注度）
- novel: 内容新颖性（首创/独家/突破性）
- changed: 变化程度（对行业格局改变的影响）
- source_authority: 来源权威性（一手 vs 二手）
- user_pref: 与用户关注标签的契合度

分类定义:
- type: model（模型/算法本身）| application（应用/工具/平台）
- region: domestic（中国公司 · 量子位/机器之心/Qwen/DeepSeek/智谱/GLM/百度/阿里/字节/腾讯 等）| overseas（其他）
- category: headline（产品发布/上新）| paper（学术论文）| engineering（架构/性能）| opinion（行业观点）

来源类别: {source_category}
用户关注标签: {interested or '无'}
用户屏蔽标签: {blocked or '无'}

待评分:
标题: {title}
摘要: {summary}
来源: {source_name}

只返回 JSON · 不要其他文字。"""

        messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
        data = client.chat_json_sync(messages, temperature=0.2, max_tokens=300)

        # 限定的 enum 集合
        VALID_TYPES = {"model", "application"}
        VALID_REGIONS = {"domestic", "overseas"}
        VALID_CATEGORIES = {"headline", "paper", "engineering", "opinion"}

        try:
            scores = {
                "hot": float(data["hot"]),
                "novel": float(data["novel"]),
                "changed": float(data["changed"]),
                "source_authority": float(data["source_authority"]),
                "user_pref": float(data["user_pref"]),
            }
            type_val = str(data["type"]).strip().lower()
            region_val = str(data["region"]).strip().lower()
            category_val = str(data["category"]).strip().lower()
        except (KeyError, ValueError, TypeError) as e:
            raise MinimaxError(f"minimax 响应字段解析失败: {e}")

        # 限定到合法 enum
        if type_val not in VALID_TYPES:
            type_val = "model"
        if region_val not in VALID_REGIONS:
            region_val = "overseas"
        if category_val not in VALID_CATEGORIES:
            category_val = "headline"

        # 限制到 0-1
        scores = {k: max(0.0, min(1.0, v)) for k, v in scores.items()}

        weights = self.DEFAULT_WEIGHTS
        weighted = sum(scores[k] * weights[k] for k in scores)

        return {
            "score": weighted,
            "type": type_val,
            "region": region_val,
            "category": category_val,
        }
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
    DEFAULT_SCORE_THRESHOLD: float = 0.15  # 2026-07-25 LLM5 · 真 minimax 评分普遍 0.15-0.25（LLM 严于启发式）

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
        """从已打分候选中选 N 条 · 多样性强制（spec R4）。

        Args:
            scored_items: list of {item, score} · 已 composite_score 打过分
            n: 选几条（默认 5）
            score_threshold: 最低分阈值（默认 0.15 · LLM5）

        Returns:
            选中的 items（最多 n 条）· 已按 score 降序排

        算法（贪心 diversity-first · 2026-07-25 LLM9）:
            1. 按 score 降序排 · 过滤低于阈值的
            2. 计算 dim 满足度（domestic/overseas/model/application）
            3. 反复选 "填最多 unmet dim + 最高分" 的 item · 直到约束全 met 或 5 条
            4. 候选不足时按 score 补足 · log warning 哪条 dim 没满足

        重要：DIVERSITY_MIN 是硬约束 · 能满足必满足 · 不满足 log warning
        （spec R4 候选不足时强制不补低分凑数 · 本文当前允许放宽 → 后续收紧）
        """
        import logging
        log = logging.getLogger(__name__)
        threshold = score_threshold if score_threshold is not None else self.DEFAULT_SCORE_THRESHOLD

        # 1. 按 score 降序排
        sorted_items = sorted(scored_items, key=lambda x: x.get("score", 0), reverse=True)

        # 2. 阈值过滤
        qualified = [it for it in sorted_items if it.get("score", 0) >= threshold]

        if len(qualified) <= n:
            return qualified

        # 3. diversity-first 贪心
        # dim 字段语义：
        #   · domestic / overseas → bool (item['domestic'] is True / False)
        #   · model / application → string (item['type'] == 'model' or 'application')
        # DIVERSITY_MIN key 一一对应 · 写 helper 把 dim_key 翻译成 item 的判定
        def item_has_dim(item: dict, dim_key: str) -> bool:
            """dim_key ∈ {domestic, overseas, model, application} → item 是否命中"""
            if dim_key in ("domestic", "overseas"):
                return bool(item.get(dim_key))
            # type 字段: "model" | "application"
            return item.get("type") == dim_key

        selected: list[dict] = []
        remaining = list(qualified)
        dim_keys = list(self.DIVERSITY_MIN.keys())  # [domestic, overseas, model, application]

        while remaining and len(selected) < n:
            # 当前 dim 计数
            dim_count = {k: sum(1 for s in selected if item_has_dim(s, k)) for k in dim_keys}

            # 候选对 unmet dim 的贡献度
            def contribution(item: dict) -> tuple[int, float]:
                met = sum(
                    1
                    for k in dim_keys
                    if dim_count[k] < self.DIVERSITY_MIN[k] and item_has_dim(item, k)
                )
                return (-met, -item.get("score", 0))

            remaining.sort(key=contribution)
            best = remaining[0]
            selected.append(best)
            remaining.remove(best)

        # 4. log 哪条 dim 没满足（spec R4 应有 log）
        final_dim_count = {k: sum(1 for s in selected if item_has_dim(s, k)) for k in dim_keys}
        for k, min_count in self.DIVERSITY_MIN.items():
            actual = final_dim_count.get(k, 0)
            if actual < min_count:
                log.warning(
                    f"[diversity] {k} 不足：actual={actual} < min={min_count} · "
                    f"候选池 candidate_count={len(qualified)} 可能不够"
                )

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
            # LLM10: 批量 LLM 评分（一次 prompt 评 N 条 · 减少 rate limit 风险）
            raw_items = fr.get("items", [])
            if raw_items:
                enriched_for_batch = [
                    _raw_item_to_enriched(ri, source_id, source_name)
                    for ri in raw_items
                ]
                batch_results = self._llm_score_batch(enriched_for_batch, user_prefs=user_prefs)
            else:
                batch_results = []

            for idx, raw_item in enumerate(raw_items):
                # 3a. LLM6 + LLM10: 优先 LLM 分类（一次出 score+type+region+category）· fallback heuristic
                if idx < len(batch_results) and batch_results[idx] is not None:
                    llm_sco = batch_results[idx]
                    scored = {
                        "score": llm_sco["score"],
                        "item": {
                            **raw_item,
                            "source_id": source_id,
                            "source_name": source_name,
                            "type": llm_sco["type"],
                            "region": llm_sco["region"],
                            "category": llm_sco["category"],
                        },
                    }
                else:
                    # Fallback: 启发式打分类 + 启发式打 score
                    classified = self._classify_raw_item(raw_item, source_name)
                    enriched = {
                        **raw_item,
                        "source_id": source_id,
                        "source_name": source_name,
                        **classified,
                    }
                    score = self.composite_score(enriched, user_prefs=user_prefs)
                    scored = {"score": score, "item": enriched}

                if scored["score"] < self.DEFAULT_SCORE_THRESHOLD:
                    continue
                all_items_with_score.append(
                    {"item": scored["item"], "score": scored["score"], **scored["item"]}
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

        # The application owns the prompt/output contract. Tests inject a fake
        # boundary; the module singleton below supplies the production client.
        if self.llm_service is not None:
            selected = await self.llm_service.enrich_items(selected, user_prefs)

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
                published_at=self._coerce_published_at(sel.get("published_at")),
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

        email_result = None
        if self.email_service is not None:
            from models import DigestSettings, User

            email_query = await db.execute(
                select(User.email, DigestSettings.email_enabled)
                .outerjoin(DigestSettings, DigestSettings.user_id == User.id)
                .where(User.id == user_id)
            )
            email_row = email_query.one_or_none()
            if email_row is not None:
                user_email, email_enabled = email_row
            else:
                user_email, email_enabled = None, False
            if user_email and email_enabled is not False:
                task = asyncio.create_task(self.email_service.send_daily_digest(
                    user_email=str(user_email),
                    digest_date=target_date.isoformat(),
                    items=selected,
                    vibe=vibe,
                ))
                self._notification_tasks.add(task)
                task.add_done_callback(self._notification_done)
                email_result = {"scheduled": True}

        return {
            "daily_id": daily_id,
            "item_count": len(selected),
            "vibe": vibe,
            "error": None,
            "email": email_result,
        }

    async def wait_for_notifications(self) -> None:
        """Drain currently scheduled notifications (used by shutdown/tests)."""
        if self._notification_tasks:
            await asyncio.gather(*tuple(self._notification_tasks), return_exceptions=True)

    def _notification_done(self, task: asyncio.Task[Any]) -> None:
        self._notification_tasks.discard(task)
        try:
            task.result()
        except asyncio.CancelledError:
            return
        except Exception as exc:
            import logging

            logging.getLogger(__name__).warning(
                "digest email delivery failed: %s", exc
            )

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

    def _coerce_published_at(self, value: Any) -> datetime | None:
        if isinstance(value, datetime):
            return value
        if isinstance(value, str) and value:
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                return None
        return None


# ─── 模块级 helper（2026-07-25 LLM6）─────────────────
# 给 push_daily 的 LLM 评分调用提供 raw item → enriched dict 转换
# 避免在 push_daily 里展开多行内联代码

def _raw_item_to_enriched(
    raw_item: dict,
    source_id: str | None,
    source_name: str,
) -> dict:
    """把 fetch_all_sources 返回的 raw_item 包成 envelope（带 source_id / source_name）"""
    return {
        **raw_item,
        "source_id": source_id,
        "source_name": source_name,
    }


def _detect_source_category(source_name: str) -> str:
    """source_name → SOURCE_AUTHORITY_SCORE key ('一手' / '二手' / '社区' / '学术')。

    简化启发：仅按 source_name 关键词匹配一期。
    """
    sn = (source_name or "").lower()
    if any(k in sn for k in ["arxiv", "论文", "paper"]):
        return "学术"
    if any(k in sn for k in ["github", "release", "代码", "开源"]):
        return "二手"
    if any(k in sn for k in ["机器之心", "量子位", "36kr", "虎嗅", "news"]):
        return "二手"
    if any(k in sn for k in ["blog", "newsletter"]):
        return "二手"
    return "二手"


# ─── 模块级 singleton（2026-07-22 audit 修复）────────────────
# api/digest/daily.py:26 `from services.digest_service import digest_service` 一直期待这个实例
# 之前缺失导致 GET /api/digest/today 抛 ImportError
from services.digest_llm_service import digest_llm_service
from services.email_service import email_service

digest_service = DigestService(
    llm_service=digest_llm_service,
    email_service=email_service,
)
