"""
Angle Generator Service
1 news story → 3-5 content angles automatically.
Each angle targets different audiences and purposes.
"""
from typing import Dict, List, Optional
import logging

from ..core.claude_client import claude

logger = logging.getLogger(__name__)

ANGLE_TYPES = {
    "consumer": {
        "th": "มุมผู้บริโภค",
        "description": "ผลกระทบต่อประชาชนทั่วไป ค่าครองชีพ",
        "platform_best_fit": ["facebook", "line"],
    },
    "policy": {
        "th": "มุมนโยบาย",
        "description": "บทบาทรัฐบาล กฎหมาย การตัดสินใจเชิงนโยบาย",
        "platform_best_fit": ["website", "twitter"],
    },
    "business": {
        "th": "มุมธุรกิจ",
        "description": "ผลกระทบต่อธุรกิจ ตลาด การลงทุน",
        "platform_best_fit": ["website", "youtube"],
    },
    "data": {
        "th": "มุม Data/ตัวเลข",
        "description": "สถิติ กราฟ การเปรียบเทียบเชิงตัวเลข",
        "platform_best_fit": ["website", "instagram"],
    },
    "global": {
        "th": "มุมต่างประเทศ",
        "description": "เปรียบเทียบกับต่างประเทศ บริบทนานาชาติ",
        "platform_best_fit": ["website", "twitter"],
    },
    "human_interest": {
        "th": "มุมมนุษย์",
        "description": "เรื่องราวของคน ผู้ที่ได้รับผลกระทบโดยตรง",
        "platform_best_fit": ["facebook", "instagram", "tiktok"],
    },
    "explainer": {
        "th": "มุมอธิบาย",
        "description": "ทำความเข้าใจเรื่องซับซ้อน ให้ความรู้",
        "platform_best_fit": ["youtube", "website"],
    },
    "future": {
        "th": "มุมอนาคต",
        "description": "แนวโน้ม ผลกระทบระยะยาว สิ่งที่จะเกิดขึ้นต่อไป",
        "platform_best_fit": ["website", "podcast"],
    },
}


class AngleGeneratorService:

    async def generate_angles(
        self,
        news_item: Dict,
        num_angles: int = 5,
        selected_angle_types: Optional[List[str]] = None,
    ) -> Dict:
        """
        Generate multiple content angles from a single news item.
        Returns list of angle proposals with title, angle description, platform fit.
        """
        title = news_item.get("title", "")
        summary = news_item.get("summary", "")
        category = news_item.get("category", "")

        # Select relevant angle types
        angle_types_to_use = selected_angle_types or list(ANGLE_TYPES.keys())[:num_angles]

        angles_description = "\n".join([
            f"- {k} ({ANGLE_TYPES[k]['th']}): {ANGLE_TYPES[k]['description']}"
            for k in angle_types_to_use if k in ANGLE_TYPES
        ])

        prompt = f"""ข่าว: {title}
สรุป: {summary}
หมวด: {category}

สร้างมุมมองการนำเสนอข่าวนี้ {num_angles} มุม จากมุมมองเหล่านี้:
{angles_description}

สำหรับแต่ละมุม ให้ระบุ:
- angle_type: ชื่อ type ภาษาอังกฤษ
- angle_name_th: ชื่อภาษาไทย
- proposed_title: หัวข้อข่าวที่เหมาะกับมุมนี้
- hook: ประโยคเปิดที่ดึงดูดความสนใจ (1 ประโยค)
- key_questions: คำถาม 3 ข้อที่บทความนี้ควรตอบ
- target_audience: กลุ่มเป้าหมายหลัก
- best_platform: platform ที่เหมาะที่สุด
- estimated_effort: low/medium/high (ระดับความยากในการผลิต)
- research_needed: สิ่งที่ต้องค้นเพิ่มเติม

ตอบเป็น JSON: {{"angles": [...]}}"""

        try:
            result = await claude.complete_json(
                prompt=prompt,
                system="คุณเป็นผู้เชี่ยวชาญด้านกลยุทธ์คอนเทนต์สำหรับ newsroom",
                max_tokens=4000,
                use_fast_model=False,
            )

            angles = result.get("angles", [])

            # Enrich with platform metadata
            for angle in angles:
                angle_type = angle.get("angle_type", "")
                if angle_type in ANGLE_TYPES:
                    angle["platform_best_fit"] = ANGLE_TYPES[angle_type]["platform_best_fit"]
                    angle["angle_description"] = ANGLE_TYPES[angle_type]["description"]

            return {
                "news_title": title,
                "angles": angles,
                "total": len(angles),
                "content_plan_summary": self._build_content_plan(angles),
            }

        except Exception as e:
            logger.error(f"Angle generation error: {e}")
            return {"angles": [], "error": str(e)}

    def _build_content_plan(self, angles: List[Dict]) -> str:
        """Build a quick content plan summary from generated angles."""
        if not angles:
            return ""

        plan_lines = []
        for i, angle in enumerate(angles, 1):
            plan_lines.append(
                f"{i}. [{angle.get('angle_name_th', '')}] "
                f"→ {angle.get('best_platform', '?')} "
                f"(ความยาก: {angle.get('estimated_effort', '?')})"
            )
        return "\n".join(plan_lines)

    async def generate_repurpose_plan(
        self,
        original_article: str,
        original_title: str,
    ) -> Dict:
        """
        Given a published article, generate a repurposing plan.
        1 article → multiple content formats.
        """
        prompt = f"""บทความต้นฉบับ:
หัวข้อ: {original_title}
เนื้อหา: {original_article[:2000]}

สร้างแผน Repurpose Content จากบทความนี้:

1. Social Media Post (Facebook/LINE) — 3 เวอร์ชัน
2. Twitter/X thread — 5-7 tweets
3. TikTok/Reels script — 60 วินาที
4. YouTube description + timestamps
5. Newsletter snippet — 100 คำ
6. Podcast intro — 30 วินาที

ตอบเป็น JSON โดยแต่ละรูปแบบมี: format, content, platform, estimated_reach_multiplier"""

        try:
            result = await claude.complete_json(
                prompt=prompt,
                system="คุณเป็นผู้เชี่ยวชาญ content repurposing สำหรับสื่อดิจิทัล",
                max_tokens=5000,
            )
            return result
        except Exception as e:
            logger.error(f"Repurpose plan error: {e}")
            return {"error": str(e)}
