"""Tests for /studio/* endpoints."""
import pytest
from unittest.mock import AsyncMock, patch


IMAGE_SPEC_RESPONSE = {
    "image_style": "news_style",
    "aspect_ratio": "16:9",
    "camera_angle": "eye_level",
    "color_palette": ["#1a1a2e", "#16213e"],
    "generation_tools": {
        "midjourney": "news photography, Thai parliament, --ar 16:9",
        "dalle": "professional news photography Thai parliament",
        "stable_diffusion": "news photography Thai parliament --ar 16:9",
    },
    "thai_alt_text": "ภาพถ่ายข่าวรัฐสภาไทย",
}

TTS_SCRIPT_RESPONSE = {
    "tts_script": "สวัสดีครับ ขอนำเสนอข่าวสำคัญ...",
    "estimated_duration_seconds": 30,
    "word_count": 50,
}


@pytest.mark.anyio
async def test_generate_image_spec(client):
    """POST /studio/image-spec returns valid image generation prompt."""
    with patch("app.services.content_studio.ContentStudioService.generate_image_spec",
               AsyncMock(return_value=IMAGE_SPEC_RESPONSE)):
        resp = await client.post("/api/v1/studio/image-spec", json={
            "title": "รัฐสภาอนุมัติงบประมาณใหม่",
            "summary": "รัฐสภาได้อนุมัติงบประมาณประจำปี",
            "preferred_style": "news_style",
        })
    assert resp.status_code == 200
    data = resp.json()
    assert "generation_tools" in data or "color_palette" in data


@pytest.mark.anyio
async def test_generate_image_spec_missing_title(client):
    """POST /studio/image-spec without title returns 422."""
    resp = await client.post("/api/v1/studio/image-spec", json={
        "summary": "No title provided",
    })
    assert resp.status_code == 422


@pytest.mark.anyio
async def test_generate_tts_script(client):
    """POST /studio/tts/script returns Thai spoken script."""
    with patch("app.services.content_studio.ContentStudioService.generate_tts_script",
               AsyncMock(return_value=TTS_SCRIPT_RESPONSE)):
        resp = await client.post("/api/v1/studio/tts/script", json={
            "article_title": "ข่าวทดสอบ",
            "article_body": "เนื้อหาข่าวทดสอบระบบ TTS สำหรับการสร้างเสียงอ่านข่าว",
        })
    assert resp.status_code == 200
    data = resp.json()
    assert "tts_script" in data


@pytest.mark.anyio
async def test_generate_tts_script_missing_body(client):
    """POST /studio/tts/script without article_body returns 422."""
    resp = await client.post("/api/v1/studio/tts/script", json={
        "article_title": "Title only",
    })
    assert resp.status_code == 422


@pytest.mark.anyio
async def test_list_voices(client):
    """GET /studio/voices returns voice list."""
    resp = await client.get("/api/v1/studio/voices")
    assert resp.status_code == 200
    data = resp.json()
    assert "voices" in data
    assert len(data["voices"]) > 0
