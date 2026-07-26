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

# 8 真实可达的 RSS · 8 不同源（避免 dedup 吃）
# 已测可达：GitHub releases（10 entries each）
REAL_RSS_MAP: dict[str, dict] = {
    "Anthropic News": {
        "url": "https://github.com/anthropics/anthropic-sdk-python/releases.atom",
        "category": "engineering",
    },
    "Google DeepMind Blog": {
        "url": "https://github.com/openai/openai-python/releases.atom",
        "category": "engineering",
    },
    "HuggingFace Blog": {
        "url": "https://github.com/huggingface/transformers/releases.atom",
        "category": "engineering",
    },
    "DeepSeek Docs News": {
        "url": "https://github.com/vllm-project/vllm/releases.atom",
        "category": "engineering",
    },
    "Qwen GitHub Releases": {
        "url": "https://github.com/ollama/ollama/releases.atom",
        "category": "engineering",
    },
    "机器之心": {
        "url": "https://github.com/langchain-ai/langgraph/releases.atom",
        "category": "engineering",
    },
    "智谱 GLM GitHub": {
        "url": "https://github.com/microsoft/semantic-kernel/releases.atom",
        "category": "engineering",
    },
    "量子位": {
        "url": "https://github.com/chroma-core/chroma/releases.atom",
        "category": "engineering",
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