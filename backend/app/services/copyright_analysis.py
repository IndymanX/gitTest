"""
Copyright Analysis Service — 3-axis analysis system.
Axis 1: Content (เนื้อหา) — factual/information similarity
Axis 2: Style (สำนวน) — phrasing/expression similarity
Axis 3: Structure (โครงสร้าง) — story structure/sequence similarity

Also provides Source Chain Transparency.
"""
import re
from typing import List, Dict, Optional, Tuple
from difflib import SequenceMatcher
import logging

from ..core.claude_client import claude
from ..config import settings

logger = logging.getLogger(__name__)


class CopyrightAnalysisService:

    def __init__(self):
        self.similarity_threshold = settings.COPYRIGHT_SIMILARITY_THRESHOLD
        self.danger_threshold = settings.COPYRIGHT_DANGER_THRESHOLD

    def _text_similarity(self, text1: str, text2: str) -> float:
        """Basic sequence-based text similarity (0-1)."""
        if not text1 or not text2:
            return 0.0
        return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()

    def _extract_sentences(self, text: str) -> List[str]:
        """Split text into sentences for granular comparison."""
        # Thai + English sentence splitting
        sentences = re.split(r'(?<=[.!?।\n])\s+|(?<=[\u0E2F\u0E46])\s+', text)
        return [s.strip() for s in sentences if len(s.strip()) > 10]

    def _calculate_content_similarity(self, draft: str, sources: List[str]) -> Tuple[float, List[Dict]]:
        """
        Axis 1: Content similarity — compare factual claims and information.
        Returns overall score and flagged segments.
        """
        draft_sentences = self._extract_sentences(draft)
        flagged = []
        max_score = 0.0

        for source_text in sources:
            source_sentences = self._extract_sentences(source_text)
            for d_sent in draft_sentences:
                for s_sent in source_sentences:
                    sim = self._text_similarity(d_sent, s_sent)
                    if sim >= self.similarity_threshold:
                        flagged.append({
                            "text": d_sent,
                            "similarity_score": round(sim, 3),
                            "risk_type": "content",
                            "matched_source": s_sent[:100],
                        })
                        max_score = max(max_score, sim)

        overall = max_score if flagged else 0.0
        return round(overall, 3), flagged

    def _calculate_style_similarity(self, draft: str, sources: List[str]) -> Tuple[float, List[Dict]]:
        """
        Axis 2: Style similarity — compare phrasing patterns and expressions.
        Looks for characteristic phrases/idioms that belong to the source.
        """
        # Extract n-grams (3-5 word phrases)
        def get_ngrams(text: str, n: int) -> List[str]:
            words = re.findall(r'\w+', text.lower())
            return [' '.join(words[i:i+n]) for i in range(len(words)-n+1)]

        draft_phrases = set(get_ngrams(draft, 4) + get_ngrams(draft, 5))
        flagged = []
        total_matches = 0

        for source_text in sources:
            source_phrases = set(get_ngrams(source_text, 4) + get_ngrams(source_text, 5))
            common = draft_phrases & source_phrases
            if common:
                total_matches += len(common)
                for phrase in list(common)[:5]:  # top 5 per source
                    flagged.append({
                        "text": phrase,
                        "similarity_score": 0.9,
                        "risk_type": "style",
                        "matched_source": f"Shared phrase: '{phrase}'",
                    })

        if not draft_phrases:
            return 0.0, []

        score = min(total_matches / max(len(draft_phrases), 1) * 3, 1.0)
        return round(score, 3), flagged

    def _calculate_structure_similarity(self, draft: str, sources: List[str]) -> Tuple[float, List[Dict]]:
        """
        Axis 3: Structure similarity — compare story structure and information sequence.
        """
        def get_structure_signature(text: str) -> List[str]:
            """Extract structural elements: paragraphs, headers, quote patterns."""
            paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
            structure = []
            for p in paragraphs:
                if p.startswith('#'):
                    structure.append("header")
                elif '"' in p or '\u201c' in p or 'กล่าวว่า' in p or 'กล่าวเพิ่มเติม' in p:
                    structure.append("quote")
                elif re.search(r'\d+\s*(คน|ราย|บาท|%)', p):
                    structure.append("statistic")
                else:
                    structure.append("prose")
            return structure

        draft_structure = get_structure_signature(draft)
        flagged = []
        max_score = 0.0

        for source_text in sources:
            source_structure = get_structure_signature(source_text)
            sim = self._text_similarity(
                ' '.join(draft_structure),
                ' '.join(source_structure)
            )
            if sim >= self.similarity_threshold:
                max_score = max(max_score, sim)
                flagged.append({
                    "text": f"Structure pattern: {' → '.join(draft_structure[:5])}",
                    "similarity_score": round(sim, 3),
                    "risk_type": "structure",
                    "matched_source": f"Similar sequence in source",
                })

        return round(max_score, 3), flagged

    def _calculate_risk_level(self, score: float) -> str:
        if score >= self.danger_threshold:
            return "high"
        elif score >= self.similarity_threshold:
            return "medium"
        return "low"

    async def analyze(
        self,
        draft_text: str,
        source_texts: List[str],
        source_chain: List[Dict],
        draft_title: str = "",
    ) -> Dict:
        """
        Full 3-axis copyright analysis with source chain transparency.
        """
        # Run 3-axis analysis
        content_score, content_flagged = self._calculate_content_similarity(draft_text, source_texts)
        style_score, style_flagged = self._calculate_style_similarity(draft_text, source_texts)
        structure_score, structure_flagged = self._calculate_structure_similarity(draft_text, source_texts)

        # Weighted overall (content matters most)
        overall = (content_score * 0.5) + (style_score * 0.3) + (structure_score * 0.2)
        overall = round(overall * 100, 1)  # convert to percentage

        all_flagged = content_flagged + style_flagged + structure_flagged
        risk_level = self._calculate_risk_level(overall / 100)

        # Get AI recommendations for risky content
        recommendations = []
        if overall > 5:
            recommendations = await self._get_ai_recommendations(
                draft_text=draft_text,
                flagged_segments=all_flagged,
                overall_score=overall,
            )

        # Analyze source chain for licensing
        enriched_chain = self._enrich_source_chain(source_chain)

        # Thai copyright act compliance check
        thai_compliant = overall < 30 or self._check_fair_use(draft_text, source_texts)

        return {
            "overall_risk_score": overall,
            "risk_level": risk_level,
            "content_similarity_score": round(content_score * 100, 1),
            "style_similarity_score": round(style_score * 100, 1),
            "structure_similarity_score": round(structure_score * 100, 1),
            "flagged_segments": all_flagged[:20],  # top 20
            "source_chain": enriched_chain,
            "recommendations": recommendations,
            "thai_copyright_act_compliant": thai_compliant,
            "fair_use_applicable": self._check_fair_use(draft_text, source_texts),
            "fair_use_reason": "การรายงานข่าวตามพ.ร.บ.ลิขสิทธิ์ มาตรา 32" if thai_compliant else None,
            "risk_breakdown": {
                "เนื้อหา": round(content_score * 100, 1),
                "สำนวน": round(style_score * 100, 1),
                "โครงสร้าง": round(structure_score * 100, 1),
            },
            "score_scale": {
                "safe": "0-30%",
                "warning": "31-60%",
                "danger": "61-100%",
            }
        }

    async def _get_ai_recommendations(
        self,
        draft_text: str,
        flagged_segments: List[Dict],
        overall_score: float,
    ) -> List[str]:
        """Use Claude to provide specific rewriting recommendations."""
        if not flagged_segments:
            return []

        flagged_summary = "\n".join([
            f"- [{f['risk_type']}] {f['text'][:100]}... (ความเสี่ยง {f['similarity_score']*100:.0f}%)"
            for f in flagged_segments[:5]
        ])

        prompt = f"""บทความนี้มีความเสี่ยงด้านลิขสิทธิ์ {overall_score:.0f}%

ส่วนที่มีความเสี่ยง:
{flagged_summary}

ให้คำแนะนำที่เป็นรูปธรรม 3-5 ข้อ เพื่อลดความเสี่ยงลิขสิทธิ์ ตอบเป็น JSON array ของ string เช่น ["แนะนำ 1", "แนะนำ 2"]"""

        try:
            result = await claude.complete_json(prompt, use_fast_model=True)
            if isinstance(result, list):
                return result
            return result.get("recommendations", [])
        except Exception:
            return [
                "เขียนเนื้อหาใหม่โดยใช้คำพูดของตัวเอง",
                "ระบุแหล่งที่มาให้ชัดเจน",
                "อ้างอิงโดยตรงให้น้อยกว่า 20% ของเนื้อหาทั้งหมด",
            ]

    def _enrich_source_chain(self, source_chain: List[Dict]) -> List[Dict]:
        """Add licensing and risk metadata to source chain."""
        enriched = []
        for source in source_chain:
            enriched.append({
                **source,
                "is_licensed": True,  # assume copyrighted unless specified
                "license_type": "all_rights_reserved",
                "transform_level_label": {
                    0: "คัดลอกโดยตรง",
                    1: "เขียนใหม่",
                    2: "สังเคราะห์",
                }.get(source.get("transform_level", 0), "ไม่ทราบ"),
            })
        return enriched

    def _check_fair_use(self, draft: str, sources: List[str]) -> bool:
        """
        Check if Thai fair use doctrine applies (พ.ร.บ. ลิขสิทธิ์ มาตรา 32).
        News reporting, commentary, criticism are generally allowed.
        """
        fair_use_indicators = [
            "รายงาน", "อ้างอิง", "กล่าวว่า", "ระบุว่า", "เปิดเผยว่า",
            "report", "according to", "citing", "quoted",
        ]
        draft_lower = draft.lower()
        return any(indicator in draft_lower for indicator in fair_use_indicators)
