"""
Feed Heartbeat Service
Real-time news aggregation with Editorial Weight Score.
Separates "must act now" from "can wait" using AI judgment.
"""
import asyncio
import aiohttp
import feedparser
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import logging
import re

from ..core.claude_client import claude
from ..models.news import NewsItem, NewsFeed, NewsStatus, NewsCategory
from ..config import settings

logger = logging.getLogger(__name__)

EDITORIAL_WEIGHT_FORMULA = {
    "public_impact": 0.40,
    "source_reliability": 0.30,
    "urgency": 0.20,
    "exclusivity": 0.10,
}

CATEGORY_KEYWORDS = {
    NewsCategory.BREAKING: ["ด่วน", "เร่งด่วน", "breaking", "urgent", "alert"],
    NewsCategory.POLITICS: ["รัฐบาล", "นายกฯ", "รัฐสภา", "เลือกตั้ง", "พรรค", "political"],
    NewsCategory.ECONOMY: ["เศรษฐกิจ", "ตลาดหุ้น", "gdp", "เงินเฟ้อ", "ธนาคาร", "economy"],
    NewsCategory.TECHNOLOGY: ["ai", "เทคโนโลยี", "tech", "startup", "digital"],
    NewsCategory.SOCIETY: ["สังคม", "ประชาชน", "ชุมชน", "สาธารณสุข"],
    NewsCategory.ENVIRONMENT: ["สิ่งแวดล้อม", "โลกร้อน", "น้ำท่วม", "climate"],
}

HIGH_IMPACT_KEYWORDS = [
    "เสียชีวิต", "บาดเจ็บ", "ระเบิด", "ไฟไหม้", "น้ำท่วม",
    "จับกุม", "ยึดทรัพย์", "ลาออก", "ยุบสภา", "ฉุกเฉิน",
    "กิโลกรัม", "ล้านบาท", "พันล้าน", "หมื่นล้าน",
    "deaths", "explosion", "arrest", "emergency", "billion",
]


class FeedHeartbeatService:

    def __init__(self):
        self._running = False
        self._fetch_task: Optional[asyncio.Task] = None

    async def fetch_feed(self, feed: NewsFeed) -> List[Dict]:
        """Fetch and parse a single RSS/Atom feed."""
        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=15)
            ) as session:
                async with session.get(feed.url) as response:
                    content = await response.text()

            parsed = feedparser.parse(content)
            items = []

            for entry in parsed.entries[:50]:  # cap per feed
                item = {
                    "title": entry.get("title", ""),
                    "summary": entry.get("summary", ""),
                    "url": entry.get("link", ""),
                    "author": entry.get("author", ""),
                    "published_at": self._parse_date(entry.get("published", "")),
                    "source_name": feed.name,
                    "feed_id": feed.id,
                    "source_chain": [{
                        "source_name": feed.name,
                        "source_url": entry.get("link", ""),
                        "fetched_at": datetime.utcnow().isoformat(),
                        "transform_level": 0,
                    }],
                }
                items.append(item)

            return items

        except Exception as e:
            logger.error(f"Error fetching feed {feed.url}: {e}")
            return []

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse various date formats from RSS feeds."""
        import email.utils
        if not date_str:
            return None
        try:
            return datetime(*email.utils.parsedate(date_str)[:6])
        except Exception:
            return None

    async def calculate_editorial_weight(self, item: Dict) -> Dict:
        """
        Calculate Editorial Weight Score using 4-component formula.
        Returns scores for each component + overall weighted score.
        """
        title = item.get("title", "")
        summary = item.get("summary", "")
        text = f"{title} {summary}".lower()

        # 1. Public Impact Score (0-1)
        impact_score = 0.3  # baseline
        impact_keyword_hits = sum(1 for kw in HIGH_IMPACT_KEYWORDS if kw.lower() in text)
        impact_score = min(0.3 + (impact_keyword_hits * 0.1), 1.0)

        # Boost for numbers indicating scale
        if re.search(r"\d+\s*(คน|ราย|ล้าน|พันล้าน|billion|million|thousand)", text):
            impact_score = min(impact_score + 0.15, 1.0)

        # 2. Source Reliability Score (from feed metadata)
        source_score = item.get("source_reliability", 0.7)

        # 3. Urgency Score (0-1) — recency based
        urgency_score = 0.5
        published_at = item.get("published_at")
        if published_at:
            age_hours = (datetime.utcnow() - published_at).total_seconds() / 3600
            if age_hours < 0.5:
                urgency_score = 1.0
            elif age_hours < 1:
                urgency_score = 0.9
            elif age_hours < 3:
                urgency_score = 0.7
            elif age_hours < 6:
                urgency_score = 0.5
            elif age_hours < 24:
                urgency_score = 0.3
            else:
                urgency_score = 0.1

        # Urgency keyword boost
        if any(kw in text for kw in ["ด่วน", "เร่งด่วน", "breaking", "urgent"]):
            urgency_score = min(urgency_score + 0.2, 1.0)

        # 4. Exclusivity Score (harder to calculate without more data)
        exclusivity_score = 0.2  # default low — most feeds share same stories
        if "exclusive" in text or "พิเศษ" in text or "สกู๊ป" in text:
            exclusivity_score = 0.8

        # Weighted overall
        overall = (
            impact_score * EDITORIAL_WEIGHT_FORMULA["public_impact"] +
            source_score * EDITORIAL_WEIGHT_FORMULA["source_reliability"] +
            urgency_score * EDITORIAL_WEIGHT_FORMULA["urgency"] +
            exclusivity_score * EDITORIAL_WEIGHT_FORMULA["exclusivity"]
        )

        return {
            "editorial_weight": round(overall, 3),
            "public_impact_score": round(impact_score, 3),
            "source_reliability_score": round(source_score, 3),
            "urgency_score": round(urgency_score, 3),
            "exclusivity_score": round(exclusivity_score, 3),
            "needs_immediate_action": overall >= 0.75 or urgency_score >= 0.9,
            "can_wait": overall < 0.4 and urgency_score < 0.5,
            "is_breaking": urgency_score >= 0.9 and impact_score >= 0.6,
        }

    async def classify_category(self, title: str, summary: str) -> NewsCategory:
        """Classify news category from title/summary."""
        text = f"{title} {summary}".lower()
        for category, keywords in CATEGORY_KEYWORDS.items():
            if any(kw in text for kw in keywords):
                return category
        return NewsCategory.SOCIETY  # default

    async def generate_editor_brief(self, items: List[Dict]) -> Dict:
        """
        Editor Brief Intelligence — summarize many news items into actionable brief.
        Returns: top stories, recommended actions, trend summary.
        """
        if not items:
            return {"brief": "ไม่มีข่าวใหม่", "top_stories": [], "recommendations": []}

        # Sort by editorial weight
        sorted_items = sorted(items, key=lambda x: x.get("editorial_weight", 0), reverse=True)
        top_items = sorted_items[:20]

        # Build prompt for Claude
        news_list = "\n".join([
            f"- [{i+1}] {item['title']} (score: {item.get('editorial_weight', 0):.2f})"
            for i, item in enumerate(top_items)
        ])

        prompt = f"""คุณเป็นบรรณาธิการข่าวอาวุโสที่มีประสบการณ์ 20 ปี วิเคราะห์ข่าวต่อไปนี้และสรุปให้ทีมข่าว:

ข่าวที่เข้ามา ({len(items)} ชิ้น — แสดงเฉพาะ {len(top_items)} อันดับแรก):
{news_list}

สรุปให้ครบ:
1. top_stories: ข่าวที่ต้องทำทันที (max 5 เรื่อง) พร้อมเหตุผล
2. can_wait_stories: ข่าวที่รอได้ (max 5 เรื่อง)
3. trend_summary: ภาพรวมแนวโน้มข่าววันนี้ (1-2 ประโยค)
4. editor_recommendations: คำแนะนำสำหรับบรรณาธิการ (max 5 ข้อ)
5. exclusive_opportunities: โอกาสข่าวเจาะ/วิเคราะห์ที่ควรทำ (max 3 เรื่อง)

ตอบเป็น JSON"""

        try:
            result = await claude.complete_json(
                prompt=prompt,
                system="คุณเป็นบรรณาธิการข่าวดิจิทัลผู้เชี่ยวชาญ ตอบกระชับ แม่นยำ เป็นประโยชน์",
                use_fast_model=True,
            )
            result["total_items"] = len(items)
            result["processed_at"] = datetime.utcnow().isoformat()
            return result
        except Exception as e:
            logger.error(f"Error generating editor brief: {e}")
            return {
                "brief": "ไม่สามารถสรุปได้",
                "top_stories": [{"index": i+1, "title": item["title"]} for i, item in enumerate(top_items[:5])],
                "recommendations": [],
                "total_items": len(items),
            }

    async def get_live_stats(self, items: List[Dict]) -> Dict:
        """Compute live statistics for Feed Heartbeat dashboard."""
        now = datetime.utcnow()
        one_hour_ago = now - timedelta(hours=1)

        breaking = [x for x in items if x.get("is_breaking")]
        urgent = [x for x in items if x.get("needs_immediate_action")]
        can_wait = [x for x in items if x.get("can_wait")]
        exclusive = [x for x in items if x.get("exclusivity_score", 0) >= 0.7]
        recent = [x for x in items if x.get("published_at") and x["published_at"] >= one_hour_ago]

        return {
            "total": len(items),
            "breaking": len(breaking),
            "urgent": len(urgent),
            "can_wait": len(can_wait),
            "exclusive": len(exclusive),
            "last_hour": len(recent),
            "avg_editorial_weight": round(
                sum(x.get("editorial_weight", 0) for x in items) / max(len(items), 1), 3
            ),
            "updated_at": now.isoformat(),
        }
