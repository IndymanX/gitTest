"""
AI Brain Maturity Service
Learns from accepted/rejected/edited drafts to build style profiles.
Enables personalized content that "sounds like" the organization or individual.
"""
from typing import Dict, List, Optional
from collections import Counter
import re
import logging

from ..core.claude_client import claude

logger = logging.getLogger(__name__)


class BrainMaturityService:

    async def learn_from_sample(
        self,
        profile: Dict,
        sample_text: str,
        feedback: str = "accepted",  # accepted/rejected/edited
        edited_version: Optional[str] = None,
    ) -> Dict:
        """
        Update brain profile from a sample + editor feedback.
        Returns updated profile data.
        """
        if not sample_text:
            return profile

        # Extract style features from the sample
        features = self._extract_style_features(sample_text)

        # If edited, compare original vs edited to learn preferences
        edit_insights = {}
        if edited_version and edited_version != sample_text:
            edit_insights = await self._analyze_edits(
                original=sample_text,
                edited=edited_version,
            )

        # Update running statistics
        updated = {**profile}
        updated["total_samples_learned"] = profile.get("total_samples_learned", 0) + 1
        updated["total_feedback_received"] = profile.get("total_feedback_received", 0) + 1

        if feedback == "accepted":
            updated["accepted_count"] = profile.get("accepted_count", 0) + 1
        elif feedback == "rejected":
            updated["rejected_count"] = profile.get("rejected_count", 0) + 1
        elif feedback == "edited":
            updated["edited_count"] = profile.get("edited_count", 0) + 1

        # Update vocabulary distribution
        vocab = profile.get("vocabulary_distribution", {})
        for word, count in features["word_freq"].items():
            vocab[word] = vocab.get(word, 0) + count
        updated["vocabulary_distribution"] = dict(
            sorted(vocab.items(), key=lambda x: x[1], reverse=True)[:500]  # top 500 words
        )

        # Update sentence patterns
        patterns = profile.get("sentence_patterns", [])
        patterns.extend(features["sentence_lengths"][:5])
        updated["sentence_patterns"] = patterns[-100:]  # keep last 100

        # Recalculate maturity score
        updated["maturity_score"] = self._calculate_maturity(updated)

        # Add edit insights
        if edit_insights:
            updated["latest_edit_insights"] = edit_insights

        return updated

    def _extract_style_features(self, text: str) -> Dict:
        """Extract measurable style features from text."""
        sentences = re.split(r'[.!?]\s+', text)
        words = re.findall(r'\w+', text.lower())

        word_freq = Counter(words)
        # Remove common stopwords
        stopwords = set(['ที่', 'และ', 'ของ', 'ใน', 'การ', 'ได้', 'มี', 'จาก', 'ว่า', 'นั้น'])
        word_freq = {w: c for w, c in word_freq.items() if w not in stopwords and len(w) > 1}

        sentence_lengths = [len(re.findall(r'\w+', s)) for s in sentences if s.strip()]

        return {
            "word_count": len(words),
            "unique_words": len(set(words)),
            "avg_sentence_length": sum(sentence_lengths) / max(len(sentence_lengths), 1),
            "sentence_lengths": sentence_lengths,
            "word_freq": word_freq,
            "vocabulary_richness": len(set(words)) / max(len(words), 1),
            "avg_word_length": sum(len(w) for w in words) / max(len(words), 1),
        }

    async def _analyze_edits(self, original: str, edited: str) -> Dict:
        """Use Claude to understand what and why something was edited."""
        prompt = f"""เปรียบเทียบต้นฉบับกับฉบับแก้ไข แล้วบอกว่าบรรณาธิการเปลี่ยนอะไร และทำไม:

ต้นฉบับ:
{original[:1000]}

ฉบับแก้ไข:
{edited[:1000]}

ตอบเป็น JSON:
{{
  "changes_made": ["การเปลี่ยนแปลง 1", "..."],
  "style_preferences_learned": ["ชอบใช้คำ X แทน Y", "..."],
  "structural_preferences": ["ชอบโครงสร้างแบบ ...", "..."],
  "tone_adjustments": "คำอธิบายการปรับโทนเสียง"
}}"""

        try:
            return await claude.complete_json(prompt, use_fast_model=True)
        except Exception:
            return {}

    def _calculate_maturity(self, profile: Dict) -> float:
        """
        Calculate Brain Maturity Score (0-100).
        Based on sample count, feedback quality, and consistency.
        """
        samples = profile.get("total_samples_learned", 0)
        accepted = profile.get("accepted_count", 0)
        total_feedback = profile.get("total_feedback_received", 1)

        # Maturity grows with more samples (logarithmic)
        import math
        sample_score = min(math.log(max(samples, 1) + 1) / math.log(101) * 60, 60)

        # Quality score based on acceptance rate
        acceptance_rate = accepted / max(total_feedback, 1)
        quality_score = acceptance_rate * 40

        return round(sample_score + quality_score, 1)

    async def generate_style_prompt_injection(self, profile: Dict) -> str:
        """
        Generate a prompt snippet that encodes the learned style.
        This is injected into AI drafting prompts.
        """
        maturity = profile.get("maturity_score", 0)
        if maturity < 20:
            return ""  # Not enough data yet

        vocab = profile.get("vocabulary_distribution", {})
        top_words = list(vocab.keys())[:30]
        patterns = profile.get("sentence_patterns", [])
        avg_len = sum(patterns) / max(len(patterns), 1) if patterns else 20

        insights = profile.get("latest_edit_insights", {})
        style_prefs = insights.get("style_preferences_learned", [])

        style_lines = [
            f"- ความยาวประโยคเฉลี่ย: {avg_len:.0f} คำ",
            f"- คำที่ใช้บ่อย: {', '.join(top_words[:10])}",
        ]
        if style_prefs:
            style_lines.extend([f"- {pref}" for pref in style_prefs[:3]])

        return "\n".join(style_lines)

    async def get_maturity_report(self, profile: Dict) -> Dict:
        """Generate a human-readable maturity report."""
        maturity = profile.get("maturity_score", 0)

        if maturity < 20:
            level = "เริ่มต้น"
            description = "ระบบยังเรียนรู้สไตล์ไม่เพียงพอ ต้องการตัวอย่างเพิ่มเติม"
        elif maturity < 50:
            level = "กำลังพัฒนา"
            description = "ระบบเริ่มจำสไตล์ได้ แต่ยังต้องการตัวอย่างเพิ่มเพื่อความแม่นยำ"
        elif maturity < 75:
            level = "เชี่ยวชาญ"
            description = "ระบบเข้าใจสไตล์ดีแล้ว เนื้อหาที่สร้างจะมีเอกลักษณ์ชัดเจน"
        else:
            level = "ผู้เชี่ยวชาญ"
            description = "ระบบเรียนรู้สไตล์อย่างลึกซึ้ง เนื้อหาจะ 'เป็นตัวตน' ของคุณอย่างแท้จริง"

        return {
            "maturity_score": maturity,
            "level": level,
            "description": description,
            "samples_learned": profile.get("total_samples_learned", 0),
            "acceptance_rate": round(
                profile.get("accepted_count", 0) /
                max(profile.get("total_feedback_received", 1), 1) * 100, 1
            ),
            "top_vocabulary": list(profile.get("vocabulary_distribution", {}).keys())[:20],
            "next_milestone": self._next_milestone(maturity),
        }

    def _next_milestone(self, current: float) -> Dict:
        milestones = [
            (20, "เริ่มใช้สไตล์ส่วนตัว", "ต้องการตัวอย่างที่ได้รับการอนุมัติ 10+ ชิ้น"),
            (50, "สไตล์ชัดเจน", "ต้องการตัวอย่างที่หลากหลายหัวข้อ"),
            (75, "เชี่ยวชาญ", "ให้ feedback อย่างต่อเนื่องเพื่อ fine-tune"),
            (100, "สมบูรณ์แบบ", "รักษาคุณภาพ feedback loop ต่อเนื่อง"),
        ]
        for score, name, action in milestones:
            if current < score:
                return {"target_score": score, "milestone_name": name, "action_needed": action}
        return {"target_score": 100, "milestone_name": "สมบูรณ์แบบ", "action_needed": "รักษาคุณภาพ"}
