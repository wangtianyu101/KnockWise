"""Tests for DigestService (T5: 2026-07-17 实施).

测试 fetch_all_sources 行为:
- 8 源全部成功 → 8 个结果 · items 填充
- 部分源失败 → 失败源 error 非空 · 成功源正常
- 全部源失败 → 所有 result error · 0 items
- 重试 3 次机制（验证 _fetch_one_with_retry 调用次数）
"""
from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from services.digest_service import DigestService


# ── Fixtures ────────────────────────────────────────────────


def make_source(
    id: str = "src-1",
    name: str = "Test Source",
    url: str = "https://test.com/feed",
    enabled: bool = True,
    is_default: bool = True,
    user_id: str | None = None,
) -> MagicMock:
    """Build a mock DigestSource with the attributes the service reads."""
    src = MagicMock()
    src.id = id
    src.name = name
    src.url = url
    src.enabled = enabled
    src.is_default = is_default
    src.user_id = user_id
    return src


SAMPLE_RSS = """<?xml version="1.0"?>
<rss version="2.0">
  <channel>
    <title>Test Feed</title>
    <link>https://test.com</link>
    <description>Test</description>
    <item>
      <title>First article</title>
      <link>https://test.com/1</link>
      <description>First summary</description>
      <pubDate>Fri, 17 Jul 2026 12:00:00 GMT</pubDate>
    </item>
    <item>
      <title>Second article</title>
      <link>https://test.com/2</link>
      <description>Second summary</description>
      <pubDate>Fri, 17 Jul 2026 13:00:00 GMT</pubDate>
    </item>
  </channel>
</rss>"""


SAMPLE_ATOM = """<?xml version="1.0"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>GitHub Releases</title>
  <link href="https://github.com/owner/repo/releases"/>
  <entry>
    <title>v1.0.0</title>
    <link href="https://github.com/owner/repo/releases/tag/v1.0.0"/>
    <updated>2026-07-17T10:00:00Z</updated>
    <summary>First release</summary>
  </entry>
</feed>"""


# ── Tests ──────────────────────────────────────────────────


class TestFetchAllSourcesHappyPath:
    @pytest.mark.asyncio
    async def test_all_sources_succeed(self):
        """8 源全部成功 → 8 个 result · 每个含 items · 0 error。"""
        sources = [make_source(id=f"src-{i}", url=f"https://test{i}.com/feed") for i in range(3)]
        service = DigestService()

        with patch.object(service, "_list_enabled_sources", AsyncMock(return_value=sources)), \
             patch.object(service, "_fetch_one_with_retry", AsyncMock(side_effect=lambda db, src, _lock=None: {
                 "source_id": src.id, "source_name": src.name,
                 "items": [{"title": f"item {src.id}"}], "error": None,
             })):
            results = await service.fetch_all_sources(db=AsyncMock())

        assert len(results) == 3
        assert all(r["error"] is None for r in results)
        assert all(len(r["items"]) == 1 for r in results)


class TestFetchAllSourcesPartialFailure:
    @pytest.mark.asyncio
    async def test_one_source_fails_others_succeed(self):
        """1 源失败 2 源成功 · 失败源 error 非空 · 成功源 items 填充。"""
        sources = [
            make_source(id="src-1"),
            make_source(id="src-2"),
            make_source(id="src-3"),
        ]
        service = DigestService()

        async def fake_fetch(db, src, _lock=None):
            if src.id == "src-2":
                return {"source_id": "src-2", "source_name": src.name,
                        "items": [], "error": "ConnectError: timeout"}
            return {"source_id": src.id, "source_name": src.name,
                    "items": [{"title": f"item {src.id}"}], "error": None}

        with patch.object(service, "_list_enabled_sources", AsyncMock(return_value=sources)), \
             patch.object(service, "_fetch_one_with_retry", side_effect=fake_fetch):
            results = await service.fetch_all_sources(db=AsyncMock())

        assert len(results) == 3
        failed = [r for r in results if r["error"] is not None]
        succeeded = [r for r in results if r["error"] is None]
        assert len(failed) == 1
        assert failed[0]["source_id"] == "src-2"
        assert "timeout" in failed[0]["error"]
        assert len(succeeded) == 2

    @pytest.mark.asyncio
    async def test_all_sources_fail(self):
        """3 源全失败 · 全部 result error 非空 · 0 items。"""
        sources = [make_source(id=f"src-{i}") for i in range(3)]
        service = DigestService()

        async def always_fail(db, src):
            return {"source_id": src.id, "source_name": src.name,
                    "items": [], "error": f"fail {src.id}"}

        with patch.object(service, "_list_enabled_sources", AsyncMock(return_value=sources)), \
             patch.object(service, "_fetch_one_with_retry", side_effect=always_fail):
            results = await service.fetch_all_sources(db=AsyncMock())

        assert len(results) == 3
        assert all(r["error"] is not None for r in results)
        assert all(r["items"] == [] for r in results)


class TestFetchAllSourcesExceptionHandling:
    @pytest.mark.asyncio
    async def test_unexpected_exception_in_one_source_does_not_break_others(self):
        """_fetch_one_with_retry 抛非预期异常 · 被 gather return_exceptions 捕获 · 转为 error 记录。"""
        sources = [make_source(id="src-1"), make_source(id="src-2")]
        service = DigestService()

        async def one_crashes(db, src, _lock=None):
            if src.id == "src-1":
                raise RuntimeError("Unexpected boom")
            return {"source_id": src.id, "source_name": src.name,
                    "items": [{"title": "x"}], "error": None}

        with patch.object(service, "_list_enabled_sources", AsyncMock(return_value=sources)), \
             patch.object(service, "_fetch_one_with_retry", side_effect=one_crashes):
            results = await service.fetch_all_sources(db=AsyncMock())

        assert len(results) == 2
        # src-1 was caught as exception → error populated
        assert results[0]["source_id"] == "src-1"
        assert results[0]["error"] is not None
        assert "RuntimeError" in results[0]["error"]
        assert results[0]["items"] == []
        # src-2 succeeded
        assert results[1]["error"] is None
        assert len(results[1]["items"]) == 1


class TestFetchAllSourcesNoSources:
    @pytest.mark.asyncio
    async def test_no_enabled_sources_returns_empty(self):
        """0 enabled 源 → 返回空 list · 不抛异常。"""
        service = DigestService()

        with patch.object(service, "_list_enabled_sources", AsyncMock(return_value=[])):
            results = await service.fetch_all_sources(db=AsyncMock())

        assert results == []


# ═════════════════════════════════════════════════════════════════
# 内部方法测试
# ═════════════════════════════════════════════════════════════════


class TestFetchOneWithRetry:
    @pytest.mark.asyncio
    async def test_success_first_attempt_no_retry(self):
        """第一次就成功 → 不重试 · 调 _update_source_after_fetch 1 次。"""
        service = DigestService()
        src = make_source()

        with patch.object(service, "_fetch_and_parse", AsyncMock(return_value=[{"title": "x"}])), \
             patch.object(service, "_update_source_after_fetch", AsyncMock()) as update_mock:
            result = await service._fetch_one_with_retry(db=AsyncMock(), source=src)

        assert result["error"] is None
        assert len(result["items"]) == 1
        update_mock.assert_called_once()

    @pytest.mark.asyncio
    async def test_retries_3_times_then_succeeds(self):
        """前 2 次失败 · 第 3 次成功 → 调 _fetch_and_parse 共 3 次。"""
        service = DigestService()
        src = make_source()

        call_count = {"n": 0}

        async def flaky_parse(url):
            call_count["n"] += 1
            if call_count["n"] < 3:
                raise httpx.ConnectError("flaky")
            return [{"title": "third try success"}]

        with patch.object(service, "_fetch_and_parse", side_effect=flaky_parse), \
             patch.object(service, "_update_source_after_fetch", AsyncMock()) as update_mock:
            with patch("asyncio.sleep", AsyncMock()):  # skip sleep
                result = await service._fetch_one_with_retry(db=AsyncMock(), source=src)

        assert result["error"] is None
        assert call_count["n"] == 3
        update_mock.assert_called_once()

    @pytest.mark.asyncio
    async def test_3_failures_records_error(self):
        """3 次都失败 → 调 _update_source_after_fetch(success=False, error=...) · 1 次。"""
        service = DigestService()
        src = make_source()

        with patch.object(service, "_fetch_and_parse", AsyncMock(side_effect=httpx.ConnectError("fail"))), \
             patch.object(service, "_update_source_after_fetch", AsyncMock()) as update_mock:
            with patch("asyncio.sleep", AsyncMock()):
                result = await service._fetch_one_with_retry(db=AsyncMock(), source=src)

        assert result["error"] is not None
        assert "ConnectError" in result["error"]
        assert result["items"] == []
        update_mock.assert_called_once()
        # Verify error was passed to update
        call_kwargs = update_mock.call_args.kwargs
        assert call_kwargs["success"] is False
        assert "ConnectError" in call_kwargs["error"]


class TestParseRssXml:
    def test_parses_rss_2_0(self):
        service = DigestService()
        items = service._parse_rss_xml(SAMPLE_RSS)
        assert len(items) == 2
        assert items[0]["title"] == "First article"
        assert items[0]["url"] == "https://test.com/1"
        assert items[1]["title"] == "Second article"

    def test_parses_atom_1_0(self):
        service = DigestService()
        items = service._parse_rss_xml(SAMPLE_ATOM)
        assert len(items) == 1
        assert items[0]["title"] == "v1.0.0"
        assert items[0]["url"] == "https://github.com/owner/repo/releases/tag/v1.0.0"
        assert items[0]["published_at"] == "2026-07-17T10:00:00Z"

    def test_handles_empty_xml(self):
        service = DigestService()
        items = service._parse_rss_xml('<?xml version="1.0"?><rss><channel></channel></rss>')
        assert items == []

    def test_handles_malformed_xml_gracefully(self):
        """畸形 XML → ET.fromstring 抛 ParseError · 由 _fetch_one_with_retry 的 try 捕获。"""
        import pytest as _pytest
        service = DigestService()
        with _pytest.raises(Exception):  # xml.etree.ElementTree.ParseError
            service._parse_rss_xml("<not<valid<xml")
