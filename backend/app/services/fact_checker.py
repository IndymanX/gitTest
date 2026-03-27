"""
Fact Checker Service
Detects claims in drafts and flags them for verification.
Integrates with source chain for provenance tracking.
"""
import re
from typing import Dict, List, Optional
import logging

from ..core.claude_client import claude

logger = logging.getLogger(__name__)

# Patterns that indicate verifiable claims
CLAIM_PATTERNS = [
    r'\d+\s*(คน|ราย|บาท|ล้าน|พันล้าน|%|เปอร์เซ็นต์)',  # Numbers with units
    r'(เพิ่มขึ้น|ลดลง|เติบโต)\s*\d+',  # Growth/decline claims
    r'(ครั้งแรก|สูงสุด|ต่ำสุด|มากที่สุด|น้อยที่สุด)',  # Superlatives
    r'(ตาม|อ้างอิง|รายงาน|เปิดเผย|ยืนยัน)ว่า',  # Attribution markers
    r'[A-Z][a-z]+\s+[A-Z][a-z]+\s+(กล่าว|บอก|ระบุ)',  # Named quotes
    r'\d{4}\s*(ปี|year)',  # Year references
]

FACT_CHECK_CATEGORIES = {
    "statistic": "ตัวเลข/สถิติ",
    "quote": "คำพูด/การอ้างอิง",
    "superlative": "การกล่าวอ้างสูงสุด/ต่ำสุด",
    "historical": "ข้อเท็จจริงทางประวัติศาสตร์",
    "attribution": "การอ้างถึงแหล่งข่าว",
    "scientific": "ข้อมูลทางวิทยาศาสตร์/การแพทย์",
}


class FactCheckerService:

    def detect_claims(self, text: str) -> List[Dict]:
        """
        Detect verifiable claims in text using pattern matching.
        Returns list of claims with position and category.
        """
        claims = []
        seen_texts = set()

        for pattern in CLAIM_PATTERNS:
            for match in re.finditer(pattern, text):
                # Get surrounding context
                start = max(0, match.start() - 50)
                end = min(len(text), match.end() + 100)
                context = text[start:end].strip()

                if context not in seen_texts:
                    seen_texts.add(context)
                    category = self._classify_claim(context)
                    claims.append({
                        "text": context,
                        "matched_pattern": match.group(),
                        "start_char": match.start(),
                        "end_char": match.end(),
                        "category": category,
                        "category_th": FACT_CHECK_CATEGORIES.get(category, category),
                        "verification_priority": self._get_priority(category, match.group()),
                    })

        return sorted(claims, key=lambda x: x["verification_priority"], reverse=True)

    def _classify_claim(self, context: str) -> str:
        if re.search(r'\d+\s*(คน|ราย|บาท|%)', context):
            return "statistic"
        if re.search(r'กล่าว|บอก|ระบุ|เปิดเผย', context):
            return "quote"
        if re.search(r'ครั้งแรก|สูงสุด|ต่ำสุด', context):
            return "superlative"
        if re.search(r'\d{4}\s*(ปี|year)', context):
            return "historical"
        if re.search(r'ตาม|อ้างอิง', context):
            return "attribution"
        return "general"

    def _get_priority(self, category: str, matched: str) -> int:
        """Higher priority = needs verification first."""
        priorities = {
            "superlative": 5,  # Highest risk
            "statistic": 4,
            "scientific": 4,
            "quote": 3,
            "historical": 3,
            "attribution": 2,
            "general": 1,
        }
        base = priorities.get(category, 1)

        # Boost if large numbers involved
        if re.search(r'(ล้าน|พันล้าน|billion|million)', matched):
            base += 1

        return base

    async def analyze_draft(self, draft_text: str, source_urls: List[str] = None) -> Dict:
        """
        Full fact-check analysis of a draft.
        Returns claims, risk assessment, and recommendations.
        """
        claims = self.detect_claims(draft_text)

        if not claims:
            return {
                "has_claims": False,
                "claims": [],
                "overall_risk": "low",
                "fact_check_score": 100.0,
                "recommendations": ["ไม่พบข้ออ้างที่ต้องตรวจสอบเป็นพิเศษ"],
            }

        # Use Claude for deeper claim analysis
        ai_analysis = await self._ai_claim_analysis(draft_text, claims[:10])

        high_risk = [c for c in claims if c["verification_priority"] >= 4]
        medium_risk = [c for c in claims if c["verification_priority"] == 3]

        if high_risk:
            overall_risk = "high"
            fact_check_score = max(0, 100 - (len(high_risk) * 20))
        elif medium_risk:
            overall_risk = "medium"
            fact_check_score = max(30, 100 - (len(medium_risk) * 10))
        else:
            overall_risk = "low"
            fact_check_score = 80.0

        return {
            "has_claims": True,
            "claims": claims,
            "high_priority_claims": high_risk,
            "medium_priority_claims": medium_risk,
            "total_claims": len(claims),
            "overall_risk": overall_risk,
            "fact_check_score": round(fact_check_score, 1),
            "ai_insights": ai_analysis,
            "source_urls_provided": source_urls or [],
            "recommendations": self._generate_recommendations(claims, overall_risk),
            "checklist": self._generate_checklist(claims),
        }

    async def _ai_claim_analysis(self, text: str, claims: List[Dict]) -> Dict:
        """Use Claude to analyze the most important claims."""
        claims_text = "\n".join([
            f"- [{c['category_th']}] {c['text'][:150]}"
            for c in claims[:5]
        ])

        prompt = f"""วิเคราะห์ข้ออ้างเหล่านี้จากบทความข่าว:

{claims_text}

สำหรับแต่ละข้ออ้าง ให้ประเมิน:
1. ความเสี่ยงที่จะผิดพลาดหรือทำให้เข้าใจผิด
2. แนะนำวิธีตรวจสอบ
3. แหล่งที่ควรไปตรวจสอบ

ตอบเป็น JSON: {{"claim_insights": [{{"claim": "...", "risk": "low|medium|high", "verify_how": "...", "verify_source": "..."}}]}}"""

        try:
            return await claude.complete_json(prompt, use_fast_model=True)
        except Exception:
            return {"claim_insights": []}

    def _generate_recommendations(self, claims: List[Dict], risk_level: str) -> List[str]:
        recs = []
        if risk_level == "high":
            recs.append("ตรวจสอบตัวเลขและสถิติก่อนเผยแพร่")
            recs.append("ยืนยันคำพูดโดยตรงกับแหล่งข่าว")
        if any(c["category"] == "superlative" for c in claims):
            recs.append("ระวังการใช้คำเช่น 'ครั้งแรก' 'สูงสุด' — ต้องมีหลักฐานยืนยัน")
        if any(c["category"] == "quote" for c in claims):
            recs.append("ตรวจสอบว่าคำพูดถูกนำมาอ้างอย่างครบถ้วน ไม่ตัดตอน")
        if not recs:
            recs.append("ข้อมูลดูสมเหตุสมผล แต่ควรระบุแหล่งที่มาให้ชัดเจน")
        return recs

    def _generate_checklist(self, claims: List[Dict]) -> List[Dict]:
        """Generate a fact-check to-do checklist for editors."""
        checklist = []
        for claim in claims[:10]:
            checklist.append({
                "task": f"ตรวจสอบ [{claim['category_th']}]: {claim['text'][:80]}...",
                "priority": claim["verification_priority"],
                "status": "pending",
            })
        return sorted(checklist, key=lambda x: x["priority"], reverse=True)
