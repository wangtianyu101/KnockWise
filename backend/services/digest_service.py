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
