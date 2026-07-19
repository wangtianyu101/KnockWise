"""Pydantic schemas for AI push module (T2: 2026-07-17 实施).

配套 docs/tasks/2026-07-17-new-feature-ai-push/:
- spec.md §4 数据契约
- api-spec.md §3 端点详细定义
- db-design.md §2 表结构

所有 UUID 用 str（与项目现有约定一致 · 服务端用 str(uuid4())）。
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


# ═══════════════════════════════════════════════════════════════════
# A · Digest Daily
# ═══════════════════════════════════════════════════════════════════


class DigestDailyItemCreate(BaseModel):
    """内部 service 层使用 · push_daily 创建时填（api-spec §3.A + spec §4）。"""

    title: str = Field(max_length=512)
    summary: Optional[str] = None
    quality_score: float = Field(ge=0.0, le=1.0)
    type: Literal["model", "application"]
    region: Literal["domestic", "overseas"]
    category: Literal["headline", "paper", "engineering", "opinion"]
    source_name: str = Field(max_length=128)
    source_url: str = Field(max_length=1024)
    published_at: Optional[datetime] = None
    related_item_ids: list[str] = Field(default_factory=list, max_length=5)
    estimated_minutes: int = Field(default=3, ge=1, le=5)


class DigestDailyItem(BaseModel):
    """GET /api/digest/today 响应 · 单条卡片（api-spec §3.A）。"""

    model_config = ConfigDict(from_attributes=True)

    id: str
    rank: int = Field(ge=1, le=5)
    title: str
    summary: Optional[str] = None
    quality_score: float = Field(ge=0.0, le=1.0)
    type: Literal["model", "application"]
    region: Literal["domestic", "overseas"]
    category: Literal["headline", "paper", "engineering", "opinion"]
    source_name: str
    source_url: str
    published_at: Optional[datetime] = None
    estimated_minutes: int = Field(ge=1, le=5)
    is_read: bool = False
    is_bookmarked: bool = False
    related_item_ids: list[str] = Field(default_factory=list)


class DigestTodayResponse(BaseModel):
    """GET /api/digest/today 响应包装。"""

    date: date
    vibe: Optional[str] = None
    item_count: int = Field(ge=0, le=5)
    items: list[DigestDailyItem] = Field(default_factory=list, max_length=5)


class DigestDailiesListItem(BaseModel):
    """GET /api/digest/dailies 列表项 · 轻量（不含 items）。"""

    date: date
    vibe: Optional[str] = None
    item_count: int


class DigestDailiesListResponse(BaseModel):
    total: int
    items: list[DigestDailiesListItem]


# ═══════════════════════════════════════════════════════════════════
# B · Bookmarks
# ═══════════════════════════════════════════════════════════════════


class BookmarkCreate(BaseModel):
    """POST /api/digest/bookmarks body（api-spec §3.B）。"""

    item_id: str = Field(min_length=36, max_length=36)  # UUID 长度


class BookmarkResponse(BaseModel):
    id: str
    user_id: str
    item_id: str
    created_at: datetime


class BookmarkListItem(BaseModel):
    """GET /api/digest/bookmarks 列表项（含内联 digest 摘要）。"""

    item_id: str
    title: str
    summary: Optional[str] = None
    type: Literal["model", "application"]
    region: Literal["domestic", "overseas"]
    source_name: str
    source_url: str
    quality_score: float
    bookmarked_at: datetime
    published_at: Optional[datetime] = None


class BookmarkListResponse(BaseModel):
    total: int
    items: list[BookmarkListItem]


# ═══════════════════════════════════════════════════════════════════
# C · Behavior (read + hide)
# ═══════════════════════════════════════════════════════════════════


class ReadCreate(BaseModel):
    """POST /api/digest/read body（api-spec §3.C + spec R7）。"""

    item_id: str = Field(min_length=36, max_length=36)
    duration_sec: int = Field(ge=0, le=86400)  # ≤ 24h


class ReadResponse(BaseModel):
    item_id: str
    read_at: datetime
    duration_sec: int
    progress: str  # e.g. "5/10" · 今日已读/总推送


class HideCreate(BaseModel):
    """POST /api/digest/hide body（api-spec §3.C + spec R5 + 防 prompt 注入）。"""

    item_id: str = Field(min_length=36, max_length=36)
    reason: Literal["not_interested", "low_quality", "already_seen"]
    topic_keywords: list[str] = Field(default_factory=list, max_length=5)
    # 业务：topic_keywords 必走白名单过滤（仅 [a-zA-Z0-9一-龥]）防 prompt 注入 · 校验在 service 层


class HideResponse(BaseModel):
    hide_id: str
    item_id: str
    topic_keywords: list[str]
    expires_at: datetime
    message: str


# ═══════════════════════════════════════════════════════════════════
# D · Sources
# ═══════════════════════════════════════════════════════════════════


class DigestSourceCreate(BaseModel):
    """POST /api/digest/sources body（api-spec §3.D）。"""

    name: str = Field(min_length=1, max_length=128)
    url: HttpUrl
    category: Literal["model", "application"]
    type: Literal["model", "application"]
    region: Literal["domestic", "overseas"]


class DigestSourceUpdate(BaseModel):
    """PATCH /api/digest/sources/{id} body（api-spec §3.D · 部分更新）。"""

    enabled: Optional[bool] = None
    name: Optional[str] = Field(default=None, max_length=128)


class DigestSource(BaseModel):
    """GET /api/digest/sources 响应（api-spec §3.D）。"""

    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: Optional[str] = None  # NULL = 系统默认源
    name: str
    url: str
    category: str
    type: Literal["model", "application"]
    region: Literal["domestic", "overseas"]
    enabled: bool
    is_default: bool
    last_fetched_at: Optional[datetime] = None
    last_item_count: int = 0


class DigestSourceListResponse(BaseModel):
    system_count: int
    user_count: int
    items: list[DigestSource]


# ═══════════════════════════════════════════════════════════════════
# E · Settings
# ═══════════════════════════════════════════════════════════════════


class DigestSettings(BaseModel):
    """GET /api/digest/settings 响应（api-spec §3.E · spec §4）。"""

    model_config = ConfigDict(from_attributes=True)

    user_id: str
    push_hour: int = Field(ge=0, le=23, default=8)
    push_minute: int = Field(ge=0, le=59, default=0)
    push_timezone: str = Field(default="Asia/Shanghai")
    email_enabled: bool = True
    macos_enabled: bool = False
    interested_tags: list[str] = Field(default_factory=list, max_length=10)
    blocked_tags: list[str] = Field(default_factory=list, max_length=10)
    daily_count: Literal[3, 5] = 5
    weekend_pause: bool = False
    updated_at: Optional[datetime] = None


class DigestSettingsUpdate(BaseModel):
    """PATCH /api/digest/settings body（部分更新 · 所有字段 optional）。"""

    push_hour: Optional[int] = Field(default=None, ge=0, le=23)
    push_minute: Optional[int] = Field(default=None, ge=0, le=59)
    push_timezone: Optional[str] = Field(default=None)
    email_enabled: Optional[bool] = None
    macos_enabled: Optional[bool] = None
    interested_tags: Optional[list[str]] = Field(default=None, max_length=10)
    blocked_tags: Optional[list[str]] = Field(default=None, max_length=10)
    weekend_pause: Optional[bool] = None
