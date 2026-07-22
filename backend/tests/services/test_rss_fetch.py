"""RSS fetch tests (T23 重写 · 2026-07-22) - 多源 RSS/Atom 解析 + 重试 + 部分失败。

覆盖 8 个 seed_data/digest_sources.json 配置的信源类型：
- RSS 2.0 (Anthropic / DeepMind / HuggingFace / DeepSeek / 量子位 / 机器之心)
- Atom 1.0 (Qwen / GLM GitHub releases)

实现位置：services/digest_service.py::DigestService._fetch_and_parse + _parse_rss_xml

测试策略：
- HTTP 层用 `patch.object(service, '_fetch_and_parse', ...)` mock（避免真请求）
- 解析层用 inline XML 字符串 fixture（RSS 2.0 + Atom 1.0 + 中文 CDATA）
- 重试用 `side_effect` 控制失败次数
"""
from __future__ import annotations

from unittest.mock import ANY, AsyncMock, MagicMock, patch

import httpx
import pytest

from services.digest_service import DigestService


# ── Fixtures ────────────────────────────────────────────────


def make_source(
    id: str = "src-1",
    name: str = "Anthropic News",
    url: str = "https://www.anthropic.com/news/rss.xml",
    enabled: bool = True,
) -> MagicMock:
    """Build a mock DigestSource with attributes the service reads."""
    src = MagicMock()
    src.id = id
    src.name = name
    src.url = url
    src.enabled = enabled
    return src


# Anthropic-style RSS 2.0（<channel><item> · <pubDate> RFC 822）
SAMPLE_ANTHROPIC_RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Anthropic News</title>
    <link>https://www.anthropic.com/news</link>
    <description>Announcements from Anthropic</description>
    <item>
      <title>Introducing Claude 4</title>
      <link>https://www.anthropic.com/news/claude-4</link>
      <description>Our latest model with extended thinking.</description>
      <pubDate>Mon, 22 Jul 2026 10:00:00 +0000</pubDate>
    </item>
    <item>
      <title>Constitutional AI Update</title>
      <link>https://www.anthropic.com/news/cai-update</link>
      <description>Improvements to our safety training.</description>
      <pubDate>Sun, 21 Jul 2026 15:30:00 +0000</pubDate>
    </item>
  </channel>
</rss>"""


# GitHub releases-style Atom 1.0（<feed><entry> · <updated> ISO 8601 · <link href=>）
SAMPLE_GITHUB_ATOM = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>Qwen3 Releases</title>
  <link href="https://github.com/QwenLM/Qwen3/releases"/>
  <updated>2026-07-22T08:00:00Z</updated>
  <entry>
    <title>Qwen3-72B Release</title>
    <link href="https://github.com/QwenLM/Qwen3/releases/tag/v3.0"/>
    <summary>Major release with 72B parameters and improved reasoning.</summary>
    <updated>2026-07-22T08:00:00Z</updated>
  </entry>
  <entry>
    <title>Qwen3-7B Beta</title>
    <link href="https://github.com/QwenLM/Qwen3/releases/tag/v3.0-beta"/>
    <summary>Beta release of the 7B variant.</summary>
    <updated>2026-07-15T08:00:00Z</updated>
  </entry>
</feed>"""


# 量子位-style Chinese RSS（CDATA 包裹 HTML 内容 · 中文标题）
SAMPLE_QBITAI_RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>量子位</title>
    <link>https://www.qbitai.com</link>
    <description>AI 前沿资讯</description>
    <item>
      <title><![CDATA[GPT-5 发布：推理能力大幅提升]]></title>
      <link>https://www.qbitai.com/2026/07/gpt5-release.html</link>
      <description><![CDATA[<p>OpenAI 今天发布 GPT-5，在多个基准上超越前代。</p>]]></description>
      <pubDate>Tue, 22 Jul 2026 12:00:00 +0800</pubDate>
    </item>
  </channel>
</rss>"""


# ── Tests · 解析层（_parse_rss_xml）───────────────────────────────


class TestParseRssXml:
    """测试 RSS/Atom XML 解析 · 不走 HTTP（直接调 _parse_rss_xml）"""

    def test_anthropic_rss_parses(self):
        """RSS 2.0 解析 · 2 个 item · RFC 822 日期转 ISO 8601"""
        service = DigestService()
        items = service._parse_rss_xml(SAMPLE_ANTHROPIC_RSS)

        assert len(items) == 2
        assert items[0]["title"] == "Introducing Claude 4"
        assert items[0]["url"] == "https://www.anthropic.com/news/claude-4"
        assert "Our latest model" in items[0]["summary"]
        # pubDate RFC 822 → ISO 8601（含时区）
        assert items[0]["published_at"] is not None
        assert "2026-07-22" in items[0]["published_at"]

    def test_github_atom_parses(self):
        """Atom 1.0 解析 · <feed><entry> · <link href=> 属性取值 · ISO 8601 直通"""
        service = DigestService()
        items = service._parse_rss_xml(SAMPLE_GITHUB_ATOM)

        assert len(items) == 2
        assert items[0]["title"] == "Qwen3-72B Release"
        assert items[0]["url"] == "https://github.com/QwenLM/Qwen3/releases/tag/v3.0"
        assert items[0]["published_at"] == "2026-07-22T08:00:00Z"

    def test_qbitai_parses(self):
        """中文 RSS · CDATA 内容 · 时区 +0800"""
        service = DigestService()
        items = service._parse_rss_xml(SAMPLE_QBITAI_RSS)

        assert len(items) == 1
        assert "GPT-5 发布" in items[0]["title"]
        assert "qbitai.com" in items[0]["url"]
        # CDATA 内的 HTML 标签应保留（不做清洗）
        assert "<p>" in items[0]["summary"]


# ── Tests · 重试层（_fetch_one_with_retry）────────────────────────────


class TestFetchOneRetry:
    """测试单源重试机制（spec § 6.7 verify-loop）"""

    @pytest.mark.asyncio
    async def test_retry_recovers_from_transient_failure(self):
        """前 2 次失败 · 第 3 次直连成功 → 不进入 RSSHub fallback。"""

        service = DigestService()
        src = make_source()

        call_count = {"n": 0}

        async def flaky_parse(url):
            call_count["n"] += 1
            if call_count["n"] < 3:
                raise httpx.ConnectError("transient")
            return [{"title": "third try success"}]

        with patch.object(service, "_fetch_and_parse", side_effect=flaky_parse), \
             patch.object(service, "_update_source_after_fetch", AsyncMock()):
            with patch("asyncio.sleep", AsyncMock()):  # skip sleep
                result = await service._fetch_one_with_retry(db=AsyncMock(), source=src)

        assert result["error"] is None
        assert call_count["n"] == 3
        assert len(result["items"]) == 1

    @pytest.mark.asyncio
    async def test_rsshub_fallback_after_direct_retries(self):
        """直连连续失败后只调用一次配置的 RSSHub route。"""
        service = DigestService()
        src = make_source(name="机器之心", url="https://www.jiqizhixin.com/rss")
        fallback_url = "http://localhost:1200/jiqizhixin"

        async def fetch(url):
            if url == fallback_url:
                return [{"title": "fallback item", "url": "https://example.com/item"}]
            raise httpx.ConnectError("direct source down")

        with patch.object(service, "_fetch_and_parse", side_effect=fetch) as mock_fetch, \
             patch.object(service, "_update_source_after_fetch", AsyncMock()) as mock_update, \
             patch.object(service, "_rsshub_fallback_url", return_value=fallback_url), \
             patch("asyncio.sleep", AsyncMock()):
            result = await service._fetch_one_with_retry(db=AsyncMock(), source=src)

        assert result["error"] is None
        assert result["items"][0]["title"] == "fallback item"
        assert mock_fetch.await_count == 4  # 3 direct + 1 RSSHub
        mock_update.assert_awaited_once_with(
            ANY, src.id, success=True, count=1, error=None
        )


# ── Tests · 并行抓取层（fetch_all_sources）─────────────────────────────


class TestFetchAllSources:
    """测试多源并行抓取 · 部分失败不影响其他源"""

    @pytest.mark.asyncio
    async def test_partial_failure_continues(self):
        """8 源中 2 源失败 · 6 源正常 · 失败源 error 非空 · 成功源 items 填充"""
        service = DigestService()
        db = AsyncMock()

        # 模拟 8 个源
        sources = [make_source(id=f"src-{i}", name=f"Source {i}", url=f"https://test.com/{i}") for i in range(8)]

        # 源 1 和 5 失败，其他成功
        async def fetch_side_effect(url):
            if "1" in url or "5" in url:
                raise httpx.ConnectError(f"failed: {url}")
            return [{"title": f"item from {url}", "url": url, "summary": "ok", "published_at": None}]

        with patch.object(service, "_list_enabled_sources", AsyncMock(return_value=sources)), \
             patch.object(service, "_fetch_and_parse", side_effect=fetch_side_effect), \
             patch.object(service, "_update_source_after_fetch", AsyncMock()), \
             patch("asyncio.sleep", AsyncMock()):
            results = await service.fetch_all_sources(db)

        assert len(results) == 8
        # 6 个成功
        success = [r for r in results if r["error"] is None]
        assert len(success) == 6
        assert all(len(r["items"]) == 1 for r in success)
        # 2 个失败
        failed = [r for r in results if r["error"] is not None]
        assert len(failed) == 2
        assert "ConnectError" in failed[0]["error"]
        assert all(r["items"] == [] for r in failed)

    @pytest.mark.asyncio
    async def test_duplicate_articles_are_removed_across_sources(self):
        """同一 canonical URL 在多个源出现时只保留第一次。"""
        service = DigestService()
        sources = [make_source(id="src-1"), make_source(id="src-2")]
        duplicated = {
            "title": "Same launch",
            "url": "https://example.com/post?utm_source=rss",
            "summary": "same",
            "published_at": None,
        }

        async def fetch_one(_db, source):
            item = dict(duplicated)
            if source.id == "src-2":
                item["url"] = "https://example.com/post"
            return {
                "source_id": source.id,
                "source_name": source.name,
                "items": [item],
                "error": None,
            }

        with patch.object(service, "_list_enabled_sources", AsyncMock(return_value=sources)), \
             patch.object(service, "_fetch_one_with_retry", side_effect=fetch_one):
            results = await service.fetch_all_sources(AsyncMock())

        assert sum(len(result["items"]) for result in results) == 1
