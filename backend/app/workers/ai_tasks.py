"""
Async AI generation tasks via Celery.
Decouples Claude API calls from HTTP request lifecycle.
"""
import asyncio
import json
import logging
from typing import Optional

from .celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="app.workers.ai_tasks.generate_brief", bind=True)
def generate_brief(self, news_item: dict, org_id: str = "default") -> dict:
    """Generate an Editor Brief for a news item asynchronously."""
    try:
        return asyncio.run(_generate_brief_async(news_item))
    except Exception as exc:
        logger.error(f"Brief generation task failed: {exc}")
        self.retry(exc=exc, countdown=30, max_retries=2)


async def _generate_brief_async(news_item: dict) -> dict:
    from ..services.feed_heartbeat import FeedHeartbeatService
    service = FeedHeartbeatService()
    return await service.generate_editor_brief([news_item])


@celery_app.task(name="app.workers.ai_tasks.generate_draft", bind=True)
def generate_draft(
    self,
    news_item: dict,
    format: str = "article",
    platform: str = "website",
    angle: Optional[str] = None,
    style_constitution: Optional[dict] = None,
    brain_profile: Optional[dict] = None,
) -> dict:
    """Generate an AI draft asynchronously with copyright + fact check."""
    try:
        return asyncio.run(_generate_draft_async(
            news_item, format, platform, angle, style_constitution, brain_profile
        ))
    except Exception as exc:
        logger.error(f"Draft generation task failed: {exc}")
        self.retry(exc=exc, countdown=60, max_retries=2)


async def _generate_draft_async(news_item, format, platform, angle, style_constitution, brain_profile):
    from ..services.ai_drafting import AIDraftingService
    from ..services.copyright_analysis import CopyrightAnalysisService
    from ..services.fact_checker import FactCheckerService
    from ..models.content import ContentFormat, Platform as PlatformEnum

    drafting = AIDraftingService()
    copyright_svc = CopyrightAnalysisService()
    fact_svc = FactCheckerService()

    draft = await drafting.generate_draft(
        news_item=news_item,
        format=ContentFormat(format),
        platform=PlatformEnum(platform),
        angle=angle,
        style_constitution=style_constitution,
        brain_profile=brain_profile,
    )

    source_text = news_item.get("content") or news_item.get("summary", "")
    copyright_result = await copyright_svc.analyze(
        draft_text=draft.get("body", ""),
        source_texts=[source_text] if source_text else [],
        source_chain=news_item.get("source_chain", []),
    )

    fact_result = await fact_svc.analyze_draft(draft.get("body", ""))

    return {"draft": draft, "copyright": copyright_result, "fact_check": fact_result}


@celery_app.task(name="app.workers.ai_tasks.generate_angles", bind=True)
def generate_angles(self, news_item: dict, num_angles: int = 5) -> dict:
    """Generate content angles asynchronously."""
    try:
        return asyncio.run(_generate_angles_async(news_item, num_angles))
    except Exception as exc:
        logger.error(f"Angle generation task failed: {exc}")
        self.retry(exc=exc, countdown=30, max_retries=2)


async def _generate_angles_async(news_item: dict, num_angles: int) -> dict:
    from ..services.angle_generator import AngleGeneratorService
    service = AngleGeneratorService()
    return await service.generate_angles(news_item=news_item, num_angles=num_angles)


@celery_app.task(name="app.workers.ai_tasks.detect_claims", bind=True)
def detect_claims(self, draft_text: str) -> dict:
    """Detect fact-checkable claims asynchronously (uses haiku model)."""
    try:
        return asyncio.run(_detect_claims_async(draft_text))
    except Exception as exc:
        logger.error(f"Claim detection task failed: {exc}")
        self.retry(exc=exc, countdown=15, max_retries=2)


async def _detect_claims_async(draft_text: str) -> dict:
    from ..services.fact_checker import FactCheckerService
    service = FactCheckerService()
    return await service.analyze_draft(draft_text)
