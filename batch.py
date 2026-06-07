from __future__ import annotations

import asyncio
import csv
import io
import logging
import os
import time
import uuid

from agents import (
    AgentExecutionError,
    TheInterviewer,
    TheProfiler,
    TheTechCritic,
)
from schemas import CriticOutput, InterviewerOutput, ProfilerOutput
from utils import extract_text_from_pdf

logger = logging.getLogger(__name__)

MAX_CONCURRENT = 1


class CvJob:
    def __init__(self, filename: str, cv_bytes: bytes | None = None, cv_path: str | None = None):
        self.filename = filename
        self.cv_bytes = cv_bytes
        self.cv_path = cv_path
        self.status = "pending"
        self.error: str | None = None
        self.profiler: ProfilerOutput | None = None
        self.critic: CriticOutput | None = None
        self.interviewer: InterviewerOutput | None = None
        self.match_score: int | None = None
        self.discarded: bool = False


class BatchSession:
    def __init__(self, title: str, job_offer: str, on_change=None):
        self.id = uuid.uuid4().hex[:12]
        self.title = title
        self.job_offer = job_offer
        self.created_at = time.time()
        self.status = "open"
        self.jobs: list[CvJob] = []
        self._queue: asyncio.Queue[CvJob] = asyncio.Queue()
        self._worker_task: asyncio.Task | None = None
        self._on_change = on_change

    def add_cv(self, filename: str, cv_bytes: bytes, cv_path: str | None = None) -> CvJob:
        existing = next((j for j in self.jobs if j.filename == filename), None)
        if existing:
            if existing.status == "processing":
                raise RuntimeError(f"'{filename}' is currently being processed")
            existing.cv_bytes = cv_bytes
            existing.cv_path = cv_path
            existing.status = "pending"
            existing.error = None
            existing.profiler = None
            existing.critic = None
            existing.interviewer = None
            existing.match_score = None
            existing.discarded = False
            self._queue.put_nowait(existing)
            return existing
        job = CvJob(filename, cv_bytes, cv_path)
        self.jobs.append(job)
        self._queue.put_nowait(job)
        return job

    async def ensure_processing(self):
        if self._worker_task is None or self._worker_task.done():
            for job in self.jobs:
                if job.status == "pending":
                    self._queue.put_nowait(job)
            self.status = "processing"
            self._worker_task = asyncio.create_task(self._process_queue())

    async def _process_queue(self):
        sem = asyncio.Semaphore(MAX_CONCURRENT)

        async def worker():
            while True:
                try:
                    job = await asyncio.wait_for(self._queue.get(), timeout=5.0)
                except asyncio.TimeoutError:
                    if all(j.status in ("complete", "error") for j in self.jobs):
                        break
                    continue
                async with sem:
                    await self._process_job(job)
                self._queue.task_done()

        workers = [asyncio.create_task(worker()) for _ in range(MAX_CONCURRENT)]
        await asyncio.gather(*workers)

        self.status = "open"
        if self._on_change:
            self._on_change(self)

    async def _process_job(self, job: CvJob):
        job.status = "processing"
        try:
            if job.cv_bytes is None and job.cv_path:
                if not os.path.exists(job.cv_path):
                    raise FileNotFoundError(f"CV file no longer exists on disk. Please re-upload '{job.filename}'.")
                with open(job.cv_path, "rb") as f:
                    job.cv_bytes = f.read()
            cv_text = extract_text_from_pdf(job.cv_bytes)

            profiler = TheProfiler()
            job.profiler = await profiler.run(cv_text)

            critic = TheTechCritic()
            job.critic = await critic.run(job.profiler, self.job_offer)
            job.match_score = job.critic.match_score

            interviewer = TheInterviewer()
            job.interviewer = await interviewer.run(job.critic, self.job_offer)

            job.status = "complete"
            logger.info("[%s] %s OK (score=%d)", self.id, job.filename, job.match_score)
        except AgentExecutionError as e:
            job.status = "error"
            job.error = str(e)
            logger.warning("[%s] %s failed: %s", self.id, job.filename, e)
        except Exception as e:
            job.status = "error"
            job.error = str(e)
            logger.error("[%s] %s error: %s", self.id, job.filename, e)
        if self._on_change:
            self._on_change(self)

    def get_ranking(self) -> list[CvJob]:
        done = [j for j in self.jobs if j.status == "complete"]
        done.sort(key=lambda j: j.match_score or 0, reverse=True)
        return done

    def to_dict(self) -> dict:
        jobs_data = []
        for j in self.jobs:
            jobs_data.append({
                "filename": j.filename,
                "status": j.status,
                "error": j.error,
                "match_score": j.match_score,
                "discarded": j.discarded,
                "cv_path": j.cv_path,
                "profiler": j.profiler.model_dump() if j.profiler else None,
                "critic": j.critic.model_dump() if j.critic else None,
                "interviewer": j.interviewer.model_dump() if j.interviewer else None,
            })
        return {
            "id": self.id,
            "title": self.title,
            "job_offer": self.job_offer,
            "created_at": self.created_at,
            "status": self.status,
            "cvs": jobs_data,
        }

    @staticmethod
    def from_dict(data: dict, on_change=None) -> BatchSession:
        data = _migrate_session_data(data)
        session = BatchSession.__new__(BatchSession)
        session.id = data["id"]
        session.title = data["title"]
        session.job_offer = data["job_offer"]
        session.created_at = data["created_at"]
        session._on_change = on_change
        session._queue = asyncio.Queue()
        session._worker_task = None
        session.jobs = []

        status = data.get("status", "open")
        session.status = _migrate_status(status)

        for jd in data.get("cvs", []):
            job = CvJob(jd["filename"], cv_path=jd.get("cv_path"))
            job.status = _migrate_job_status(jd.get("status", "pending"))
            job.error = jd.get("error")
            job.match_score = jd.get("match_score")
            job.discarded = jd.get("discarded", False)
            if jd.get("profiler"):
                job.profiler = ProfilerOutput.model_validate(jd["profiler"])
            if jd.get("critic"):
                job.critic = CriticOutput.model_validate(jd["critic"])
            if jd.get("interviewer"):
                job.interviewer = InterviewerOutput.model_validate(jd["interviewer"])
            session.jobs.append(job)

        for job in session.jobs:
            if job.status == "processing":
                job.status = "pending"
                job.error = None

        for job in session.jobs:
            if job.status == "pending" and not job.cv_path and not job.profiler:
                job.status = "error"
                job.error = "The original PDF is no longer available. Please re-upload the file."

        return session

    def to_csv(self) -> str:
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow([
            "Rank", "Filename", "Status", "Discarded",
            "Match Score", "Location",
            "Years Exp.", "Technologies",
            "Strengths", "Tech Gaps",
            "Conclusion", "# Questions", "Error",
        ])
        all_jobs = sorted(self.jobs, key=lambda j: j.match_score or 0, reverse=True)
        for rank, job in enumerate(all_jobs, 1):
            if job.status == "error":
                continue
            w.writerow([
                rank,
                job.filename,
                job.status,
                "Yes" if job.discarded else "No",
                job.match_score or "",
                job.profiler.location if job.profiler else "",
                job.profiler.years_experience if job.profiler else "",
                "; ".join(job.profiler.main_technologies) if job.profiler else "",
                "; ".join(job.critic.strengths) if job.critic else "",
                "; ".join(job.critic.tech_gaps) if job.critic else "",
                job.critic.analysis_conclusion if job.critic else "",
                len(job.interviewer.questions) if job.interviewer else 0,
                job.error or "",
            ])
        for job in self.jobs:
            if job.status == "error":
                w.writerow([
                    "-", job.filename, job.status, "",
                    "", "", "", "", "", "", "", "", job.error or "",
                ])
        return buf.getvalue()


def _migrate_status(status: str) -> str:
    mapping = {
        "abierta": "open",
        "cerrada": "closed",
        "procesando": "processing",
        "accepting_cvs": "open",
        "complete": "open",
    }
    return mapping.get(status, status)


def _migrate_job_status(status: str) -> str:
    mapping = {
        "pending": "pending",
        "processing": "processing",
        "complete": "complete",
        "error": "error",
    }
    return mapping.get(status, status)


_SPANISH_TO_ENGLISH_FIELDS = {
    "experiencia_anos": "years_experience",
    "tecnologias_principales": "main_technologies",
    "proyectos_anonimos": "anonymous_projects",
    "certificaciones": "certifications",
    "telefono": "phone",
    "ubicacion": "location",
    "puntos_fuertes": "strengths",
    "conclusion_analisis": "analysis_conclusion",
    "pregunta": "question",
    "justificacion_de_la_pregunta": "question_justification",
    "respuesta_correcta_esperada": "expected_correct_answer",
    "preguntas": "questions",
}


def _migrate_agent_fields(data: dict | None) -> dict | None:
    if data is None:
        return None
    migrated = {}
    for k, v in data.items():
        new_key = _SPANISH_TO_ENGLISH_FIELDS.get(k, k)
        migrated[new_key] = v
    return migrated


def _migrate_session_data(data: dict) -> dict:
    data = dict(data)
    status = data.get("status", "open")
    data["status"] = _migrate_status(status)
    cvs = []
    for jd in data.get("cvs", []):
        jd = dict(jd)
        jd["status"] = _migrate_job_status(jd.get("status", "pending"))
        if jd.get("profiler"):
            jd["profiler"] = _migrate_agent_fields(jd["profiler"])
        if jd.get("critic"):
            jd["critic"] = _migrate_agent_fields(jd["critic"])
        if jd.get("interviewer"):
            jd["interviewer"] = _migrate_agent_fields(jd["interviewer"])
        cvs.append(jd)
    data["cvs"] = cvs
    return data
