"""Tests for /settings/* endpoints."""
import pytest
from unittest.mock import AsyncMock, patch
import json


@pytest.mark.anyio
async def test_list_feeds_empty(client):
    """GET /settings/feeds returns empty list when no sources."""
    with patch("app.api.routes.settings.redis_client") as mock_redis:
        mock_redis.hgetall = AsyncMock(return_value={})
        resp = await client.get("/api/v1/settings/feeds")
    assert resp.status_code == 200
    data = resp.json()
    assert data["sources"] == []
    assert data["total"] == 0


@pytest.mark.anyio
async def test_add_feed(client):
    """POST /settings/feeds creates a new feed source."""
    with patch("app.api.routes.settings.redis_client") as mock_redis:
        mock_redis.hset = AsyncMock(return_value=1)
        resp = await client.post("/api/v1/settings/feeds", json={
            "name": "ไทยรัฐ",
            "url": "https://www.thairath.co.th/rss/news.xml",
            "reliability_score": 0.85,
        })
    assert resp.status_code == 200
    data = resp.json()
    assert data["source"]["name"] == "ไทยรัฐ"
    assert "id" in data["source"]


@pytest.mark.anyio
async def test_delete_feed_not_found(client):
    """DELETE /settings/feeds/{id} returns 404 for unknown id."""
    with patch("app.api.routes.settings.redis_client") as mock_redis:
        mock_redis.hdel = AsyncMock(return_value=0)
        resp = await client.delete("/api/v1/settings/feeds/nonexistent-id")
    assert resp.status_code == 404


@pytest.mark.anyio
async def test_get_style_constitution_default(client):
    """GET /settings/style-constitution returns defaults when not set."""
    with patch("app.api.routes.settings.redis_client") as mock_redis:
        mock_redis.get = AsyncMock(return_value=None)
        resp = await client.get("/api/v1/settings/style-constitution")
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_default"] is True
    assert "formality_level" in data["style_constitution"]


@pytest.mark.anyio
async def test_save_style_constitution(client):
    """POST /settings/style-constitution persists data."""
    with patch("app.api.routes.settings.redis_client") as mock_redis:
        mock_redis.set = AsyncMock(return_value=True)
        resp = await client.post("/api/v1/settings/style-constitution", json={
            "formality_level": 0.8,
            "preferred_structure": "narrative",
            "forbidden_words": ["เสียชีวิต"],
            "brand_voice_markers": ["รายงานพิเศษ"],
        })
    assert resp.status_code == 200
    data = resp.json()
    assert data["style_constitution"]["preferred_structure"] == "narrative"


@pytest.mark.anyio
async def test_token_usage_zero(client):
    """GET /settings/token-usage returns zeros when no usage recorded."""
    with patch("app.api.routes.settings.redis_client") as mock_redis:
        mock_redis.get = AsyncMock(return_value=None)
        resp = await client.get("/api/v1/settings/token-usage")
    assert resp.status_code == 200
    data = resp.json()
    assert data["monthly_tokens"] == 0
    assert data["alert"] is False
    assert len(data["daily_trend"]) == 7
