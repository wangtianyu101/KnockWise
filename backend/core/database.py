from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import inspect, text

from core.config import settings

engine = create_async_engine(settings.database_url, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()


# Lightweight schema migrations for dev/prod tables that already exist when
# a new column is added. Base.metadata.create_all() only creates missing
# tables — it does NOT alter existing ones, so an in-place upgrade path
# needs these explicit ALTERs.
#
# Keep this list flat and append-only. Each entry is (table, column, ddl).
# `applied` is filled at startup time and skipped on subsequent boots.
_MIGRATIONS: list[tuple[str, str, str]] = [
    ("interviews", "is_favorite", "ALTER TABLE interviews ADD COLUMN is_favorite BOOLEAN DEFAULT 0"),
    ("interviews", "deleted_at", "ALTER TABLE interviews ADD COLUMN deleted_at DATETIME NULL"),
    ("reports", "summary", "ALTER TABLE reports ADD COLUMN summary TEXT NULL"),
    ("reports", "overall_score", "ALTER TABLE reports ADD COLUMN overall_score FLOAT NULL"),
    # Phase 1a · 学习复习模块 Profile 扩字段 (面试题库-技术设计.md 2.8)
    ("profiles", "weak_topics", "ALTER TABLE profiles ADD COLUMN weak_topics JSON NOT NULL DEFAULT (JSON_ARRAY())"),
    ("profiles", "mastered_topics", "ALTER TABLE profiles ADD COLUMN mastered_topics JSON NOT NULL DEFAULT (JSON_ARRAY())"),
    ("profiles", "learning_trajectory", "ALTER TABLE profiles ADD COLUMN learning_trajectory JSON NOT NULL DEFAULT (JSON_OBJECT())"),
    ("profiles", "last_active_at", "ALTER TABLE profiles ADD COLUMN last_active_at DATETIME NULL"),
]


# Phase 1a · 大数据量优化 (HASH 分区 + 覆盖索引)
# 注意: 分区在 create_all 之后跑, 对新建表生效
# TODO(P3): MySQL 9 暂不支持 VARCHAR HASH 分区, 留 TODO 等待用户量 > 5k 时再考虑
#   或改用 KEY partitioning / 手动 sharding
_PHASE1A_PARTITION_DDL: list[str] = [
    # 占位: MySQL 9 + VARCHAR user_id 不允许 HASH partition
    # 启用条件: 用户量 > 5k 行 OR MySQL 升级支持后再开
]

_PHASE1A_INDEX_DDL: list[tuple[str, str]] = [
    # (table, ddl) — review_queue 的 hot query 走这个
    # 注: MySQL 不支持 INCLUDE 关键字 (那是 PostgreSQL 语法)
    # 这里用普通复合索引, query 性能足够
    (
        "question_progress",
        "CREATE INDEX idx_qp_review_queue ON question_progress("
        "user_id, next_review_at, status, id, question_id"
        ")",
    ),
]


async def _run_migrations():
    """Run ALTER TABLE migrations for any missing columns on existing tables.

    We don't introspect the schema up front (PRAGMA is SQLite-only, MySQL would
    need INFORMATION_SCHEMA). Instead, run the ALTER and swallow the
    "duplicate column" error — every dialect surfaces that as a clear message.
    """
    import logging
    log = logging.getLogger("codemock.migration")
    for _table, _col, ddl in _MIGRATIONS:
        try:
            async with engine.begin() as conn:
                await conn.execute(text(ddl))
            log.info(f"migration applied: {ddl}")
        except Exception as e:
            msg = str(e).lower()
            # MySQL: 1060 "Duplicate column name"; SQLite: "duplicate column"
            if "duplicate" in msg or "1060" in msg:
                log.debug(f"migration already applied: {_table}.{_col}")
                continue
            log.warning(f"migration {_table}.{_col} failed: {e}")


async def _is_partitioned(table: str) -> bool:
    """Check if MySQL table is already partitioned (PARTITION BY ...)."""
    try:
        async with engine.begin() as conn:
            result = await conn.execute(text(
                "SELECT CREATE_OPTIONS FROM information_schema.TABLES "
                "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = :t"
            ), {"t": table})
            row = result.first()
            if row is None:
                return False
            options = (row[0] or "").lower()
            return "partitioned" in options
    except Exception:
        return False


async def _index_exists(table: str, index_name: str) -> bool:
    """Check if MySQL index already exists."""
    try:
        async with engine.begin() as conn:
            result = await conn.execute(text(
                "SELECT 1 FROM information_schema.STATISTICS "
                "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = :t "
                "AND INDEX_NAME = :i LIMIT 1"
            ), {"t": table, "i": index_name})
            return result.first() is not None
    except Exception:
        return False


async def _run_phase1a_optimizations():
    """Phase 1a · 大数据量优化: HASH 分区 + 覆盖索引。

    分区逻辑:
      - 只对 MySQL 跑 (SQLite 无分区)
      - 已分区的表跳过 (幂等)
      - DROP FK 是 idempotent 的 (FK 不存在时报错被 swallow)

    覆盖索引逻辑:
      - INFORMATION_SCHEMA.STATISTICS 查
      - 已存在则跳过
    """
    import logging
    log = logging.getLogger("codemock.migration")

    # 1) 分区
    if await _is_partitioned("question_progress"):
        log.debug("question_progress already partitioned, skip")
    else:
        for ddl in _PHASE1A_PARTITION_DDL:
            try:
                async with engine.begin() as conn:
                    await conn.execute(text(ddl))
                log.info(f"phase1a partition applied: {ddl.strip()[:60]}...")
            except Exception as e:
                msg = str(e).lower()
                # DROP FK 报 "check that column/key exists" → 跳过
                if "1091" in msg or "check that column/key exists" in msg:
                    log.debug(f"FK already dropped: {e}")
                    continue
                log.warning(f"phase1a partition failed: {e}")
                break  # 一旦失败不再继续

    # 2) 覆盖索引
    for table, ddl in _PHASE1A_INDEX_DDL:
        # 提取 index name (CREATE INDEX xxx ON ...)
        try:
            idx_name = ddl.split("CREATE INDEX")[1].split("ON")[0].strip().strip("`")
        except Exception:
            idx_name = ""
        if idx_name and await _index_exists(table, idx_name):
            log.debug(f"{idx_name} already exists, skip")
            continue
        try:
            async with engine.begin() as conn:
                await conn.execute(text(ddl))
            log.info(f"phase1a index applied: {idx_name}")
        except Exception as e:
            msg = str(e).lower()
            if "1061" in msg or "duplicate key name" in msg:
                log.debug(f"index {idx_name} already exists")
                continue
            log.warning(f"phase1a index {idx_name} failed: {e}")


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await _run_migrations()
    await _run_phase1a_optimizations()
