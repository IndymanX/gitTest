"""Tests for /brain/* endpoints."""
import pytest


@pytest.mark.anyio
async def test_create_profile(client):
    """POST /brain/profiles creates a new profile."""
    resp = await client.post("/api/v1/brain/profiles", json={
        "profile_id": "test-profile",
        "name": "Test Profile",
        "organization_id": "org-1",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["profile"]["id"] == "test-profile"
    assert data["profile"]["maturity_score"] == 0.0


@pytest.mark.anyio
async def test_get_profile_not_found(client):
    """GET /brain/profiles/{id} returns 404 for unknown profile."""
    resp = await client.get("/api/v1/brain/profiles/nonexistent-xyz")
    assert resp.status_code == 404


@pytest.mark.anyio
async def test_learn_creates_profile_if_missing(client):
    """POST /brain/learn auto-creates profile and returns maturity report."""
    resp = await client.post("/api/v1/brain/learn", json={
        "profile_id": "auto-create-test",
        "sample_text": "ข่าวทดสอบระบบ นายกรัฐมนตรีแถลงนโยบายใหม่ เน้นการพัฒนาเศรษฐกิจดิจิทัล",
        "feedback": "accepted",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "profile" in data
    assert data["profile"]["total_samples_learned"] == 1


@pytest.mark.anyio
async def test_learn_invalid_feedback(client):
    """POST /brain/learn with invalid feedback returns 400."""
    resp = await client.post("/api/v1/brain/learn", json={
        "profile_id": "test",
        "sample_text": "some text",
        "feedback": "invalid_value",
    })
    assert resp.status_code == 400


@pytest.mark.anyio
async def test_bulk_learn(client):
    """POST /brain/bulk-learn processes multiple samples."""
    resp = await client.post("/api/v1/brain/bulk-learn", json={
        "profile_id": "bulk-test",
        "samples": [
            "บทความข่าวที่ 1 เกี่ยวกับเศรษฐกิจไทย",
            "บทความข่าวที่ 2 เกี่ยวกับการเมือง",
            "บทความข่าวที่ 3 เกี่ยวกับกีฬา",
        ],
        "feedback": "accepted",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["processed"] == 3
    assert data["profile"]["total_samples_learned"] == 3


@pytest.mark.anyio
async def test_bulk_learn_empty_list(client):
    """POST /brain/bulk-learn with empty samples returns 400."""
    resp = await client.post("/api/v1/brain/bulk-learn", json={
        "profile_id": "bulk-test",
        "samples": [],
    })
    assert resp.status_code == 400


@pytest.mark.anyio
async def test_list_profiles(client):
    """GET /brain/profiles returns list."""
    resp = await client.get("/api/v1/brain/profiles")
    assert resp.status_code == 200
    assert "profiles" in resp.json()
