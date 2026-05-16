"""AI Brain Maturity API routes — Redis-persistent profiles."""
import json
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Literal

from ...services.brain_maturity import BrainMaturityService
from ...core.redis_client import redis_client, BRAIN_PROFILES_KEY

router = APIRouter(prefix="/brain", tags=["AI Brain Maturity"])
brain_service = BrainMaturityService()


async def _get_profile(profile_id: str) -> dict | None:
    raw = await redis_client.hget(BRAIN_PROFILES_KEY, profile_id)
    if not raw:
        return None
    return json.loads(raw)


async def _save_profile(profile: dict) -> None:
    await redis_client.hset(BRAIN_PROFILES_KEY, profile["id"], json.dumps(profile))


class LearnRequest(BaseModel):
    profile_id: str
    sample_text: str
    feedback: str = "accepted"
    edited_version: Optional[str] = None


class ProfileCreateRequest(BaseModel):
    profile_id: str
    name: str
    organization_id: str
    user_id: Optional[str] = None


class BulkLearnRequest(BaseModel):
    profile_id: str
    samples: List[str]
    feedback: Literal["accepted", "rejected", "edited"] = "accepted"


@router.post("/profiles")
async def create_profile(request: ProfileCreateRequest):
    """Create a new Brain Maturity profile (Redis-backed)."""
    profile = {
        "id": request.profile_id,
        "name": request.name,
        "organization_id": request.organization_id,
        "user_id": request.user_id,
        "maturity_score": 0.0,
        "total_samples_learned": 0,
        "total_feedback_received": 0,
        "accepted_count": 0,
        "rejected_count": 0,
        "edited_count": 0,
        "vocabulary_distribution": {},
        "sentence_patterns": [],
        "topic_expertise": {},
    }
    await _save_profile(profile)
    return {"profile": profile, "message": "Profile created. Start adding samples to build maturity."}


@router.get("/profiles/{profile_id}")
async def get_profile(profile_id: str):
    """Get a brain profile with maturity report."""
    profile = await _get_profile(profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    report = await brain_service.get_maturity_report(profile)
    return {"profile": profile, "report": report}


def _make_default_profile(profile_id: str) -> dict:
    return {
        "id": profile_id,
        "maturity_score": 0.0,
        "total_samples_learned": 0,
        "total_feedback_received": 0,
        "accepted_count": 0,
        "rejected_count": 0,
        "edited_count": 0,
        "vocabulary_distribution": {},
        "sentence_patterns": [],
    }


@router.post("/learn")
async def learn_from_sample(request: LearnRequest):
    """Submit a sample + feedback to train the brain profile."""
    if request.feedback not in ("accepted", "rejected", "edited"):
        raise HTTPException(status_code=400, detail="feedback must be: accepted/rejected/edited")

    profile = await _get_profile(request.profile_id) or _make_default_profile(request.profile_id)

    updated = await brain_service.learn_from_sample(
        profile=profile,
        sample_text=request.sample_text,
        feedback=request.feedback,
        edited_version=request.edited_version,
    )
    await _save_profile(updated)
    report = await brain_service.get_maturity_report(updated)

    return {
        "profile": updated,
        "report": report,
        "message": f"Learned from sample. Maturity: {updated['maturity_score']:.1f}%",
    }


@router.post("/bulk-learn")
async def bulk_learn(request: BulkLearnRequest):
    """Batch-train from multiple articles (max 50). Useful for cold-start onboarding."""
    if not request.samples:
        raise HTTPException(status_code=400, detail="samples list is empty")

    samples = [s for s in request.samples if s.strip()][:50]
    profile = await _get_profile(request.profile_id) or _make_default_profile(request.profile_id)

    for sample in samples:
        profile = await brain_service.learn_from_sample(
            profile=profile,
            sample_text=sample,
            feedback=request.feedback,
        )

    await _save_profile(profile)
    report = await brain_service.get_maturity_report(profile)

    return {
        "profile": profile,
        "report": report,
        "processed": len(samples),
        "message": f"เรียนรู้จาก {len(samples)} บทความสำเร็จ Maturity: {profile['maturity_score']:.1f}%",
    }


@router.get("/profiles/{profile_id}/style-prompt")
async def get_style_prompt(profile_id: str):
    """Get the style prompt injection for use in drafting."""
    profile = await _get_profile(profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    prompt = await brain_service.generate_style_prompt_injection(profile)
    return {
        "profile_id": profile_id,
        "style_prompt": prompt,
        "maturity_score": profile.get("maturity_score", 0),
        "is_usable": profile.get("maturity_score", 0) >= 20,
    }


@router.get("/profiles")
async def list_profiles():
    """List all brain profiles."""
    raw = await redis_client.hgetall(BRAIN_PROFILES_KEY)
    profiles_with_reports = []
    for pid, profile_json in raw.items():
        try:
            profile = json.loads(profile_json)
            report = await brain_service.get_maturity_report(profile)
            profiles_with_reports.append({
                "id": pid,
                "name": profile.get("name", pid),
                "maturity_score": profile.get("maturity_score", 0),
                "level": report["level"],
                "samples": profile.get("total_samples_learned", 0),
            })
        except Exception:
            pass
    return {"profiles": profiles_with_reports}
