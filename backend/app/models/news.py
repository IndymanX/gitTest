from sqlalchemy import Column, String, Text, Float, Integer, Boolean, DateTime, Enum, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase
from datetime import datetime
from enum import Enum as PyEnum
import uuid


class Base(AsyncAttrs, DeclarativeBase):
    pass


class NewsStatus(str, PyEnum):
    INCOMING = "incoming"
    PRIORITIZED = "prioritized"
    BRIEFED = "briefed"
    DRAFTING = "drafting"
    REVIEWING = "reviewing"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class NewsCategory(str, PyEnum):
    BREAKING = "breaking"
    POLITICS = "politics"
    ECONOMY = "economy"
    TECHNOLOGY = "technology"
    SOCIETY = "society"
    ENVIRONMENT = "environment"
    ENTERTAINMENT = "entertainment"
    SPORTS = "sports"
    INTERNATIONAL = "international"
    LOCAL = "local"


class NewsFeed(Base):
    """RSS/API news feed sources"""
    __tablename__ = "news_feeds"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    url = Column(String(1000), nullable=False)
    source_type = Column(String(50), default="rss")  # rss, api, webhook
    is_active = Column(Boolean, default=True)
    reliability_score = Column(Float, default=0.8)  # 0-1 source reliability
    last_fetched_at = Column(DateTime, nullable=True)
    fetch_interval_seconds = Column(Integer, default=60)
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    items = relationship("NewsItem", back_populates="feed")


class NewsItem(Base):
    """Individual news items from feeds"""
    __tablename__ = "news_items"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    feed_id = Column(String, ForeignKey("news_feeds.id"), nullable=True)
    title = Column(String(1000), nullable=False)
    summary = Column(Text, nullable=True)
    content = Column(Text, nullable=True)
    url = Column(String(2000), nullable=True)
    source_name = Column(String(255), nullable=True)
    author = Column(String(255), nullable=True)
    published_at = Column(DateTime, nullable=True)
    fetched_at = Column(DateTime, default=datetime.utcnow)
    category = Column(Enum(NewsCategory), nullable=True)
    status = Column(Enum(NewsStatus), default=NewsStatus.INCOMING)
    language = Column(String(10), default="th")

    # Editorial Weight Score components
    editorial_weight = Column(Float, default=0.0)  # 0-1 overall score
    public_impact_score = Column(Float, default=0.0)  # ผลกระทบต่อสาธารณะ
    source_reliability_score = Column(Float, default=0.0)  # ความน่าเชื่อถือแหล่งข่าว
    urgency_score = Column(Float, default=0.0)  # ความเร่งด่วน
    exclusivity_score = Column(Float, default=0.0)  # Exclusivity

    # Classification
    is_breaking = Column(Boolean, default=False)
    is_exclusive = Column(Boolean, default=False)
    needs_immediate_action = Column(Boolean, default=False)
    can_wait = Column(Boolean, default=False)

    # Source chain for copyright
    source_chain = Column(JSON, default=list)  # [{source, url, fetched_at, transform_level}]
    original_source_url = Column(String(2000), nullable=True)

    # Embeddings for similarity (stored as JSON array)
    embedding = Column(JSON, nullable=True)

    # Related
    tags = Column(JSON, default=list)
    entities = Column(JSON, default=list)  # people, places, organizations mentioned

    organization_id = Column(String, ForeignKey("organizations.id"), nullable=True)

    feed = relationship("NewsFeed", back_populates="items")
    drafts = relationship("DraftContent", back_populates="news_item")
