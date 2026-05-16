"""Tests for /feed/* endpoints."""
import pytest
from unittest.mock import AsyncMock, patch


@pytest.mark.anyio
async def test_feed_stats(client):
    """GET /feed/stats returns expected structure."""
    with patch("app.core.redis_client.redis_client") as mock_redis:
        mock_redis.hgetall = AsyncMock(return_value={})
        resp = await client.get("/api/v1/feed/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert "total_items" in data


@pytest.mark.anyio
async def test_feed_live_empty(client):
    """GET /feed/live returns empty list when cache is cold."""
    with patch("app.core.redis_client.redis_client") as mock_redis:
        mock_redis.hgetall = AsyncMock(return_value={})
        resp = await client.get("/api/v1/feed/live")
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert isinstance(data["items"], list)


@pytest.mark.anyio
async def test_feed_fetch_missing_urls(client):
    """POST /feed/fetch with no URLs returns 422."""
    resp = await client.post("/api/v1/feed/fetch", json={})
    assert resp.status_code == 422


@pytest.mark.anyio
async def test_feed_fetch_valid(client):
    """POST /feed/fetch with a URL list processes without crashing."""
    with patch("feedparser.parse") as mock_parse:
        mock_parse.return_value = MagicMock(
            bozo=False,
            entries=[MagicMock(
                title="Test News",
                summary="Summary",
                link="http://example.com/news",
                published_parsed=None,
                get=lambda k, d=None: d,
            )],
        )
        with patch("app.core.redis_client.redis_client") as mock_redis:
            mock_redis.hset = AsyncMock(return_value=1)
            mock_redis.expire = AsyncMock(return_value=True)
            resp = await client.post("/api/v1/feed/fetch", json={
                "urls": ["http://example.com/rss"],
                "source_name": "Test",
            })
    assert resp.status_code == 200


from unittest.mock import MagicMock
