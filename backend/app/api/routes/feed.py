"""Feed Heartbeat API routes."""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from pydantic import BaseModel
import json

from ...core.database import get_db
from ...services.feed_heartbeat import FeedHeartbeatService

router = APIRouter(prefix="/feed", tags=["Feed Heartbeat"])
heartbeat_service = FeedHeartbeatService()

# In-memory cache for demo (replace with Redis in production)
_feed_cache: dict = {}


class FeedSourceCreate(BaseModel):
    name: str
    url: str
    source_type: str = "rss"
    reliability_score: float = 0.8


class FeedSourceResponse(BaseModel):
    id: str
    name: str
    url: str
    source_type: str
    reliability_score: float
    is_active: bool


@router.get("/live")
async def get_live_feed(
    limit: int = 50,
    category: Optional[str] = None,
    min_weight: float = 0.0,
):
    """
    Get live news feed with editorial weight scores.
    The core of Feed Heartbeat — real-time, prioritized news.
    """
    # Return cached items (populated by background task)
    items = list(_feed_cache.values())

    if category:
        items = [x for x in items if x.get("category") == category]
    if min_weight > 0:
        items = [x for x in items if x.get("editorial_weight", 0) >= min_weight]

    items = sorted(items, key=lambda x: x.get("editorial_weight", 0), reverse=True)
    return {"items": items[:limit], "total": len(items)}


@router.get("/stats")
async def get_feed_stats():
    """Get live statistics for the Feed Heartbeat dashboard."""
    items = list(_feed_cache.values())
    if not items:
        return {
            "total": 0, "breaking": 0, "urgent": 0,
            "can_wait": 0, "exclusive": 0, "last_hour": 0,
        }
    return await heartbeat_service.get_live_stats(items)


@router.post("/fetch")
async def fetch_feeds(
    background_tasks: BackgroundTasks,
    urls: List[str],
    source_name: str = "Manual",
):
    """Manually trigger feed fetch for given URLs."""
    from ...models.news import NewsFeed
    import uuid

    results = []
    for url in urls:
        mock_feed = NewsFeed()
        mock_feed.id = str(uuid.uuid4())
        mock_feed.name = source_name
        mock_feed.url = url

        items = await heartbeat_service.fetch_feed(mock_feed)

        for item in items:
            weight_data = await heartbeat_service.calculate_editorial_weight(item)
            item.update(weight_data)
            category = await heartbeat_service.classify_category(
                item.get("title", ""), item.get("summary", "")
            )
            item["category"] = category.value if hasattr(category, 'value') else str(category)
            _feed_cache[item.get("url", item.get("title", ""))] = item

        results.append({"url": url, "items_fetched": len(items)})

    return {"results": results, "total_in_cache": len(_feed_cache)}


@router.get("/brief")
async def get_editor_brief():
    """Get Editor Brief Intelligence — actionable summary for editors."""
    items = list(_feed_cache.values())
    if not items:
        return {
            "brief": "ไม่มีข่าวในระบบ กรุณา fetch ข่าวก่อน",
            "top_stories": [],
            "recommendations": [],
        }
    return await heartbeat_service.generate_editor_brief(items)


@router.get("/items/breaking")
async def get_breaking_news():
    """Get only breaking/urgent news items."""
    items = [x for x in _feed_cache.values() if x.get("is_breaking") or x.get("needs_immediate_action")]
    items = sorted(items, key=lambda x: x.get("editorial_weight", 0), reverse=True)
    return {"items": items, "count": len(items)}


@router.get("/items/{item_url:path}")
async def get_news_item(item_url: str):
    """Get a specific news item by URL."""
    item = _feed_cache.get(item_url)
    if not item:
        raise HTTPException(status_code=404, detail="News item not found")
    return item
