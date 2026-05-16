"""Shared test fixtures for AInewsroom backend."""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest_asyncio.fixture
async def client():
    """Async HTTP client with mocked external dependencies."""
    # Patch Redis so tests don't need a real Redis server
    mock_redis = AsyncMock()
    mock_redis.hgetall = AsyncMock(return_value={})
    mock_redis.hset = AsyncMock(return_value=1)
    mock_redis.hdel = AsyncMock(return_value=1)
    mock_redis.hlen = AsyncMock(return_value=0)
    mock_redis.get = AsyncMock(return_value=None)
    mock_redis.set = AsyncMock(return_value=True)
    mock_redis.incrby = AsyncMock(return_value=1)
    mock_redis.expire = AsyncMock(return_value=True)
    mock_redis.pipeline = MagicMock(return_value=AsyncMock(
        incrby=AsyncMock(), expire=AsyncMock(), execute=AsyncMock(return_value=[])
    ))
    mock_redis.aclose = AsyncMock()

    with patch("app.core.redis_client.redis_client", mock_redis), \
         patch("app.core.database.init_db", AsyncMock()), \
         patch("app.core.database.engine", MagicMock()):

        from app.main import app
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            yield ac


@pytest.fixture
def mock_claude():
    """Patch Claude client to return deterministic responses."""
    with patch("app.core.claude_client.claude") as mock:
        mock.complete = AsyncMock(return_value="Mock AI response for testing")
        mock.complete_json = AsyncMock(return_value={
            "title": "Test Title",
            "body": "Test body content",
            "tags": ["test"],
            "seo_title": "Test SEO",
            "seo_description": "Test description",
            "word_count": 10,
            "reading_time_minutes": 1.0,
        })
        mock.stream = AsyncMock()
        yield mock
