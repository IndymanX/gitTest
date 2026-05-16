"""Analytics route — aggregate editorial metrics from Redis."""
import json
from collections import Counter
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from ...core.redis_client import redis_client, FEED_CACHE_KEY, BRAIN_PROFILES_KEY
from ..routes.auth import require_user

router = APIRouter(prefix="/analytics", tags=["Analytics"])

DRAFTS_HISTORY_KEY = "drafts:history"
SCHEDULED_KEY = "scheduled:posts"


@router.get("/summary")
async def analytics_summary(user: dict = Depends(require_user)):
    """Aggregate editorial metrics: drafts, tokens, feed, brain."""
    # Draft history
    raw_drafts = await redis_client.lrange(DRAFTS_HISTORY_KEY, 0, 199)
    drafts = [json.loads(r) for r in raw_drafts]

    platform_counts = Counter(d.get("platform", "unknown") for d in drafts)
    format_counts = Counter(d.get("format", "unknown") for d in drafts)
    total_words = sum(d.get("word_count", 0) for d in drafts)

    # Last 14 days draft counts
    today = datetime.utcnow().date()
    daily = {(today - timedelta(days=i)).isoformat(): 0 for i in range(13, -1, -1)}
    for d in drafts:
        day = (d.get("generated_at") or "")[:10]
        if day in daily:
            daily[day] += 1

    # Token usage (monthly + last 7 days daily)
    monthly_tokens = int(await redis_client.get("token:monthly:default") or 0)
    daily_tokens = []
    for i in range(6, -1, -1):
        day = (today - timedelta(days=i)).isoformat()
        inp = int(await redis_client.get(f"token:daily:{day}:input") or 0)
        out = int(await redis_client.get(f"token:daily:{day}:output") or 0)
        daily_tokens.append({"date": day, "input_tokens": inp, "output_tokens": out, "total": inp + out})

    # Feed
    feed_count = await redis_client.llen(FEED_CACHE_KEY)

    # Brain profiles
    profiles_raw = await redis_client.hgetall(BRAIN_PROFILES_KEY)
    profiles = [json.loads(v) for v in profiles_raw.values()]
    avg_maturity = (
        sum(p.get("maturity_score", 0) for p in profiles) / len(profiles)
        if profiles else 0
    )

    # Scheduled posts pending
    scheduled_count = await redis_client.zcard(SCHEDULED_KEY)

    return {
        "drafts": {
            "total": len(drafts),
            "by_platform": dict(platform_counts.most_common()),
            "by_format": dict(format_counts.most_common()),
            "last_14_days": [{"date": k, "count": v} for k, v in daily.items()],
            "avg_word_count": round(total_words / len(drafts)) if drafts else 0,
        },
        "tokens": {
            "monthly_total": monthly_tokens,
            "last_7_days": daily_tokens,
        },
        "feed": {
            "total_items": feed_count,
        },
        "brain": {
            "total_profiles": len(profiles),
            "avg_maturity": round(avg_maturity, 2),
        },
        "scheduler": {
            "pending_posts": scheduled_count,
        },
    }
