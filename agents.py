from __future__ import annotations

import asyncio
import json
import logging
import os
from typing import Any

import ollama
from ollama import ResponseError

from schemas import (
    AgentError,
    CriticOutput,
    InterviewerOutput,
    ProfilerOutput,
)

logger = logging.getLogger(__name__)

OLLAMA_TIMEOUT = 120


class AgentExecutionError(Exception):
    def __init__(self, agent_name: str, message: str, raw: str | None = None):
        super().__init__(message)
        self.agent_name = agent_name
        self.raw = raw

    def to_schema(self) -> AgentError:
        return AgentError(agent=self.agent_name, error=str(self), detail=self.raw)


class BaseAgent:
    name: str = "BaseAgent"
    model: str = ""
    system_prompt: str = ""

    async def _call_ollama(self, user_content: str) -> str:
        client = ollama.AsyncClient()
        try:
            response = await asyncio.wait_for(
                client.chat(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": user_content},
                    ],
                    format="json",
                    options={"temperature": 0},
                ),
                timeout=OLLAMA_TIMEOUT,
            )
        except asyncio.TimeoutError:
            raise AgentExecutionError(
                self.name,
                f"Ollama did not respond within {OLLAMA_TIMEOUT}s (model: {self.model}). "
                "The model may be too large for your hardware or the service is blocked.",
            )
        except ResponseError as exc:
            raise AgentExecutionError(
                self.name,
                f"Ollama could not load '{self.model}': {exc}",
            ) from exc
        except ConnectionError as exc:
            raise AgentExecutionError(
                self.name,
                "No connection to Ollama. Check that the service is running (ollama serve).",
            ) from exc
        except Exception as exc:
            raise AgentExecutionError(
                self.name,
                f"Error calling Ollama ({self.model}): {exc}",
            ) from exc
        return response["message"]["content"]

    def _parse_json(self, raw: str) -> Any:
        try:
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            raise AgentExecutionError(
                self.name,
                f"LLM response is not valid JSON: {exc}",
                raw=raw[:500],
            ) from exc

    async def _call_with_retry(self, user_content: str, validator=None, max_retries: int = 1):
        last_error = None
        for attempt in range(max_retries + 1):
            raw = None
            try:
                raw = await self._call_ollama(user_content)
                data = self._parse_json(raw)
                if validator:
                    return validator(data, raw)
                return raw
            except (AgentExecutionError, Exception) as e:
                last_error = e
                if attempt < max_retries:
                    logger.warning("[%s] Error on attempt %d/%d: %s", self.name, attempt + 1, max_retries, e)
                    continue
                if isinstance(e, AgentExecutionError):
                    raise
                raise AgentExecutionError(self.name, f"Invalid schema: {e}", raw=raw[:500] if raw else None) from e


class TheProfiler(BaseAgent):
    name = "TheProfiler"
    model = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")
    system_prompt = """You are The Profiler, an agent specialized in CV analysis.

YOUR TASKS:
1. Extract technical skills (hard skills) from the CV.
2. Identify years of professional experience.
3. List relevant projects anonymously.
4. Detect certifications and technical degrees.
5. Extract contact info: phone, email and location (city/region).
6. ANONYMIZE: technical output (technologies, projects, certifications) must not
   contain personally identifiable data, but phone/email/location fields
   are stored separately for internal recruiter use.

INSTRUCTIONS:
- If you find phone, email or location in the CV, extract them to their respective fields.
- If not found, leave them as null.
- Location can be city, region, or country — whatever appears in the CV.
- For the rest of the fields: extract objective professional and technical information.
- If you cannot determine a value with certainty, use 0 or empty list.

OUTPUT FORMAT — return ONLY this JSON (no extra text):
{
  "years_experience": <integer>,
  "main_technologies": ["...", "..."],
  "anonymous_projects": ["anonymous project description", "..."],
  "certifications": ["...", "..."],
  "phone": "..." | null,
  "email": "..." | null,
  "location": "..." | null
}"""

    async def run(self, cv_text: str) -> ProfilerOutput:
        user_content = json.dumps(
            {"instruction": "Analyze the following CV and extract the anonymous technical profile.", "cv_text": cv_text},
            ensure_ascii=False,
        )
        def validate(data, raw):
            return ProfilerOutput.model_validate(data)
        result = await self._call_with_retry(user_content, validator=validate)
        logger.debug("[TheProfiler] OK: %d technologies", len(result.main_technologies))
        return result


class TheTechCritic(BaseAgent):
    name = "TheTechCritic"
    model = os.getenv("OLLAMA_CRITIC_MODEL", "phi4-mini")
    system_prompt = """You are The Tech Critic, an expert technical evaluator for candidate profile analysis.

YOUR TASKS:
1. Compare the candidate's technical profile (JSON) against the job requirements.
2. Calculate a realistic match_score (0–100).
3. List technologies the candidate masters that the offer requires (strengths).
4. Detect gaps: required technologies the candidate does not demonstrate (tech_gaps).
5. Write a brief executive conclusion.

INSTRUCTIONS:
- Be critical and objective; match_score must reflect real evidence.
- If the offer requires X and the candidate does not mention it, it is a tech_gap.
- tech_gaps is the most important output: it feeds the next agent.

OUTPUT FORMAT — return ONLY this JSON (no extra text):
{
  "match_score": <integer 0-100>,
  "strengths": ["...", "..."],
  "tech_gaps": ["Missing technology or area", "..."],
  "analysis_conclusion": "..."
}"""

    async def run(self, profile: ProfilerOutput, job_offer: str) -> CriticOutput:
        user_content = json.dumps(
            {
                "instruction": "Evaluate the fit between the candidate profile and the job offer.",
                "candidate_profile": profile.model_dump(),
                "job_offer": job_offer,
            },
            ensure_ascii=False,
        )
        def validate(data, raw):
            return CriticOutput.model_validate(data)
        result = await self._call_with_retry(user_content, validator=validate)
        logger.debug("[TheTechCritic] OK: score=%d, gaps=%d", result.match_score, len(result.tech_gaps))
        return result


class TheInterviewer(BaseAgent):
    """
    Generates 3 technical questions to validate detected gaps.
    """

    name = "TheInterviewer"
    model = os.getenv("OLLAMA_INTERVIEWER_MODEL", "qwen2.5-coder:7b-instruct-q4_K_M")
    system_prompt = """You are The Interviewer, an expert in designing technical validation questions for interviews.

YOUR TASKS:
1. Analyze the tech_gaps reported by the previous evaluator.
2. Design EXACTLY 3 complex or "trick" technical questions.
3. Each question must validate whether the candidate really masters the area of concern.
4. Include justification and expected technical answer for each.

INSTRUCTIONS:
- Questions are aimed at a NON-technical recruiter who will read them during a call.
- They should be specific, not generic: avoid "What is Docker?" — prefer
  "How would you manage data persistence in a Docker container in production?"
- The expected answer should be technical and precise, not a textbook definition.

OUTPUT FORMAT — return ONLY a JSON with this structure (no extra text):
{
  "questions": [
    {
      "question": "...",
      "question_justification": "...",
      "expected_correct_answer": "..."
    },
    { ... },
    { ... }
  ]
}"""

    async def run(self, critic: CriticOutput, job_offer: str) -> InterviewerOutput:
        user_content = json.dumps(
            {
                "instruction": "Generate 3 technical questions to validate the candidate's gaps.",
                "tech_gaps": critic.tech_gaps,
                "match_score": critic.match_score,
                "job_offer": job_offer,
            },
            ensure_ascii=False,
        )
        def validate(data, raw):
            if isinstance(data, list):
                data = {"questions": data}
            return InterviewerOutput.model_validate(data)
        result = await self._call_with_retry(user_content, validator=validate)
        logger.debug("[TheInterviewer] OK: %d questions", len(result.questions))
        return result
