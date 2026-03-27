from sqlalchemy import Column, String, Text, Float, Integer, Boolean, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from .news import Base


class Organization(Base):
    """Media organization using AInewsroom"""
    __tablename__ = "organizations"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    name_th = Column(String(255), nullable=True)
    slug = Column(String(100), unique=True, nullable=False)
    logo_url = Column(String(2000), nullable=True)
    website = Column(String(500), nullable=True)

    # Subscription
    plan = Column(String(50), default="starter")  # starter, professional, enterprise
    news_coins = Column(Integer, default=100)
    monthly_coin_allowance = Column(Integer, default=100)

    # Settings
    primary_language = Column(String(10), default="th")
    default_publish_platforms = Column(JSON, default=list)
    copyright_strictness = Column(String(20), default="standard")  # strict/standard/lenient

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    users = relationship("User", back_populates="organization")
    brain_profiles = relationship("BrainProfile", back_populates="organization")
    style_constitutions = relationship("StyleConstitution", back_populates="organization")


class User(Base):
    """Newsroom users"""
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(String(50), default="reporter")  # admin/editor/reporter/viewer
    is_active = Column(Boolean, default=True)

    # Personal writing style
    personal_brain_profile_id = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    last_login_at = Column(DateTime, nullable=True)

    organization = relationship("Organization", back_populates="users")


class StyleConstitution(Base):
    """Organization's style guide — the 'DNA' of their writing"""
    __tablename__ = "style_constitutions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    name = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)

    # Tone DNA
    formality_level = Column(Float, default=0.7)  # 0=very informal, 1=very formal
    active_voice_ratio = Column(Float, default=0.8)  # target active voice %
    average_sentence_length = Column(Integer, default=20)  # words per sentence
    paragraph_length = Column(String(20), default="medium")  # short/medium/long

    # Story structure preferences
    preferred_structure = Column(String(50), default="inverted_pyramid")
    # inverted_pyramid / narrative / explainer / listicle

    # Vocabulary
    forbidden_words = Column(JSON, default=list)
    preferred_terms = Column(JSON, default=dict)  # {"term": "preferred_alternative"}
    brand_voice_markers = Column(JSON, default=list)  # phrases that sound like "us"

    # Ethical guidelines
    requires_source_attribution = Column(Boolean, default=True)
    min_sources_required = Column(Integer, default=2)
    thai_press_ethics_compliant = Column(Boolean, default=True)

    # Platform-specific adaptations
    platform_tone_overrides = Column(JSON, default=dict)
    # {"twitter": {"max_length": 280, "tone": "casual"}}

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    organization = relationship("Organization", back_populates="style_constitutions")


class BrainProfile(Base):
    """AI Brain Maturity — learned writing style per user or organization"""
    __tablename__ = "brain_profiles"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=True)  # None = org-level
    name = Column(String(255), nullable=False)

    # Maturity level 0-100
    maturity_score = Column(Float, default=0.0)
    total_samples_learned = Column(Integer, default=0)
    total_feedback_received = Column(Integer, default=0)

    # Learned patterns (JSON embeddings/stats)
    style_vector = Column(JSON, nullable=True)  # style embedding
    vocabulary_distribution = Column(JSON, default=dict)  # word frequency profile
    sentence_patterns = Column(JSON, default=list)  # common sentence structures
    topic_expertise = Column(JSON, default=dict)  # {"topic": confidence_score}

    # Feedback history
    accepted_count = Column(Integer, default=0)
    rejected_count = Column(Integer, default=0)
    edited_count = Column(Integer, default=0)

    last_trained_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    organization = relationship("Organization", back_populates="brain_profiles")
