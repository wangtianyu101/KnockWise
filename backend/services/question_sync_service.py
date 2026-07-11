"""
PR 3 · V3.7 题目同步服务（用户 2026-07-10 拍 agent 方向 + 混合拉取 + 数据解耦）

混合数据源适配器（用户 2026-07-10 决定）：
- LocalDataSource：从本地 /data 目录读 JSON
- GitHubDataSource：从 GitHub repo 拉 JSON
- HTTPAPI DataSource：从公司内部 HTTP API 拉

字段映射：统一 JSON schema → V1 Question 模型
去重逻辑：按 id 检查存在
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import Question

log = logging.getLogger("knockwise.question_sync")


# ════════════════════════════════════════════════════════════
# 统一 JSON schema（外部 → V1 Question 字段映射）
# ════════════════════════════════════════════════════════════


class QuestionDataSource(ABC):
    """抽象数据源。"""

    @abstractmethod
    async def fetch_questions(self) -> list[dict]:
        """拉取题目列表（统一 schema）。"""
        ...


class LocalDataSource(QuestionDataSource):
    """从本地 /data 目录读 JSON。"""

    def __init__(self, base_path: str = "/data"):
        self.base_path = Path(base_path)

    async def fetch_questions(self) -> list[dict]:
        questions: list[dict] = []
        if not self.base_path.exists():
            log.warning(f"local data path {self.base_path} not found")
            return questions
        for json_file in self.base_path.glob("*.json"):
            try:
                data = json.loads(json_file.read_text(encoding="utf-8"))
                if isinstance(data, list):
                    questions.extend(data)
                elif isinstance(data, dict) and "questions" in data:
                    questions.extend(data["questions"])
                log.info(f"local: {len(data) if isinstance(data, list) else len(data.get('questions', []))} questions from {json_file.name}")
            except Exception as e:
                log.warning(f"local: failed to parse {json_file.name}: {e}")
        return questions


class GitHubDataSource(QuestionDataSource):
    """从 GitHub repo 拉 JSON（公开 repo · raw.githubusercontent.com）。"""

    def __init__(self, repo: str, branch: str = "main", path_prefix: str = "questions"):
        """
        repo: 'owner/repo' 形式
        path_prefix: JSON 文件所在子目录
        """
        self.repo = repo
        self.branch = branch
        self.path_prefix = path_prefix
        self.base_url = f"https://raw.githubusercontent.com/{repo}/{branch}/{path_prefix}"

    async def fetch_questions(self) -> list[dict]:
        questions: list[dict] = []
        async with httpx.AsyncClient(timeout=30.0) as client:
            # 先拉目录列表（GitHub API 或 manifest）
            # 简化：拉 manifest.json 列出所有题目文件
            try:
                manifest_resp = await client.get(f"{self.base_url}/manifest.json")
                if manifest_resp.status_code != 200:
                    log.warning(f"github: manifest.json not found, status {manifest_resp.status_code}")
                    return questions
                manifest = manifest_resp.json()
            except Exception as e:
                log.warning(f"github: failed to fetch manifest: {e}")
                return questions

            for filename in manifest.get("files", []):
                try:
                    file_resp = await client.get(f"{self.base_url}/{filename}")
                    if file_resp.status_code == 200:
                        data = file_resp.json()
                        if isinstance(data, list):
                            questions.extend(data)
                        log.info(f"github: {len(data) if isinstance(data, list) else '?'} questions from {filename}")
                except Exception as e:
                    log.warning(f"github: failed to fetch {filename}: {e}")
        return questions


class HTTPAPIDataSource(QuestionDataSource):
    """从公司内部 HTTP API 拉。"""

    def __init__(self, base_url: str, api_key: Optional[str] = None, endpoint: str = "/api/questions"):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.endpoint = endpoint

    async def fetch_questions(self) -> list[dict]:
        url = f"{self.base_url}{self.endpoint}"
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(url, headers=headers)
                resp.raise_for_status()
                data = resp.json()
                if isinstance(data, list):
                    return data
                if isinstance(data, dict) and "questions" in data:
                    return data["questions"]
                return []
        except Exception as e:
            log.warning(f"http_api: failed to fetch {url}: {e}")
            return []


# ════════════════════════════════════════════════════════════
# 字段映射（统一 JSON → V1 Question 模型）
# ════════════════════════════════════════════════════════════

# 统一外部 JSON schema（用户后续可调整）：
# {
#   "id": "agent_001",
#   "topic": "agent_architecture",
#   "sub_topic": "react_agent",
#   "difficulty": 3,
#   "round": "round1",                  # 可选 · 默认 round1
#   "question_text": "...",
#   "answer_key_points": ["..."],      # 可选 · 默认 []
#   "followup_tree": { ... },          # 可选 · 默认 {}
#   "tags": ["sys_algorithm", ...]     # 可选 · V3.x 写到 QuestionTagMap
# }

REQUIRED_FIELDS = {"id", "topic", "sub_topic", "question_text"}


def map_external_to_question(raw: dict) -> Optional[dict]:
    """字段映射：统一外部 JSON → V1 Question 字段。返回 None 表示无效。"""
    # 必填字段检查
    missing = REQUIRED_FIELDS - set(raw.keys())
    if missing:
        log.warning(f"sync: skip {raw.get('id', '?')} - missing fields {missing}")
        return None

    # 字段映射
    return {
        "id": str(raw["id"]).strip(),
        "topic": str(raw["topic"]).strip(),
        "sub_topic": str(raw["sub_topic"]).strip(),
        "difficulty": int(raw.get("difficulty", 3)),
        "round": str(raw.get("round", "round1")).strip(),
        "question_text": str(raw["question_text"]).strip(),
        "answer_key_points": raw.get("answer_key_points") or [],
        "followup_tree": raw.get("followup_tree") or {},
    }


def compute_question_hash(q: dict) -> str:
    """去重 hash：id + 题目文本 hash（避免重复题目）。"""
    content = f"{q['id']}|{q['question_text']}"
    return hashlib.md5(content.encode("utf-8")).hexdigest()


# ════════════════════════════════════════════════════════════
# 主服务：sync_questions()
# ════════════════════════════════════════════════════════════


async def sync_questions(
    db: AsyncSession,
    sources: list[QuestionDataSource],
    *,
    collection_id: Optional[str] = None,
    dry_run: bool = False,
) -> dict:
    """主同步入口：拉取 → 映射 → 去重 → 写入。

    Args:
        db: AsyncSession
        sources: 数据源列表（混合）
        collection_id: 可选，关联到精选题单（如 agent_foundation）
        dry_run: True = 只统计不入库

    Returns:
        {"fetched": int, "created": int, "skipped": int, "errors": int}
    """
    stats = {"fetched": 0, "created": 0, "skipped": 0, "errors": 0}

    # 1. 拉取所有数据源
    all_raw: list[dict] = []
    for src in sources:
        try:
            items = await src.fetch_questions()
            all_raw.extend(items)
            stats["fetched"] += len(items)
            log.info(f"sync: source {type(src).__name__} returned {len(items)} questions")
        except Exception as e:
            stats["errors"] += 1
            log.error(f"sync: source {type(src).__name__} failed: {e}")

    # 2. 字段映射
    mapped: list[dict] = []
    for raw in all_raw:
        try:
            q = map_external_to_question(raw)
            if q is not None:
                mapped.append(q)
        except Exception as e:
            stats["errors"] += 1
            log.warning(f"sync: map failed for {raw.get('id', '?')}: {e}")

    log.info(f"sync: mapped {len(mapped)}/{len(all_raw)} questions")

    # 3. 去重：按 id 查询已存在
    if mapped:
        existing_ids: set[str] = set()
        result = await db.execute(
            select(Question.id).where(Question.id.in_([q["id"] for q in mapped]))
        )
        existing_ids = {row[0] for row in result.all()}

    # 4. 写入
    for q in mapped:
        if q["id"] in existing_ids:
            stats["skipped"] += 1
            continue
        if dry_run:
            stats["created"] += 1
            continue
        try:
            db.add(Question(**q))
            stats["created"] += 1
        except Exception as e:
            stats["errors"] += 1
            log.warning(f"sync: insert failed for {q['id']}: {e}")

    if not dry_run:
        await db.commit()

    # 5. 可选：关联到题单（V3.1 简化为只更新 count · 不动 collection_maps · 题目后续手动布局）
    if collection_id and stats["created"] > 0 and not dry_run:
        await db.execute(
            # 简单更新 question_count（V3.1 数据解耦：题目进题单但 collection_maps 后续手动）
            __import__('sqlalchemy').text(
                "UPDATE question_collections SET question_count = "
                "(SELECT COUNT(*) FROM questions) WHERE id = :cid"
            ),
            {"cid": collection_id},
        )
        await db.commit()

    log.info(f"sync: stats {stats}")
    return stats


# ════════════════════════════════════════════════════════════
# 工厂：根据环境变量构造数据源列表
# ════════════════════════════════════════════════════════════


def build_default_sources() -> list[QuestionDataSource]:
    """根据环境变量构造默认数据源列表（用户 2026-07-10 拍 混合拉取）。"""
    import os
    sources: list[QuestionDataSource] = []

    # Local（默认开启）
    local_path = os.environ.get("QUESTION_SYNC_LOCAL_PATH", "/data")
    sources.append(LocalDataSource(local_path))

    # GitHub（可选 · 设置 QUESTION_SYNC_GITHUB_REPO=owner/repo 启用）
    github_repo = os.environ.get("QUESTION_SYNC_GITHUB_REPO")
    if github_repo:
        sources.append(GitHubDataSource(repo=github_repo))

    # HTTP API（可选 · 设置 QUESTION_SYNC_HTTP_API 启用）
    http_url = os.environ.get("QUESTION_SYNC_HTTP_API")
    if http_url:
        sources.append(HTTPAPIDataSource(base_url=http_url))

    return sources
