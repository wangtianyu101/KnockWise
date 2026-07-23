"""
P1-3 E2E Fixture: 8 项契约 (per refactor-test-foundation research.md § 4.3)
- DB 边界: DB 名含 _test / test
- 用户命名空间: 每 worker 唯一 e2e_<run>_w<worker>@example.invalid
- 登录态: 真实 dev-login + 反查 user_id
- Digest 预生成: 1 settings + 2 sources + 1 daily + 5 items
- seed_data 只读: 不修改 backend/seed_data/*.json
- 时间固定: 2026-07-22T00:00:00Z
- 清理幂等: setup/test/teardown 幂等
- 并行隔离: CI 独立 MySQL service + 每 worker 不同 DB
"""
import os
import uuid
from datetime import datetime, timezone

import pytest

# ─── 1. DB 边界 fixture ───────────────────────────────────
@pytest.fixture(scope="session")
def e2e_db_url() -> str:
    """DB 名必须包含 _test 或 test，否则 skip"""
    url = os.environ.get("DATABASE_URL", "")
    if not any(t in url.lower() for t in ("_test", "test")):
        pytest.skip("e2e requires DATABASE_URL with 'test' or '_test' in name")
    return url


@pytest.fixture(scope="session")
def e2e_run_id() -> str:
    """CI run id + attempt；本地随机 UUID"""
    return os.environ.get("GITHUB_RUN_ID", uuid.uuid4().hex[:8])


@pytest.fixture(scope="session")
def e2e_worker_id() -> str:
    """每 worker 唯一 ID"""
    return os.environ.get("PYTEST_XDIST_WORKER", "0")


# ─── 2. 用户命名空间 fixture ───────────────────────────────
@pytest.fixture
def e2e_user_id(e2e_run_id, e2e_worker_id) -> str:
    """e2e_<run>_w<worker>@example.invalid 唯一"""
    return f"e2e_{e2e_run_id}_w{e2e_worker_id}"


@pytest.fixture
def e2e_user_email(e2e_user_id) -> str:
    return f"{e2e_user_id}@example.invalid"


# ─── 4. Digest 预生成 fixture (3+4+5) ──────────────────────
DIGEST_FIXED_TS = datetime(2026, 7, 22, 0, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def p1_3_digest_arrange(db_session, e2e_user):
    """1 DigestSettings + 2 test DigestSource + 1 DigestDaily + 5 DigestDailyItem
    约束: DigestDaily(user_id, date) UNIQUE + DigestDailyItem(daily_id, rank) UNIQUE
    → 天然验证幂等 (REQ-7)"""
    from backend.models import (
        DigestSettings, DigestSource, DigestDaily, DigestDailyItem,
    )

    settings = DigestSettings(
        user_id=e2e_user.id,
        push_hour=8, push_minute=0, timezone="UTC",
    )
    sources = [
        DigestSource(
            id=uuid.uuid4(), user_id=e2e_user.id, is_default=False,
            url="https://fixtures.invalid/source-1", name="Test Source 1",
        ),
        DigestSource(
            id=uuid.uuid4(), user_id=e2e_user.id, is_default=False,
            url="https://fixtures.invalid/source-2", name="Test Source 2",
        ),
    ]
    daily = DigestDaily(
        user_id=e2e_user.id, date=DIGEST_FIXED_TS.date(), vibe="calm",
    )
    items = [
        DigestDailyItem(
            id=uuid.uuid4(), daily_id=daily.id, rank=i+1,
            title=f"Test Item {i+1}",
            summary=f"Summary for item {i+1}",
            type="paper", category="ai",
        )
        for i in range(5)
    ]
    db_session.add_all([settings, *sources, daily, *items])
    db_session.commit()
    return {
        "user": e2e_user,
        "settings": settings,
        "sources": sources,
        "daily": daily,
        "items": items,
    }


# ─── 6. 时间固定 fixture ──────────────────────────────────
@pytest.fixture
def fixed_now() -> datetime:
    """2026-07-22T00:00:00Z 固定时间"""
    return DIGEST_FIXED_TS


@pytest.fixture
def e2e_now_provider(fixed_now):
    """给 scheduler / digest service 注入的 now_provider"""
    return lambda: fixed_now
