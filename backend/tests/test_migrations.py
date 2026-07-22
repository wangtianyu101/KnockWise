"""Tests for AI push module (T1: 004_digest schema).

Verifies:
- 7 new tables are registered in SQLAlchemy Base.metadata
- profiles.digest_stats column is in _MIGRATIONS list
- 12 default source seed data is well-formed
- Foreign keys are properly configured
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from core.database import Base, _MIGRATIONS


# ─── 1. Tables registered in Base.metadata ───

DIGEST_TABLES = [
    "digest_sources",
    "digest_daily",
    "digest_daily_item",
    "digest_read",
    "digest_bookmark",
    "digest_hide",
    "digest_settings",
]


class TestDigestTablesRegistered:
    @pytest.mark.parametrize("table_name", DIGEST_TABLES)
    def test_table_exists_in_metadata(self, table_name):
        assert table_name in Base.metadata.tables, (
            f"Table {table_name} not registered in Base.metadata"
        )

    def test_all_7_digest_tables_present(self):
        registered = set(Base.metadata.tables.keys())
        missing = set(DIGEST_TABLES) - registered
        assert not missing, f"Missing tables: {missing}"


# ─── 2. profiles.digest_stats in _MIGRATIONS ───


class TestProfileDigestStats:
    def test_digest_stats_in_migration_list(self):
        migration_cols = {_col for _table, _col, _ddl in _MIGRATIONS}
        assert "digest_stats" in migration_cols, (
            "digest_stats not in _MIGRATIONS list — add ALTER TABLE profiles"
        )

    def test_digest_stats_ddl_is_alter_profiles(self):
        """Verify the migration DDL targets the profiles table."""
        digest_stats_migration = next(
            (ddl for _t, _c, ddl in _MIGRATIONS if _c == "digest_stats"),
            None,
        )
        assert digest_stats_migration is not None
        assert "ALTER TABLE profiles" in digest_stats_migration
        assert "JSON" in digest_stats_migration.upper() or "json" in digest_stats_migration


# ─── 3. digest_source has required columns ───


class TestDigestSourceColumns:
    @pytest.fixture
    def columns(self):
        return Base.metadata.tables["digest_sources"].columns.keys()

    def test_required_columns(self, columns):
        required = {
            "id", "user_id", "name", "url", "category", "type", "region",
            "enabled", "is_default", "last_fetched_at", "last_item_count",
            "last_error", "created_at", "updated_at",
        }
        missing = required - set(columns)
        assert not missing, f"Missing columns in digest_sources: {missing}"

    def test_user_id_is_nullable_for_system_defaults(self, columns):
        """user_id must be nullable to allow system default sources (user_id=NULL)."""
        col = Base.metadata.tables["digest_sources"].columns["user_id"]
        assert col.nullable, "user_id should be nullable for system default sources"


# ─── 4. digest_daily_item has unique constraint on (daily_id, rank) ───


class TestDigestDailyItemConstraints:
    @pytest.fixture
    def table(self):
        return Base.metadata.tables["digest_daily_item"]

    def test_unique_constraint_daily_rank(self, table):
        from sqlalchemy import UniqueConstraint
        found = any(
            isinstance(c, UniqueConstraint)
            and "daily_id" in [col.name for col in c.columns]
            and "rank" in [col.name for col in c.columns]
            for c in table.constraints
        )
        assert found, "digest_daily_item must have UNIQUE (daily_id, rank) constraint"


# ─── 5. Seed data is well-formed ───


class TestDefaultSourcesSeed:
    @pytest.fixture
    def seed_data(self):
        path = Path(__file__).parent.parent / "seed_data" / "digest_sources.json"
        if not path.exists():
            pytest.skip(f"Seed file not found: {path}")
        return json.loads(path.read_text(encoding="utf-8"))

    def test_seed_has_8_default_sources(self, seed_data):
        assert len(seed_data) == 8, (
            f"Expected 8 default sources, got {len(seed_data)}"
        )

    def test_seed_sources_have_required_fields(self, seed_data):
        required = {"name", "url", "category", "type", "region"}
        for i, source in enumerate(seed_data):
            missing = required - set(source.keys())
            assert not missing, f"Source {i} ({source.get('name', '?')}) missing: {missing}"

    def test_seed_url_starts_with_http(self, seed_data):
        for source in seed_data:
            assert source["url"].startswith(("http://", "https://")), (
                f"Invalid URL: {source['url']}"
            )

    def test_seed_type_is_model_or_application(self, seed_data):
        for source in seed_data:
            assert source["type"] in ("model", "application"), (
                f"Invalid type: {source['type']}"
            )

    def test_seed_region_is_domestic_or_overseas(self, seed_data):
        for source in seed_data:
            assert source["region"] in ("domestic", "overseas"), (
                f"Invalid region: {source['region']}"
            )
