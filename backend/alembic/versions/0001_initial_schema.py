"""initial schema — all Phase 1+2 tables

Revision ID: 0001
Revises:
Create Date: 2026-05-16

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── organizations ──────────────────────────────────────────────────────────
    op.create_table(
        "organizations",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("name_th", sa.String(255), nullable=True),
        sa.Column("slug", sa.String(100), nullable=False),
        sa.Column("logo_url", sa.String(2000), nullable=True),
        sa.Column("website", sa.String(500), nullable=True),
        sa.Column("plan", sa.String(50), nullable=True),
        sa.Column("news_coins", sa.Integer(), nullable=True),
        sa.Column("monthly_coin_allowance", sa.Integer(), nullable=True),
        sa.Column("primary_language", sa.String(10), nullable=True),
        sa.Column("default_publish_platforms", sa.JSON(), nullable=True),
        sa.Column("copyright_strictness", sa.String(20), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )

    # ── users ──────────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("organization_id", sa.String(), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("role", sa.String(50), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column("personal_brain_profile_id", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("last_login_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )

    # ── brain_profiles ────────────────────────────────────────────────────────
    op.create_table(
        "brain_profiles",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("organization_id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("maturity_score", sa.Float(), nullable=True),
        sa.Column("total_samples_learned", sa.Integer(), nullable=True),
        sa.Column("total_feedback_received", sa.Integer(), nullable=True),
        sa.Column("style_vector", sa.JSON(), nullable=True),
        sa.Column("vocabulary_distribution", sa.JSON(), nullable=True),
        sa.Column("sentence_patterns", sa.JSON(), nullable=True),
        sa.Column("topic_expertise", sa.JSON(), nullable=True),
        sa.Column("accepted_count", sa.Integer(), nullable=True),
        sa.Column("rejected_count", sa.Integer(), nullable=True),
        sa.Column("edited_count", sa.Integer(), nullable=True),
        sa.Column("last_trained_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # ── style_constitutions ───────────────────────────────────────────────────
    op.create_table(
        "style_constitutions",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("organization_id", sa.String(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column("formality_level", sa.Float(), nullable=True),
        sa.Column("active_voice_ratio", sa.Float(), nullable=True),
        sa.Column("average_sentence_length", sa.Integer(), nullable=True),
        sa.Column("paragraph_length", sa.String(20), nullable=True),
        sa.Column("preferred_structure", sa.String(50), nullable=True),
        sa.Column("forbidden_words", sa.JSON(), nullable=True),
        sa.Column("preferred_terms", sa.JSON(), nullable=True),
        sa.Column("brand_voice_markers", sa.JSON(), nullable=True),
        sa.Column("requires_source_attribution", sa.Boolean(), nullable=True),
        sa.Column("min_sources_required", sa.Integer(), nullable=True),
        sa.Column("thai_press_ethics_compliant", sa.Boolean(), nullable=True),
        sa.Column("platform_tone_overrides", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # ── news_feeds ────────────────────────────────────────────────────────────
    op.create_table(
        "news_feeds",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("url", sa.String(1000), nullable=False),
        sa.Column("source_type", sa.String(50), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column("reliability_score", sa.Float(), nullable=True),
        sa.Column("last_fetched_at", sa.DateTime(), nullable=True),
        sa.Column("fetch_interval_seconds", sa.Integer(), nullable=True),
        sa.Column("organization_id", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # ── news_items ────────────────────────────────────────────────────────────
    op.create_table(
        "news_items",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("feed_id", sa.String(), nullable=True),
        sa.Column("title", sa.String(1000), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("url", sa.String(2000), nullable=True),
        sa.Column("source_name", sa.String(255), nullable=True),
        sa.Column("author", sa.String(255), nullable=True),
        sa.Column("published_at", sa.DateTime(), nullable=True),
        sa.Column("fetched_at", sa.DateTime(), nullable=True),
        sa.Column("category", sa.String(50), nullable=True),
        sa.Column("status", sa.String(20), nullable=True),
        sa.Column("language", sa.String(10), nullable=True),
        sa.Column("editorial_weight", sa.Float(), nullable=True),
        sa.Column("public_impact_score", sa.Float(), nullable=True),
        sa.Column("source_reliability_score", sa.Float(), nullable=True),
        sa.Column("urgency_score", sa.Float(), nullable=True),
        sa.Column("exclusivity_score", sa.Float(), nullable=True),
        sa.Column("is_breaking", sa.Boolean(), nullable=True),
        sa.Column("is_exclusive", sa.Boolean(), nullable=True),
        sa.Column("needs_immediate_action", sa.Boolean(), nullable=True),
        sa.Column("can_wait", sa.Boolean(), nullable=True),
        sa.Column("source_chain", sa.JSON(), nullable=True),
        sa.Column("original_source_url", sa.String(2000), nullable=True),
        sa.Column("embedding", sa.JSON(), nullable=True),
        sa.Column("tags", sa.JSON(), nullable=True),
        sa.Column("entities", sa.JSON(), nullable=True),
        sa.Column("organization_id", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["feed_id"], ["news_feeds.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # ── draft_contents ────────────────────────────────────────────────────────
    op.create_table(
        "draft_contents",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("news_item_id", sa.String(), nullable=True),
        sa.Column("organization_id", sa.String(), nullable=False),
        sa.Column("author_id", sa.String(), nullable=True),
        sa.Column("title", sa.String(1000), nullable=False),
        sa.Column("lead", sa.Text(), nullable=True),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("tags", sa.JSON(), nullable=True),
        sa.Column("seo_title", sa.String(200), nullable=True),
        sa.Column("seo_description", sa.String(500), nullable=True),
        sa.Column("aio_keywords", sa.JSON(), nullable=True),
        sa.Column("format", sa.String(50), nullable=True),
        sa.Column("platform_target", sa.JSON(), nullable=True),
        sa.Column("angle", sa.String(500), nullable=True),
        sa.Column("angle_type", sa.String(100), nullable=True),
        sa.Column("status", sa.String(30), nullable=True),
        sa.Column("ai_model_used", sa.String(100), nullable=True),
        sa.Column("brain_profile_id", sa.String(), nullable=True),
        sa.Column("generation_prompt", sa.Text(), nullable=True),
        sa.Column("word_count", sa.Integer(), nullable=True),
        sa.Column("reading_time_minutes", sa.Float(), nullable=True),
        sa.Column("quality_score", sa.Float(), nullable=True),
        sa.Column("fact_check_score", sa.Float(), nullable=True),
        sa.Column("copyright_risk_score", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["author_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["brain_profile_id"], ["brain_profiles.id"]),
        sa.ForeignKeyConstraint(["news_item_id"], ["news_items.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # ── content_versions ──────────────────────────────────────────────────────
    op.create_table(
        "content_versions",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("draft_id", sa.String(), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(1000), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("changed_by", sa.String(), nullable=True),
        sa.Column("change_reason", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["changed_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["draft_id"], ["draft_contents.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # ── content_studio_settings ───────────────────────────────────────────────
    op.create_table(
        "content_studio_settings",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("draft_id", sa.String(), nullable=False),
        sa.Column("image_style", sa.String(50), nullable=True),
        sa.Column("image_aspect_ratio", sa.String(10), nullable=True),
        sa.Column("camera_angle", sa.String(30), nullable=True),
        sa.Column("image_prompt", sa.Text(), nullable=True),
        sa.Column("generated_image_url", sa.String(2000), nullable=True),
        sa.Column("voice_profile", sa.String(30), nullable=True),
        sa.Column("reading_tone", sa.String(30), nullable=True),
        sa.Column("speed", sa.Float(), nullable=True),
        sa.Column("voiceover_url", sa.String(2000), nullable=True),
        sa.Column("voiceover_duration_seconds", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["draft_id"], ["draft_contents.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # ── published_contents ────────────────────────────────────────────────────
    op.create_table(
        "published_contents",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("draft_id", sa.String(), nullable=False),
        sa.Column("platform", sa.String(30), nullable=False),
        sa.Column("platform_post_id", sa.String(500), nullable=True),
        sa.Column("platform_url", sa.String(2000), nullable=True),
        sa.Column("adapted_title", sa.String(1000), nullable=True),
        sa.Column("adapted_body", sa.Text(), nullable=True),
        sa.Column("published_at", sa.DateTime(), nullable=True),
        sa.Column("published_by", sa.String(), nullable=True),
        sa.Column("performance_metrics", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(["draft_id"], ["draft_contents.id"]),
        sa.ForeignKeyConstraint(["published_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # ── copyright_analysis_results ─────────────────────────────────────────────
    op.create_table(
        "copyright_analysis_results",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("draft_id", sa.String(), nullable=False),
        sa.Column("overall_risk_score", sa.Float(), nullable=True),
        sa.Column("risk_level", sa.String(20), nullable=True),
        sa.Column("content_similarity_score", sa.Float(), nullable=True),
        sa.Column("style_similarity_score", sa.Float(), nullable=True),
        sa.Column("structure_similarity_score", sa.Float(), nullable=True),
        sa.Column("source_chain", sa.JSON(), nullable=True),
        sa.Column("flagged_segments", sa.JSON(), nullable=True),
        sa.Column("recommendations", sa.JSON(), nullable=True),
        sa.Column("thai_copyright_act_compliant", sa.Boolean(), nullable=True),
        sa.Column("fair_use_applicable", sa.Boolean(), nullable=True),
        sa.Column("fair_use_reason", sa.String(500), nullable=True),
        sa.Column("analyzed_at", sa.DateTime(), nullable=True),
        sa.Column("analyzer_version", sa.String(20), nullable=True),
        sa.ForeignKeyConstraint(["draft_id"], ["draft_contents.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("copyright_analysis_results")
    op.drop_table("published_contents")
    op.drop_table("content_studio_settings")
    op.drop_table("content_versions")
    op.drop_table("draft_contents")
    op.drop_table("news_items")
    op.drop_table("news_feeds")
    op.drop_table("style_constitutions")
    op.drop_table("brain_profiles")
    op.drop_table("users")
    op.drop_table("organizations")
