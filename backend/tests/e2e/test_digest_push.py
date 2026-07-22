"""Real Scheduler → Service → MySQL → API → Email digest harness.

Only external boundaries are replaced: RSS, LLM, email and clock. Scheduler,
selection, ORM persistence, MySQL queries and FastAPI serialization stay real.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch
from uuid import uuid4
from zoneinfo import ZoneInfo

import httpx
import pytest
from sqlalchemy import delete, func, select
from sqlalchemy.engine import make_url

from core.config import settings
from core.database import Base, async_session, engine, get_db
from core.dependencies import get_current_user
from main import app
from models import (
    DigestDaily,
    DigestDailyItem,
    DigestSettings,
    DigestSource,
    User,
)
from services.digest_scheduler import DigestScheduler
from services.digest_service import DigestService


def _isolated_mysql_enabled() -> bool:
    if os.getenv("RUN_MYSQL_INTEGRATION") != "1":
        return False
    database_name = make_url(settings.database_url).database or ""
    return "test" in database_name.lower()


pytestmark = [
    pytest.mark.skipif(
        not _isolated_mysql_enabled(),
        reason="Requires RUN_MYSQL_INTEGRATION=1 and an isolated *test* database",
    ),
    pytest.mark.asyncio,
]


async def test_scheduler_to_api_persists_once_and_degrades_per_source():
    await _create_schema()
    user_id = str(uuid4())
    healthy_source_id = str(uuid4())
    failing_source_id = str(uuid4())
    fixed_now = datetime.now(timezone.utc).replace(second=0, microsecond=0)
    local_now = fixed_now.astimezone(ZoneInfo("Asia/Shanghai"))

    await _seed_user_and_sources(
        user_id=user_id,
        healthy_source_id=healthy_source_id,
        failing_source_id=failing_source_id,
        push_hour=local_now.hour,
        push_minute=local_now.minute,
    )

    llm_boundary = AsyncMock()

    async def enrich(items, _preferences):
        return [
            {**item, "summary": "LLM contract summary", "llm_fallback": False}
            for item in items
        ]

    llm_boundary.enrich_items.side_effect = enrich
    email_boundary = AsyncMock()
    email_boundary.send_daily_digest.return_value = {
        "message_id": "message-e2e-1",
        "error": None,
    }
    service = DigestService(
        llm_service=llm_boundary,
        email_service=email_boundary,
    )

    async def rss_boundary(url: str):
        if "failing" in url:
            raise httpx.ConnectError("fixture source unavailable")
        return [
            {
                "title": "AI agent 首次重大突破发布",
                "summary": "Fixture source summary",
                "url": "https://articles.example.com/agent-release",
                "published_at": fixed_now.isoformat(),
            }
        ]

    service._fetch_and_parse = AsyncMock(side_effect=rss_boundary)
    scheduler = DigestScheduler(service=service, now_provider=lambda: fixed_now)

    try:
        async with async_session() as session:
            with patch(
                "services.digest_service.asyncio.sleep", new_callable=AsyncMock
            ):
                first_run = await scheduler.check_and_push(session)
        await service.wait_for_notifications()

        assert first_run == {
            "checked": 1,
            "pushed": 1,
            "skipped": 0,
            "errors": 0,
        }

        async with async_session() as session:
            daily_count = await session.scalar(
                select(func.count(DigestDaily.id)).where(
                    DigestDaily.user_id == user_id
                )
            )
            daily = (
                await session.execute(
                    select(DigestDaily).where(DigestDaily.user_id == user_id)
                )
            ).scalar_one()
            item = (
                await session.execute(
                    select(DigestDailyItem).where(
                        DigestDailyItem.daily_id == daily.id
                    )
                )
            ).scalar_one()
            failed_source = await session.get(DigestSource, failing_source_id)

        assert daily_count == 1
        assert item.summary == "LLM contract summary"
        assert failed_source is not None
        assert "fixture source unavailable" in (failed_source.last_error or "")
        llm_boundary.enrich_items.assert_awaited_once()
        email_boundary.send_daily_digest.assert_awaited_once()

        # A fresh scheduler instance proves dedup survives process memory loss.
        restarted_scheduler = DigestScheduler(
            service=service,
            now_provider=lambda: fixed_now,
        )
        async with async_session() as session:
            second_run = await restarted_scheduler.check_and_push(session)
        assert second_run == {
            "checked": 1,
            "pushed": 0,
            "skipped": 1,
            "errors": 0,
        }
        email_boundary.send_daily_digest.assert_awaited_once()

        async def override_db():
            async with async_session() as session:
                yield session

        app.dependency_overrides[get_db] = override_db
        app.dependency_overrides[get_current_user] = lambda: User(
            id=user_id,
            email="harness@example.com",
        )
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://testserver",
        ) as client:
            response = await client.get(
                "/api/digest/today",
                params={"target_date": fixed_now.date().isoformat()},
            )

        assert response.status_code == 200
        body = response.json()
        assert body["item_count"] == 1
        assert body["items"][0]["title"] == "AI agent 首次重大突破发布"
        assert body["items"][0]["summary"] == "LLM contract summary"
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_current_user, None)
        await _cleanup(user_id, healthy_source_id, failing_source_id)


async def _create_schema() -> None:
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)


async def _seed_user_and_sources(
    *,
    user_id: str,
    healthy_source_id: str,
    failing_source_id: str,
    push_hour: int,
    push_minute: int,
) -> None:
    async with async_session() as session:
        session.add(
            User(
                id=user_id,
                email=f"harness-{user_id}@example.com",
                display_name="Harness E2E",
            )
        )
        await session.flush()
        session.add(
            DigestSettings(
                user_id=user_id,
                push_hour=push_hour,
                push_minute=push_minute,
                push_timezone="Asia/Shanghai",
                email_enabled=True,
                interested_tags=["AI"],
                blocked_tags=[],
            )
        )
        session.add_all(
            [
                DigestSource(
                    id=healthy_source_id,
                    user_id=user_id,
                    name="Harness Healthy",
                    url="https://fixtures.invalid/healthy.xml",
                    category="一手",
                    type="model",
                    region="overseas",
                    enabled=True,
                    is_default=False,
                ),
                DigestSource(
                    id=failing_source_id,
                    user_id=user_id,
                    name="Harness Failing",
                    url="https://fixtures.invalid/failing.xml",
                    category="一手",
                    type="model",
                    region="overseas",
                    enabled=True,
                    is_default=False,
                ),
            ]
        )
        await session.commit()


async def _cleanup(user_id: str, *source_ids: str) -> None:
    async with async_session() as session:
        daily_ids = select(DigestDaily.id).where(DigestDaily.user_id == user_id)
        await session.execute(
            delete(DigestDailyItem).where(DigestDailyItem.daily_id.in_(daily_ids))
        )
        await session.execute(
            delete(DigestDaily).where(DigestDaily.user_id == user_id)
        )
        await session.execute(
            delete(DigestSource).where(DigestSource.id.in_(source_ids))
        )
        await session.execute(
            delete(DigestSettings).where(DigestSettings.user_id == user_id)
        )
        await session.execute(delete(User).where(User.id == user_id))
        await session.commit()
