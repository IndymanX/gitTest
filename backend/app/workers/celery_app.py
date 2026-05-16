"""
Celery application factory for AInewsroom background tasks.

Queue routing:
  feed      → feed polling tasks (high-frequency, lightweight)
  ai_heavy  → Claude drafting, brief generation, angle generation
  ai_light  → Claude claim detection (haiku model)
  media     → TTS, image processing
  publish   → social platform dispatch
"""
from celery import Celery
from celery.schedules import crontab
import os

BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/1")
RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/2")

celery_app = Celery(
    "ainewsroom",
    broker=BROKER_URL,
    result_backend=RESULT_BACKEND,
    include=[
        "app.workers.feed_tasks",
        "app.workers.ai_tasks",
        "app.workers.scheduler_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Bangkok",
    enable_utc=True,
    task_routes={
        "app.workers.feed_tasks.*": {"queue": "feed"},
        "app.workers.ai_tasks.generate_brief": {"queue": "ai_heavy"},
        "app.workers.ai_tasks.generate_draft": {"queue": "ai_heavy"},
        "app.workers.ai_tasks.generate_angles": {"queue": "ai_heavy"},
        "app.workers.ai_tasks.detect_claims": {"queue": "ai_light"},
        "app.workers.scheduler_tasks.*": {"queue": "publish"},
    },
    beat_schedule={
        "poll-all-feeds-every-5-min": {
            "task": "app.workers.feed_tasks.poll_all_feeds",
            "schedule": 300.0,
        },
        "process-scheduled-posts-every-minute": {
            "task": "app.workers.scheduler_tasks.process_scheduled_posts",
            "schedule": 60.0,  # every 60 seconds
        },
    },
    worker_prefetch_multiplier=1,
    task_acks_late=True,
)
