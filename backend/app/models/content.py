from sqlalchemy import Column, String, Text, Float, Integer, Boolean, DateTime, Enum, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum as PyEnum
import uuid

from .news import Base


class Platform(str, PyEnum):
    WEBSITE = "website"
    FACEBOOK = "facebook"
    TWITTER = "twitter"
    INSTAGRAM = "instagram"
    TIKTOK = "tiktok"
    YOUTUBE = "youtube"
    LINE = "line"
    PODCAST = "podcast"


class ContentFormat(str, PyEnum):
    ARTICLE = "article"
    SOCIAL_POST = "social_post"
    VIDEO_SCRIPT = "video_script"
    PODCAST_SCRIPT = "podcast_script"
    INFOGRAPHIC_TEXT = "infographic_text"
    NEWSLETTER = "newsletter"


class DraftStatus(str, PyEnum):
    DRAFT = "draft"
    FACT_CHECKING = "fact_checking"
    COPYRIGHT_CHECKING = "copyright_checking"
    EDITOR_REVIEW = "editor_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    PUBLISHED = "published"


class ImageStyle(str, PyEnum):
    PHOTOREALISTIC = "photorealistic"
    CINEMATIC = "cinematic"
    ILLUSTRATION = "illustration"
    MINIMALIST = "minimalist"
    ABSTRACT = "abstract"
    NEWS_STYLE = "news_style"


class ImageAspectRatio(str, PyEnum):
    RATIO_16_9 = "16:9"
    RATIO_1_1 = "1:1"
    RATIO_9_16 = "9:16"
    RATIO_4_5 = "4:5"
    RATIO_3_2 = "3:2"
    RATIO_4_3 = "4:3"


class CameraAngle(str, PyEnum):
    EYE_LEVEL = "eye_level"
    AERIAL = "aerial"
    LOW_ANGLE = "low_angle"
    HIGH_ANGLE = "high_angle"
    CLOSE_UP = "close_up"
    WIDE_ANGLE = "wide_angle"
    OVER_SHOULDER = "over_shoulder"
    DUTCH_ANGLE = "dutch_angle"
    ISOMETRIC = "isometric"


class VoiceProfile(str, PyEnum):
    LIAM = "liam"
    RACHEL = "rachel"
    ADAM = "adam"
    BELLA = "bella"
    ANTONI = "antoni"
    JOSH = "josh"


class ReadingTone(str, PyEnum):
    NEWS = "news"
    STORYTELLING = "storytelling"
    CASUAL = "casual"
    EDUCATIONAL = "educational"
    DRAMA = "drama"
    PODCAST = "podcast"


class DraftContent(Base):
    """AI-generated draft articles"""
    __tablename__ = "draft_contents"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    news_item_id = Column(String, ForeignKey("news_items.id"), nullable=True)
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    author_id = Column(String, ForeignKey("users.id"), nullable=True)

    title = Column(String(1000), nullable=False)
    lead = Column(Text, nullable=True)  # ย่อหน้านำ
    body = Column(Text, nullable=False)
    tags = Column(JSON, default=list)
    seo_title = Column(String(200), nullable=True)
    seo_description = Column(String(500), nullable=True)
    aio_keywords = Column(JSON, default=list)  # AI-Optimized keywords

    format = Column(Enum(ContentFormat), default=ContentFormat.ARTICLE)
    platform_target = Column(JSON, default=list)  # list of Platform values
    angle = Column(String(500), nullable=True)  # content angle used
    angle_type = Column(String(100), nullable=True)  # consumer/policy/business/data/global

    status = Column(Enum(DraftStatus), default=DraftStatus.DRAFT)

    # AI generation metadata
    ai_model_used = Column(String(100), nullable=True)
    brain_profile_id = Column(String, ForeignKey("brain_profiles.id"), nullable=True)
    generation_prompt = Column(Text, nullable=True)
    word_count = Column(Integer, default=0)
    reading_time_minutes = Column(Float, default=0.0)

    # Scores
    quality_score = Column(Float, nullable=True)  # 0-1
    fact_check_score = Column(Float, nullable=True)
    copyright_risk_score = Column(Float, default=0.0)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    news_item = relationship("NewsItem", back_populates="drafts")
    versions = relationship("ContentVersion", back_populates="draft")
    copyright_analysis = relationship("CopyrightAnalysisResult", back_populates="draft", uselist=False)
    published_contents = relationship("PublishedContent", back_populates="draft")


class ContentVersion(Base):
    """Version history for drafts"""
    __tablename__ = "content_versions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    draft_id = Column(String, ForeignKey("draft_contents.id"), nullable=False)
    version_number = Column(Integer, nullable=False)
    title = Column(String(1000), nullable=False)
    body = Column(Text, nullable=False)
    changed_by = Column(String, ForeignKey("users.id"), nullable=True)
    change_reason = Column(String(500), nullable=True)  # editor note
    created_at = Column(DateTime, default=datetime.utcnow)

    draft = relationship("DraftContent", back_populates="versions")


class ContentStudioSettings(Base):
    """Settings for content studio (image/voice generation)"""
    __tablename__ = "content_studio_settings"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    draft_id = Column(String, ForeignKey("draft_contents.id"), nullable=False)

    # Image settings
    image_style = Column(Enum(ImageStyle), default=ImageStyle.NEWS_STYLE)
    image_aspect_ratio = Column(Enum(ImageAspectRatio), default=ImageAspectRatio.RATIO_16_9)
    camera_angle = Column(Enum(CameraAngle), default=CameraAngle.EYE_LEVEL)
    image_prompt = Column(Text, nullable=True)
    generated_image_url = Column(String(2000), nullable=True)

    # Voice settings
    voice_profile = Column(Enum(VoiceProfile), default=VoiceProfile.LIAM)
    reading_tone = Column(Enum(ReadingTone), default=ReadingTone.NEWS)
    speed = Column(Float, default=1.0)  # 0.8=slow, 1.0=normal, 1.1=fast, 1.2=very fast
    voiceover_url = Column(String(2000), nullable=True)
    voiceover_duration_seconds = Column(Float, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)


class PublishedContent(Base):
    """Published content records per platform"""
    __tablename__ = "published_contents"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    draft_id = Column(String, ForeignKey("draft_contents.id"), nullable=False)
    platform = Column(Enum(Platform), nullable=False)
    platform_post_id = Column(String(500), nullable=True)
    platform_url = Column(String(2000), nullable=True)
    adapted_title = Column(String(1000), nullable=True)
    adapted_body = Column(Text, nullable=True)
    published_at = Column(DateTime, default=datetime.utcnow)
    published_by = Column(String, ForeignKey("users.id"), nullable=True)
    performance_metrics = Column(JSON, default=dict)  # views, shares, engagement

    draft = relationship("DraftContent", back_populates="published_contents")
