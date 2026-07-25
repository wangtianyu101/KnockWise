"""Dev tool: seed today's digest with sample items (for local dev only)."""
import asyncio
from datetime import date, datetime, timezone
from uuid import uuid4
from core.database import async_session
from models import DigestDaily, DigestDailyItem, User
from sqlalchemy import delete, select

SAMPLE_ITEMS = [
    {
        "title": "Claude 4.7 Sonnet 发布 · 1M 上下文 + Agentic Coding 优化",
        "summary": "Anthropic 发布 Claude 4.7 Sonnet，主打 1M token 上下文 + 工具调用稳定性提升 23%。SWE-bench Verified 得分 78.4%。",
        "type": "model", "region": "overseas", "category": "headline",
        "source_name": "Anthropic News",
        "source_url": "https://www.anthropic.com/news/claude-4-7-sonnet",
        "quality_score": 0.95, "estimated_minutes": 4,
    },
    {
        "title": "DeepSeek V4 Pro 永久降价至原价 1/4",
        "summary": "缓存命中输入 0.025 元/M tokens（降 75%）。1M 上下文。推理对标 GPT-5 中端。月成本降至 25%。",
        "type": "model", "region": "domestic", "category": "headline",
        "source_name": "DeepSeek Docs",
        "source_url": "https://api-docs.deepseek.com/news/v4-pro",
        "quality_score": 0.93, "estimated_minutes": 3,
    },
    {
        "title": "阿里通义 Qwen3-Coder 30B 开源 · HumanEval 82.1%",
        "summary": "1M 上下文 + 代码补全。超过 Code Llama 70B。MIT 协议可商用。",
        "type": "application", "region": "domestic", "category": "engineering",
        "source_name": "Qwen GitHub",
        "source_url": "https://github.com/QwenLM/Qwen3-Coder",
        "quality_score": 0.88, "estimated_minutes": 3,
    },
    {
        "title": "[arXiv] Sparse MoE · 1T active params · 推理 4x 速度",
        "summary": "MIT + Together AI · 总 8T 参数。推理成本降至 1/4。开源实现即将发布。",
        "type": "application", "region": "overseas", "category": "paper",
        "source_name": "arXiv cs.CL",
        "source_url": "https://arxiv.org/abs/2026.sparse-moe",
        "quality_score": 0.91, "estimated_minutes": 5,
    },
    {
        "title": "机器之心 · Anthropic 推出 Agentic Tool Use 协议 MCP v2",
        "summary": "MCP v2 协议升级。Claude Code 全量支持。开发者生态进一步开放。",
        "type": "application", "region": "domestic", "category": "engineering",
        "source_name": "机器之心",
        "source_url": "https://www.jiqizhixin.com/articles/mcp-v2",
        "quality_score": 0.86, "estimated_minutes": 4,
    },
]


async def seed_today():
    async with async_session() as db:
        # 真实 dev-login 用户（按 profile/me API 查）
        r = await db.execute(select(User).where(User.id == "d9cabf34-1f00-4e49-8240-b53f2e18643d"))
        user = r.scalar_one_or_none()
        if user is None:
            # fallback: 任意用户
            r = await db.execute(select(User).limit(1))
            user = r.scalar_one()
            print(f"warning: dev user not found, using {user.id}")
        today = date.today()

        # 清掉旧 daily for today
        await db.execute(delete(DigestDaily).where(
            DigestDaily.user_id == str(user.id),
            DigestDaily.date == today,
        ))

        # 创建 daily
        daily = DigestDaily(
            id=str(uuid4()),
            user_id=str(user.id),
            date=today,
            vibe="今日 5 条 · 正常推送",
            item_ids=[],
            pushed_at=datetime.now(timezone.utc),
        )
        db.add(daily)
        await db.flush()

        # 创建 items
        for rank, sample in enumerate(SAMPLE_ITEMS, 1):
            item = DigestDailyItem(
                id=str(uuid4()),
                daily_id=daily.id,
                rank=rank,
                title=sample["title"],
                summary=sample["summary"],
                quality_score=sample["quality_score"],
                type=sample["type"],
                region=sample["region"],
                category=sample["category"],
                source_name=sample["source_name"],
                source_url=sample["source_url"],
                published_at=datetime.now(timezone.utc),
                estimated_minutes=sample["estimated_minutes"],
                related_item_ids=[],
            )
            db.add(item)
            daily.item_ids.append(item.id)

        await db.commit()
        await db.refresh(daily)
        print(f"seeded daily {daily.id} with {len(SAMPLE_ITEMS)} items")


if __name__ == "__main__":
    asyncio.run(seed_today())