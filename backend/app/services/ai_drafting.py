"""
AI Drafting Service
Generates news content using Claude with Style Constitution awareness.
Integrates with Brain Maturity profiles for personalized output.
"""
from typing import Dict, List, Optional, AsyncIterator
import logging

from ..core.claude_client import claude
from ..models.content import ContentFormat, Platform

logger = logging.getLogger(__name__)

PLATFORM_FORMAT_RULES = {
    Platform.WEBSITE: {
        "max_words": 800,
        "structure": "inverted_pyramid",
        "include_seo": True,
        "tone_modifier": "",
    },
    Platform.FACEBOOK: {
        "max_words": 300,
        "structure": "narrative",
        "include_seo": False,
        "tone_modifier": "เป็นกันเอง ใช้ภาษาพูดมากขึ้น",
    },
    Platform.TWITTER: {
        "max_words": 60,
        "structure": "headline_only",
        "include_seo": False,
        "tone_modifier": "กระชับ ตรงประเด็น",
    },
    Platform.LINE: {
        "max_words": 150,
        "structure": "bullet_points",
        "include_seo": False,
        "tone_modifier": "อ่านง่าย ใช้หัวข้อย่อย",
    },
    Platform.YOUTUBE: {
        "max_words": 500,
        "structure": "narrative",
        "include_seo": True,
        "tone_modifier": "สำหรับนำเสนอบนวิดีโอ",
    },
}

STRUCTURE_PROMPTS = {
    "inverted_pyramid": "เรียงลำดับจากสำคัญที่สุดก่อน (Inverted Pyramid) — ตอบ 5W1H ในย่อหน้าแรก",
    "narrative": "เล่าเป็นเรื่องราว มีจุดเริ่มต้น จุดสุดยอด และบทสรุป",
    "explainer": "อธิบายที่มาที่ไป ให้ความรู้ บอกผลกระทบ",
    "listicle": "นำเสนอเป็นรายการ มีหัวข้อย่อย ง่ายต่อการอ่าน",
    "bullet_points": "นำเสนอเป็น bullet points กระชับ",
    "headline_only": "ประโยคเดียว/สองประโยค ครบคำถามหลัก",
}


class AIDraftingService:

    async def generate_draft(
        self,
        news_item: Dict,
        format: ContentFormat = ContentFormat.ARTICLE,
        platform: Platform = Platform.WEBSITE,
        angle: Optional[str] = None,
        style_constitution: Optional[Dict] = None,
        brain_profile: Optional[Dict] = None,
        stream: bool = False,
    ) -> Dict:
        """
        Generate a news draft from a news item.
        Returns: title, lead, body, seo_title, seo_description, tags
        """
        platform_rules = PLATFORM_FORMAT_RULES.get(platform, PLATFORM_FORMAT_RULES[Platform.WEBSITE])
        structure_instruction = STRUCTURE_PROMPTS.get(
            platform_rules["structure"], STRUCTURE_PROMPTS["inverted_pyramid"]
        )

        system_prompt = self._build_system_prompt(style_constitution, brain_profile)
        user_prompt = self._build_draft_prompt(
            news_item=news_item,
            platform_rules=platform_rules,
            structure_instruction=structure_instruction,
            angle=angle,
            format=format,
        )

        if stream:
            return {"stream": True, "prompt": user_prompt, "system": system_prompt}

        try:
            result = await claude.complete_json(
                prompt=user_prompt,
                system=system_prompt,
                max_tokens=6000,
            )
            result["platform"] = platform.value
            result["format"] = format.value
            result["angle_used"] = angle
            result["word_count"] = len(result.get("body", "").split())
            result["reading_time_minutes"] = round(result["word_count"] / 200, 1)
            return result

        except Exception as e:
            logger.error(f"Draft generation error: {e}")
            raise

    async def stream_draft(
        self,
        news_item: Dict,
        format: ContentFormat = ContentFormat.ARTICLE,
        platform: Platform = Platform.WEBSITE,
        angle: Optional[str] = None,
        style_constitution: Optional[Dict] = None,
        brain_profile: Optional[Dict] = None,
    ) -> AsyncIterator[str]:
        """Stream draft generation token by token."""
        platform_rules = PLATFORM_FORMAT_RULES.get(platform, PLATFORM_FORMAT_RULES[Platform.WEBSITE])
        structure_instruction = STRUCTURE_PROMPTS.get(platform_rules["structure"], "")
        system_prompt = self._build_system_prompt(style_constitution, brain_profile)
        user_prompt = self._build_draft_prompt(
            news_item=news_item,
            platform_rules=platform_rules,
            structure_instruction=structure_instruction,
            angle=angle,
            format=format,
        )

        async for chunk in claude.stream(
            prompt=user_prompt,
            system=system_prompt,
            max_tokens=6000,
        ):
            yield chunk

    def _build_system_prompt(
        self,
        style_constitution: Optional[Dict],
        brain_profile: Optional[Dict],
    ) -> str:
        base = """คุณเป็นนักข่าวและนักเขียนมืออาชีพ ผู้เชี่ยวชาญการเขียนข่าวภาษาไทยตามมาตรฐานวารสารศาสตร์
หลักการสำคัญ:
- เขียนด้วยข้อเท็จจริงที่ตรวจสอบได้
- ใช้ภาษาที่กระชับ ชัดเจน อ่านง่าย
- ตอบ 5W1H (ใคร ทำอะไร ที่ไหน เมื่อไร ทำไม อย่างไร)
- ไม่แสดงความเห็นส่วนตัวในข่าวตรง
- ปฏิบัติตามจรรยาบรรณสื่อมวลชนไทย"""

        if style_constitution:
            formality = style_constitution.get("formality_level", 0.7)
            structure = style_constitution.get("preferred_structure", "inverted_pyramid")
            forbidden = style_constitution.get("forbidden_words", [])
            brand_voice = style_constitution.get("brand_voice_markers", [])

            base += f"""

สไตล์ขององค์กร:
- ระดับทางการ: {"ทางการสูง" if formality > 0.7 else "กึ่งทางการ" if formality > 0.4 else "เป็นกันเอง"}
- โครงสร้างที่ต้องการ: {structure}
- คำที่ห้ามใช้: {', '.join(forbidden) if forbidden else 'ไม่มี'}
- เอกลักษณ์สำนักข่าว: {', '.join(brand_voice) if brand_voice else 'ไม่มีข้อกำหนดพิเศษ'}"""

        if brain_profile and brain_profile.get("maturity_score", 0) > 20:
            base += f"""

สไตล์ส่วนตัว (ระดับ Brain Maturity {brain_profile['maturity_score']:.0f}%):
{brain_profile.get('style_summary', '')}"""

        return base

    def _build_draft_prompt(
        self,
        news_item: Dict,
        platform_rules: Dict,
        structure_instruction: str,
        angle: Optional[str],
        format: ContentFormat,
    ) -> str:
        title = news_item.get("title", "")
        summary = news_item.get("summary", "")
        content = news_item.get("content", "")
        source = news_item.get("source_name", "ไม่ระบุ")
        source_url = news_item.get("url", "")

        angle_instruction = f"\n**มุมมองที่ต้องการ:** {angle}" if angle else ""
        max_words = platform_rules["max_words"]
        tone_mod = platform_rules.get("tone_modifier", "")
        include_seo = platform_rules.get("include_seo", True)

        seo_instruction = """
- "seo_title": หัวข้อ SEO/AIO ที่ดึงดูดและมีคีย์เวิร์ด (max 60 ตัวอักษร)
- "seo_description": คำอธิบาย SEO (max 160 ตัวอักษร)
- "aio_keywords": คีย์เวิร์ดสำหรับ AI Optimization ["คำ1", "คำ2", ...]
- "tags": แท็กที่เกี่ยวข้อง 5-8 แท็ก""" if include_seo else """
- "seo_title": null
- "seo_description": null
- "aio_keywords": []
- "tags": แท็กที่เกี่ยวข้อง 3-5 แท็ก"""

        return f"""เขียน{format.value}ข่าวจากข้อมูลนี้:

**แหล่งข่าว:** {source}
**หัวข้อ:** {title}
**สรุป:** {summary}
**เนื้อหา:** {content[:2000] if content else "ไม่มีข้อมูลเพิ่มเติม"}
**URL อ้างอิง:** {source_url}
{angle_instruction}

**ข้อกำหนด:**
- ความยาว: ไม่เกิน {max_words} คำ
- โครงสร้าง: {structure_instruction}
- โทนเสียง: {tone_mod if tone_mod else "เป็นทางการ ตามมาตรฐานข่าว"}

ตอบเป็น JSON:
{{
  "title": "หัวข้อข่าวที่ดึงดูด",
  "lead": "ย่อหน้านำ (ตอบ 5W1H ใน 2-3 ประโยค)",
  "body": "เนื้อหาข่าวทั้งหมด",
  "source_attribution": "อ้างอิงแหล่งข่าวที่ชัดเจน",{seo_instruction}
  "fact_claims": ["ข้อเท็จจริงที่ควรตรวจสอบ 1", "ข้อเท็จจริง 2"]
}}"""

    async def adapt_for_platform(
        self,
        draft_body: str,
        draft_title: str,
        target_platform: Platform,
        style_constitution: Optional[Dict] = None,
    ) -> Dict:
        """Adapt existing draft for a specific platform."""
        platform_rules = PLATFORM_FORMAT_RULES.get(target_platform, PLATFORM_FORMAT_RULES[Platform.WEBSITE])

        prompt = f"""ปรับบทความข่าวนี้ให้เหมาะกับ {target_platform.value}:

หัวข้อเดิม: {draft_title}
เนื้อหาเดิม: {draft_body[:3000]}

ข้อกำหนด {target_platform.value}:
- ความยาวสูงสุด: {platform_rules['max_words']} คำ
- โครงสร้าง: {platform_rules['structure']}
- โทน: {platform_rules.get('tone_modifier', 'ตามมาตรฐานปกติ')}

ตอบเป็น JSON: {{"adapted_title": "...", "adapted_body": "..."}}"""

        result = await claude.complete_json(
            prompt=prompt,
            use_fast_model=True,
            max_tokens=2000,
        )
        result["platform"] = target_platform.value
        return result
