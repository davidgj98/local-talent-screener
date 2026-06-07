# local-hr-agent-squad

> **English** · [Español](#español)

> Local Multi-Agent AI HR Screening System — **Privacy-First · 100% On-Premise · GDPR-Compliant**

Process CVs in batch against a job offer using local models via [Ollama](https://ollama.com/). Three specialized agents (Profiler, Tech Critic, Interviewer) collaborate to extract technical profiles, score match fit, and generate validation questions — all without sending data outside your machine.

---

## What It Does

Automates **technical CV screening** in two modes:

1. **Individual** — Upload one CV + job offer, get a full report in seconds.
2. **Batch** — Create an offer, upload multiple CVs, and the system processes them in the background with real-time polling from the frontend.

Each CV goes through a three-agent pipeline:
- **The Profiler** — Extracts anonymous technical profile from the CV
- **The Tech Critic** — Compares profile vs offer, assigns score and detects gaps
- **The Interviewer** — Generates personalized technical questions

---

## Tech Stack

| Component | Technology |
|---|---|
| Backend | Python 3.10+ · FastAPI |
| Frontend | Vanilla JS · Standalone HTML (no build tooling) |
| Local Inference | Ollama (`AsyncClient`) with 3 different models |
| PDF Extraction | `markitdown[pdf]` |
| Validation | Pydantic v2 |
| ASGI Server | Uvicorn |

---

## Project Structure

```
local-hr-agent-squad/
├── main.py          ← FastAPI server · REST endpoints (individual + batch)
├── batch.py         ← Async batch engine: queue, workers, persistence
├── agents.py        ← Agent logic, prompts and Ollama clients for all 3 agents
├── schemas.py       ← Pydantic contracts between agents (source of truth)
├── storage.py       ← JSON disk persistence for batch sessions
├── utils.py         ← PDF text extraction
├── frontend.html    ← Standalone web UI (no build tooling)
├── requirements.txt
└── README.md
```

---

## Prerequisites

### 1. Ollama installed and running

```bash
curl -fsSL https://ollama.com/install.sh | sh

# Pull the models (the system uses 3 different models per agent)
ollama pull qwen2.5:3b
ollama pull phi4-mini
ollama pull qwen2.5-coder:7b-instruct-q4_K_M

# Verify Ollama is running
ollama list
```

> Models are configured in `agents.py`. The system is designed to run with small models (3B-7B) that fit on consumer GPUs. You can swap them for other Ollama models.

### 2. Python 3.10+

```bash
python --version  # must be >= 3.10
```

---

## Docker (recommended)

```bash
# Clone and run
git clone <your-repo>
cd local-hr-agent-squad
docker compose up -d

# Pull the models (the UI will show errors until models are ready)
docker exec -it ollama ollama pull qwen2.5:3b
docker exec -it ollama ollama pull phi4-mini
docker exec -it ollama ollama pull qwen2.5-coder:7b-instruct-q4_K_M

# Open http://localhost:8000
```

---

## Installation

```bash
git clone <your-repo>
cd local-hr-agent-squad

python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## Usage

### Start the server

```bash
RELOAD=true python main.py          # development with auto-reload
# or: uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Server at `http://localhost:8000`.

### Web UI

Open `http://localhost:8000/` in your browser.

Two tabs:
- **Individual** — Analyze one CV against an offer (classic mode)
- **Offers** — Create offers, batch upload CVs and monitor progress

### REST API

#### Individual
```bash
curl -X POST http://localhost:8000/api/v1/analyze \
  -F "cv_file=@cv.pdf" \
  -F "job_offer=Looking for a Backend Engineer with Python experience..."
```

#### Batch — Create offer
```bash
curl -X POST http://localhost:8000/api/v1/batch/sessions \
  -H "Content-Type: application/json" \
  -d '{"title":"Backend Senior","job_offer":"Looking for..."}'
# → {"id": "abc123", ...}
```

#### Batch — Upload CVs
```bash
curl -X POST http://localhost:8000/api/v1/batch/sessions/abc123/cv \
  -F "files=@cv1.pdf" -F "files=@cv2.pdf"
# Processing starts automatically
```

#### Batch — Check status
```bash
curl http://localhost:8000/api/v1/batch/sessions/abc123
# → CVs with scores, status and detailed agent results
```

#### Batch — Export CSV
```bash
curl http://localhost:8000/api/v1/batch/sessions/abc123/export
# → CSV with ranking, scores and data for each CV
```

### Interactive docs

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## Architecture: Asymmetric Local Model Orchestration

```
                    ┌──────────────────────────┐
                    │   Batch Mode              │
                    │   (upload_cvs → queue)    │
                    │   Persistent sessions     │
                    └────────┬─────────────────┘
                             │
PDF CV  ─────────────────────┤
                             ▼
                    ┌─────────────────┐
                    │  The Profiler   │  qwen2.5:3b
                    │  (Extractor)    │  Extracts anonymous technical profile
                    └────────┬────────┘
                             │  ProfilerOutput (validated JSON)
                             ▼
                    ┌─────────────────┐
                    │ The Tech Critic │  phi4-mini
                    │  (Evaluator)    │  match_score + tech_gaps
                    └────────┬────────┘
                             │  CriticOutput (validated JSON)
                             ▼
                    ┌─────────────────┐
                    │ The Interviewer │  qwen2.5-coder:7b
                    │ (Interviewer)   │  3 personalized questions
                    └────────┬────────┘
                             │
                             ▼
                       AnalysisResponse
                       (JSON per CV)
```

Each agent uses the most suitable model: Profiler uses a lightweight model (3B), Critic uses a reasoning model (phi4-mini), and Interviewer uses a code-specialized model (7B). Communication between agents uses Pydantic schemas for strict type safety.

---

## Privacy & GDPR

- **Zero data exfiltration:** no data leaves your machine.
- **Active anonymization:** The Profiler removes personal data before downstream agents process it.
- **Optional local persistence:** in batch mode, results are saved in `data/offers/` (local JSON, never uploaded).
- **Full model control:** you decide which Ollama models to use and where they run.

---

## Configuration

Each agent's model is defined in `agents.py`:

```python
class TheProfiler(BaseAgent):
    model = "qwen2.5:3b"

class TheTechCritic(BaseAgent):
    model = "phi4-mini"
```

You can swap them for any model available in Ollama. The asymmetry allows VRAM optimization: smaller models for extraction, larger for reasoning.

---

## Troubleshooting

| Symptom | Likely cause | Solution |
|---|---|---|
| `Connection refused` when calling Ollama | Ollama not running | `ollama serve` |
| `model not found` | Model not downloaded | `ollama pull <model>` |
| `Could not extract text from PDF` | Scanned PDF without OCR | Use a selectable-text PDF |
| Slow response | Large model on CPU | Use a smaller version |
| Workers die when saving JSON | watchfiles reload | Configure `reload_excludes` (already set in `main.py`) |

---

## Roadmap

- [x] Batch mode: process multiple CVs against the same offer
- [x] Real-time polling from frontend
- [x] CSV export of results
- [x] Session persistence on disk (survives server restarts)
- [ ] DOCX CV support
- [ ] Selective re-processing of errored CVs
- [ ] Automated integration tests

---

## Español

# local-hr-agent-squad

> Sistema Multi-Agente Local de Selección de Personal con IA — **Privacy-First · 100 % On-Premise · RGPD-Compliant**

Procesa CVs de forma masiva contra una oferta de empleo usando modelos locales vía [Ollama](https://ollama.com/). Tres agentes especializados (Profiler, Tech Critic, Interviewer) colaboran para extraer perfil técnico, puntuar el encaje y generar preguntas de validación — todo sin enviar datos fuera de tu máquina.

---

### ¿Qué hace?

Automatiza el **cribado técnico de CVs** en dos modos:

1. **Individual** — Subes un CV + oferta, obtienes informe completo en segundos.
2. **Batch** — Creas una oferta, subes múltiples CVs y el sistema los procesa en segundo plano con polling en tiempo real desde el frontend.

### Stack Tecnológico

| Componente | Tecnología |
|---|---|
| Backend | Python 3.10+ · FastAPI |
| Frontend | Vanilla JS · HTML standalone (sin build tooling) |
| Inferencia local | Ollama (`AsyncClient`) con 3 modelos distintos |
| Extracción PDF | `markitdown[pdf]` |
| Validación | Pydantic v2 |
| Servidor ASGI | Uvicorn |

### Requisitos Previos

```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull qwen2.5:3b
ollama pull phi4-mini
ollama pull qwen2.5-coder:7b-instruct-q4_K_M
```

### Instalación

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Uso

```bash
python main.py
# Abre http://localhost:8000
```

### Privacidad y RGPD

- **Zero data exfiltration:** ningún dato sale de tu máquina.
- **Anonimización activa:** The Profiler elimina datos personales antes de que los agentes posteriores procesen la información.
- **Persistencia local opcional:** en modo batch, los resultados se guardan en `data/offers/` (JSON local, nunca subido a ningún servidor).
- **Control total de modelos:** decides qué modelos de Ollama usar y dónde se ejecutan.
