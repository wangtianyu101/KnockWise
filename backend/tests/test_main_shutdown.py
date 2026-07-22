"""Regression test for graceful FastAPI shutdown."""
import asyncio

import pytest


@pytest.mark.asyncio
async def test_shutdown_swallows_cancelled_archive_task(monkeypatch):
    import main

    task = asyncio.create_task(asyncio.sleep(60))
    monkeypatch.setitem(main.__dict__, "_archive_task", task)

    await main.on_shutdown()

    assert task.cancelled()
