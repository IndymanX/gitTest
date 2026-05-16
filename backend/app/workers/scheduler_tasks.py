"""Celery task — process due scheduled social posts."""
import json
import logging
import asyncio
from datetime import datetime

from .celery_app import celery_app

logger = logging.getLogger(__name__)

SCHEDULED_KEY = "scheduled:posts"


@celery_app.task(bind=True, name="app.workers.scheduler_tasks.process_scheduled_posts",
                 max_retries=1, default_retry_delay=60)
def process_scheduled_posts(self):
    """Check Redis sorted set for due posts and dispatch them to social platforms."""
    asyncio.run(_dispatch_due_posts())


async def _dispatch_due_posts():
    from ..core.redis_client import redis_client
    from ..services.social_publisher import SocialPublisherService

    now = datetime.utcnow().timestamp()
    raw_items = await redis_client.zrangebyscore(SCHEDULED_KEY, "-inf", now)
    if not raw_items:
        return

    publisher = SocialPublisherService()
    for raw in raw_items:
        post = json.loads(raw)
        try:
            body_text = f"{post['title']}\n\n{post['body']}"
            results = await publisher.publish_to_platforms(
                platforms=post["platforms"],
                message=body_text,
                link=post.get("link"),
            )
            logger.info(f"Scheduled post {post['id']} dispatched: {results}")
        except Exception as e:
            logger.error(f"Failed to dispatch scheduled post {post['id']}: {e}")
        finally:
            await redis_client.zrem(SCHEDULED_KEY, raw)
