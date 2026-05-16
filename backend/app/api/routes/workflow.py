"""Editorial workflow — draft review and approval pipeline.

Status flow: reporter submits → pending_review → editor approves/rejects
Workflow items stored in Redis HSET workflow:drafts {draft_id} {json}
"""
import json
from datetime import datetime
from typing import Literal, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from ...core.redis_client import redis_client
from ..routes.auth import require_user, require_role

router = APIRouter(prefix="/workflow", tags=["Editorial Workflow"])

WORKFLOW_KEY = "workflow:drafts"

STATUS_PENDING = "pending_review"
STATUS_APPROVED = "approved"
STATUS_REJECTED = "rejected"


class SubmitRequest(BaseModel):
    draft_id: str
    title: str
    body: str
    platform: str = "website"
    format: str = "article"
    word_count: int = 0
    news_title: str = ""
    note: str = ""  # reporter's note to editor


class ReviewRequest(BaseModel):
    action: Literal["approve", "reject"]
    comment: str = ""


@router.post("/submit")
async def submit_for_review(req: SubmitRequest, user: dict = Depends(require_user)):
    """Reporter submits a draft for editorial review."""
    existing = await redis_client.hget(WORKFLOW_KEY, req.draft_id)
    if existing:
        item = json.loads(existing)
        if item["status"] != STATUS_REJECTED:
            raise HTTPException(status_code=400, detail="บทความนี้อยู่ในกระบวนการตรวจสอบแล้ว")

    record = {
        "draft_id": req.draft_id,
        "title": req.title,
        "body": req.body,
        "platform": req.platform,
        "format": req.format,
        "word_count": req.word_count,
        "news_title": req.news_title,
        "note": req.note,
        "status": STATUS_PENDING,
        "submitted_by": user.get("email", ""),
        "submitted_by_name": user.get("full_name", ""),
        "submitted_at": datetime.utcnow().isoformat(),
        "reviewed_by": None,
        "reviewed_at": None,
        "review_comment": "",
    }
    await redis_client.hset(WORKFLOW_KEY, req.draft_id, json.dumps(record))
    return record


@router.get("/queue")
async def get_review_queue(reviewer: dict = require_role("editor", "admin")):
    """[Editor/Admin] List all pending drafts awaiting review."""
    all_raw = await redis_client.hgetall(WORKFLOW_KEY)
    pending = []
    for raw in all_raw.values():
        item = json.loads(raw)
        if item["status"] == STATUS_PENDING:
            pending.append(item)
    pending.sort(key=lambda x: x.get("submitted_at", ""), reverse=False)
    return {"items": pending, "total": len(pending)}


@router.get("/mine")
async def get_my_submissions(user: dict = Depends(require_user)):
    """Return all workflow items submitted by the current user."""
    all_raw = await redis_client.hgetall(WORKFLOW_KEY)
    mine = []
    email = user.get("email", "")
    for raw in all_raw.values():
        item = json.loads(raw)
        if item.get("submitted_by") == email:
            mine.append(item)
    mine.sort(key=lambda x: x.get("submitted_at", ""), reverse=True)
    return {"items": mine, "total": len(mine)}


@router.get("/statuses")
async def get_workflow_statuses(user: dict = Depends(require_user)):
    """Return a map of {draft_id: status} for all workflow items the user can see."""
    all_raw = await redis_client.hgetall(WORKFLOW_KEY)
    email = user.get("email", "")
    role = user.get("role", "reporter")

    statuses = {}
    for draft_id, raw in all_raw.items():
        item = json.loads(raw)
        if role in ("admin", "editor") or item.get("submitted_by") == email:
            statuses[draft_id] = {
                "status": item["status"],
                "review_comment": item.get("review_comment", ""),
                "reviewed_by": item.get("reviewed_by"),
            }
    return statuses


@router.patch("/{draft_id}")
async def review_draft(
    draft_id: str,
    req: ReviewRequest,
    reviewer: dict = require_role("editor", "admin"),
):
    """[Editor/Admin] Approve or reject a draft."""
    raw = await redis_client.hget(WORKFLOW_KEY, draft_id)
    if not raw:
        raise HTTPException(status_code=404, detail="ไม่พบบทความในคิวตรวจสอบ")

    item = json.loads(raw)
    if item["status"] != STATUS_PENDING:
        raise HTTPException(status_code=400, detail="บทความนี้ถูกตรวจสอบแล้ว")

    item["status"] = STATUS_APPROVED if req.action == "approve" else STATUS_REJECTED
    item["reviewed_by"] = reviewer.get("email", "")
    item["reviewed_by_name"] = reviewer.get("full_name", "")
    item["reviewed_at"] = datetime.utcnow().isoformat()
    item["review_comment"] = req.comment

    await redis_client.hset(WORKFLOW_KEY, draft_id, json.dumps(item))
    return item


@router.get("/{draft_id}")
async def get_workflow_item(draft_id: str, user: dict = Depends(require_user)):
    """Get workflow status for a specific draft."""
    raw = await redis_client.hget(WORKFLOW_KEY, draft_id)
    if not raw:
        raise HTTPException(status_code=404, detail="ไม่พบบทความในระบบตรวจสอบ")
    return json.loads(raw)
