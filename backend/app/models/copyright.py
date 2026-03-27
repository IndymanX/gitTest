from sqlalchemy import Column, String, Text, Float, Integer, Boolean, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from .news import Base


class CopyrightAnalysisResult(Base):
    """Copyright analysis results for drafts"""
    __tablename__ = "copyright_analysis_results"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    draft_id = Column(String, ForeignKey("draft_contents.id"), nullable=False)

    # Overall score
    overall_risk_score = Column(Float, default=0.0)  # 0-100%
    risk_level = Column(String(20), default="low")  # low/medium/high

    # 3-axis analysis
    content_similarity_score = Column(Float, default=0.0)  # เนื้อหา
    style_similarity_score = Column(Float, default=0.0)   # สำนวน
    structure_similarity_score = Column(Float, default=0.0)  # โครงสร้าง

    # Source chain transparency
    source_chain = Column(JSON, default=list)
    # [{
    #   "source_name": str,
    #   "source_url": str,
    #   "fetched_at": str,
    #   "transform_level": int,  # 0=direct copy, 1=rewrite, 2=synthesized
    #   "similarity_score": float,
    #   "is_licensed": bool,
    #   "license_type": str  # "all_rights_reserved"/"cc"/"public_domain"
    # }]

    # Flagged segments
    flagged_segments = Column(JSON, default=list)
    # [{
    #   "text": str,
    #   "start_char": int,
    #   "end_char": int,
    #   "similarity_score": float,
    #   "matched_source": str,
    #   "risk_type": "content"|"style"|"structure"
    # }]

    # Recommendations
    recommendations = Column(JSON, default=list)
    # ["Rewrite paragraph 3", "Add attribution for quote in paragraph 5"]

    # Thai law compliance
    thai_copyright_act_compliant = Column(Boolean, nullable=True)
    fair_use_applicable = Column(Boolean, default=False)
    fair_use_reason = Column(String(500), nullable=True)

    analyzed_at = Column(DateTime, default=datetime.utcnow)
    analyzer_version = Column(String(20), default="1.0")

    draft = relationship("DraftContent", back_populates="copyright_analysis")
