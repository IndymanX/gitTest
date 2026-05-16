"""Full-text search across feed items and draft history."""
import json
from fastapi import APIRouter, Depends
from ...core.redis_client import redis_client
from ..routes.auth import require_user

router = APIRouter(prefix="/search", tags=["Search"])

DRAFTS_HISTORY_KEY = "drafts:history"
FEED_CACHE_KEY = "feed:items"


@router.get("")
async def search(
    q: str = "",
    type: str = "all",
    limit: int = 20,
    user: dict = Depends(require_user),
):
    """Search across feed items and draft history. type: all | feed | draft"""
    q_lower = q.strip().lower()
    if len(q_lower) < 2:
        return {"results": [], "total": 0, "query": q}

    results = []

    # Search draft history
    if type in ("all", "draft"):
        raw_drafts = await redis_client.lrange(DRAFTS_HISTORY_KEY, 0, 199)
        for raw in raw_drafts:
            item = json.loads(raw)
            searchable = " ".join([
                item.get("title", ""),
                item.get("news_title", ""),
                item.get("body_preview", ""),
            ]).lower()
            if q_lower in searchable:
                results.append({
                    "type": "draft",
                    "id": item.get("id", ""),
                    "title": item.get("title", ""),
                    "subtitle": item.get("news_title", ""),
                    "platform": item.get("platform", ""),
                    "date": item.get("generated_at", ""),
                })
            if len(results) >= limit * 2:
                break

    # Search feed items
    if type in ("all", "feed"):
        raw_feed = await redis_client.lrange(FEED_CACHE_KEY, 0, 499)
        for raw in raw_feed:
            item = json.loads(raw)
            searchable = " ".join([
                item.get("title", ""),
                item.get("summary") or "",
                item.get("source_name", ""),
            ]).lower()
            if q_lower in searchable:
                results.append({
                    "type": "feed",
                    "id": item.get("id", ""),
                    "title": item.get("title", ""),
                    "subtitle": item.get("source_name", ""),
                    "editorial_weight": item.get("editorial_weight", 0),
                    "date": item.get("published_at", ""),
                })
            if len(results) >= limit * 3:
                break

    return {"results": results[:limit], "total": len(results), "query": q}
