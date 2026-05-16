"""Tests for /draft/* endpoints."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock


NEWS_ITEM = {
    "title": "ทดสอบระบบ AI Drafting",
    "summary": "ระบบกำลังถูกทดสอบ",
    "content": "เนื้อหาข่าวทดสอบสำหรับการสร้างแบบร่าง",
    "url": "http://example.com/news/1",
    "source_name": "Test",
}

MOCK_DRAFT = {
    "title": "ทดสอบระบบ",
    "lead": "ระบบถูกทดสอบ",
    "body": "เนื้อหาทดสอบ",
    "tags": ["test"],
    "seo_title": "Test SEO",
    "seo_description": "Test desc",
    "word_count": 5,
    "reading_time_minutes": 1.0,
}


@pytest.mark.anyio
async def test_generate_draft(client, mock_claude):
    """POST /draft/generate returns draft + copyright (no inline fact-check)."""
    with patch("app.services.ai_drafting.AIDraftingService.generate_draft", AsyncMock(return_value=MOCK_DRAFT)), \
         patch("app.services.copyright_analysis.CopyrightAnalysisService.analyze", AsyncMock(return_value={
             "overall_risk_score": 0.1, "risk_level": "low",
             "content_similarity_score": 0.1, "style_similarity_score": 0.05,
             "structure_similarity_score": 0.05, "recommendations": [],
         })), \
         patch("app.workers.ai_tasks.detect_claims_task.delay", return_value=MagicMock(id="task-123")):

        resp = await client.post("/api/v1/draft/generate", json={
            "news_item": NEWS_ITEM,
            "format": "article",
            "platform": "website",
            "auto_check_copyright": True,
            "auto_check_facts": True,
        })

    assert resp.status_code == 200
    data = resp.json()
    assert "draft" in data
    assert "copyright" in data
    assert data["fact_check"] is None
    assert "fact_check_task_id" in data


@pytest.mark.anyio
async def test_generate_draft_invalid_format(client):
    """POST /draft/generate with unknown format returns 400."""
    resp = await client.post("/api/v1/draft/generate", json={
        "news_item": NEWS_ITEM,
        "format": "INVALID_FORMAT",
        "platform": "website",
    })
    assert resp.status_code == 400


@pytest.mark.anyio
async def test_generate_angles(client):
    """POST /draft/angles returns angle list."""
    mock_result = {
        "angles": [{"angle_type": "consumer", "title": "มุมมองผู้บริโภค", "hook": "hook"}],
        "total": 1,
        "content_plan_summary": "summary",
    }
    with patch("app.services.angle_generator.AngleGeneratorService.generate_angles", AsyncMock(return_value=mock_result)):
        resp = await client.post("/api/v1/draft/angles", json={"news_item": NEWS_ITEM})
    assert resp.status_code == 200
    data = resp.json()
    assert "angles" in data


@pytest.mark.anyio
async def test_factcheck_status_pending(client):
    """GET /draft/factcheck/status/{id} returns pending for unknown task."""
    with patch("app.api.routes.draft.AsyncResult") as mock_result_cls, \
         patch("app.api.routes.draft.celery_app", MagicMock()):
        mock_result = MagicMock()
        mock_result.state = "PENDING"
        mock_result_cls.return_value = mock_result
        resp = await client.get("/api/v1/draft/factcheck/status/fake-task-id")
    assert resp.status_code == 200
    assert resp.json()["status"] == "pending"


@pytest.mark.anyio
async def test_adapt_for_platform(client):
    """POST /draft/adapt/{platform} returns adapted content."""
    mock_adapted = {"adapted_content": "Facebook version of the article", "platform": "facebook"}
    with patch("app.services.ai_drafting.AIDraftingService.adapt_for_platform", AsyncMock(return_value=mock_adapted)):
        resp = await client.post("/api/v1/draft/adapt/facebook", json={
            "title": "Test Title",
            "body": "Test body content for adaptation",
        })
    assert resp.status_code == 200


@pytest.mark.anyio
async def test_adapt_unknown_platform(client):
    """POST /draft/adapt/{platform} with unknown platform returns 400."""
    resp = await client.post("/api/v1/draft/adapt/snapchat", json={
        "title": "Test",
        "body": "Body",
    })
    assert resp.status_code == 400
