"""
Feed polling Celery tasks.
Runs every 5 minutes via beat scheduler to fetch all configured RSS sources.
"""
import asyncio
import json
import logging
from datetime import datetime

from .celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="app.workers.feed_tasks.poll_all_feeds", bind=True, max_retries=3)
def poll_all_feeds(self):
    """
    Fetch all active feed sources, score items, store in Redis.
    Triggered by beat every 5 minutes.
    """
    try:
        asyncio.run(_poll_all_feeds_async())
    except Exception as exc:
        logger.error(f"Feed poll failed: {exc}")
        self.retry(exc=exc, countdown=60)


async def _poll_all_feeds_async():
    import redis.asyncio as aioredis
    from ..services.feed_heartbeat import FeedHeartbeatService
    from ..models.news import NewsFeed
    from ..core.redis_client import FEED_CACHE_KEY, FEED_SOURCES_KEY, FEED_PUBSUB_CHANNEL
    import os

    redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
    r = aioredis.from_url(redis_url, decode_responses=True)

    service = FeedHeartbeatService()

    # Load sources from Redis (set via Settings page or default feeds)
    sources_raw = await r.hgetall(FEED_SOURCES_KEY)
    if not sources_raw:
        logger.info("No feed sources configured, skipping poll")
        await r.close()
        return

    total_new = 0
    for source_id, source_json in sources_raw.items():
        try:
            source_data = json.loads(source_json)

            # Build a mock feed object
            feed = NewsFeed()
            feed.id = source_id
            feed.name = source_data.get("name", "Unknown")
            feed.url = source_data["url"]
            feed.reliability_score = source_data.get("reliability_score", 0.7)

            items = await service.fetch_feed(feed)

            for item in items:
                weight_data = await service.calculate_editorial_weight(item)
                item.update(weight_data)
                category = await service.classify_category(
                    item.get("title", ""), item.get("summary", "")
                )
                item["category"] = category.value if hasattr(category, "value") else str(category)
                item["source_reliability"] = source_data.get("reliability_score", 0.7)

                item_key = item.get("url") or item.get("title", "unknown")
                await r.hset(FEED_CACHE_KEY, item_key, json.dumps(item, default=str))
                await r.expire(FEED_CACHE_KEY, 7200)  # 2 hour TTL
                total_new += 1

        except Exception as e:
            logger.error(f"Error polling source {source_id}: {e}")

    # Broadcast update count via pub/sub (WebSocket clients subscribe)
    await r.publish(FEED_PUBSUB_CHANNEL, json.dumps({
        "type": "feed_updated",
        "new_items": total_new,
        "timestamp": datetime.utcnow().isoformat(),
    }))

    logger.info(f"Feed poll complete: {total_new} items processed")
    await r.close()


@celery_app.task(name="app.workers.feed_tasks.fetch_single_source")
def fetch_single_source(source_id: str, name: str, url: str, reliability_score: float = 0.7):
    """Fetch a single feed source on demand (triggered from Settings page)."""
    asyncio.run(_fetch_single_async(source_id, name, url, reliability_score))


async def _fetch_single_async(source_id: str, name: str, url: str, reliability_score: float):
    import redis.asyncio as aioredis
    from ..services.feed_heartbeat import FeedHeartbeatService
    from ..models.news import NewsFeed
    from ..core.redis_client import FEED_CACHE_KEY, FEED_PUBSUB_CHANNEL
    import os

    redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
    r = aioredis.from_url(redis_url, decode_responses=True)

    service = FeedHeartbeatService()
    feed = NewsFeed()
    feed.id = source_id
    feed.name = name
    feed.url = url
    feed.reliability_score = reliability_score

    items = await service.fetch_feed(feed)
    count = 0
    for item in items:
        weight_data = await service.calculate_editorial_weight(item)
        item.update(weight_data)
        item["source_reliability"] = reliability_score
        category = await service.classify_category(item.get("title", ""), item.get("summary", ""))
        item["category"] = category.value if hasattr(category, "value") else str(category)

        item_key = item.get("url") or item.get("title", "unknown")
        await r.hset(FEED_CACHE_KEY, item_key, json.dumps(item, default=str))
        count += 1

    await r.expire(FEED_CACHE_KEY, 7200)
    await r.publish(FEED_PUBSUB_CHANNEL, json.dumps({
        "type": "source_fetched",
        "source": name,
        "items": count,
    }))
    await r.close()
    logger.info(f"Single source fetch: {name} → {count} items")
