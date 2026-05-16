"""
Content Studio Service
Generates image specifications and TTS scripts using Claude.
Optionally synthesizes audio via ElevenLabs API.
"""
import aiohttp
import logging
from typing import Optional, Dict, Any

from ..core.claude_client import claude
from ..config import settings

logger = logging.getLogger(__name__)

VOICE_IDS = {
    "liam": "TX3LPaxmHKxFdv7VOQHJ",
    "rachel": "21m00Tcm4TlvDq8ikWAM",
    "adam": "pNInz6obpgDQGcFmaJgB",
    "bella": "EXAVITQu4vr4xnSDxMaL",
    "antoni": "ErXwobaYiN019PkySvjV",
    "josh": "TxGEqnHWrfWFTfGW9XjX",
}

IMAGE_STYLE_PROMPTS = {
    "photorealistic": "ultra-realistic photography, sharp focus, professional camera",
    "cinematic": "cinematic film still, dramatic lighting, movie-quality",
    "illustration": "editorial illustration, clean lines, professional design",
    "minimalist": "minimalist composition, clean background, simple elements",
    "abstract": "abstract art, geometric forms, conceptual",
    "news_style": "news photography style, documentary, factual, neutral",
}

CAMERA_ANGLE_PROMPTS = {
    "eye_level": "eye-level shot, direct perspective",
    "aerial": "aerial view, drone shot, bird's eye perspective",
    "low_angle": "low angle shot, looking up, powerful perspective",
    "high_angle": "high angle shot, looking down",
    "close_up": "close-up shot, macro detail, tight frame",
    "wide_angle": "wide angle shot, panoramic view",
    "over_shoulder": "over the shoulder shot",
    "dutch_angle": "dutch angle, tilted frame, dramatic tension",
    "isometric": "isometric 3D view, equal perspective",
}

ASPECT_RATIO_DIMS = {
    "16:9": "1920x1080",
    "1:1": "1080x1080",
    "9:16": "1080x1920",
    "4:5": "1080x1350",
    "3:2": "1200x800",
    "4:3": "1200x900",
}


class ContentStudioService:

    async def generate_image_spec(
        self,
        title: str,
        summary: str,
        category: str = "",
        preferred_style: str = "news_style",
        preferred_ratio: str = "16:9",
        preferred_angle: str = "eye_level",
    ) -> Dict[str, Any]:
        """
        Generate a complete image specification for a news article.
        Returns prompt for image generation tools (Midjourney, DALL-E, Stable Diffusion).
        """
        prompt = f"""วิเคราะห์ข่าวนี้และสร้างสเปคภาพประกอบที่เหมาะสม:

หัวข้อ: {title}
สรุป: {summary}
หมวด: {category}

สร้าง JSON ที่มี:
{{
  "image_style": "{preferred_style}",
  "aspect_ratio": "{preferred_ratio}",
  "camera_angle": "{preferred_angle}",
  "main_subject": "สิ่งที่ควรเป็นจุดสนใจหลักในภาพ",
  "color_palette": ["#hex1", "#hex2", "#hex3"],
  "mood": "บรรยากาศภาพ",
  "image_prompt_en": "English image generation prompt (Midjourney/DALL-E style, 50-80 words)",
  "image_prompt_th": "คำอธิบายภาพภาษาไทย",
  "thai_alt_text": "คำอธิบาย alt text ภาษาไทยสำหรับ accessibility",
  "avoid": ["สิ่งที่ควรหลีกเลี่ยงในภาพ"]
}}"""

        result = await claude.complete_json(
            prompt=prompt,
            system="คุณเป็นผู้เชี่ยวชาญด้านการออกแบบสื่อและภาพประกอบข่าว",
            use_fast_model=True,
        )

        # Enrich with style/ratio/angle prompts for image gen tools
        style_modifier = IMAGE_STYLE_PROMPTS.get(preferred_style, "")
        angle_modifier = CAMERA_ANGLE_PROMPTS.get(preferred_angle, "")
        dimensions = ASPECT_RATIO_DIMS.get(preferred_ratio, "1920x1080")

        full_prompt = f"{result.get('image_prompt_en', '')} {style_modifier} {angle_modifier} --ar {preferred_ratio} --v 6"

        result["full_image_prompt"] = full_prompt.strip()
        result["dimensions"] = dimensions
        result["generation_tools"] = {
            "midjourney": f"/imagine {full_prompt}",
            "dalle": result.get("image_prompt_en", ""),
            "stable_diffusion": full_prompt,
        }

        return result

    async def generate_tts_script(
        self,
        article_body: str,
        article_title: str,
        reading_tone: str = "news",
        voice_profile: str = "liam",
        speed: float = 1.0,
    ) -> Dict[str, Any]:
        """
        Rewrite article as natural spoken Thai for TTS synthesis.
        Claude optimizes: shorter sentences, connectors, pronunciation hints.
        """
        tone_instructions = {
            "news": "ภาษาข่าวทางการ ชัดเจน กระชับ มีพลัง",
            "storytelling": "เล่าเรื่องราว มีจังหวะ สร้างความสนใจ",
            "casual": "เป็นกันเอง ภาษาพูดธรรมชาติ",
            "educational": "อธิบายชัดเจน เข้าใจง่าย มีการเน้นคำสำคัญ",
            "drama": "มีอารมณ์ เน้นความรู้สึก สร้างความตึงเครียด",
            "podcast": "สบายๆ เป็นธรรมชาติ เหมือนคุยกับเพื่อน",
        }

        tone_desc = tone_instructions.get(reading_tone, tone_instructions["news"])

        speed_label = {0.8: "ช้า", 1.0: "ปกติ", 1.1: "เร็ว", 1.2: "เร็วมาก"}.get(speed, "ปกติ")

        prompt = f"""แปลงบทความข่าวนี้เป็นสคริปต์อ่านออกเสียง:

หัวข้อ: {article_title}
เนื้อหา: {article_body[:3000]}

ข้อกำหนด:
- โทนเสียง: {tone_desc}
- ความเร็ว: {speed_label} ({speed}x)
- ประโยคสั้น ไม่เกิน 20 คำต่อประโยค
- หลีกเลี่ยงตัวย่อ ตัวเลขให้เขียนเป็นคำ (เช่น "1,000 บาท" → "หนึ่งพันบาท")
- ใส่ [หยุด] สั้นๆ ระหว่างประโยคสำคัญ
- ใส่ [เน้น] หน้าคำที่ควรเน้นเสียง
- ขึ้นต้นด้วย "สวัสดีครับ/ค่ะ" หรือเริ่มด้วยการเกริ่นนำที่น่าสนใจ

ตอบเป็น JSON:
{{
  "tts_script": "สคริปต์ฉบับเต็ม",
  "script_sections": [
    {{"section": "intro", "text": "ส่วนเปิด", "pause_after": true}},
    {{"section": "body", "text": "เนื้อหาหลัก", "pause_after": false}},
    {{"section": "closing", "text": "ส่วนปิด", "pause_after": false}}
  ],
  "estimated_duration_seconds": 120,
  "word_count": 200,
  "ssml": "<speak>...</speak>"
}}"""

        result = await claude.complete_json(
            prompt=prompt,
            system="คุณเป็นผู้เชี่ยวชาญด้านการผลิตสื่อเสียงและ Text-to-Speech ภาษาไทย",
            max_tokens=4000,
            use_fast_model=False,
        )

        result["voice_profile"] = voice_profile
        result["reading_tone"] = reading_tone
        result["speed"] = speed
        return result

    async def synthesize_audio(
        self,
        tts_script: str,
        voice_profile: str = "liam",
        speed: float = 1.0,
    ) -> Dict[str, Any]:
        """
        Synthesize audio via ElevenLabs API.
        Returns audio URL or error if API key not configured.
        """
        if not settings.ELEVENLABS_API_KEY:
            return {
                "success": False,
                "error": "ElevenLabs API key not configured",
                "tip": "ใส่ ELEVENLABS_API_KEY ใน .env เพื่อเปิดใช้งาน TTS",
                "tts_script": tts_script,
            }

        voice_id = VOICE_IDS.get(voice_profile, VOICE_IDS["liam"])
        url = f"{settings.ELEVENLABS_BASE_URL}/text-to-speech/{voice_id}"

        headers = {
            "xi-api-key": settings.ELEVENLABS_API_KEY,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
        }

        payload = {
            "text": tts_script,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.75,
                "similarity_boost": 0.75,
                "speed": speed,
            },
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=60)) as resp:
                    if resp.status == 200:
                        audio_bytes = await resp.read()
                        # In production: upload to S3/storage, return URL
                        # For demo: return base64 encoded audio
                        import base64
                        audio_b64 = base64.b64encode(audio_bytes).decode()
                        return {
                            "success": True,
                            "audio_base64": audio_b64,
                            "content_type": "audio/mpeg",
                            "voice_profile": voice_profile,
                            "duration_hint": f"{len(tts_script) // 15} วินาที (ประมาณ)",
                        }
                    else:
                        error_text = await resp.text()
                        logger.error(f"ElevenLabs error {resp.status}: {error_text}")
                        return {"success": False, "error": f"ElevenLabs API error: {resp.status}"}

        except Exception as e:
            logger.error(f"TTS synthesis error: {e}")
            return {"success": False, "error": str(e)}
