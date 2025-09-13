from fastapi.testclient import TestClient
from fastapi import FastAPI
from unittest.mock import Mock
import app.services.job_manager as jm
from app.routes.translation import router as translation_router


_app = FastAPI()
_app.include_router(translation_router, prefix="/api/v1/translation")
client = TestClient(_app)


def test_create_and_get_job(monkeypatch):
    # Ensure TESTING mode for in-memory JobManager
    monkeypatch.setenv("TESTING", "true")
    # Patch DB session to avoid real DB
    mock_db = Mock()
    monkeypatch.setattr(jm, "get_db", lambda: iter([mock_db]))

    payload = {
        "youtube_url": "https://www.youtube.com/watch?v=jNQXAC9IVRw",
        "source_language": "en",
        "target_language": "es",
    }
    r = client.post("/api/v1/translation/jobs", json=payload)
    assert r.status_code == 201, r.text
    data = r.json()
    assert "job_id" in data and data["job_id"]
    assert data["stage"] in {"downloading", "chunking", "transcribing", "translating", "synthesizing", "reconstructing", "complete", "failed"}

    job_id = data["job_id"]
    r2 = client.get(f"/api/v1/translation/jobs/{job_id}")
    assert r2.status_code == 200, r2.text
    data2 = r2.json()
    assert data2["job_id"] == job_id
    assert "progress" in data2
