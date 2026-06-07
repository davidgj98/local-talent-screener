from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest

from agents import (
    AgentExecutionError,
    TheInterviewer,
    TheProfiler,
    TheTechCritic,
)
from schemas import CriticOutput, ProfilerOutput


def fake_ollama_response(content: str):
    mock_client = AsyncMock()
    mock_client.chat.return_value = {"message": {"content": content}}
    return mock_client


class TestAgentExecutionError:
    def test_to_schema(self):
        exc = AgentExecutionError("TheProfiler", "Something failed", raw='{"bad json}')
        err = exc.to_schema()
        assert err.agent == "TheProfiler"
        assert err.error == "Something failed"
        assert err.detail == '{"bad json}'


class TestTheProfiler:
    @pytest.mark.asyncio
    @patch("agents.ollama.AsyncClient")
    async def test_run_valid_response(self, mock_ollama_cls, sample_profiler_data):
        mock_client = fake_ollama_response(json.dumps(sample_profiler_data))
        mock_ollama_cls.return_value = mock_client

        agent = TheProfiler()
        result = await agent.run("cv text")
        assert result.years_experience == 5
        assert "Python" in result.main_technologies
        assert result.phone == "+34 600 000 000"

    @pytest.mark.asyncio
    @patch("agents.ollama.AsyncClient")
    async def test_run_invalid_json_raises(self, mock_ollama_cls):
        mock_client = fake_ollama_response("not json at all")
        mock_ollama_cls.return_value = mock_client

        agent = TheProfiler()
        with pytest.raises(AgentExecutionError, match="not valid JSON"):
            await agent.run("text")

    @pytest.mark.asyncio
    @patch("agents.ollama.AsyncClient")
    async def test_run_validation_error_raises(self, mock_ollama_cls):
        bad_data = json.dumps({"years_experience": -5})
        mock_client = fake_ollama_response(bad_data)
        mock_ollama_cls.return_value = mock_client

        agent = TheProfiler()
        with pytest.raises(AgentExecutionError, match="Invalid schema"):
            await agent.run("text")


class TestTheTechCritic:
    @pytest.mark.asyncio
    @patch("agents.ollama.AsyncClient")
    async def test_run_valid_response(self, mock_ollama_cls, sample_profiler_data, sample_critic_data):
        mock_client = fake_ollama_response(json.dumps(sample_critic_data))
        mock_ollama_cls.return_value = mock_client

        agent = TheTechCritic()
        profile = ProfilerOutput(**sample_profiler_data)
        result = await agent.run(profile, "Job offer with many requirements")
        assert result.match_score == 75
        assert "Kubernetes" in result.tech_gaps

    @pytest.mark.asyncio
    @patch("agents.ollama.AsyncClient")
    async def test_run_retry_on_failure(self, mock_ollama_cls, sample_profiler_data):
        mock_client = AsyncMock()
        mock_client.chat.side_effect = [
            {"message": {"content": "invalid json"}},
            {"message": {"content": "invalid json too"}},
        ]
        mock_ollama_cls.return_value = mock_client

        agent = TheTechCritic()
        profile = ProfilerOutput(**sample_profiler_data)
        with pytest.raises(AgentExecutionError):
            await agent.run(profile, "Offer")
        assert mock_client.chat.call_count == 2


class TestTheInterviewer:
    @pytest.mark.asyncio
    @patch("agents.ollama.AsyncClient")
    async def test_run_valid_response(self, mock_ollama_cls, sample_critic_data, sample_interviewer_data):
        mock_client = fake_ollama_response(json.dumps(sample_interviewer_data))
        mock_ollama_cls.return_value = mock_client

        agent = TheInterviewer()
        critic = CriticOutput(**sample_critic_data)
        result = await agent.run(critic, "Offer")
        assert len(result.questions) == 2

    @pytest.mark.asyncio
    @patch("agents.ollama.AsyncClient")
    async def test_run_list_root(self, mock_ollama_cls):
        data = [
            {
                "question": "Test question with sufficient length here",
                "question_justification": "Sufficient justification here for test",
                "expected_correct_answer": "Sufficient answer here for validation test",
            }
        ]
        mock_client = fake_ollama_response(json.dumps(data))
        mock_ollama_cls.return_value = mock_client

        agent = TheInterviewer()
        critic = CriticOutput(
            match_score=50,
            strengths=[],
            tech_gaps=["Kubernetes"],
            analysis_conclusion="Test conclusion with more than ten characters here",
        )
        result = await agent.run(critic, "Offer")
        assert len(result.questions) == 1
