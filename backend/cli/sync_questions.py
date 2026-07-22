"""
PR 3 · V3.7 题目同步 CLI 入口

用法：
  cd backend
  python -m cli.sync_questions
  python -m cli.sync_questions --dry-run
  python -m cli.sync_questions --collection agent_foundation
"""
from __future__ import annotations

import argparse
import asyncio
import logging
import sys

from core.database import async_session, engine
from services.question_sync_service import build_default_sources, sync_questions

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
log = logging.getLogger("cli.sync_questions")


async def main():
    parser = argparse.ArgumentParser(description="KnockWise 题目同步 CLI · V3.8 P3b")
    parser.add_argument("--dry-run", action="store_true", help="只统计不入库")
    parser.add_argument("--collection", type=str, default=None, help="关联到精选题单 ID（如 agent_foundation）")
    parser.add_argument("--source", type=str, choices=["local", "github", "http", "all"], default="all", help="指定数据源（默认 all）")
    args = parser.parse_args()

    log.info(f"sync starting: dry_run={args.dry_run}, collection={args.collection}, source={args.source}")

    sources = build_default_sources()
    if args.source != "all":
        # 过滤指定源
        from services.question_sync_service import LocalDataSource, GitHubDataSource, HTTPAPIDataSource
        type_map = {"local": LocalDataSource, "github": GitHubDataSource, "http": HTTPAPIDataSource}
        sources = [s for s in sources if isinstance(s, type_map[args.source])]
        if not sources:
            log.error(f"data source {args.source} not configured (check env vars)")
            sys.exit(1)

    try:
        async with async_session() as db:
            stats = await sync_questions(
                db,
                sources,
                collection_id=args.collection,
                dry_run=args.dry_run,
            )
        log.info(f"sync done: {stats}")
        if args.dry_run:
            print(f"\n[DRY RUN] would create {stats['created']} questions")
        else:
            print(f"\nsync done: {stats}")
    except Exception as e:
        log.error(f"sync failed: {e}")
        sys.exit(1)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
