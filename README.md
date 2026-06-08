# local-talent-screener

> **English** · [Español](#español)

> Local Multi-Agent AI CV Screening System — **Privacy-First · 100% On-Premise · GDPR-Compliant**

Process CVs in batch against a job offer using local models via [Ollama](https://ollama.com/). Three specialized agents collaborate to extract technical profiles, score candidate fit, and generate validation questions — all without sending data outside your machine.

---

## What It Does

Automates **technical CV screening** in two modes:

1. **Individual** — Upload one CV + job offer, get a full report in seconds.
2. **Batch** — Create an offer, upload multiple CVs, and the system processes them in the background with real-time polling from the frontend.

Each CV goes through a three-agent pipeline:
- **The Profiler** — Extracts an anonymous technical profile from the CV
- **The Tech Critic** — Compares profile vs. offer, assigns a match score and detects skill gaps
- **The Interviewer** — Generates 3 personalized technical validation questions

Results are exportable as CSV with ranking, scores and contact data per candidate.

---

## Tech Stack

| Component | Technology |
|---|---|
| Backend | Python 3.10+ · FastAPI |
| Frontend | Vanilla JS · Standalone HTML (no build tooling) |
| Local Inference | Ollama (`AsyncClient`) — asymmetric model assignment per agent |
| PDF Extraction | `markitdown[pdf]` |
| Validation | Pydantic v2 |
| ASGI Server | Uvicorn |
| Containerization | Docker · Docker Compose |

---

## Architecture: Asymmetric Local Model Orchestration

Each agent is assigned the most suitable model for its task — lightweight for extraction, reasoning-focused for evaluation, code-specialized for question generation. Communication between agents uses strict Pydantic schemas.

```
PDF CV ──────────────────────────────────────────────┐
                                                      ▼
                                           ┌─────────────────┐
                                           │  The Profiler   │  qwen2.5:3b
                                           │  (Extractor)    │  Anonymous technical profile
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
                                              (JSON / CSV export)
```

Batch mode adds a persistent session layer with async queue, background workers and real-time status polling.

---

## Project Structure

```
local-talent-screener/
├── main.py          ← FastAPI server · REST endpoints (individual + batch)
├── batch.py         ← Async batch engine: queue, workers, persistence
├── agents.py        ← Agent logic, prompts and Ollama clients for all 3 agents
├── schemas.py       ← Pydantic contracts between agents (source of truth)
├── storage.py       ← JSON disk persistence for batch sessions
├── utils.py         ← PDF text extraction
├── frontend.html    ← Standalone web UI (no build tooling)
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── tests/           ← Unit tests (pytest)
```

---

## Prerequisites

### 1. Ollama installed and running

```bash
curl -fsSL https://ollama.com/install.sh | sh

# Pull the models used by each agent
ollama pull qwen2.5:3b
ollama pull phi4-mini
ollama pull qwen2.5-coder:7b-instruct-q4_K_M

# Verify Ollama is running
ollama list
```

> Models are configured in `agents.py` and overridable via env vars (`OLLAMA_MODEL`, `OLLAMA_CRITIC_MODEL`, `OLLAMA_INTERVIEWER_MODEL`). The system is designed to run with small models (3B–7B) that fit on consumer GPUs.

### 2. Python 3.10+

```bash
python --version  # must be >= 3.10
```

---

## Docker (recommended)

```bash
git clone https://github.com/your-username/local-talent-screener
cd local-talent-screener
docker compose up -d

# Pull the models (the UI will show errors until models are ready)
docker exec -it ollama ollama pull qwen2.5:3b
docker exec -it ollama ollama pull phi4-mini
docker exec -it ollama ollama pull qwen2.5-coder:7b-instruct-q4_K_M

# Open http://localhost:8000
```

---

## Local Installation

```bash
git clone https://github.com/your-username/local-talent-screener
cd local-talent-screener

python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## Usage

### Start the server

```bash
python main.py
# or: uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Server at `http://localhost:8000`.

### Web UI

Open `http://localhost:8000/` in your browser. Two tabs:
- **Individual** — Analyze one CV against an offer
- **Offers** — Create offers, batch-upload CVs, monitor progress, export CSV

### REST API

#### Individual analysis
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
```

#### Batch — Export CSV
```bash
curl http://localhost:8000/api/v1/batch/sessions/abc123/export
```

### Interactive docs

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## Privacy & GDPR

- **Zero data exfiltration:** no data ever leaves your machine.
- **Active anonymization:** The Profiler strips personal identifiers before downstream agents process the profile.
- **Local persistence only:** batch results are saved in `data/offers/` as local JSON — never uploaded anywhere.
- **Full model control:** you decide which Ollama models to use and where they run.

---

## Configuration

Agent models are defined in `agents.py` and can be overridden via environment variables:

```bash
OLLAMA_MODEL=qwen2.5:7b \
OLLAMA_CRITIC_MODEL=phi4-mini \
OLLAMA_INTERVIEWER_MODEL=qwen2.5-coder:7b-instruct-q4_K_M \
python main.py
```

The asymmetric model assignment allows VRAM optimization: a lightweight 3B model handles extraction while a reasoning-focused model handles evaluation.

---

## Troubleshooting

| Symptom | Likely cause | Solution |
|---|---|---|
| `Connection refused` when calling Ollama | Ollama not running | `ollama serve` |
| `model not found` | Model not pulled | `ollama pull <model>` |
| `Could not extract text from PDF` | Scanned PDF without text layer | Use a selectable-text PDF |
| Slow response | Large model running on CPU | Switch to a smaller model variant |
| Workers crash on JSON save | watchfiles reload conflict | `reload_excludes` already configured in `main.py` |

---

## Roadmap

- [x] Batch mode: process multiple CVs against the same offer
- [x] Real-time polling from frontend
- [x] CSV export with ranking and scores
- [x] Session persistence (survives server restarts)
- [x] Env-variable model configuration
- [ ] DOCX CV support
- [ ] Selective re-processing of errored CVs
- [ ] Screenshot / demo GIF

---

---

## Español

# local-talent-screener

> Sistema Multi-Agente Local de Cribado de CVs con IA — **Privacy-First · 100% On-Premise · RGPD-Compliant**

Procesa CVs de forma masiva contra una oferta de empleo usando modelos locales vía [Ollama](https://ollama.com/). Tres agentes especializados colaboran para extraer el perfil técnico, puntuar el encaje y generar preguntas de validación — todo sin enviar datos fuera de tu máquina.

---

### ¿Qué hace?

Automatiza el **cribado técnico de CVs** en dos modos:

1. **Individual** — Sube un CV + oferta, obtén informe completo en segundos.
2. **Batch** — Crea una oferta, sube múltiples CVs y el sistema los procesa en segundo plano con polling en tiempo real desde el frontend.

Los resultados son exportables como CSV con ranking, puntuaciones y datos de contacto por candidato.

---

### Stack Tecnológico

| Componente | Tecnología |
|---|---|
| Backend | Python 3.10+ · FastAPI |
| Frontend | Vanilla JS · HTML standalone (sin build tooling) |
| Inferencia local | Ollama (`AsyncClient`) — modelos asimétricos por agente |
| Extracción PDF | `markitdown[pdf]` |
| Validación | Pydantic v2 |
| Servidor ASGI | Uvicorn |
| Contenedores | Docker · Docker Compose |

---

### Pipeline de Agentes

```
The Profiler  →  qwen2.5:3b           Extrae perfil técnico anónimo
The Tech Critic  →  phi4-mini         Evalúa encaje y detecta gaps
The Interviewer  →  qwen2.5-coder:7b  Genera 3 preguntas de validación
```

---

### Instalación

```bash
git clone https://github.com/your-username/local-talent-screener
cd local-talent-screener

python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

ollama pull qwen2.5:3b
ollama pull phi4-mini
ollama pull qwen2.5-coder:7b-instruct-q4_K_M
```

### Uso

```bash
python main.py
# Abre http://localhost:8000
```

---

### Privacidad y RGPD

- **Zero data exfiltration:** ningún dato sale de tu máquina.
- **Anonimización activa:** The Profiler elimina datos personales antes de que los agentes posteriores procesen el perfil.
- **Persistencia local:** los resultados batch se guardan en `data/offers/` como JSON local — nunca se suben a ningún servidor.
- **Control total de modelos:** tú decides qué modelos de Ollama usar y dónde se ejecutan.
