# Bilingual (Arabic/English) Methodology Agent

A local, Docker-based, open-source AI agent that converts unstructured bilingual
business discussion into structured statistical methodology knowledge.

The agent:

- understands Arabic, English, and Arabic/English code switching;
- extracts structured methodology requirements, definitions, data sources,
  constraints, and decisions;
- identifies missing methodology information (gaps);
- generates precise, non-leading, English methodology questions;
- separates inference from confirmed fact;
- never finalizes methodology without human approval.

## Architecture

```
User / Developer
      │
      ▼
Methodology Agent API  (FastAPI, app/)
      │
      ├──────────────►  Methodology Engine  (custom Python)
      │                        │
      │                        ├── Structured Methodology State
      │                        ├── Gap Detector
      │                        └── Question Generator
      │
      ▼
LLM Service  (llama.cpp, OpenAI-compatible)
      │
      ▼
Qwen3-4B-Instruct-2507  (Q4_K_M GGUF)
```

The LLM is a **reasoning component** of the agent, not the agent itself. The
agent consists of the LLM plus structured state, methodology rules, terminology,
gap detection, question prioritization, validation, and human approval.

## Prerequisites

- Docker Desktop (WSL2 backend recommended on Windows)
- NVIDIA GPU passthrough into Docker
- ~2.5 GB free disk for the model, plus Docker images

## Quick Start

1. Verify GPU access:

   ```powershell
   docker run --rm --gpus all nvidia/cuda:12.8.1-base-ubuntu24.04 nvidia-smi
   ```

2. Download the model:

   ```powershell
   py -m pip install -U huggingface_hub
   huggingface-cli download `
     unsloth/Qwen3-4B-Instruct-2507-GGUF `
     Qwen3-4B-Instruct-2507-Q4_K_M.gguf `
     --local-dir .\models
   ```

3. Build and start:

   ```powershell
   docker compose build
   docker compose up -d
   docker compose ps
   ```

4. Verify:

   ```powershell
   curl.exe http://127.0.0.1:8000/health
   curl.exe http://127.0.0.1:8080/health
   ```

5. Analyze a bilingual discussion:

   ```powershell
   $body = @{
       text = "نريد مؤشر شهري عن المنشآت النشطة. البيانات من السجل التجاري، لكن تعريف المنشأة النشطة غير متفق عليه."
       language = "ar"
   } | ConvertTo-Json

   Invoke-RestMethod `
       -Uri http://127.0.0.1:8000/analyze `
       -Method POST `
       -ContentType "application/json" `
       -Body $body
   ```

## API

| Method | Endpoint             | Description                                   |
| ------ | -------------------- | --------------------------------------------- |
| GET    | `/health`            | API + LLM health status                       |
| POST   | `/analyze`           | Full pipeline: extract + state + gap + question |
| POST   | `/extract`           | Structured methodology extraction             |
| POST   | `/question`          | Gap detection + question generation           |
| POST   | `/methodology-state` | Current structured methodology state          |

All endpoints return JSON. Methodology questions are always produced in English.

## Configuration

Configuration is read from environment variables (see `.env.example`):

| Variable               | Default                  |
| ---------------------- | ------------------------ |
| `LLM_BASE_URL`         | `http://llm:8080/v1`     |
| `LLM_MODEL`            | `qwen3-4b-instruct-2507` |
| `LLM_TIMEOUT_SECONDS`  | `120`                    |
| `LLM_TEMPERATURE`      | `0.1`                    |
| `LLM_MAX_TOKENS`       | `700`                    |

The default is fully local: no cloud AI provider and no API keys are required.

## Testing

Unit tests mock the LLM and require no GPU, Docker, or internet:

```powershell
py -m pytest -q
```

## Project Layout

```
methodology-agent/
├── app/
│   ├── main.py
│   ├── api/          # FastAPI routes + health
│   ├── agent/        # methodology engine (extractor, gap detector, ...)
│   ├── llm/          # OpenAI-compatible LLM client
│   ├── models/       # Pydantic models
│   └── core/         # config + logging
├── prompts/          # human-readable prompt references
├── tests/            # unit tests + bilingual fixtures
├── scripts/          # download / benchmark / healthcheck helpers
├── models/           # GGUF model (not committed)
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

## License

See [LICENSE](LICENSE). The application is Apache-2.0. The Qwen3 model is
Apache-2.0. Review the license of every dependency before organizational
deployment.
