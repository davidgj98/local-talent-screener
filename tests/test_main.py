from __future__ import annotations

import shutil
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from main import app
from schemas import CriticOutput, InterviewerOutput, ProfilerOutput
from storage import DATA_DIR

client = TestClient(app)

SAMPLE_PDF = b"%PDF-1.4 fake content for testing ................"


@pytest.fixture(autouse=True)
def clear_state():
    from main import _session_cache

    _session_cache.clear()
    offers_dir = DATA_DIR / "offers"
    if offers_dir.exists():
        shutil.rmtree(offers_dir)
    offers_dir.mkdir(parents=True, exist_ok=True)


class TestHealth:
    def test_root(self):
        r = client.get("/")
        assert r.status_code in (200, 404)

    def test_api_root(self):
        r = client.get("/api/v1")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "ok"
        assert data["service"] == "local-hr-agent-squad"

    def test_health(self):
        r = client.get("/api/v1/health")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "ok"
        assert "models" in data


class TestAnalyze:
    @patch("main.extract_text_from_pdf")
    @patch("main.profiler_agent")
    @patch("main.critic_agent")
    @patch("main.interviewer_agent")
    def test_analyze_success(
        self,
        mock_interviewer,
        mock_critic,
        mock_profiler,
        mock_extract,
        sample_profiler_data,
        sample_critic_data,
        sample_interviewer_data,
    ):
        mock_extract.return_value = "Extracted CV text"
        mock_profiler.run = AsyncMock(
            return_value=ProfilerOutput(**sample_profiler_data)
        )
        mock_critic.run = AsyncMock(return_value=CriticOutput(**sample_critic_data))
        mock_interviewer.run = AsyncMock(
            return_value=InterviewerOutput(**sample_interviewer_data)
        )

        r = client.post(
            "/api/v1/analyze",
            files={"cv_file": ("cv.pdf", SAMPLE_PDF, "application/pdf")},
            data={
                "job_offer": "We need a Python developer with more than twenty chars"
            },
        )
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["profiler"]["years_experience"] == 5
        assert data["tech_critic"]["match_score"] == 75
        assert len(data["interviewer"]["questions"]) == 2

    def test_analyze_no_file(self):
        r = client.post(
            "/api/v1/analyze",
            data={"job_offer": "A" * 30},
        )
        assert r.status_code == 422

    def test_analyze_no_offer(self):
        r = client.post(
            "/api/v1/analyze",
            files={"cv_file": ("cv.pdf", SAMPLE_PDF, "application/pdf")},
        )
        assert r.status_code == 422

    def test_analyze_short_offer(self):
        r = client.post(
            "/api/v1/analyze",
            files={"cv_file": ("cv.pdf", SAMPLE_PDF, "application/pdf")},
            data={"job_offer": "Short"},
        )
        assert r.status_code == 400
        assert "short" in r.text.lower()

    def test_analyze_non_pdf_extension(self):
        r = client.post(
            "/api/v1/analyze",
            files={"cv_file": ("cv.txt", b"not a pdf", "text/plain")},
            data={"job_offer": "A" * 30},
        )
        assert r.status_code == 400
        assert "PDF" in r.text


class TestBatchSessions:
    def test_create_session(self):
        r = client.post(
            "/api/v1/batch/sessions",
            json={"title": "Test Offer", "job_offer": "A" * 30},
        )
        assert r.status_code == 200
        data = r.json()
        assert data["title"] == "Test Offer"
        assert data["status"] == "open"
        assert len(data["id"]) == 12
        self._last_sid = data["id"]

    def test_list_sessions(self):
        client.post(
            "/api/v1/batch/sessions", json={"title": "A", "job_offer": "B" * 30}
        )
        client.post(
            "/api/v1/batch/sessions", json={"title": "B", "job_offer": "C" * 30}
        )
        r = client.get("/api/v1/batch/sessions")
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 2

    def test_get_session(self):
        self.test_create_session()
        sid = self._last_sid
        r = client.get(f"/api/v1/batch/sessions/{sid}")
        assert r.status_code == 200
        assert r.json()["id"] == sid

    def test_get_session_not_found(self):
        r = client.get("/api/v1/batch/sessions/nonexistent")
        assert r.status_code == 404

    def test_close_session(self):
        self.test_create_session()
        sid = self._last_sid
        r = client.post(f"/api/v1/batch/sessions/{sid}/close")
        assert r.status_code == 200
        assert r.json()["status"] == "closed"

    def test_close_already_closed_raises(self):
        self.test_create_session()
        sid = self._last_sid
        client.post(f"/api/v1/batch/sessions/{sid}/close")
        r = client.post(f"/api/v1/batch/sessions/{sid}/close")
        assert r.status_code == 400

    def test_reopen_session(self):
        self.test_create_session()
        sid = self._last_sid
        client.post(f"/api/v1/batch/sessions/{sid}/close")
        r = client.post(f"/api/v1/batch/sessions/{sid}/reopen")
        assert r.status_code == 200
        assert r.json()["status"] == "open"

    def test_upload_cvs(self):
        self.test_create_session()
        sid = self._last_sid
        r = client.post(
            f"/api/v1/batch/sessions/{sid}/cv",
            files=[
                ("files", ("cv1.pdf", SAMPLE_PDF, "application/pdf")),
                ("files", ("cv2.pdf", SAMPLE_PDF, "application/pdf")),
            ],
        )
        assert r.status_code == 200
        data = r.json()
        assert data["total_cvs"] == 2

    def test_upload_cvs_session_not_found(self):
        r = client.post(
            "/api/v1/batch/sessions/nonexistent/cv",
            files=[("files", ("cv.pdf", SAMPLE_PDF, "application/pdf"))],
        )
        assert r.status_code == 404

    def test_upload_cvs_closed_session(self):
        self.test_create_session()
        sid = self._last_sid
        client.post(f"/api/v1/batch/sessions/{sid}/close")
        r = client.post(
            f"/api/v1/batch/sessions/{sid}/cv",
            files=[("files", ("cv.pdf", SAMPLE_PDF, "application/pdf"))],
        )
        assert r.status_code == 400

    def test_discard_cv(self):
        self.test_create_session()
        sid = self._last_sid
        client.post(
            f"/api/v1/batch/sessions/{sid}/cv",
            files=[("files", ("cv.pdf", SAMPLE_PDF, "application/pdf"))],
        )
        r = client.patch(f"/api/v1/batch/sessions/{sid}/cv/cv.pdf/discard")
        assert r.status_code == 200
        assert r.json()["cvs"][0]["discarded"] is True

    def test_discard_cv_not_found(self):
        self.test_create_session()
        sid = self._last_sid
        r = client.patch(f"/api/v1/batch/sessions/{sid}/cv/unknown.pdf/discard")
        assert r.status_code == 404

    def test_export_csv_empty(self):
        self.test_create_session()
        sid = self._last_sid
        r = client.get(f"/api/v1/batch/sessions/{sid}/export")
        assert r.status_code == 200
        assert "text/csv" in r.headers["content-type"]

    def test_export_csv_not_found(self):
        r = client.get("/api/v1/batch/sessions/nonexistent/export")
        assert r.status_code == 404
