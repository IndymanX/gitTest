"""Content Studio API routes — image spec + TTS voiceover."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List

from ...services.content_studio import ContentStudioService

router = APIRouter(prefix="/studio", tags=["Content Studio"])
studio_service = ContentStudioService()


class ImageSpecRequest(BaseModel):
    title: str
    summary: str = ""
    category: str = ""
    preferred_style: str = "news_style"
    preferred_ratio: str = "16:9"
    preferred_angle: str = "eye_level"


class TTSScriptRequest(BaseModel):
    article_title: str
    article_body: str
    reading_tone: str = "news"
    voice_profile: str = "liam"
    speed: float = Field(default=1.0, ge=0.5, le=2.0)


class TTSSynthesizeRequest(BaseModel):
    tts_script: str
    voice_profile: str = "liam"
    speed: float = Field(default=1.0, ge=0.5, le=2.0)


@router.post("/image-spec")
async def generate_image_spec(request: ImageSpecRequest):
    """
    Generate complete image specification for a news article.
    Returns prompt for Midjourney, DALL-E, Stable Diffusion.
    """
    return await studio_service.generate_image_spec(
        title=request.title,
        summary=request.summary,
        category=request.category,
        preferred_style=request.preferred_style,
        preferred_ratio=request.preferred_ratio,
        preferred_angle=request.preferred_angle,
    )


@router.post("/tts/script")
async def generate_tts_script(request: TTSScriptRequest):
    """
    Rewrite article as natural spoken Thai optimized for TTS.
    Claude shortens sentences, adds connectors, pronunciation hints.
    """
    if not request.article_body.strip():
        raise HTTPException(status_code=400, detail="article_body is required")

    return await studio_service.generate_tts_script(
        article_body=request.article_body,
        article_title=request.article_title,
        reading_tone=request.reading_tone,
        voice_profile=request.voice_profile,
        speed=request.speed,
    )


@router.post("/tts/generate")
async def synthesize_audio(request: TTSSynthesizeRequest):
    """
    Synthesize audio via ElevenLabs API.
    Returns base64 audio or error with tip if API key not set.
    """
    if not request.tts_script.strip():
        raise HTTPException(status_code=400, detail="tts_script is required")

    return await studio_service.synthesize_audio(
        tts_script=request.tts_script,
        voice_profile=request.voice_profile,
        speed=request.speed,
    )


@router.get("/voices")
async def list_voices():
    """Available voice profiles with metadata."""
    return {
        "voices": [
            {"id": "liam", "name": "Liam", "gender": "male", "style": "professional"},
            {"id": "rachel", "name": "Rachel", "gender": "female", "style": "warm"},
            {"id": "adam", "name": "Adam", "gender": "male", "style": "authoritative"},
            {"id": "bella", "name": "Bella", "gender": "female", "style": "expressive"},
            {"id": "antoni", "name": "Antoni", "gender": "male", "style": "natural"},
            {"id": "josh", "name": "Josh", "gender": "male", "style": "casual"},
        ],
        "tones": [
            {"id": "news", "label": "ข่าว", "description": "ชัดเจน น่าเชื่อถือ"},
            {"id": "storytelling", "label": "เล่าเรื่อง", "description": "มีจังหวะ ดึงดูด"},
            {"id": "casual", "label": "สบายๆ", "description": "เป็นกันเอง ธรรมชาติ"},
            {"id": "educational", "label": "สาระ", "description": "อธิบายชัด เข้าใจง่าย"},
            {"id": "drama", "label": "ดราม่า", "description": "มีอารมณ์ เร้าใจ"},
            {"id": "podcast", "label": "พอดแคสต์", "description": "สบาย เหมือนคุยกัน"},
        ],
    }


@router.get("/image-styles")
async def list_image_styles():
    """Available image styles with metadata."""
    return {
        "styles": [
            {"id": "photorealistic", "label": "Photorealistic", "icon": "📸"},
            {"id": "cinematic", "label": "Cinematic", "icon": "🎬"},
            {"id": "illustration", "label": "Illustration", "icon": "🎨"},
            {"id": "minimalist", "label": "Minimalist", "icon": "⬜"},
            {"id": "abstract", "label": "Abstract", "icon": "🔷"},
            {"id": "news_style", "label": "News Style", "icon": "📰"},
        ],
        "aspect_ratios": [
            {"id": "16:9", "label": "16:9", "description": "YouTube / Blog"},
            {"id": "1:1", "label": "1:1", "description": "IG / FB Post"},
            {"id": "9:16", "label": "9:16", "description": "Reels / TikTok"},
            {"id": "4:5", "label": "4:5", "description": "IG สี่เหลี่ยม"},
            {"id": "3:2", "label": "3:2", "description": "Twitter / X"},
            {"id": "4:3", "label": "4:3", "description": "Presentation"},
        ],
        "camera_angles": [
            {"id": "eye_level", "label": "Eye Level", "description": "มุมตรง (ปกติ)"},
            {"id": "aerial", "label": "Aerial", "description": "มุมสูง / โดรน"},
            {"id": "low_angle", "label": "Low Angle", "description": "มุมต่ำ ดูยิ่งใหญ่"},
            {"id": "high_angle", "label": "High Angle", "description": "มุมกดลง"},
            {"id": "close_up", "label": "Close-Up", "description": "ถ่ายใกล้ / แมโคร"},
            {"id": "wide_angle", "label": "Wide Angle", "description": "มุมกว้าง / พาโนรามา"},
            {"id": "over_shoulder", "label": "Over Shoulder", "description": "มุมข้ามไหล่"},
            {"id": "dutch_angle", "label": "Dutch Angle", "description": "เอียง / ดราม่า"},
            {"id": "isometric", "label": "Isometric", "description": "มุม 3 มิติ"},
        ],
    }
