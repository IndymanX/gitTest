"""Settings API routes — RSS sources + Style Constitution + Token Usage."""
import json
import uuid
from datetime import date, timedelta
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List

from ...core.redis_client import redis_client, FEED_SOURCES_KEY
from ...core.default_feeds import DEFAULT_THAI_FEEDS
from ...config import settings

router = APIRouter(prefix="/settings", tags=["Settings"])


class FeedSourceCreate(BaseModel):
    name: str
    url: str
    reliability_score: float = 0.8
    source_type: str = "rss"


class StyleConstitutionSave(BaseModel):
    formality_level: float = 0.7
    preferred_structure: str = "inverted_pyramid"
    forbidden_words: List[str] = []
    brand_voice_markers: List[str] = []
    avg_sentence_length: int = 20
    requires_source_attribution: bool = True
    min_sources_required: int = 2


STYLE_CONSTITUTION_KEY = "settings:style_constitution"


@router.get("/feeds")
async def list_feed_sources():
    """List all configured RSS feed sources."""
    sources_raw = await redis_client.hgetall(FEED_SOURCES_KEY)
    sources = []
    for source_id, source_json in sources_raw.items():
        try:
            source = json.loads(source_json)
            source["id"] = source_id
            sources.append(source)
        except Exception:
            pass
    return {"sources": sources, "total": len(sources)}


@router.post("/feeds")
async def add_feed_source(request: FeedSourceCreate):
    """Add a new RSS feed source."""
    source_id = str(uuid.uuid4())
    source_data = {
        "id": source_id,
        "name": request.name,
        "url": request.url,
        "reliability_score": request.reliability_score,
        "source_type": request.source_type,
        "is_active": True,
    }
    await redis_client.hset(FEED_SOURCES_KEY, source_id, json.dumps(source_data))
    return {"source": source_data, "message": "เพิ่มแหล่งข่าวสำเร็จ"}


@router.delete("/feeds/{source_id}")
async def remove_feed_source(source_id: str):
    """Remove a feed source."""
    deleted = await redis_client.hdel(FEED_SOURCES_KEY, source_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="ไม่พบแหล่งข่าวนี้")
    return {"message": "ลบแหล่งข่าวสำเร็จ"}


@router.post("/feeds/load-thai-defaults")
async def load_thai_default_feeds():
    """One-click: load all pre-configured Thai news RSS sources."""
    loaded = []
    for feed in DEFAULT_THAI_FEEDS:
        source_id = str(uuid.uuid4())
        source_data = {**feed, "id": source_id, "is_active": True}
        await redis_client.hset(FEED_SOURCES_KEY, source_id, json.dumps(source_data))
        loaded.append(source_data)
    return {"loaded": loaded, "count": len(loaded), "message": f"โหลดแหล่งข่าวไทย {len(loaded)} แหล่งสำเร็จ"}


@router.get("/style-constitution")
async def get_style_constitution():
    """Get current organization style constitution."""
    raw = await redis_client.get(STYLE_CONSTITUTION_KEY)
    if not raw:
        return {
            "style_constitution": {
                "formality_level": 0.7,
                "preferred_structure": "inverted_pyramid",
                "forbidden_words": [],
                "brand_voice_markers": [],
                "avg_sentence_length": 20,
                "requires_source_attribution": True,
                "min_sources_required": 2,
            },
            "is_default": True,
        }
    return {"style_constitution": json.loads(raw), "is_default": False}


@router.post("/style-constitution")
async def save_style_constitution(request: StyleConstitutionSave):
    """Save organization style constitution."""
    data = request.model_dump()
    await redis_client.set(STYLE_CONSTITUTION_KEY, json.dumps(data))
    return {"message": "บันทึก Style Constitution สำเร็จ", "style_constitution": data}


@router.get("/token-usage")
async def get_token_usage():
    """Return monthly token usage, cost estimate, and 7-day daily trend."""
    monthly_total = int(await redis_client.get("token:monthly:default") or 0)

    # Collect daily breakdown for last 7 days
    today = date.today()
    daily = []
    for i in range(6, -1, -1):
        day = (today - timedelta(days=i)).isoformat()
        inp = int(await redis_client.get(f"token:daily:{day}:input") or 0)
        out = int(await redis_client.get(f"token:daily:{day}:output") or 0)
        daily.append({"date": day, "input_tokens": inp, "output_tokens": out, "total": inp + out})

    # Rough cost estimate (uses default model pricing; mix of haiku/opus in practice)
    cost_usd = (monthly_total / 1_000_000) * 15.0  # conservative opus-level estimate

    budget_pct = 0.0
    if settings.MONTHLY_TOKEN_BUDGET > 0:
        budget_pct = min(monthly_total / settings.MONTHLY_TOKEN_BUDGET * 100, 100)

    return {
        "monthly_tokens": monthly_total,
        "estimated_cost_usd": round(cost_usd, 4),
        "budget_tokens": settings.MONTHLY_TOKEN_BUDGET,
        "budget_pct": round(budget_pct, 1),
        "alert": budget_pct >= 80,
        "daily_trend": daily,
    }
