"""Dev tool: 把 8 个默认 digest_sources URL 改成 localhost:1200（本地 mock RSS）.

用法:
  cd backend && ./.venv/bin/python _dev_use_local_rss.py
"""
import asyncio
from sqlalchemy import update
from core.database import async_session
from models import DigestSource

# (source name, mock slug) · 默认 8 源一一对应到 mock_rss/*.xml
SOURCE_MAP = {
    "Anthropic News": "anthropic.xml",
    "Google DeepMind Blog": "deepmind.xml",
    "HuggingFace Blog": "huggingface.xml",
    "DeepSeek Docs News": "deepseek.xml",
    "Qwen GitHub Releases": "qwen.xml",
    "机器之心": "jiqizhixin.xml",
    "智谱 GLM GitHub": "zhipu.xml",
    "量子位": "jiqizhixin.xml",  # 同为中文 AI 媒体
    "稀土掘金 AI 标签": "zhipu.xml",  # fallback alias
}

LOCAL_RSS_BASE = "http://localhost:1200/rss"


async def main():
    async with async_session() as db:
        r = await db.execute(select(DigestSource).where(DigestSource.is_default.is_(True)))
        sources = list(r.scalars().all())
        print(f"Found {len(sources)} default sources")
        updated = 0
        for s in sources:
            slug = SOURCE_MAP.get(s.name)
            if slug:
                new_url = f"{LOCAL_RSS_BASE}/{slug}"
                if s.url != new_url:
                    s.url = new_url
                    s.enabled = True
                    s.last_error = None
                    updated += 1
                    print(f"  ✓ {s.name} → {new_url}")
            else:
                print(f"  ! {s.name} 没有 mock 对应 · 保留原 URL")
        await db.commit()
        print(f"Updated {updated} sources")


from sqlalchemy import select  # noqa: E402

if __name__ == "__main__":
    asyncio.run(main())