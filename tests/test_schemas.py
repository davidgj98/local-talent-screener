from __future__ import annotations

import pytest
from pydantic import ValidationError

from schemas import (
    AnalysisResponse,
    CriticOutput,
    InterviewQuestion,
    InterviewerOutput,
    ProfilerOutput,
    BatchCvResult,
    BatchSessionCreate,
    AgentError,
)


class TestProfilerOutput:
    def test_valid(self, sample_profiler_data):
        p = ProfilerOutput(**sample_profiler_data)
        assert p.years_experience == 5
        assert "Python" in p.main_technologies
        assert p.phone == "+34 600 000 000"

    def test_minimal_valid(self):
        p = ProfilerOutput(
            years_experience=0,
            main_technologies=[],
            anonymous_projects=[],
            certifications=[],
        )
        assert p.years_experience == 0
        assert p.main_technologies == []

    def test_negative_experience_raises(self):
        with pytest.raises(ValidationError):
            ProfilerOutput(
                years_experience=-1,
                main_technologies=[],
                anonymous_projects=[],
                certifications=[],
            )

    def test_experience_over_60_raises(self):
        with pytest.raises(ValidationError):
            ProfilerOutput(
                years_experience=99,
                main_technologies=[],
                anonymous_projects=[],
                certifications=[],
            )

    def test_none_lists_coerced_to_empty(self):
        p = ProfilerOutput(
            years_experience=3,
            main_technologies=None,
            anonymous_projects=None,
            certifications=None,
        )
        assert p.main_technologies == []
        assert p.anonymous_projects == []
        assert p.certifications == []

    def test_contact_fields_optional(self):
        p = ProfilerOutput(
            years_experience=3,
            main_technologies=[],
            anonymous_projects=[],
            certifications=[],
        )
        assert p.phone is None
        assert p.email is None
        assert p.location is None


class TestCriticOutput:
    def test_valid(self, sample_critic_data):
        c = CriticOutput(**sample_critic_data)
        assert c.match_score == 75
        assert len(c.strengths) == 2
        assert len(c.tech_gaps) == 2

    def test_match_score_raises_out_of_range(self):
        with pytest.raises(ValidationError):
            CriticOutput(
                match_score=150,
                strengths=[],
                tech_gaps=[],
                analysis_conclusion="Valid conclusion text here for testing",
            )

    def test_match_score_negative_raises(self):
        with pytest.raises(ValidationError):
            CriticOutput(
                match_score=-10,
                strengths=[],
                tech_gaps=[],
                analysis_conclusion="Valid conclusion text here for testing",
            )

    def test_conclusion_min_length_raises(self):
        with pytest.raises(ValidationError):
            CriticOutput(
                match_score=50,
                strengths=[],
                tech_gaps=[],
                analysis_conclusion="Short",
            )

    def test_none_lists_coerced(self):
        c = CriticOutput(
            match_score=50,
            strengths=None,
            tech_gaps=None,
            analysis_conclusion="Valid conclusion text with more than ten chars",
        )
        assert c.strengths == []
        assert c.tech_gaps == []


class TestInterviewerOutput:
    def test_valid(self, sample_interviewer_data):
        i = InterviewerOutput(**sample_interviewer_data)
        assert len(i.questions) == 2
        assert i.questions[0].question.startswith("Explain")

    def test_min_questions_raises(self):
        with pytest.raises(ValidationError):
            InterviewerOutput(questions=[])

    def test_list_root_normalized(self):
        data = [
            {
                "question": "Test question with sufficient length here",
                "question_justification": "Sufficient justification here for test",
                "expected_correct_answer": "Sufficient answer here for validation test",
            }
        ]
        i = InterviewerOutput(questions=data)
        assert len(i.questions) == 1

    def test_question_min_length(self):
        with pytest.raises(ValidationError):
            InterviewQuestion(
                question="Short",
                question_justification="Sufficient justification here for test",
                expected_correct_answer="Sufficient answer here for validation test",
            )


class TestAnalysisResponse:
    def test_valid(
        self, sample_profiler_data, sample_critic_data, sample_interviewer_data
    ):
        r = AnalysisResponse(
            profiler=ProfilerOutput(**sample_profiler_data),
            tech_critic=CriticOutput(**sample_critic_data),
            interviewer=InterviewerOutput(**sample_interviewer_data),
        )
        assert r.profiler.years_experience == 5
        assert r.tech_critic.match_score == 75
        assert len(r.interviewer.questions) == 2


class TestBatchModels:
    def test_batch_session_create_valid(self):
        b = BatchSessionCreate(
            title="Test", job_offer="Test description with more than twenty chars"
        )
        assert b.title == "Test"

    def test_batch_session_create_short_title_raises(self):
        with pytest.raises(ValidationError):
            BatchSessionCreate(
                title="", job_offer="Test description with more than twenty chars"
            )

    def test_batch_session_create_short_offer_raises(self):
        with pytest.raises(ValidationError):
            BatchSessionCreate(title="Test", job_offer="Short")

    def test_batch_cv_result_defaults(self):
        r = BatchCvResult(filename="test.pdf", status="pending")
        assert r.match_score is None
        assert r.error is None
        assert r.technologies == []
        assert r.discarded is False

    def test_agent_error(self):
        e = AgentError(agent="TheProfiler", error="Something failed")
        assert e.agent == "TheProfiler"
        assert e.detail is None
