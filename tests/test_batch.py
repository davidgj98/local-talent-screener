from __future__ import annotations

import time


import pytest

from batch import BatchSession, CvJob


class TestCvJob:
    def test_defaults(self):
        job = CvJob("test.pdf")
        assert job.filename == "test.pdf"
        assert job.status == "pending"
        assert job.error is None
        assert job.match_score is None
        assert job.discarded is False

    def test_with_bytes(self):
        job = CvJob("test.pdf", cv_bytes=b"pdf content")
        assert job.cv_bytes == b"pdf content"


class TestBatchSession:
    def test_create(self):
        session = BatchSession(
            "Test Offer", "Job description with more than twenty characters"
        )
        assert session.title == "Test Offer"
        assert session.status == "open"
        assert len(session.id) == 12
        assert session.jobs == []

    def test_add_cv(self):
        session = BatchSession("Test", "A" * 30)
        job = session.add_cv("cv.pdf", b"%PDF-1.4 content")
        assert job.filename == "cv.pdf"
        assert job.status == "pending"
        assert len(session.jobs) == 1

    def test_add_duplicate_replaces(self):
        session = BatchSession("Test", "A" * 30)
        session.add_cv("cv.pdf", b"original")
        assert session.jobs[0].cv_bytes == b"original"
        session.add_cv("cv.pdf", b"updated")
        assert session.jobs[0].cv_bytes == b"updated"

    def test_add_duplicate_processing_raises(self):
        session = BatchSession("Test", "A" * 30)
        job = session.add_cv("cv.pdf", b"data")
        job.status = "processing"
        with pytest.raises(RuntimeError, match="being processed"):
            session.add_cv("cv.pdf", b"data")

    def test_to_dict(self):
        session = BatchSession("Test", "A" * 30)
        session.add_cv("cv.pdf", b"data")
        d = session.to_dict()
        assert d["title"] == "Test"
        assert d["status"] == "open"
        assert len(d["cvs"]) == 1
        assert d["cvs"][0]["filename"] == "cv.pdf"

    def test_from_dict_roundtrip(self):
        original = BatchSession("Original", "A" * 30)
        original.add_cv("cv1.pdf", b"data1")
        original.add_cv("cv2.pdf", b"data2")
        original.jobs[0].status = "complete"
        original.jobs[0].match_score = 85
        data = original.to_dict()
        restored = BatchSession.from_dict(data)
        assert restored.title == "Original"
        assert restored.id == original.id
        assert len(restored.jobs) == 2
        assert restored.jobs[0].status == "complete"
        assert restored.jobs[0].match_score == 85

    def test_from_dict_resets_processing_status(self):
        data = {
            "id": "test123",
            "title": "Test",
            "job_offer": "A" * 30,
            "created_at": time.time(),
            "status": "open",
            "cvs": [
                {
                    "filename": "cv.pdf",
                    "status": "processing",
                    "cv_path": "/tmp/test.pdf",
                }
            ],
        }
        restored = BatchSession.from_dict(data)
        assert restored.jobs[0].status == "pending"

    def test_from_dict_marks_orphan_pending_as_error(self):
        data = {
            "id": "test456",
            "title": "Test",
            "job_offer": "A" * 30,
            "created_at": time.time(),
            "status": "open",
            "cvs": [{"filename": "cv.pdf", "status": "pending"}],
        }
        restored = BatchSession.from_dict(data)
        assert restored.jobs[0].status == "error"

    def test_get_ranking(self):
        session = BatchSession("Test", "A" * 30)
        j1 = session.add_cv("low.pdf", b"data")
        j2 = session.add_cv("high.pdf", b"data")
        j3 = session.add_cv("mid.pdf", b"data")
        j1.status = "complete"
        j1.match_score = 30
        j2.status = "complete"
        j2.match_score = 90
        j3.status = "complete"
        j3.match_score = 60
        ranking = session.get_ranking()
        assert [r.match_score for r in ranking] == [90, 60, 30]

    def test_get_ranking_ignores_non_complete(self):
        session = BatchSession("Test", "A" * 30)
        j1 = session.add_cv("complete.pdf", b"data")
        j2 = session.add_cv("pending.pdf", b"data")
        j1.status = "complete"
        j1.match_score = 80
        j2.status = "pending"
        ranking = session.get_ranking()
        assert len(ranking) == 1

    def test_to_csv(self):
        session = BatchSession("Test", "A" * 30)
        session.add_cv("cv.pdf", b"data")
        session.jobs[0].status = "complete"
        session.jobs[0].match_score = 80
        csv_out = session.to_csv()
        assert "cv.pdf" in csv_out
        assert "80" in csv_out
        assert "Match Score" in csv_out

    def test_to_csv_includes_errors(self):
        session = BatchSession("Test", "A" * 30)
        session.add_cv("ok.pdf", b"data")
        session.add_cv("err.pdf", b"data")
        session.jobs[0].status = "complete"
        session.jobs[0].match_score = 90
        session.jobs[1].status = "error"
        session.jobs[1].error = "Something failed"
        csv_out = session.to_csv()
        assert "ok.pdf" in csv_out
        assert "err.pdf" in csv_out
        assert "Something failed" in csv_out
