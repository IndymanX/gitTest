"""AI Drafting API routes."""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List
import json

from ...services.ai_drafting import AIDraftingService
from ...services.copyright_analysis import CopyrightAnalysisService
from ...services.fact_checker import FactCheckerService
from ...services.angle_generator import AngleGeneratorService
from ...models.content import ContentFormat, Platform

router = APIRouter(prefix="/draft", tags=["AI Drafting"])

drafting_service = AIDraftingService()
copyright_service = CopyrightAnalysisService()
fact_check_service = FactCheckerService()
angle_service = AngleGeneratorService()


class DraftRequest(BaseModel):
    news_item: dict
    format: str = "article"
    platform: str = "website"
    angle: Optional[str] = None
    style_constitution: Optional[dict] = None
    brain_profile: Optional[dict] = None
    auto_check_copyright: bool = True
    auto_check_facts: bool = True


class AngleRequest(BaseModel):
    news_item: dict
    num_angles: int = 5
    angle_types: Optional[List[str]] = None


class CopyrightRequest(BaseModel):
    draft_text: str
    draft_title: str = ""
    source_texts: List[str] = []
    source_chain: List[dict] = []


class FactCheckRequest(BaseModel):
    draft_text: str
    source_urls: List[str] = []


class RepurposeRequest(BaseModel):
    original_article: str
    original_title: str
    target_platforms: List[str] = ["facebook", "twitter", "line"]


@router.post("/generate")
async def generate_draft(request: DraftRequest):
    """
    Generate an AI draft from a news item.
    Automatically runs copyright + fact-check if enabled.
    """
    try:
        format_enum = ContentFormat(request.format)
        platform_enum = Platform(request.platform)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid format/platform: {e}")

    # Generate draft
    draft = await drafting_service.generate_draft(
        news_item=request.news_item,
        format=format_enum,
        platform=platform_enum,
        angle=request.angle,
        style_constitution=request.style_constitution,
        brain_profile=request.brain_profile,
    )

    result = {"draft": draft}

    # Auto copyright check
    if request.auto_check_copyright:
        source_text = request.news_item.get("content", "") or request.news_item.get("summary", "")
        copyright_result = await copyright_service.analyze(
            draft_text=draft.get("body", ""),
            source_texts=[source_text] if source_text else [],
            source_chain=request.news_item.get("source_chain", []),
            draft_title=draft.get("title", ""),
        )
        result["copyright"] = copyright_result

    # Auto fact check
    if request.auto_check_facts:
        fact_result = await fact_check_service.analyze_draft(
            draft_text=draft.get("body", ""),
            source_urls=[request.news_item.get("url", "")],
        )
        result["fact_check"] = fact_result

    return result


@router.post("/generate/stream")
async def generate_draft_stream(request: DraftRequest):
    """Stream draft generation token by token."""
    try:
        format_enum = ContentFormat(request.format)
        platform_enum = Platform(request.platform)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    async def token_stream():
        async for token in drafting_service.stream_draft(
            news_item=request.news_item,
            format=format_enum,
            platform=platform_enum,
            angle=request.angle,
            style_constitution=request.style_constitution,
            brain_profile=request.brain_profile,
        ):
            yield f"data: {json.dumps({'token': token})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(token_stream(), media_type="text/event-stream")


@router.post("/angles")
async def generate_angles(request: AngleRequest):
    """Generate multiple content angles from a single news item."""
    return await angle_service.generate_angles(
        news_item=request.news_item,
        num_angles=min(request.num_angles, 8),
        selected_angle_types=request.angle_types,
    )


@router.post("/copyright/check")
async def check_copyright(request: CopyrightRequest):
    """Run 3-axis copyright analysis on a draft."""
    return await copyright_service.analyze(
        draft_text=request.draft_text,
        source_texts=request.source_texts,
        source_chain=request.source_chain,
        draft_title=request.draft_title,
    )


@router.post("/factcheck")
async def fact_check(request: FactCheckRequest):
    """Run fact-check claim detection on a draft."""
    return await fact_check_service.analyze_draft(
        draft_text=request.draft_text,
        source_urls=request.source_urls,
    )


@router.post("/repurpose")
async def repurpose_content(request: RepurposeRequest):
    """Generate repurpose plan: 1 article → multiple platform formats."""
    return await angle_service.generate_repurpose_plan(
        original_article=request.original_article,
        original_title=request.original_title,
    )


@router.post("/adapt/{platform}")
async def adapt_for_platform(
    platform: str,
    body: dict,
):
    """Adapt an existing draft for a specific platform."""
    try:
        platform_enum = Platform(platform)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Unknown platform: {platform}")

    return await drafting_service.adapt_for_platform(
        draft_body=body.get("body", ""),
        draft_title=body.get("title", ""),
        target_platform=platform_enum,
        style_constitution=body.get("style_constitution"),
    )
