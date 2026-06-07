from __future__ import annotations

import pytest


@pytest.fixture
def minimal_pdf() -> bytes:
    return (
        b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
        b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R"
        b"/Resources<<>>>>endobj\n"
        b"xref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n"
        b"0000000058 00000 n \n0000000115 00000 n \n"
        b"trailer<</Size 4/Root 1 0 R>>\nstartxref\n190\n%%EOF"
    )


@pytest.fixture
def sample_profiler_data() -> dict:
    return {
        "years_experience": 5,
        "main_technologies": ["Python", "Docker"],
        "anonymous_projects": ["ML recommendation system"],
        "certifications": ["AWS Solutions Architect"],
        "phone": "+34 600 000 000",
        "email": "juan@example.com",
        "location": "Madrid",
    }


@pytest.fixture
def sample_critic_data() -> dict:
    return {
        "match_score": 75,
        "strengths": ["Python", "FastAPI"],
        "tech_gaps": ["Kubernetes", "Redis"],
        "analysis_conclusion": "Good technical fit although infrastructure skills are missing.",
    }


@pytest.fixture
def sample_interviewer_data() -> dict:
    return {
        "questions": [
            {
                "question": "Explain how you would deploy FastAPI on Kubernetes",
                "question_justification": "Validates knowledge of k8s deployment",
                "expected_correct_answer": "I would use a Deployment with health checks...",
            },
            {
                "question": "How would you manage sessions with Redis?",
                "question_justification": "Covers Redis tech_gap",
                "expected_correct_answer": "I would use redis-py with a connection pool...",
            },
        ]
    }
