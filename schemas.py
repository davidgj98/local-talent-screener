from __future__ import annotations

from typing import Annotated, Optional
from pydantic import BaseModel, Field, field_validator


class ProfilerOutput(BaseModel):
    years_experience: Annotated[int, Field(ge=0, le=60)] = Field(
        ...,
        description="Total estimated years of professional experience.",
    )
    main_technologies: list[str] = Field(
        default_factory=list,
        description="List of technologies, languages, frameworks and tools.",
    )
    anonymous_projects: list[str] = Field(
        default_factory=list,
        description="Project descriptions without personal data or company names.",
    )
    certifications: list[str] = Field(
        default_factory=list,
        description="Relevant certifications and degrees (without institution if identifiable).",
    )
    phone: str | None = Field(
        default=None,
        description="Candidate contact phone (only visible on request).",
    )
    email: str | None = Field(
        default=None,
        description="Candidate contact email (only visible on request).",
    )
    location: str | None = Field(
        default=None,
        description="Candidate geographic location (city, region, etc).",
    )

    @field_validator("main_technologies", "anonymous_projects", "certifications", mode="before")
    @classmethod
    def ensure_list_of_strings(cls, v: object) -> list[str]:
        if v is None:
            return []
        if isinstance(v, list):
            return [str(item) for item in v]
        return []


class CriticOutput(BaseModel):
    match_score: Annotated[int, Field(ge=0, le=100)] = Field(
        ...,
        description="Candidate/offer match percentage (0–100).",
    )
    strengths: list[str] = Field(
        default_factory=list,
        description="Technologies or skills that match offer requirements.",
    )
    tech_gaps: list[str] = Field(
        default_factory=list,
        description="Missing technical skills: required technologies the candidate lacks.",
    )
    analysis_conclusion: str = Field(
        ...,
        min_length=10,
        description="Executive summary of the comparative analysis.",
    )

    @field_validator("strengths", "tech_gaps", mode="before")
    @classmethod
    def ensure_list_of_strings(cls, v: object) -> list[str]:
        if v is None:
            return []
        if isinstance(v, list):
            return [str(item) for item in v]
        return []


class InterviewQuestion(BaseModel):
    question: str = Field(
        ...,
        min_length=10,
        description="Complex technical question for the validation call.",
    )
    question_justification: str = Field(
        ...,
        min_length=10,
        description="Why this question validates the detected gap.",
    )
    expected_correct_answer: str = Field(
        ...,
        min_length=10,
        description="Precise technical answer that would prove real domain expertise.",
    )


class InterviewerOutput(BaseModel):
    questions: Annotated[list[InterviewQuestion], Field(min_length=1, max_length=3)] = Field(
        ...,
        description="List of technical questions (exactly 3).",
    )

    @field_validator("questions", mode="before")
    @classmethod
    def normalize_questions(cls, v: object) -> list[dict]:
        if isinstance(v, list):
            return v
        if isinstance(v, dict) and "questions" in v:
            return v["questions"]
        return []


class AnalysisResponse(BaseModel):
    profiler: ProfilerOutput
    tech_critic: CriticOutput
    interviewer: InterviewerOutput

    model_config = {"populate_by_name": True}


class AgentError(BaseModel):
    agent: str = Field(..., description="Name of the agent that failed.")
    error: str = Field(..., description="Error description.")
    detail: str | None = Field(None, description="Raw LLM output if available.")


class BatchSessionCreate(BaseModel):
    title: str = Field(..., min_length=1, description="Session title.")
    job_offer: str = Field(..., min_length=20, description="Full job offer description.")


class BatchCvResult(BaseModel):
    filename: str
    status: str
    match_score: int | None = None
    error: str | None = None
    technologies: list[str] = []
    years_experience: int | None = None
    location: str | None = None
    strengths: list[str] = []
    tech_gaps: list[str] = []
    conclusion: str | None = None
    question_count: int = 0
    discarded: bool = False
    profiler: Optional[ProfilerOutput] = None
    critic: Optional[CriticOutput] = None
    interviewer: Optional[InterviewerOutput] = None


class BatchSessionInfo(BaseModel):
    id: str
    title: str
    job_offer: str
    created_at: float
    status: str
    total_cvs: int
    cvs: list[BatchCvResult]
