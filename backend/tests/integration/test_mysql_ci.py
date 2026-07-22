"""Real MySQL smoke test used by the backend CI service container."""
from __future__ import annotations

import os

import pytest
from sqlalchemy import text

from core.database import engine


@pytest.mark.skipif(
    os.getenv("RUN_MYSQL_INTEGRATION") != "1",
    reason="Requires the isolated MySQL service configured by the CI workflow",
)
@pytest.mark.asyncio
async def test_mysql_temporary_table_round_trip():
    async with engine.begin() as connection:
        await connection.execute(
            text("CREATE TEMPORARY TABLE harness_ci_probe (id INT PRIMARY KEY, value_text VARCHAR(32))")
        )
        await connection.execute(
            text("INSERT INTO harness_ci_probe (id, value_text) VALUES (1, 'verified')")
        )
        value = await connection.scalar(
            text("SELECT value_text FROM harness_ci_probe WHERE id = 1")
        )

    assert value == "verified"
