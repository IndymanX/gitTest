"""Content scheduler — queue social posts for future publication."""
import json
import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from ...core.redis_client import redis_client
from ..routes.auth import require_user

router = APIRouter(prefix="/schedule", tags=["Scheduler"])

SCHEDULED_KEY = "scheduled:posts"


class ScheduleRequest(BaseModel):
    title: str
    body: str
    platforms: List[str]
    scheduled_at: datetime
    link: Optional[str] = None


@router.post("")
async def create_scheduled_post(req: ScheduleRequest, user: dict = Depends(require_user)):
    """Queue a social post for future publication."""
    if req.scheduled_at <= datetime.utcnow():
        raise HTTPException(status_code=400, detail="เวลาที่กำหนดต้องอยู่ในอนาคต")

    post_id = str(uuid.uuid4())
    post = {
        "id": post_id,
        "title": req.title,
        "body": req.body,
        "platforms": req.platforms,
        "scheduled_at": req.scheduled_at.isoformat(),
        "link": req.link,
        "created_by": user.get("email", ""),
        "status": "pending",
    }
    score = req.scheduled_at.timestamp()
    await redis_client.zadd(SCHEDULED_KEY, {json.dumps(post): score})
    return post


@router.get("")
async def list_scheduled_posts(user: dict = Depends(require_user)):
    """Return all pending scheduled posts ordered by publish time."""
    raw_items = await redis_client.zrange(SCHEDULED_KEY, 0, -1, withscores=True)
    posts = []
    for raw, score in raw_items:
        post = json.loads(raw)
        posts.append(post)
    return {"posts": posts, "total": len(posts)}


@router.delete("/{post_id}")
async def delete_scheduled_post(post_id: str, user: dict = Depends(require_user)):
    """Cancel a scheduled post by ID."""
    raw_items = await redis_client.zrange(SCHEDULED_KEY, 0, -1)
    for raw in raw_items:
        post = json.loads(raw)
        if post["id"] == post_id:
            await redis_client.zrem(SCHEDULED_KEY, raw)
            return {"deleted": post_id}
    raise HTTPException(status_code=404, detail="ไม่พบโพสต์ที่กำหนดไว้")
