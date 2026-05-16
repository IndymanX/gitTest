"""Social media publishing service.

Supports: LINE Notify, Facebook Page, Twitter/X API v2.
All platforms are opt-in — returns a 'skipped' result when credentials not set.
"""
import logging
from typing import Optional
import aiohttp

from ..config import settings

logger = logging.getLogger(__name__)


class SocialPublisherService:

    async def publish_line(self, message: str, image_url: Optional[str] = None) -> dict:
        """Publish to LINE Notify (token-based, no OAuth needed)."""
        if not settings.LINE_NOTIFY_TOKEN:
            return {"platform": "line", "status": "skipped", "reason": "LINE_NOTIFY_TOKEN not set"}

        data = aiohttp.FormData()
        data.add_field("message", f"\n{message[:999]}")  # LINE Notify max ~1000 chars
        if image_url:
            data.add_field("imageThumbnail", image_url)
            data.add_field("imageFullsize", image_url)

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://notify-api.line.me/api/notify",
                    headers={"Authorization": f"Bearer {settings.LINE_NOTIFY_TOKEN}"},
                    data=data,
                    timeout=aiohttp.ClientTimeout(total=15),
                ) as resp:
                    body = await resp.json()
                    if resp.status == 200:
                        return {"platform": "line", "status": "published", "response": body}
                    return {"platform": "line", "status": "error", "http_status": resp.status, "response": body}
        except Exception as e:
            logger.error(f"LINE Notify error: {e}")
            return {"platform": "line", "status": "error", "reason": str(e)}

    async def publish_facebook(self, message: str, link: Optional[str] = None) -> dict:
        """Publish to Facebook Page via Graph API."""
        if not settings.FACEBOOK_PAGE_ID or not settings.FACEBOOK_PAGE_ACCESS_TOKEN:
            return {"platform": "facebook", "status": "skipped", "reason": "FACEBOOK_PAGE_ID or FACEBOOK_PAGE_ACCESS_TOKEN not set"}

        payload = {
            "message": message[:63206],  # FB max length
            "access_token": settings.FACEBOOK_PAGE_ACCESS_TOKEN,
        }
        if link:
            payload["link"] = link

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"https://graph.facebook.com/v19.0/{settings.FACEBOOK_PAGE_ID}/feed",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=15),
                ) as resp:
                    body = await resp.json()
                    if resp.status == 200 and "id" in body:
                        post_id = body["id"]
                        return {
                            "platform": "facebook",
                            "status": "published",
                            "post_id": post_id,
                            "url": f"https://facebook.com/{post_id.replace('_', '/posts/')}",
                        }
                    return {"platform": "facebook", "status": "error", "http_status": resp.status, "response": body}
        except Exception as e:
            logger.error(f"Facebook API error: {e}")
            return {"platform": "facebook", "status": "error", "reason": str(e)}

    async def publish_twitter(self, text: str) -> dict:
        """Publish to Twitter/X using OAuth 2.0 user context (Bearer Token)."""
        if not settings.TWITTER_BEARER_TOKEN:
            return {"platform": "twitter", "status": "skipped", "reason": "TWITTER_BEARER_TOKEN not set"}

        try:
            import base64
            import hmac
            import hashlib
            import time
            import urllib.parse
            import uuid

            # OAuth 1.0a user-context (needed for write access with free tier)
            if all([settings.TWITTER_API_KEY, settings.TWITTER_API_SECRET,
                    settings.TWITTER_ACCESS_TOKEN, settings.TWITTER_ACCESS_SECRET]):
                oauth_timestamp = str(int(time.time()))
                oauth_nonce = uuid.uuid4().hex
                url = "https://api.twitter.com/2/tweets"

                params = {
                    "oauth_consumer_key": settings.TWITTER_API_KEY,
                    "oauth_nonce": oauth_nonce,
                    "oauth_signature_method": "HMAC-SHA1",
                    "oauth_timestamp": oauth_timestamp,
                    "oauth_token": settings.TWITTER_ACCESS_TOKEN,
                    "oauth_version": "1.0",
                }
                sig_base = "&".join([
                    "POST",
                    urllib.parse.quote(url, safe=""),
                    urllib.parse.quote("&".join(f"{k}={v}" for k, v in sorted(params.items())), safe=""),
                ])
                signing_key = f"{urllib.parse.quote(settings.TWITTER_API_SECRET, safe='')}&{urllib.parse.quote(settings.TWITTER_ACCESS_SECRET, safe='')}"
                signature = base64.b64encode(
                    hmac.new(signing_key.encode(), sig_base.encode(), hashlib.sha1).digest()
                ).decode()
                params["oauth_signature"] = signature
                auth_header = "OAuth " + ", ".join(f'{k}="{urllib.parse.quote(v, safe="")}"' for k, v in sorted(params.items()))

                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        url,
                        json={"text": text[:280]},
                        headers={"Authorization": auth_header, "Content-Type": "application/json"},
                        timeout=aiohttp.ClientTimeout(total=15),
                    ) as resp:
                        body = await resp.json()
                        if resp.status in (200, 201) and body.get("data"):
                            tweet_id = body["data"]["id"]
                            return {
                                "platform": "twitter",
                                "status": "published",
                                "tweet_id": tweet_id,
                                "url": f"https://twitter.com/i/web/status/{tweet_id}",
                            }
                        return {"platform": "twitter", "status": "error", "http_status": resp.status, "response": body}
            else:
                return {"platform": "twitter", "status": "skipped", "reason": "OAuth 1.0a credentials incomplete"}
        except Exception as e:
            logger.error(f"Twitter API error: {e}")
            return {"platform": "twitter", "status": "error", "reason": str(e)}

    async def publish_to_platforms(
        self,
        platforms: list[str],
        message: str,
        link: Optional[str] = None,
        image_url: Optional[str] = None,
    ) -> dict:
        """Publish to multiple platforms concurrently."""
        import asyncio
        tasks = {}
        if "line" in platforms:
            tasks["line"] = self.publish_line(message, image_url)
        if "facebook" in platforms:
            tasks["facebook"] = self.publish_facebook(message, link)
        if "twitter" in platforms:
            tasks["twitter"] = self.publish_twitter(message[:280])

        results = await asyncio.gather(*tasks.values(), return_exceptions=True)
        return {
            platform: (result if not isinstance(result, Exception) else {"status": "error", "reason": str(result)})
            for platform, result in zip(tasks.keys(), results)
        }
