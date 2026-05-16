"""Social publishing routes."""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, List

from ...services.social_publisher import SocialPublisherService
from ...config import settings

router = APIRouter(prefix="/publish", tags=["Social Publisher"])
publisher_service = SocialPublisherService()


class PublishRequest(BaseModel):
    title: str
    body: str
    platforms: List[str] = ["line"]
    link: Optional[str] = None
    image_url: Optional[str] = None
    platform_overrides: Optional[dict] = None  # {"line": "custom message", "facebook": "custom message"}


@router.get("/status")
async def publishing_status():
    """Return which publishing platforms are configured."""
    return {
        "line": bool(settings.LINE_NOTIFY_TOKEN),
        "facebook": bool(settings.FACEBOOK_PAGE_ID and settings.FACEBOOK_PAGE_ACCESS_TOKEN),
        "twitter": bool(settings.TWITTER_BEARER_TOKEN or settings.TWITTER_API_KEY),
    }


@router.post("/send")
async def publish_to_platforms(request: PublishRequest):
    """
    Publish adapted content to one or more social platforms.
    Automatically truncates to platform limits.
    Returns per-platform status (published / skipped / error).
    """
    # Build per-platform message (use override if provided, else auto-format)
    overrides = request.platform_overrides or {}
    results = {}

    for platform in request.platforms:
        message = overrides.get(platform) or _format_for_platform(platform, request.title, request.body)

        if platform == "line":
            results["line"] = await publisher_service.publish_line(message, request.image_url)
        elif platform == "facebook":
            results["facebook"] = await publisher_service.publish_facebook(message, request.link)
        elif platform == "twitter":
            results["twitter"] = await publisher_service.publish_twitter(message[:280])

    published = [p for p, r in results.items() if r.get("status") == "published"]
    skipped = [p for p, r in results.items() if r.get("status") == "skipped"]
    errors = [p for p, r in results.items() if r.get("status") == "error"]

    return {
        "results": results,
        "summary": {
            "published": published,
            "skipped": skipped,
            "errors": errors,
        },
    }


def _format_for_platform(platform: str, title: str, body: str) -> str:
    """Default message formatter per platform."""
    if platform == "twitter":
        return f"{title}\n\n{body}"[:280]
    elif platform == "line":
        return f"📰 {title}\n\n{body[:500]}"
    else:
        return f"{title}\n\n{body}"
