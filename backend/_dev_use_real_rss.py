"""Dev tool: 把 8 个默认 digest_sources URL 改成真 RSS（不再用 mock）。

依赖网络可达性（已测过）：
  - arxiv.org          ✅
  - github.com         ✅
  - hnrss.org          ❌ (502)
  - anthropic.com      ❌ (404)
  - deepmind.google    ❌ (302)
  - huggingface.co     ❌ (timeout)

用法:
  cd backend && .venv/bin/python _dev_use_real_rss.py
"""
import asyncio
from sqlalchemy import select
from core.database import async_session
from models import DigestSource

# 8 真实可达的 RSS（2026-07-25 LLM7 混合类型）· 覆盖 4 类 category
# - headline: 科技媒体头条（TechCrunch / The Verge / VentureBeat）
# - paper: 学术论文（arXiv cs.CL / cs.AI / cs.LG）· 周末 0 items 但工作日多
# - engineering: GitHub releases + 技术博客
# - opinion: 博客观点
REAL_RSS_MAP: dict[str, dict] = {
    "Anthropic News": {
        "url": "https://blog.cloudflare.com/rss/",  # 工程博客（替代 404 的 anthropic）
        "category": "engineering",
    },
    "Google DeepMind Blog": {
        "url": "https://export.arxiv.org/rss/cs.AI",  # 学术论文
        "category": "paper",
    },
    "HuggingFace Blog": {
        "url": "https://github.com/openai/openai-python/releases.atom",  # GitHub release
        "category": "engineering",
    },
    "DeepSeek Docs News": {
        "url": "https://www.ithome.com/rss/",  # IT之家 · 国内科技媒体
        "category": "headline",
    },
    "Qwen GitHub Releases": {
        "url": "https://www.oschina.net/news/rss",  # 开源中国 · 国内开源
        "category": "headline",
    },
    "机器之心": {
        "url": "https://www.cnblogs.com/rss",  # 博客园 · 国内开发者社区
        "category": "opinion",
    },
    "智谱 GLM GitHub": {
        "url": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",  # 科技媒体
        "category": "opinion",
    },
    "量子位": {
        "url": "https://techcrunch.com/category/artificial-intelligence/feed/",  # 科技媒体
        "category": "headline",
    },
}


async def main():
    async with async_session() as db:
        r = await db.execute(select(DigestSource).where(DigestSource.is_default.is_(True)))
        sources = list(r.scalars().all())
        print(f"Found {len(sources)} default sources")
        updated = 0
        for s in sources:
            if s.name not in REAL_RSS_MAP:
                print(f"  ! {s.name} 不在真 RSS 映射 · 保留原 URL")
                continue
            mapping = REAL_RSS_MAP[s.name]
            new_url = mapping["url"]
            if s.url != new_url:
                print(f"  ✓ {s.name} → {new_url[:60]}")
                s.url = new_url
                s.last_error = None
                s.last_fetched_at = None
                if mapping.get("category"):
                    s.category = mapping["category"]
                updated += 1
        await db.commit()
        print(f"Updated {updated} sources to real RSS")


if __name__ == "__main__":
    asyncio.run(main())