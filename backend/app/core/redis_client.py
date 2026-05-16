import redis.asyncio as aioredis
from ..config import settings

redis_client: aioredis.Redis = aioredis.from_url(
    settings.REDIS_URL,
    encoding="utf-8",
    decode_responses=True,
)

FEED_CACHE_KEY = "feed:items"
FEED_SOURCES_KEY = "feed:sources"
TOKEN_COUNTER_KEY = "token:monthly:{org_id}"
FEED_PUBSUB_CHANNEL = "feed:updates"
