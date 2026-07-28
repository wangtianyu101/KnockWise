"""GET /api/digest/metrics endpoint (T13 · P1-9 L1 平台层 · v1.2 决策 3 修正 counter 键).

按 spec § 2.2 SCN-P1.9.4 + SCN-P1.9.7 + api-spec.md：

- 绑定 127.0.0.1（仅本地 · 不暴露公网）
- 返回 4 counter：push_total / push_failed / fetch_failures / rsshub_routes_broken
  （v1.2 决策 3 修正：与 backend/utils/metrics.py:32-37 一致）
- 无认证（本地基础设施）
- 无副作用（只读 endpoint）
"""
from __future__ import annotations

from fastapi import APIRouter

from utils.metrics import digest_metrics


router = APIRouter(prefix="/api/digest", tags=["digest-metrics"])


@router.get("/metrics")
async def get_metrics():
    """返回 digest_metrics 当前 snapshot（4 counter + timings）。

    业务代码通过 digest_metrics.inc(key) / timing(key, ms) 累计。
    本 endpoint 提供观察口（仅本地 · SCN-P1.9.7）。
    """
    return digest_metrics.snapshot()


# 注：endpoint 路由注册在 backend/main.py（绑定 127.0.0.1 通过 uvicorn --host 127.0.0.1）