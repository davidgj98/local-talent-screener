from __future__ import annotations

import asyncio
import logging
import os
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse

from agents import AgentExecutionError, TheInterviewer, TheProfiler, TheTechCritic
from batch import BatchSession
from schemas import (
    AgentError,
    AnalysisResponse,
    BatchCvResult,
    BatchSessionCreate,
    BatchSessionInfo,
)
from storage import list_offers, load_offer, save_offer
from utils import extract_text_from_pdf

BASE_DIR = Path(__file__).resolve().parent
FRONTEND_PATH = BASE_DIR / "frontend.html"
UPLOAD_DIR = BASE_DIR / "uploads"
MAX_CV_BYTES = 10 * 1024 * 1024  # 10 MB

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    logger.info("local-hr-agent-squad starting...")
    yield
    logger.info("local-hr-agent-squad shutting down.")


def _is_pdf_bytes(data: bytes) -> bool:
    return len(data) >= 4 and data[:4] == b"%PDF"


async def _read_and_store_cv(cv_file: UploadFile) -> tuple[bytes, Path | None]:
    raw_bytes = await cv_file.read()
    if not raw_bytes:
        raise HTTPException(status_code=400, detail="PDF file is empty")
    if len(raw_bytes) > MAX_CV_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"PDF exceeds limit of {MAX_CV_BYTES // (1024 * 1024)} MB",
        )
    if not _is_pdf_bytes(raw_bytes):
        raise HTTPException(
            status_code=400, detail="Content does not appear to be a valid PDF"
        )

    temp_path: Path | None = None
    try:
        suffix = Path(cv_file.filename or "cv.pdf").suffix or ".pdf"
        temp_path = UPLOAD_DIR / f"{uuid.uuid4().hex}{suffix}"
        temp_path.write_bytes(raw_bytes)
        logger.debug(
            "CV temporarily saved to %s (%d bytes)", temp_path.name, len(raw_bytes)
        )
    except OSError as exc:
        logger.warning("Could not save temporary CV copy: %s", exc)
        temp_path = None

    return raw_bytes, temp_path


app = FastAPI(
    title="local-hr-agent-squad",
    description=(
        "Local Multi-Agent HR Screening System. "
        "Processes CVs 100% locally (on-premise) ensuring GDPR privacy."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

profiler_agent = TheProfiler()
critic_agent = TheTechCritic()
interviewer_agent = TheInterviewer()

_session_cache: dict[str, BatchSession] = {}


def _load_session(session_id: str) -> BatchSession | None:
    if session_id in _session_cache:
        return _session_cache[session_id]
    data = load_offer(session_id)
    if data is None:
        return None
    session = BatchSession.from_dict(data, on_change=_persist_session)
    _session_cache[session_id] = session
    _maybe_auto_process(session)
    return session


def _load_all_sessions() -> list[BatchSession]:
    result = []
    for d in list_offers():
        sid = d["id"]
        if sid in _session_cache:
            result.append(_session_cache[sid])
        else:
            session = BatchSession.from_dict(d, on_change=_persist_session)
            _session_cache[sid] = session
            _maybe_auto_process(session)
            result.append(session)
    return result


def _maybe_auto_process(session: BatchSession):
    if session.status == "open" and any(j.status == "pending" for j in session.jobs):
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(_start_session_processing(session))
        except RuntimeError:
            pass


def _persist_session(session: BatchSession):
    save_offer(session.to_dict())


async def _start_session_processing(session: BatchSession):
    await session.ensure_processing()
    _persist_session(session)


def _session_to_info(s: BatchSession) -> BatchSessionInfo:
    return BatchSessionInfo(
        id=s.id,
        title=s.title,
        job_offer=s.job_offer,
        created_at=s.created_at,
        status=s.status,
        total_cvs=len(s.jobs),
        cvs=[
            BatchCvResult(
                filename=j.filename,
                status=j.status,
                match_score=j.match_score,
                error=j.error,
                technologies=j.profiler.main_technologies if j.profiler else [],
                years_experience=j.profiler.years_experience if j.profiler else None,
                location=j.profiler.location if j.profiler else None,
                strengths=j.critic.strengths if j.critic else [],
                tech_gaps=j.critic.tech_gaps if j.critic else [],
                conclusion=j.critic.analysis_conclusion if j.critic else None,
                question_count=len(j.interviewer.questions) if j.interviewer else 0,
                discarded=j.discarded,
                profiler=j.profiler,
                critic=j.critic,
                interviewer=j.interviewer,
            )
            for j in s.jobs
        ],
    )


@app.get("/", include_in_schema=False)
async def serve_frontend():
    if not FRONTEND_PATH.is_file():
        raise HTTPException(status_code=404, detail="frontend.html not found")
    return FileResponse(FRONTEND_PATH, media_type="text/html")


@app.get("/api/v1", tags=["Health"])
async def api_root():
    return {"status": "ok", "service": "local-hr-agent-squad", "version": "1.0.0"}


@app.get("/api/v1/health", tags=["Health"])
async def health():
    return {
        "status": "ok",
        "models": {
            "profiler": profiler_agent.model,
            "tech_critic": critic_agent.model,
            "interviewer": interviewer_agent.model,
        },
    }


@app.post(
    "/api/v1/analyze",
    response_model=AnalysisResponse,
    responses={
        400: {"model": AgentError, "description": "Invalid file or parameters"},
        422: {"description": "Schema validation error"},
        500: {"model": AgentError, "description": "Internal agent failure"},
    },
    tags=["Pipeline"],
    summary="Analyze CV against a job offer",
)
async def analyze_cv(
    cv_file: UploadFile = File(..., description="Candidate CV in PDF format"),
    job_offer: str = Form(..., description="Full job offer description"),
) -> AnalysisResponse:
    start = time.monotonic()

    if not cv_file.filename or not cv_file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="File must be a PDF (.pdf)")

    if not job_offer or len(job_offer.strip()) < 20:
        raise HTTPException(
            status_code=400,
            detail="Job offer description is too short (min. 20 characters)",
        )

    temp_path: Path | None = None
    try:
        raw_bytes, temp_path = await _read_and_store_cv(cv_file)
        cv_text = extract_text_from_pdf(raw_bytes)
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    finally:
        if temp_path and temp_path.exists():
            try:
                temp_path.unlink()
            except OSError as exc:
                logger.warning("Could not delete temp file %s: %s", temp_path, exc)

    if not cv_text.strip():
        raise HTTPException(
            status_code=400,
            detail="Could not extract text from PDF. Is it a scanned PDF without OCR?",
        )

    logger.info(
        "PDF received: %s | %d bytes | %d chars extracted",
        cv_file.filename,
        len(raw_bytes),
        len(cv_text),
    )

    try:
        logger.info("Running TheProfiler (%s)...", profiler_agent.model)
        profiler_result = await profiler_agent.run(cv_text)
        logger.info(
            "TheProfiler completed. Technologies detected: %d",
            len(profiler_result.main_technologies),
        )
    except AgentExecutionError as exc:
        logger.error("TheProfiler failed: %s", exc)
        raise HTTPException(
            status_code=500, detail=exc.to_schema().model_dump()
        ) from exc

    try:
        logger.info("Running TheTechCritic (%s)...", critic_agent.model)
        critic_result = await critic_agent.run(profiler_result, job_offer)
        logger.info(
            "TheTechCritic completed. match_score=%d, tech_gaps=%d",
            critic_result.match_score,
            len(critic_result.tech_gaps),
        )
    except AgentExecutionError as exc:
        logger.error("TheTechCritic failed: %s", exc)
        raise HTTPException(
            status_code=500, detail=exc.to_schema().model_dump()
        ) from exc

    try:
        logger.info("Running TheInterviewer (%s)...", interviewer_agent.model)
        interviewer_result = await interviewer_agent.run(critic_result, job_offer)
        logger.info(
            "TheInterviewer completed. Questions generated: %d",
            len(interviewer_result.questions),
        )
    except AgentExecutionError as exc:
        logger.error("TheInterviewer failed: %s", exc)
        raise HTTPException(
            status_code=500, detail=exc.to_schema().model_dump()
        ) from exc

    elapsed = time.monotonic() - start
    logger.info("Pipeline completed in %.1fs", elapsed)

    return AnalysisResponse(
        profiler=profiler_result,
        tech_critic=critic_result,
        interviewer=interviewer_result,
    )


@app.post("/api/v1/batch/sessions", tags=["Offers"], summary="Create new offer")
async def create_session(body: BatchSessionCreate) -> BatchSessionInfo:
    session = BatchSession(
        title=body.title, job_offer=body.job_offer, on_change=_persist_session
    )
    _persist_session(session)
    logger.info("[%s] Offer created: %s", session.id, session.title)
    return _session_to_info(session)


@app.get("/api/v1/batch/sessions", tags=["Offers"], summary="List offers")
async def list_sessions() -> list[BatchSessionInfo]:
    sessions = _load_all_sessions()
    sessions.sort(key=lambda s: s.created_at, reverse=True)
    return [_session_to_info(s) for s in sessions]


@app.post(
    "/api/v1/batch/sessions/{session_id}/cv",
    tags=["Offers"],
    summary="Upload CVs to an offer",
)
async def upload_cvs(
    session_id: str,
    files: list[UploadFile] = File(..., description="CVs in PDF (multiple allowed)"),
) -> BatchSessionInfo:
    session = _load_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.status != "open":
        raise HTTPException(status_code=400, detail="Session is not open")

    added = 0
    for f in files:
        if not f.filename or not f.filename.lower().endswith(".pdf"):
            logger.warning("[%s] Skipped (not PDF): %s", session_id, f.filename)
            continue
        raw_bytes = await f.read()
        if not raw_bytes or len(raw_bytes) > MAX_CV_BYTES:
            logger.warning(
                "[%s] Skipped (empty or too large): %s", session_id, f.filename
            )
            continue
        if not _is_pdf_bytes(raw_bytes):
            logger.warning("[%s] Skipped (not PDF bytes): %s", session_id, f.filename)
            continue
        try:
            cv_path = UPLOAD_DIR / f"{uuid.uuid4().hex}.pdf"
            cv_path.write_bytes(raw_bytes)
            session.add_cv(f.filename, raw_bytes, cv_path=str(cv_path))
        except RuntimeError as e:
            logger.warning("[%s] %s", session_id, e)
            continue
        added += 1

    logger.info("[%s] %d CV(s) added (total=%d)", session_id, added, len(session.jobs))

    _persist_session(session)

    if added > 0:
        try:
            await _start_session_processing(session)
        except Exception as e:
            logger.warning("[%s] Could not auto-start processing: %s", session_id, e)

    return _session_to_info(session)


@app.post(
    "/api/v1/batch/sessions/{session_id}/process",
    tags=["Offers"],
    summary="Start CV processing",
)
async def process_session(session_id: str) -> BatchSessionInfo:
    session = _load_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.status != "open":
        raise HTTPException(status_code=400, detail="Session is not open")
    if not session.jobs:
        raise HTTPException(status_code=400, detail="No CVs to process")

    await _start_session_processing(session)
    return _session_to_info(session)


@app.post(
    "/api/v1/batch/sessions/{session_id}/close",
    tags=["Offers"],
    summary="Close offer manually",
)
async def close_session(session_id: str) -> BatchSessionInfo:
    session = _load_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.status != "open":
        raise HTTPException(status_code=400, detail="Only an open offer can be closed")

    session.status = "closed"
    _persist_session(session)
    return _session_to_info(session)


@app.post(
    "/api/v1/batch/sessions/{session_id}/reopen",
    tags=["Offers"],
    summary="Reopen closed offer",
)
async def reopen_session(session_id: str) -> BatchSessionInfo:
    session = _load_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.status != "closed":
        raise HTTPException(
            status_code=400, detail="Only a closed offer can be reopened"
        )

    session.status = "open"
    _persist_session(session)
    return _session_to_info(session)


@app.get(
    "/api/v1/batch/sessions/{session_id}", tags=["Offers"], summary="Get offer status"
)
async def get_session(session_id: str) -> BatchSessionInfo:
    session = _load_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return _session_to_info(session)


@app.get(
    "/api/v1/batch/sessions/{session_id}/export",
    tags=["Offers"],
    summary="Export results as CSV",
)
async def export_session_csv(session_id: str):
    session = _load_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    csv_content = session.to_csv()
    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="{session.title}-results.csv"',
        },
    )


@app.patch(
    "/api/v1/batch/sessions/{session_id}/cv/{filename}/discard",
    tags=["Offers"],
    summary="Mark/unmark a CV as discarded",
)
async def discard_cv(session_id: str, filename: str) -> BatchSessionInfo:
    session = _load_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    for j in session.jobs:
        if j.filename == filename:
            j.discarded = not j.discarded
            _persist_session(session)
            logger.info("[%s] %s discarded=%s", session_id, filename, j.discarded)
            return _session_to_info(session)
    raise HTTPException(status_code=404, detail=f"CV '{filename}' not found")


@app.get(
    "/api/v1/batch/sessions/{session_id}/cv/{filename}/contact",
    tags=["Offers"],
    summary="Get contact data for a CV",
)
async def contact_cv(session_id: str, filename: str):
    session = _load_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    for j in session.jobs:
        if j.filename == filename:
            if not j.profiler:
                raise HTTPException(status_code=400, detail="CV not yet processed")
            return {
                "phone": j.profiler.phone,
                "email": j.profiler.email,
                "location": j.profiler.location,
            }
    raise HTTPException(status_code=404, detail=f"CV '{filename}' not found")


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=os.getenv("RELOAD", "false").lower() == "true",
        reload_excludes=["data/*", "uploads/*"],
    )
