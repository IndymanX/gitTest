"""Feed Heartbeat API routes — Redis-backed real-time feed."""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Optional
from pydantic import BaseModel
import json
import uuid

from ...core.redis_client import redis_client, FEED_CACHE_KEY, FEED_SOURCES_KEY
from ...services.feed_heartbeat import FeedHeartbeatService

router = APIRouter(prefix="/feed", tags=["Feed Heartbeat"])
heartbeat_service = FeedHeartbeatService()


async def _get_all_items() -> List[dict]:
    """Load all feed items from Redis."""
    raw = await redis_client.hgetall(FEED_CACHE_KEY)
    items = []
    for v in raw.values():
        try:
            items.append(json.loads(v))
        except Exception:
            pass
    return items


@router.get("/live")
async def get_live_feed(
    limit: int = 50,
    category: Optional[str] = None,
    min_weight: float = 0.0,
):
    """
    Get live news feed with editorial weight scores (Redis-backed).
    Auto-sorted by Editorial Weight Score descending.
    """
    items = await _get_all_items()

    if category:
        items = [x for x in items if x.get("category") == category]
    if min_weight > 0:
        items = [x for x in items if x.get("editorial_weight", 0) >= min_weight]

    items = sorted(items, key=lambda x: x.get("editorial_weight", 0), reverse=True)
    return {"items": items[:limit], "total": len(items)}


@router.get("/stats")
async def get_feed_stats():
    """Get live statistics for the Feed Heartbeat dashboard."""
    items = await _get_all_items()
    if not items:
        return {
            "total": 0, "breaking": 0, "urgent": 0,
            "can_wait": 0, "exclusive": 0, "last_hour": 0,
            "avg_editorial_weight": 0,
        }
    return await heartbeat_service.get_live_stats(items)


@router.post("/fetch")
async def fetch_feeds(urls: List[str], source_name: str = "Manual"):
    """
    Manually fetch RSS feeds from given URLs.
    Items are stored in Redis with 2-hour TTL.
    """
    from ...models.news import NewsFeed

    results = []
    for url in urls:
        mock_feed = NewsFeed()
        mock_feed.id = str(uuid.uuid4())
        mock_feed.name = source_name
        mock_feed.url = url
        mock_feed.reliability_score = 0.75

        items = await heartbeat_service.fetch_feed(mock_feed)

        for item in items:
            weight_data = await heartbeat_service.calculate_editorial_weight(item)
            item.update(weight_data)
            category = await heartbeat_service.classify_category(
                item.get("title", ""), item.get("summary", "")
            )
            item["category"] = category.value if hasattr(category, "value") else str(category)

            item_key = item.get("url") or item.get("title", str(uuid.uuid4()))
            await redis_client.hset(FEED_CACHE_KEY, item_key, json.dumps(item, default=str))

        await redis_client.expire(FEED_CACHE_KEY, 7200)
        results.append({"url": url, "items_fetched": len(items)})

    total = await redis_client.hlen(FEED_CACHE_KEY)
    return {"results": results, "total_in_cache": total}


@router.get("/brief")
async def get_editor_brief():
    """Get Editor Brief Intelligence — actionable summary for editors."""
    items = await _get_all_items()
    if not items:
        return {
            "brief": "ไม่มีข่าวในระบบ กรุณาตั้งค่าแหล่งข่าวใน Settings หรือ fetch ด้วยตนเอง",
            "top_stories": [],
            "recommendations": [],
            "total_items": 0,
        }
    return await heartbeat_service.generate_editor_brief(items)


@router.get("/items/breaking")
async def get_breaking_news():
    """Get only breaking/urgent news items."""
    items = await _get_all_items()
    breaking = [x for x in items if x.get("is_breaking") or x.get("needs_immediate_action")]
    breaking = sorted(breaking, key=lambda x: x.get("editorial_weight", 0), reverse=True)
    return {"items": breaking, "count": len(breaking)}


@router.delete("/cache")
async def clear_feed_cache():
    """Clear the feed cache (admin utility)."""
    await redis_client.delete(FEED_CACHE_KEY)
    return {"message": "Feed cache cleared"}
