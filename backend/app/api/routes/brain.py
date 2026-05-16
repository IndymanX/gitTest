"""AI Brain Maturity API routes."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Literal

from ...services.brain_maturity import BrainMaturityService

router = APIRouter(prefix="/brain", tags=["AI Brain Maturity"])
brain_service = BrainMaturityService()

# In-memory profiles store (replace with DB in production)
_profiles: dict = {}


class LearnRequest(BaseModel):
    profile_id: str
    sample_text: str
    feedback: str = "accepted"  # accepted/rejected/edited
    edited_version: Optional[str] = None


class ProfileCreateRequest(BaseModel):
    profile_id: str
    name: str
    organization_id: str
    user_id: Optional[str] = None


@router.post("/profiles")
async def create_profile(request: ProfileCreateRequest):
    """Create a new Brain Maturity profile."""
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
    _profiles[request.profile_id] = profile
    return {"profile": profile, "message": "Profile created. Start adding samples to build maturity."}


@router.get("/profiles/{profile_id}")
async def get_profile(profile_id: str):
    """Get a brain profile with maturity report."""
    profile = _profiles.get(profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    report = await brain_service.get_maturity_report(profile)
    return {"profile": profile, "report": report}


@router.post("/learn")
async def learn_from_sample(request: LearnRequest):
    """
    Submit a sample + feedback to train the brain profile.
    This is the core learning loop of AI Brain Maturity.
    """
    profile = _profiles.get(request.profile_id)
    if not profile:
        # Create default profile if not exists
        profile = {
            "id": request.profile_id,
            "maturity_score": 0.0,
            "total_samples_learned": 0,
            "total_feedback_received": 0,
            "accepted_count": 0,
            "rejected_count": 0,
            "edited_count": 0,
            "vocabulary_distribution": {},
            "sentence_patterns": [],
        }

    if request.feedback not in ("accepted", "rejected", "edited"):
        raise HTTPException(status_code=400, detail="feedback must be: accepted/rejected/edited")

    updated_profile = await brain_service.learn_from_sample(
        profile=profile,
        sample_text=request.sample_text,
        feedback=request.feedback,
        edited_version=request.edited_version,
    )

    _profiles[request.profile_id] = updated_profile
    report = await brain_service.get_maturity_report(updated_profile)

    return {
        "profile": updated_profile,
        "report": report,
        "message": f"Learned from sample. Maturity: {updated_profile['maturity_score']:.1f}%",
    }


@router.get("/profiles/{profile_id}/style-prompt")
async def get_style_prompt(profile_id: str):
    """Get the style prompt injection for use in drafting."""
    profile = _profiles.get(profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    prompt = await brain_service.generate_style_prompt_injection(profile)
    return {
        "profile_id": profile_id,
        "style_prompt": prompt,
        "maturity_score": profile.get("maturity_score", 0),
        "is_usable": profile.get("maturity_score", 0) >= 20,
    }


class BulkLearnRequest(BaseModel):
    profile_id: str
    samples: List[str]
    feedback: Literal["accepted", "rejected", "edited"] = "accepted"


@router.post("/bulk-learn")
async def bulk_learn(request: BulkLearnRequest):
    """
    Batch-train Brain profile from multiple articles in one call.
    Useful for cold-start onboarding: paste 10+ articles, learn in one step.
    Max 50 samples per request.
    """
    if not request.samples:
        raise HTTPException(status_code=400, detail="samples list is empty")

    samples = [s for s in request.samples if s.strip()][:50]

    profile = _profiles.get(request.profile_id)
    if not profile:
        profile = {
            "id": request.profile_id,
            "maturity_score": 0.0,
            "total_samples_learned": 0,
            "total_feedback_received": 0,
            "accepted_count": 0,
            "rejected_count": 0,
            "edited_count": 0,
            "vocabulary_distribution": {},
            "sentence_patterns": [],
        }

    for sample in samples:
        profile = await brain_service.learn_from_sample(
            profile=profile,
            sample_text=sample,
            feedback=request.feedback,
        )

    _profiles[request.profile_id] = profile
    report = await brain_service.get_maturity_report(profile)

    return {
        "profile": profile,
        "report": report,
        "processed": len(samples),
        "message": f"เรียนรู้จาก {len(samples)} บทความสำเร็จ Maturity: {profile['maturity_score']:.1f}%",
    }


@router.get("/profiles")
async def list_profiles():
    """List all brain profiles."""
    profiles_with_reports = []
    for pid, profile in _profiles.items():
        report = await brain_service.get_maturity_report(profile)
        profiles_with_reports.append({
            "id": pid,
            "name": profile.get("name", pid),
            "maturity_score": profile.get("maturity_score", 0),
            "level": report["level"],
            "samples": profile.get("total_samples_learned", 0),
        })
    return {"profiles": profiles_with_reports}
