# Bilingual (Arabic/English) Methodology Agent

## Open-Source, Docker-Based Local AI Implementation Guide

**Document purpose:** Self-contained implementation specification for an LLM coding agent or developer.

**Target environment:** Developer laptop with NVIDIA RTX GPU, approximately 4 GB dedicated VRAM, Docker already installed.

**Primary objective:** Build a locally hosted, bilingual **Arabic/English Statistical Methodology Agent** that can understand methodology discussions, identify missing methodological information, ask targeted questions, extract structured requirements, and produce auditable methodology outputs.

---

# 1. Executive Summary

Build a small, local, open-source AI agent with the following architecture:

```text
                    User / Developer
                           │
                           ▼
                  Methodology Agent API
                           │
             ┌─────────────┴─────────────┐
             │                           │
             ▼                           ▼
       Methodology Engine           LLM Service
       Custom Python               llama.cpp
             │                           │
             │                    Qwen3-4B-Instruct
             │                    2507 / Q4 quantized
             │
             ├──────────────┐
             │              │
             ▼              ▼
       Structured       Knowledge /
       Methodology       Retrieval
         State
```

The first implementation should **not** attempt to build the complete meeting/video platform.

The immediate objective is to establish a reliable bilingual methodology reasoning engine.

The system should subsequently be capable of being integrated into:

* Jitsi Meet
* a corporate meeting platform
* a methodology workflow platform
* document-generation agents
* statistical data agents
* indicator-development agents
* a shared methodology knowledge base.

---

# 2. Important Hardware Assumption

The development laptop has approximately:

```text
GPU: NVIDIA RTX 500 Ada Generation Laptop GPU
Dedicated VRAM: 4 GB
Shared GPU memory: approximately 8 GB
```

Treat the machine as a **4 GB VRAM GPU**.

Do **not** treat the Windows-reported 12 GB "GPU memory" as 12 GB of dedicated VRAM.

The 8 GB shared memory is system RAM and is substantially slower than dedicated VRAM.

The previously reported "RTF 0.211" is not sufficient by itself to determine model capacity. The benchmark should be treated as an unknown external performance result until the actual benchmark definition is identified.

## Design consequence

The agent must be:

> **GPU-accelerated but GPU-optional.**

The same application must eventually be capable of running:

```text
Development laptop:
Small quantized LLM + GPU

Corporate CPU-only VDI:
Small CPU LLM

Future enterprise GPU server:
Larger GPU LLM
```

The application must not contain GPU-specific business logic.

---

# 3. Primary Model Recommendation

## Primary LLM

Use:

**Qwen3-4B-Instruct-2507**

Repository:

`Qwen/Qwen3-4B-Instruct-2507`

The model is Apache 2.0 licensed and is an instruction-tuned 4B-parameter Qwen3 model.

Qwen3 provides multilingual support including Arabic and multiple Arabic variants. The Qwen3 model documentation lists Arabic language coverage, including `ara`, `ars`, `apc`, `arz`, `ary`, `acm`, `acq`, and `aeb`.

## Why Qwen3-4B-Instruct-2507?

It is selected because it provides a strong balance between:

* multilingual capability;
* Arabic support;
* English support;
* instruction following;
* structured output;
* reasoning capability;
* relatively small model size;
* Apache 2.0 licensing;
* local deployment feasibility.

The official Qwen model repository identifies the model as Apache 2.0 licensed.

---

# 4. Quantization Strategy

The laptop has only approximately 4 GB of dedicated VRAM.

Therefore, **do not initially run the model in FP16/BF16**.

Use a GGUF quantized version.

A suitable starting point is:

```text
Qwen3-4B-Instruct-2507-Q4_K_M.gguf
```

The Unsloth GGUF repository provides Q4_K_M and several other quantization levels; its Q4_K_M file is approximately 2.5 GB.

The model's underlying license is Apache 2.0. Verify the model card and license before any production redistribution.

## Recommended test order

```text
Q4_K_M
   ↓
Q4_K_S
   ↓
Q3_K_M
```

Start with Q4_K_M.

If VRAM pressure is excessive:

```text
Q4_K_M → Q4_K_S → Q3_K_M
```

Do not immediately sacrifice model quality for maximum speed.

---

# 5. Alternative Models

The coding agent should keep the model backend configurable.

Possible alternatives include:

| Model                  | Approx. Size | Intended Role                | License / Status                          |
| ---------------------- | -----------: | ---------------------------- | ----------------------------------------- |
| Qwen3-4B-Instruct-2507 |           4B | **Primary**                  | Apache 2.0                                |
| Qwen3-0.6B             |         0.6B | Very lightweight fallback    | Verify current model license              |
| Qwen3-1.7B             |         1.7B | Lightweight fallback         | Verify current model license              |
| Qwen3-8B               |           8B | Future higher-quality server | Apache 2.0; not recommended for 4 GB VRAM |
| Qwen3-30B-A3B          |          MoE | Future enterprise GPU        | Apache 2.0; not laptop target             |

The vLLM model list currently includes Qwen3 models and Qwen3 ASR models, demonstrating current ecosystem support.

The primary laptop implementation should remain **Qwen3-4B-Instruct-2507 Q4**.

---

# 6. LLM Runtime Recommendation

## Primary runtime: llama.cpp

Use:

**llama.cpp**

Why:

* open source;
* lightweight;
* excellent support for GGUF;
* efficient quantized inference;
* CPU fallback;
* NVIDIA CUDA support;
* OpenAI-compatible HTTP server;
* suitable for low-VRAM machines;
* easy Docker deployment.

The official llama.cpp Docker documentation provides server images and CUDA-enabled deployment using `--gpus all` and GPU-layer offloading.

## Why not make vLLM the first runtime?

vLLM is an excellent future server runtime and provides official Docker images and an OpenAI-compatible API.

However, for a laptop with only 4 GB dedicated VRAM, llama.cpp + GGUF gives us finer control over:

```text
quantization
GPU layers
context size
CPU/GPU split
memory consumption
```

Therefore:

```text
Laptop development:
llama.cpp

Future GPU server:
vLLM or llama.cpp
```

The application must communicate with either through an OpenAI-compatible interface.

---

# 7. Open-Source Technology Stack

| Component                   | Technology             | License / Notes                                                                |
| --------------------------- | ---------------------- | ------------------------------------------------------------------------------ |
| LLM                         | Qwen3-4B-Instruct-2507 | Apache 2.0                                                                     |
| Quantization                | GGUF                   | Model/runtime format                                                           |
| LLM runtime                 | llama.cpp              | MIT                                                                            |
| API                         | FastAPI                | MIT                                                                            |
| Python                      | CPython                | PSF License                                                                    |
| HTTP client                 | httpx                  | BSD-3-Clause                                                                   |
| Validation                  | Pydantic               | MIT                                                                            |
| Configuration               | pydantic-settings      | MIT                                                                            |
| ASR, future                 | faster-whisper         | MIT                                                                            |
| Embeddings, future          | sentence-transformers  | Apache 2.0                                                                     |
| Vector database, future     | Qdrant                 | Apache 2.0                                                                     |
| Relational database, future | PostgreSQL             | PostgreSQL License                                                             |
| Frontend, future            | React                  | MIT                                                                            |
| Frontend language           | TypeScript             | Apache 2.0                                                                     |
| Containerization            | Docker                 | Open-source components; verify Docker Desktop licensing for organizational use |
| Orchestration               | Docker Compose         | Open-source specification/tooling                                              |

The faster-whisper project is MIT licensed.

---

# 8. Architectural Principle

Do **not** build the methodology agent as a generic chatbot.

The agent is a:

> **Structured methodology reasoning system.**

Its job is to transform unstructured bilingual business discussion into structured statistical methodology knowledge.

---

# 9. High-Level Agent Architecture

```text
                 Arabic / English Input
                         │
                         ▼
                 Language Detection
                         │
                         ▼
              Bilingual Normalization
                         │
                         ▼
               Methodology Interpreter
                         │
              ┌──────────┼──────────┐
              │          │          │
              ▼          ▼          ▼
          Requirement  Definition  Constraint
              │          │          │
              └──────────┼──────────┘
                         ▼
                 Methodology State
                         │
                         ▼
                   Gap Detector
                         │
                         ▼
                 Question Generator
                         │
                         ▼
                  Human Approval
                         │
                         ▼
                  Final Knowledge
```

---

# 10. Bilingual Processing Strategy

Do **not** force:

```text
Arabic
 ↓
English translation
 ↓
LLM
```

as the main architecture.

Instead:

```text
Arabic / English / Mixed
          │
          ▼
     LLM understanding
          │
          ▼
Canonical methodology concepts
          │
          ▼
English structured representation
```

The LLM should be allowed to understand Arabic directly.

For example:

```text
Arabic:

نريد نطلع مؤشر شهري عن المنشآت النشطة.
```

The system should derive:

```json
{
  "concept": "indicator",
  "value": "Active establishments",
  "frequency": "monthly",
  "language": "ar"
}
```

Then:

```text
Arabic discussion
        ↓
English canonical methodology representation
        ↓
English AI question
```

---

# 11. Language Policy

The system should support:

```text
Input:
Arabic
English
Arabic-English mixed
English-Arabic mixed
```

Default output:

```text
English
```

The system should also retain:

```text
original_input
normalized_interpretation
canonical_concept
```

Example:

```json
{
  "original_input": "نريد نطلع مؤشر شهري عن المنشآت النشطة",
  "language": "ar",
  "normalized_interpretation": "The business team wants a monthly indicator for active establishments.",
  "canonical_concept": "active_establishment_indicator"
}
```

---

# 12. Methodology State

The agent must maintain a structured state.

Create:

```text
app/models/methodology_state.py
```

with the following logical structure:

```json
{
  "objective": {
    "value": null,
    "status": "unknown",
    "confidence": 0.0
  },
  "target_population": {
    "value": null,
    "status": "unknown",
    "confidence": 0.0
  },
  "statistical_unit": {
    "value": null,
    "status": "unknown",
    "confidence": 0.0
  },
  "reference_period": {
    "value": null,
    "status": "unknown",
    "confidence": 0.0
  },
  "frequency": {
    "value": null,
    "status": "unknown",
    "confidence": 0.0
  },
  "geographic_scope": {
    "value": null,
    "status": "unknown",
    "confidence": 0.0
  },
  "indicators": [],
  "dimensions": [],
  "data_sources": [],
  "definitions": [],
  "business_rules": [],
  "quality_rules": [],
  "constraints": [],
  "decisions": [],
  "open_questions": []
}
```

Possible status values:

```text
unknown
inferred
proposed
confirmed
rejected
conflicting
```

---

# 13. Critical Principle: Inference Is Not Fact

The agent must distinguish:

```text
OBSERVED
INFERRED
ASSUMED
PROPOSED
CONFIRMED
REJECTED
```

For example:

```text
Business says:

"We normally consider companies active if they filed something."

```

The system must NOT automatically record:

```text
Active = companies that filed something
```

as confirmed methodology.

Instead:

```json
{
  "statement": "An establishment may be considered active based on filing activity.",
  "status": "inferred",
  "confidence": 0.74
}
```

The agent should then ask:

> "Should filing activity be the formal criterion for defining an active establishment?"

---

# 14. Question Generation

The agent's most important capability is identifying missing methodology information.

Example:

```text
Business:

"We want a monthly active establishment indicator."
```

The agent should detect missing:

```text
Definition of active
Reference population
Statistical unit
Reference date
Data source
```

It should prioritize the most important gap.

Output:

```json
{
  "question": "How should an establishment be defined as active?",
  "reason": "The definition is required to determine which establishments are included in the indicator.",
  "priority": 0.96,
  "domain": "definition"
}
```

---

# 15. Question Rules

Questions should be:

* concise;
* specific;
* non-leading;
* methodology-relevant;
* written in English;
* based on an identified gap;
* not repetitive;
* not asked if already resolved.

Bad:

```text
Can you tell us more about the indicator?
```

Good:

```text
What reference period should be used to determine whether an establishment is active?
```

---

# 16. Question Priority

Calculate priority conceptually as:

```text
priority =
    methodology_impact
  × uncertainty
  × downstream_dependency
  × confidence_gap
```

The implementation can use a deterministic scoring function before invoking the LLM.

This reduces unnecessary LLM calls.

---

# 17. Agent Pipeline

Implement:

```text
Input
 ↓
Context preparation
 ↓
LLM extraction
 ↓
Structured JSON validation
 ↓
Methodology state update
 ↓
Gap detection
 ↓
Question ranking
 ↓
Question generation
 ↓
Human review
```

Do not allow the LLM to directly mutate persistent state.

Instead:

```text
LLM
 ↓
proposed structured changes
 ↓
Pydantic validation
 ↓
business-rule validation
 ↓
state update
```

---

# 18. Suggested Python Project Structure

Create:

```text
methodology-agent/
│
├── README.md
├── LICENSE
├── .gitignore
├── .env.example
├── docker-compose.yml
│
├── app/
│   ├── __init__.py
│   ├── main.py
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes.py
│   │   └── health.py
│   │
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── methodology_agent.py
│   │   ├── prompts.py
│   │   ├── extractor.py
│   │   ├── gap_detector.py
│   │   ├── question_generator.py
│   │   └── state_manager.py
│   │
│   ├── llm/
│   │   ├── __init__.py
│   │   └── client.py
│   │
│   ├── models/
│   │   ├── methodology.py
│   │   ├── question.py
│   │   └── extraction.py
│   │
│   └── core/
│       ├── config.py
│       └── logging.py
│
├── prompts/
│   ├── system.md
│   ├── extraction.md
│   ├── question_generation.md
│   └── knowledge_consolidation.md
│
├── models/
│   └── Qwen3-4B-Instruct-2507-Q4_K_M.gguf
│
├── tests/
│   ├── test_extraction.py
│   ├── test_questions.py
│   ├── test_bilingual.py
│   └── fixtures/
│       ├── arabic.json
│       ├── english.json
│       └── mixed.json
│
└── scripts/
    ├── download_model.ps1
    ├── benchmark.ps1
    └── healthcheck.ps1
```

---

# 19. Create the Project

PowerShell:

```powershell
mkdir methodology-agent
cd methodology-agent

mkdir app
mkdir app\api
mkdir app\agent
mkdir app\llm
mkdir app\models
mkdir app\core
mkdir prompts
mkdir models
mkdir tests
mkdir tests\fixtures
mkdir scripts
```

---

# 20. Docker Compose

Create:

```text
docker-compose.yml
```

Use:

```yaml
name: methodology-agent

services:

  llm:
    image: ghcr.io/ggml-org/llama.cpp:server-cuda
    container_name: methodology-llm
    restart: unless-stopped

    command:
      - -m
      - /models/Qwen3-4B-Instruct-2507-Q4_K_M.gguf
      - --host
      - 0.0.0.0
      - --port
      - "8080"
      - -c
      - "2048"
      - -ngl
      - "999"
      - --jinja

    volumes:
      - ./models:/models:ro

    ports:
      - "127.0.0.1:8080:8080"

    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

    healthcheck:
      test:
        [
          "CMD-SHELL",
          "curl -fsS http://localhost:8080/health || exit 1"
        ]
      interval: 10s
      timeout: 5s
      retries: 20
      start_period: 60s

  api:
    build:
      context: .
      dockerfile: Dockerfile

    container_name: methodology-api

    restart: unless-stopped

    environment:
      LLM_BASE_URL: http://llm:8080/v1
      LLM_MODEL: qwen3-4b-instruct-2507
      LLM_TIMEOUT_SECONDS: "120"

    ports:
      - "127.0.0.1:8000:8000"

    depends_on:
      llm:
        condition: service_healthy
```

The llama.cpp project documents the CUDA server image and GPU-layer offloading with `--gpus all` / CUDA-enabled execution.

---

# 21. Important Docker Note for Windows

If Docker Desktop is being used with WSL2, first verify that Docker can access the NVIDIA GPU.

Run:

```powershell
docker run --rm --gpus all nvidia/cuda:12.8.1-base-ubuntu24.04 nvidia-smi
```

If this successfully displays your NVIDIA GPU, GPU passthrough is working.

If it fails, **do not continue with the LLM container**.

Fix Docker Desktop / WSL2 GPU access first.

Do not randomly install a Linux NVIDIA driver inside WSL2.

---

# 22. Download the Model

Use the Unsloth GGUF repository:

```text
unsloth/Qwen3-4B-Instruct-2507-GGUF
```

The repository provides multiple quantizations, including:

```text
Q4_K_M
Q4_K_S
Q3_K_M
Q5_K_M
Q6_K
Q8_0
```

and identifies the model as Apache 2.0.

### Option A — Download through Hugging Face CLI

Install:

```powershell
py -m pip install -U huggingface_hub
```

Then:

```powershell
huggingface-cli download `
  unsloth/Qwen3-4B-Instruct-2507-GGUF `
  Qwen3-4B-Instruct-2507-Q4_K_M.gguf `
  --local-dir .\models
```

Verify:

```powershell
Get-ChildItem .\models
```

Expected:

```text
Qwen3-4B-Instruct-2507-Q4_K_M.gguf
```

---

# 23. Start the LLM

Run:

```powershell
docker compose up -d llm
```

Check:

```powershell
docker compose ps
```

Then:

```powershell
docker compose logs -f llm
```

Look for evidence that:

```text
CUDA backend loaded
GPU detected
model loaded
server listening on 0.0.0.0:8080
```

Do not proceed until the model successfully loads.

---

# 24. Verify LLM API

Run:

```powershell
curl.exe http://127.0.0.1:8080/health
```

Expected:

```text
OK
```

Then:

```powershell
curl.exe http://127.0.0.1:8080/v1/models
```

The exact model identifier returned by llama.cpp may differ from the filename.

Use the returned identifier when testing chat completions.

---

# 25. Test English

Run:

```powershell
curl.exe -X POST `
  http://127.0.0.1:8080/v1/chat/completions `
  -H "Content-Type: application/json" `
  -d '{"messages":[{"role":"user","content":"What is a statistical unit?"}],"max_tokens":100}'
```

Expected behavior:

* coherent answer;
* no external API call;
* response generated locally.

---

# 26. Test Arabic

Run:

```powershell
curl.exe -X POST `
  http://127.0.0.1:8080/v1/chat/completions `
  -H "Content-Type: application/json" `
  -d '{"messages":[{"role":"user","content":"ما هي الوحدة الإحصائية؟"}],"max_tokens":100}'
```

The answer may be Arabic or multilingual depending on prompt.

---

# 27. Test Arabic-to-English Methodology Reasoning

Use:

```powershell
curl.exe -X POST `
  http://127.0.0.1:8080/v1/chat/completions `
  -H "Content-Type: application/json" `
  -d '{"messages":[{"role":"system","content":"You are a statistical methodology elicitation agent. Understand Arabic and English. Always formulate methodology questions in English."},{"role":"user","content":"نريد نطلع مؤشر شهري عن المنشآت النشطة. البيانات من السجل التجاري، لكن تعريف المنشأة النشطة غير متفق عليه."}],"max_tokens":250}'
```

The desired behavior is approximately:

```text
The business team wants a monthly indicator
for active establishments.

Missing methodological element:
Definition of active establishment.

Recommended question:
How should an establishment be defined as active?
```

The exact wording may differ.

---

# 28. Build the FastAPI Application

Create:

```text
app/main.py
```

Use:

```python
from fastapi import FastAPI
from pydantic import BaseModel

from app.llm.client import LLMClient
from app.agent.methodology_agent import MethodologyAgent

app = FastAPI(
    title="Bilingual Methodology Agent",
    version="0.1.0",
)

llm_client = LLMClient()
agent = MethodologyAgent(llm_client)


class AnalyzeRequest(BaseModel):
    text: str
    language: str | None = None


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


@app.post("/analyze")
def analyze(request: AnalyzeRequest):
    return agent.analyze(
        text=request.text,
        language=request.language,
    )
```

---

# 29. LLM Client

Create:

```text
app/llm/client.py
```

Use:

```python
import os
import httpx


class LLMClient:

    def __init__(self):
        self.base_url = os.getenv(
            "LLM_BASE_URL",
            "http://llm:8080/v1"
        )

        self.model = os.getenv(
            "LLM_MODEL",
            "qwen3-4b-instruct-2507"
        )

        self.timeout = float(
            os.getenv(
                "LLM_TIMEOUT_SECONDS",
                "120"
            )
        )

    def chat(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 512,
    ):

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
            "temperature": 0.1,
            "max_tokens": max_tokens,
        }

        with httpx.Client(
            timeout=self.timeout
        ) as client:

            response = client.post(
                f"{self.base_url}/chat/completions",
                json=payload,
            )

            response.raise_for_status()

            data = response.json()

        return data["choices"][0]["message"]["content"]
```

---

# 30. Pydantic Data Models

Create:

```text
app/models/extraction.py
```

```python
from typing import Literal
from pydantic import BaseModel, Field


class Evidence(BaseModel):

    text: str

    language: str

    status: Literal[
        "observed",
        "inferred",
        "proposed",
        "confirmed",
        "rejected"
    ]

    confidence: float = Field(
        ge=0.0,
        le=1.0
    )


class Requirement(BaseModel):

    concept: str

    value: str | None = None

    domain: str

    status: Literal[
        "unknown",
        "inferred",
        "proposed",
        "confirmed",
        "rejected",
        "conflicting"
    ]

    confidence: float = Field(
        ge=0.0,
        le=1.0
    )

    evidence: list[Evidence] = []
```

---

# 31. Question Model

Create:

```text
app/models/question.py
```

```python
from pydantic import BaseModel, Field


class MethodologyQuestion(BaseModel):

    question: str

    domain: str

    reason: str

    priority: float = Field(
        ge=0.0,
        le=1.0
    )

    status: str = "candidate"
```

---

# 32. Methodology Agent

Create:

```text
app/agent/methodology_agent.py
```

```python
import json

from app.llm.client import LLMClient


SYSTEM_PROMPT = """
You are a Statistical Methodology Elicitation Agent.

Your purpose is to help a statistical methodology team convert
business discussions into a well-defined statistical methodology.

You understand:
- Arabic
- English
- Arabic-English code switching
- statistical terminology
- business terminology

Input may be Arabic, English, or mixed.

You must reason directly from the input.

Do not treat an inference as a confirmed fact.

Classify information as:
- observed
- inferred
- proposed
- confirmed
- rejected

Identify:
1. Requirements
2. Definitions
3. Statistical units
4. Populations
5. Reference periods
6. Frequencies
7. Geographic scope
8. Indicators
9. Dimensions
10. Data sources
11. Business rules
12. Quality requirements
13. Constraints
14. Decisions
15. Missing information

If important information is missing, propose ONE highest-priority
methodology question.

All methodology questions must be written in English.

Return valid JSON only.
"""


class MethodologyAgent:

    def __init__(self, llm: LLMClient):
        self.llm = llm

    def analyze(
        self,
        text: str,
        language: str | None = None,
    ):

        prompt = f"""
Analyze the following business discussion.

Language:
{language or "auto-detect"}

Discussion:
{text}

Return JSON using this structure:

{{
  "language": "...",
  "summary": "...",
  "requirements": [],
  "definitions": [],
  "data_sources": [],
  "decisions": [],
  "constraints": [],
  "open_questions": [],
  "recommended_question": {{
      "question": "...",
      "reason": "...",
      "domain": "...",
      "priority": 0.0
  }}
}}
"""

        result = self.llm.chat(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=prompt,
            max_tokens=700,
        )

        try:
            return json.loads(result)

        except json.JSONDecodeError:

            return {
                "raw_response": result,
                "parse_error": True,
            }
```

---

# 33. Dockerfile

Create:

```text
Dockerfile
```

Use:

```dockerfile
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN useradd \
    --create-home \
    --uid 10001 \
    appuser

COPY requirements.txt .

RUN pip install \
    --no-cache-dir \
    -r requirements.txt

COPY app ./app

USER appuser

EXPOSE 8000

CMD [
    "uvicorn",
    "app.main:app",
    "--host",
    "0.0.0.0",
    "--port",
    "8000"
]
```

---

# 34. Python Dependencies

Create:

```text
requirements.txt
```

Use:

```text
fastapi
uvicorn[standard]
httpx
pydantic
pydantic-settings
```

For the first version, do not install LangChain or LlamaIndex.

---

# 35. Why Custom Agent Code Instead of LangChain?

The first version should use:

```text
FastAPI
+
Pydantic
+
custom methodology engine
+
OpenAI-compatible LLM client
```

rather than introducing a large orchestration framework.

Reasons:

* fewer dependencies;
* easier debugging;
* clearer methodology logic;
* better control of structured outputs;
* easier security review;
* easier migration between llama.cpp and vLLM;
* easier future integration with SCAD systems.

A framework can be introduced later if workflow complexity justifies it.

---

# 36. Build the API

Run:

```powershell
docker compose build api
```

Then:

```powershell
docker compose up -d
```

Check:

```powershell
docker compose ps
```

Expected:

```text
methodology-llm
methodology-api
```

---

# 37. Test API Health

```powershell
curl.exe http://127.0.0.1:8000/health
```

Expected:

```json
{
  "status": "healthy"
}
```

---

# 38. Test the Methodology Agent

PowerShell:

```powershell
$body = @{
    text = "نريد نطلع مؤشر شهري عن المنشآت النشطة. البيانات من السجل التجاري، لكن تعريف المنشأة النشطة غير متفق عليه."
    language = "ar"
} | ConvertTo-Json

Invoke-RestMethod `
    -Uri http://127.0.0.1:8000/analyze `
    -Method POST `
    -ContentType "application/json" `
    -Body $body
```

The response should identify:

```text
Indicator:
Active establishments

Frequency:
Monthly

Data source:
Business Register

Missing:
Definition of active establishment

Recommended question:
How should an establishment be defined as active?
```

---

# 39. Bilingual Test Cases

Create at least these test cases.

## Test 1 — Arabic

```text
نريد مؤشر شهري للمنشآت النشطة.
```

Expected:

```text
indicator = active establishments
frequency = monthly
```

---

## Test 2 — English

```text
We need a monthly indicator of active establishments.
```

Expected equivalent state.

---

## Test 3 — Mixed

```text
نريد نطلع monthly indicator عن active establishments.
```

Expected:

```text
indicator = active establishments
frequency = monthly
```

---

## Test 4 — Missing definition

```text
نريد نحسب active establishments لكن ما اتفقنا على definition.
```

Expected question:

```text
How should an establishment be defined as active?
```

---

## Test 5 — Reference period

```text
The indicator should be monthly, but we have not decided
which date determines whether the establishment is active.
```

Expected question:

```text
What reference date should be used to determine whether
an establishment is active?
```

---

## Test 6 — Data source

```text
البيانات من السجل التجاري، لكن ما نعرف إذا يتم تحديثها يومياً أو شهرياً.
```

Expected question:

```text
How frequently is the Business Register updated?
```

---

# 40. Prompt Engineering Rules

The system prompt should enforce:

```text
1. Never invent facts.
2. Preserve uncertainty.
3. Separate inference from confirmation.
4. Never silently resolve contradictions.
5. Prefer structured extraction.
6. Ask only methodology-relevant questions.
7. Do not repeat already answered questions.
8. Questions are always in English.
9. Preserve original Arabic evidence.
10. Use canonical English concepts.
```

---

# 41. Canonical Methodology Vocabulary

Create:

```text
app/agent/terminology.py
```

Start with:

```python
TERMINOLOGY = {

    "منشأة": "establishment",

    "المنشآت": "establishments",

    "مؤشر": "indicator",

    "مؤشر شهري": "monthly indicator",

    "السجل التجاري": "business register",

    "الوحدة الإحصائية": "statistical unit",

    "السكان المستهدفون": "target population",

    "الفترة المرجعية": "reference period",

    "التكرار": "frequency",

    "المصدر": "data source",

    "التعريف": "definition",

    "النطاق الجغرافي": "geographic scope",
}
```

This dictionary must grow based on actual SCAD terminology.

---

# 42. Terminology Normalization

The LLM should not be forced to use literal translations.

For example:

```text
المنشأة
```

could map to:

```text
establishment
```

while:

```text
الوحدة الإحصائية
```

maps to:

```text
statistical unit
```

The canonical concept should be used consistently throughout downstream methodology documents.

---

# 43. Future Speech Layer

Do not implement speech recognition in the first MVP unless required immediately.

When added, use:

**faster-whisper**

The project is MIT licensed.

Architecture:

```text
Audio
  ↓
VAD
  ↓
faster-whisper
  ↓
Arabic / English transcript
  ↓
Methodology Agent
```

For the meeting platform, the speech layer should eventually support:

* Arabic;
* English;
* code switching;
* timestamps;
* speaker identification;
* confidence scores;
* partial transcription;
* final transcription.

---

# 44. Future Speech Model Strategy

Start benchmarking:

```text
Whisper Small
Whisper Medium
```

before considering larger models.

Measure:

```text
Arabic accuracy
English accuracy
Mixed-language accuracy
Processing speed
GPU memory
CPU memory
```

Do not select an ASR model solely based on English benchmark performance.

The critical benchmark is **Arabic business terminology and code switching**.

---

# 45. Methodology Agent API

The initial API should expose:

```text
GET  /health

POST /analyze

POST /extract

POST /question

POST /methodology-state
```

Future API:

```text
POST /meetings
POST /meetings/{id}/transcript
GET  /meetings/{id}/state
POST /meetings/{id}/question
POST /meetings/{id}/approve
POST /knowledge/candidate
POST /knowledge/{id}/approve
GET  /knowledge/search
```

---

# 46. Structured Extraction API

The `/extract` endpoint should eventually return:

```json
{
  "requirements": [],
  "definitions": [],
  "statistical_units": [],
  "populations": [],
  "reference_periods": [],
  "frequencies": [],
  "geographic_scopes": [],
  "indicators": [],
  "dimensions": [],
  "data_sources": [],
  "business_rules": [],
  "quality_rules": [],
  "constraints": [],
  "decisions": [],
  "open_questions": []
}
```

---

# 47. Human-in-the-Loop

The agent must never independently finalize methodology.

Correct:

```text
AI proposes
    ↓
Human reviews
    ↓
Human modifies if necessary
    ↓
Human approves
    ↓
Knowledge becomes authoritative
```

Incorrect:

```text
AI inference
    ↓
Automatically becomes methodology
```

---

# 48. Knowledge Lifecycle

Use:

```text
Captured
   ↓
Extracted
   ↓
Normalized
   ↓
Candidate
   ↓
Human Validated
   ↓
Approved
   ↓
Published
   ↓
Reusable
```

Every approved knowledge item must have provenance.

Example:

```json
{
  "knowledge_id": "K-000001",
  "concept": "active_establishment",
  "statement": "...",
  "status": "approved",
  "source": "meeting",
  "evidence": "SEG-000102",
  "validated_by": "user",
  "effective_from": null
}
```

---

# 49. Knowledge Precedence

When knowledge conflicts, use:

```text
Approved Methodology
        >
Approved Organizational Standard
        >
Validated Business Requirement
        >
Meeting-derived Knowledge
        >
AI Inference
        >
AI Hypothesis
```

Never silently overwrite conflicting knowledge.

---

# 50. Future RAG Layer

After the core agent works, add:

```text
PostgreSQL
+
Qdrant
+
Embedding Model
```

Architecture:

```text
Question
   ↓
Embedding
   ↓
Qdrant
   ↓
Relevant methodology knowledge
   ↓
LLM
   ↓
Context-aware answer/question
```

Do not introduce RAG before the basic methodology reasoning works.

---

# 51. Future Embedding Model

Use an open multilingual embedding model suitable for Arabic and English.

The model should be evaluated on:

```text
Arabic → English semantic similarity
English → Arabic semantic similarity
Methodology terminology
Business terminology
SCAD terminology
```

Do not select an embedding model solely from generic MTEB rankings.

Create an internal benchmark dataset.

---

# 52. Benchmark Dataset

Create:

```text
tests/fixtures/
```

with at least:

```text
arabic.json
english.json
mixed.json
```

Each record:

```json
{
  "input": "...",
  "expected_concepts": [],
  "expected_missing_information": [],
  "expected_question": "..."
}
```

Target:

```text
50 Arabic cases
50 English cases
50 mixed cases
```

for the first meaningful evaluation.

---

# 53. Evaluation Metrics

Measure:

### Extraction

```text
Requirement precision
Requirement recall
Definition precision
Data-source accuracy
Indicator accuracy
```

### Question generation

```text
Relevance
Non-redundancy
Specificity
Methodological usefulness
Language correctness
```

### Bilingual capability

```text
Arabic understanding
English understanding
Code-switching understanding
Canonical terminology accuracy
```

### Safety

```text
Hallucination rate
Unsupported assertion rate
False confirmation rate
```

---

# 54. Critical Metric: False Confirmation Rate

This should be one of the most important evaluation metrics.

Example:

Input:

```text
We usually consider an establishment active if it files something.
```

Bad output:

```text
Confirmed definition:
Active = establishment that files something.
```

Good output:

```text
Potential definition identified.
Confirmation required.

Question:
Should filing activity be used as the formal definition
of an active establishment?
```

---

# 55. GPU Memory Benchmark

Run:

```powershell
nvidia-smi -l 1
```

while starting the LLM.

Record:

```text
VRAM before model
VRAM after model
VRAM during inference
Peak VRAM
```

Target:

```text
Peak VRAM < 4 GB
```

with enough headroom to avoid instability.

If Q4_K_M exceeds practical VRAM limits:

```text
Q4_K_S
```

then:

```text
Q3_K_M
```

---

# 56. Context Window

Do not start with a huge context window.

Use:

```text
2048 tokens
```

initially.

Then benchmark:

```text
2048
4096
8192
```

A larger context increases memory usage.

For the methodology agent, long meeting transcripts should **not** be continuously inserted into the LLM context.

Instead use:

```text
Transcript
 ↓
Relevant segment
 ↓
Structured state
 ↓
Compact context
 ↓
LLM
```

---

# 57. Do Not Feed the Entire Meeting to the LLM

Incorrect:

```text
2-hour meeting transcript
        ↓
LLM
```

Correct:

```text
2-hour meeting
      ↓
Transcript segments
      ↓
Relevant methodology signals
      ↓
Structured methodology state
      ↓
Recent evidence
      ↓
LLM
```

This dramatically reduces computational requirements.

---

# 58. LLM Calling Strategy

Use the LLM selectively.

Potential trigger conditions:

```text
New requirement
New definition
Potential contradiction
Unresolved concept
Potential data source
Potential business rule
Important decision
Missing methodology field
```

Do not invoke the LLM for every sentence.

---

# 59. Model Temperature

For methodology extraction:

```text
temperature = 0.0–0.2
```

Recommended:

```text
0.1
```

The system should favor deterministic, repeatable outputs.

Creative generation is not the goal.

---

# 60. JSON Output

Whenever possible, force structured output.

Preferred:

```json
{
  "type": "requirement",
  "concept": "reference_period",
  "value": "monthly",
  "status": "confirmed",
  "confidence": 0.95
}
```

Avoid:

```text
The business seems to want a monthly indicator...
```

for machine-to-machine processing.

---

# 61. Security Requirements

The application must:

* operate locally;
* make no external AI API calls;
* store no API keys for commercial AI providers;
* avoid telemetry where technically possible;
* never send methodology content to third-party inference services;
* avoid logging confidential prompts;
* avoid storing secrets in Git;
* bind development APIs to localhost by default;
* use read-only model volumes;
* run application containers as non-root users;
* minimize container privileges.

---

# 62. Network Architecture

For local development:

```text
127.0.0.1:8000 → Methodology API
127.0.0.1:8080 → LLM
```

Do not expose:

```text
0.0.0.0:8080
```

unless external access is explicitly required.

The LLM should normally only be reachable by the API container.

---

# 63. Secrets

The initial system should not require a model API key.

If future services require secrets:

```text
.env
```

must not be committed to Git.

Create:

```text
.env.example
```

with placeholders only.

Example:

```dotenv
LLM_BASE_URL=http://llm:8080/v1
LLM_MODEL=qwen3-4b-instruct-2507
LLM_TIMEOUT_SECONDS=120
```

---

# 64. No Cloud AI

The system must not contain:

```text
OpenAI API
Anthropic API
Google Gemini API
Azure OpenAI
AWS Bedrock
Cohere API
```

unless explicitly introduced as an optional future provider.

The default implementation must be completely local.

---

# 65. Internet Access

Internet access should only be required for:

```text
Downloading Docker images
Downloading models
Installing packages
```

Runtime inference should not require Internet connectivity.

After downloading:

```text
Docker images
Models
Python dependencies
```

the system should be capable of operating offline.

---

# 66. Model Provenance

Record:

```text
Model name
Model repository
Model version/revision
Quantization
SHA/hash where available
License
Download date
```

Example:

```yaml
model:
  name: Qwen3-4B-Instruct-2507
  quantization: Q4_K_M
  runtime: llama.cpp
  license: Apache-2.0
  source: unsloth/Qwen3-4B-Instruct-2507-GGUF
```

---

# 67. Do Not Use `latest` for Production

For experimentation:

```text
latest
```

may be acceptable.

For reproducible deployments:

```text
pinned image tag
+
model revision
```

must be used.

Record the exact llama.cpp image digest once the benchmark environment is finalized.

---

# 68. Docker Health Checks

LLM:

```text
GET /health
```

API:

```text
GET /health
```

The API health endpoint should eventually report:

```json
{
  "status": "healthy",
  "llm": "available",
  "model": "Qwen3-4B-Instruct-2507-Q4_K_M"
}
```

---

# 69. Logs

Application logs should include:

```text
timestamp
request ID
operation
latency
model
input language
token counts
status
error
```

Do NOT log:

```text
full confidential transcript
full meeting recording
credentials
API keys
```

unless explicitly enabled for controlled debugging.

---

# 70. Performance Benchmark

Create:

```text
scripts/benchmark.ps1
```

The benchmark should measure:

```text
Model load time
First-token latency
Total generation time
Tokens/second
VRAM
RAM
CPU utilization
```

Run at least:

```text
10 repeated prompts
```

and report:

```text
minimum
maximum
mean
median
p95
```

---

# 71. Methodology Benchmark Prompts

Use representative tasks.

## Task A — Definition gap

```text
The business team wants a monthly indicator of active establishments.
They have not agreed on the definition of active.

Identify the missing methodology element and formulate one
high-priority question in English.
```

## Task B — Statistical unit

```text
The source contains establishments, companies and branches.
The business team has not specified which entity should be counted.

Identify the methodological ambiguity and formulate one question.
```

## Task C — Reference period

```text
The indicator is monthly but it is unclear whether activity
is measured at the beginning, end, or throughout the month.

Identify the gap and ask the most useful question.
```

## Task D — Arabic

```text
نريد قياس المنشآت النشطة بشكل شهري ولكن لم يتم الاتفاق
على تعريف المنشأة النشطة.
```

## Task E — Mixed

```text
نريد monthly indicator للمنشآت النشطة، والdata source
هو Business Register، لكن ما اتفقنا على reference date.
```

---

# 72. Expected Agent Behavior

For Task E, a good response would be conceptually:

```json
{
  "requirements": [
    {
      "concept": "indicator",
      "value": "active establishments",
      "status": "confirmed"
    },
    {
      "concept": "frequency",
      "value": "monthly",
      "status": "confirmed"
    },
    {
      "concept": "data_source",
      "value": "Business Register",
      "status": "confirmed"
    }
  ],
  "open_questions": [
    {
      "concept": "reference_date",
      "status": "unknown"
    }
  ],
  "recommended_question": {
    "question": "What reference date should be used to determine whether an establishment is active?",
    "priority": 0.95
  }
}
```

---

# 73. Expected Performance on 4 GB GPU

Do not define success as:

```text
"LLM must generate 50 tokens/second."
```

For this application, the relevant target is:

```text
Useful methodology question
within a few seconds
after a relevant discussion segment.
```

The actual speed must be measured on the user's laptop.

Expected behavior:

```text
Q4 4B model:
Potentially usable

Q3 4B:
Potentially faster / lower memory

Q5 4B:
Potentially higher quality but higher memory

8B:
Not a primary target for 4 GB VRAM
```

These are expectations, not guaranteed benchmark results.

---

# 74. CPU Fallback

The architecture must support:

```text
GPU unavailable
      ↓
CPU inference
```

The API must continue functioning.

The application must never contain:

```python
if gpu:
    methodology_logic()
else:
    different_methodology_logic()
```

Instead:

```text
same methodology logic
        ↓
different LLM runtime
```

---

# 75. Runtime Abstraction

Define:

```text
LLMClient
```

as the application interface.

The application should not know whether the backend is:

```text
llama.cpp
vLLM
Transformers
CPU
GPU
```

All it needs:

```python
llm.chat(...)
```

This makes the platform portable.

---

# 76. Future GPU Server

When an internal GPU server becomes available:

```text
Application
     │
     ▼
LLMClient
     │
     ▼
vLLM
     │
     ▼
Larger Qwen model
```

The application should require no methodology-code rewrite.

vLLM provides an OpenAI-compatible server and official Docker images.

---

# 77. Optional Future Audio/Video Integration

Do not implement Jitsi in this first benchmark.

After the methodology agent works:

```text
Jitsi
  ↓
Audio
  ↓
ASR
  ↓
Transcript segments
  ↓
Methodology Agent
```

The methodology agent should receive text through an API.

This separation allows independent testing.

---

# 78. Future Meeting Input Contract

Eventually:

```json
{
  "meeting_id": "M-000001",
  "segment_id": "SEG-000001",
  "speaker_id": "P-000001",
  "language": "ar",
  "text_original": "نريد مؤشر شهري...",
  "timestamp_start": "00:14:32",
  "timestamp_end": "00:14:45",
  "confidence": 0.93
}
```

The methodology agent should transform this into:

```json
{
  "requirements": [],
  "inferences": [],
  "decisions": [],
  "gaps": [],
  "question": {}
}
```

---

# 79. Testing Strategy

Use four test layers.

## Unit

Test:

```text
state updates
gap detection
question ranking
terminology
language detection
JSON validation
```

## Integration

Test:

```text
API → LLM → structured response
```

## Bilingual

Test:

```text
Arabic
English
Mixed
```

## End-to-end

Test:

```text
Input
 ↓
LLM
 ↓
Extraction
 ↓
Methodology State
 ↓
Gap
 ↓
Question
```

---

# 80. Automated Test Example

Create:

```text
tests/test_bilingual.py
```

```python
def test_arabic_methodology_input():

    text = """
    نريد مؤشر شهري عن المنشآت النشطة.
    """

    assert text
```

The real test should mock the LLM and validate structured outputs rather than depend on live model inference.

---

# 81. Mock LLM for Tests

Unit tests must not require:

```text
GPU
LLM
Docker
Internet
```

Use a fake LLM:

```python
class FakeLLM:

    def chat(
        self,
        system_prompt,
        user_prompt,
        max_tokens=512
    ):
        return """
        {
          "language": "ar",
          "summary": "Monthly active establishment indicator",
          "requirements": [],
          "definitions": [],
          "data_sources": [],
          "decisions": [],
          "constraints": [],
          "open_questions": [
            "Definition of active establishment"
          ],
          "recommended_question": {
            "question": "How should an establishment be defined as active?",
            "reason": "The definition is required to determine inclusion in the indicator.",
            "domain": "definition",
            "priority": 0.95
          }
        }
        """
```

---

# 82. Build and Run

Final basic sequence:

```powershell
docker compose build
```

Then:

```powershell
docker compose up -d
```

Check:

```powershell
docker compose ps
```

Logs:

```powershell
docker compose logs -f
```

Stop:

```powershell
docker compose down
```

Restart:

```powershell
docker compose restart
```

---

# 83. GPU Monitoring

While running:

```powershell
nvidia-smi -l 1
```

Monitor:

```text
GPU utilization
VRAM
temperature
power
```

Record the peak VRAM.

---

# 84. Troubleshooting

## Problem: Docker cannot see GPU

Run:

```powershell
docker run --rm --gpus all nvidia/cuda:12.8.1-base-ubuntu24.04 nvidia-smi
```

If this fails:

1. Confirm NVIDIA driver.
2. Confirm WSL2.
3. Confirm Docker Desktop uses WSL2.
4. Restart Docker Desktop.
5. Restart WSL:

```powershell
wsl --shutdown
```

Then restart Docker Desktop.

Retry.

---

# 85. Problem: LLM runs out of VRAM

Reduce:

```text
quantization
context size
GPU layers
```

Try:

```text
Q4_K_M
 ↓
Q4_K_S
 ↓
Q3_K_M
```

Also reduce:

```text
-c 2048
```

to:

```text
-c 1024
```

if necessary.

---

# 86. Problem: Model loads but is slow

Check:

```powershell
nvidia-smi
```

If GPU utilization is close to zero, GPU offloading may not be working.

Check:

```powershell
docker compose logs llm
```

Look for CUDA backend initialization.

If necessary, explicitly test llama.cpp's CUDA image outside Compose.

---

# 87. Problem: LLM produces inconsistent answers

Reduce:

```text
temperature
```

to:

```text
0.0–0.1
```

Improve:

```text
system prompt
JSON schema
few-shot examples
validation
```

Do not solve this problem simply by increasing model size.

---

# 88. Problem: Arabic quality is weak

Do not immediately assume the LLM is unsuitable.

Check:

```text
Prompt
Arabic terminology
Model quantization
Context
Question formulation
```

Compare:

```text
Q4_K_M
Q4_K_S
Q3_K_M
```

against the same Arabic evaluation set.

---

# 89. Problem: Mixed Arabic-English is poor

Add explicit instructions:

```text
The input may contain Arabic, English, technical English terms,
abbreviations, and code switching.

Do not translate literally.

Infer the underlying statistical concept.
```

Add SCAD-specific terminology examples.

---

# 90. Problem: JSON parsing fails

Implement:

```text
LLM response
 ↓
JSON extraction
 ↓
Pydantic validation
 ↓
retry once with correction prompt
 ↓
failure recorded
```

Never silently accept malformed data.

---

# 91. Security Warning

Do not place confidential corporate meeting transcripts into external online model services during development unless explicitly authorized.

The objective of this architecture is:

```text
Data
 ↓
Local Docker
 ↓
Local LLM
```

No external inference provider is required.

---

# 92. Licensing and Compliance

Before organizational deployment, maintain a software bill of materials containing:

```text
component
version
license
source
model revision
model license
Docker image digest
```

The model's Apache 2.0 license does not mean every surrounding dataset, dependency, or model derivative automatically has identical licensing.

Review each component before production use.

---

# 93. Model Download and Reproducibility

Once the model is downloaded successfully:

```text
models/
└── Qwen3-4B-Instruct-2507-Q4_K_M.gguf
```

Record:

```text
repository
filename
revision
SHA/hash
license
```

Do not automatically redownload a potentially different model revision during production deployment.

---

# 94. Minimal `.gitignore`

Create:

```text
.gitignore
```

```gitignore
.env
.venv/
__pycache__/
*.pyc

models/*.gguf

.pytest_cache/
.mypy_cache/

.vscode/
.idea/

logs/
tmp/
```

Never commit multi-gigabyte model files to Git.

---

# 95. `.dockerignore`

Create:

```text
.dockerignore
```

```text
.git
.gitignore
.venv
__pycache__
*.pyc

models
tests
logs
tmp
.env
```

---

# 96. Makefile Alternative

If using Linux/WSL:

```makefile
build:
	docker compose build

up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f

health:
	curl http://127.0.0.1:8000/health

llm-health:
	curl http://127.0.0.1:8080/health

test:
	pytest -q
```

---

# 97. Windows PowerShell Commands

The equivalent common commands are:

```powershell
docker compose build
docker compose up -d
docker compose down
docker compose ps
docker compose logs -f
```

Health:

```powershell
curl.exe http://127.0.0.1:8000/health
```

GPU:

```powershell
nvidia-smi
```

---

# 98. First Development Milestone

The first milestone is complete when this works:

```text
Arabic input
      ↓
Qwen3
      ↓
Structured methodology extraction
      ↓
Missing methodological element
      ↓
English methodology question
```

Example:

```text
Input:

نريد مؤشر شهري عن المنشآت النشطة،
لكن تعريف المنشأة النشطة غير متفق عليه.

                ↓

Output:

{
  "missing": "definition of active establishment",
  "question":
    "How should an establishment be defined as active?"
}
```

---

# 99. Second Development Milestone

The second milestone:

```text
Arabic
English
Mixed
      ↓
Same canonical methodology state
```

For example:

```text
Arabic:
نريد مؤشر شهري...

English:
We need a monthly indicator...

Mixed:
نريد monthly indicator...
```

must all produce equivalent structured concepts.

---

# 100. Third Development Milestone

The third milestone:

```text
Conversation
      ↓
Multiple extracted requirements
      ↓
Methodology state
      ↓
Missing fields
      ↓
Prioritized question
```

Example:

```text
Objective:
Measure business activity

Population:
Establishments

Frequency:
Monthly

Data source:
Business Register

Missing:
Definition of active establishment

Question:
How should an establishment be defined as active?
```

---

# 101. Fourth Development Milestone

The fourth milestone:

```text
Meeting transcript
       ↓
Relevant segments
       ↓
Methodology state
       ↓
Question
       ↓
Answer
       ↓
Updated state
       ↓
Validated knowledge
```

At this stage, the agent becomes suitable for integration with the larger methodology platform.

---

# 102. Future Production Architecture

The eventual architecture should be:

```text
                 ┌──────────────────────┐
                 │      Web Frontend    │
                 └──────────┬───────────┘
                            │
                 ┌──────────▼───────────┐
                 │     FastAPI API      │
                 └──────────┬───────────┘
                            │
                 ┌──────────▼───────────┐
                 │ Methodology Engine   │
                 └──────────┬───────────┘
                            │
            ┌───────────────┼────────────────┐
            │               │                │
            ▼               ▼                ▼
          LLM             RAG             State
       llama.cpp         Qdrant         PostgreSQL
            │
            ▼
         Qwen3
```

Later:

```text
Jitsi
 ↓
Speech
 ↓
Transcript
 ↓
Methodology Engine
```

---

# 103. Future Multi-Agent Integration

The methodology agent should eventually become one agent in a larger platform:

```text
                  Methodology Agent
                         │
          ┌──────────────┼──────────────┐
          │              │              │
          ▼              ▼              ▼
     Research Agent   Data Agent   Indicator Agent
          │              │              │
          └──────────────┼──────────────┘
                         ▼
                  Documentation Agent
                         │
                         ▼
                   Review Agent
```

All agents should use the shared methodology knowledge model.

---

# 104. Do Not Couple Agents Directly

Incorrect:

```text
Agent A → Agent B internal Python function
```

Prefer:

```text
Agent A
 ↓
API / shared state
 ↓
Agent B
```

This makes agents independently deployable.

---

# 105. Future Shared Knowledge

The knowledge system should store:

```text
Concept
Definition
Domain
Statement
Status
Source
Evidence
Confidence
Validated by
Effective date
Superseded by
Related concepts
```

Every knowledge statement must have provenance.

---

# 106. Production Human Approval

No AI-generated methodology should become authoritative without human approval.

Required:

```text
AI
 ↓
Candidate
 ↓
Human review
 ↓
Approve / Reject / Modify
 ↓
Published knowledge
```

This is a non-negotiable design requirement.

---

# 107. What Not to Build Yet

Do not initially build:

```text
Kubernetes
Kafka
Temporal
Complex multi-agent orchestration
Knowledge graph
Jitsi integration
Video processing
Large LLM
Fine-tuning
Distributed inference
```

First prove:

```text
Bilingual understanding
+
Methodology extraction
+
Gap detection
+
Question generation
```

---

# 108. Recommended Development Sequence

## Phase 1

```text
Docker
 ↓
llama.cpp
 ↓
Qwen3-4B Q4
```

## Phase 2

```text
FastAPI
 ↓
LLM API
```

## Phase 3

```text
Methodology extraction
 ↓
Structured state
```

## Phase 4

```text
Gap detection
 ↓
Question generation
```

## Phase 5

```text
Arabic
English
Mixed-language evaluation
```

## Phase 6

```text
ASR
 ↓
Meeting transcript
```

## Phase 7

```text
PostgreSQL
 ↓
Qdrant
```

## Phase 8

```text
Jitsi
 ↓
Real-time methodology agent
```

---

# 109. Definition of Done — MVP

The MVP is complete when all of the following are true:

* [ ] Docker runs successfully.
* [ ] Docker can access the NVIDIA GPU.
* [ ] Qwen3-4B-Instruct-2507 loads locally.
* [ ] Q4 quantization runs within the laptop's practical VRAM limit.
* [ ] llama.cpp exposes an OpenAI-compatible API.
* [ ] FastAPI communicates with llama.cpp.
* [ ] Arabic input works.
* [ ] English input works.
* [ ] Arabic-English mixed input works.
* [ ] Requirements are extracted.
* [ ] Definitions are extracted.
* [ ] Missing information is detected.
* [ ] Questions are generated in English.
* [ ] Questions contain rationale.
* [ ] JSON output is validated.
* [ ] Inference is distinguished from confirmation.
* [ ] Tests exist for Arabic/English/mixed inputs.
* [ ] No cloud AI API is required.
* [ ] Model provenance is recorded.
* [ ] GPU usage has been benchmarked.
* [ ] LLM latency has been benchmarked.

---

# 110. Recommended Benchmark Report

Create:

```text
BENCHMARK.md
```

with:

```markdown
# Methodology Agent Benchmark

## Hardware

GPU:
VRAM:
CPU:
RAM:
OS:
Docker:
Driver:

## Model

Model:
Quantization:
Runtime:
Revision:

## GPU

Model load time:
Peak VRAM:
GPU utilization:

## LLM

Prompt tokens:
Output tokens:
Time to first token:
Generation time:
Tokens/sec:

## Arabic

Quality:
Latency:
Issues:

## English

Quality:
Latency:
Issues:

## Mixed

Quality:
Latency:
Issues:

## Methodology Tasks

Requirement extraction:
Definition extraction:
Gap detection:
Question generation:

## Decision

Selected model:
Selected quantization:
Selected runtime:

## Known Limitations

...

## Next Steps

...
```

---

# 111. Final Architecture Decision

For the current laptop:

```text
OS
 ↓
Docker Desktop / WSL2
 ↓
Docker Compose
 ↓
llama.cpp CUDA
 ↓
Qwen3-4B-Instruct-2507 Q4_K_M
 ↓
FastAPI
 ↓
Custom Methodology Agent
```

The agent is:

```text
Arabic-aware
English-aware
Code-switching-aware
Structured
Auditable
Local
Open-source
GPU-accelerated
GPU-optional
```

---

# 112. Exact First-Run Sequence

Assuming Docker GPU support is already functional:

```powershell
mkdir methodology-agent
cd methodology-agent
```

Download the model:

```powershell
py -m pip install -U huggingface_hub
```

```powershell
huggingface-cli download `
  unsloth/Qwen3-4B-Instruct-2507-GGUF `
  Qwen3-4B-Instruct-2507-Q4_K_M.gguf `
  --local-dir .\models
```

Verify:

```powershell
Get-ChildItem .\models
```

Create the project files described in this document.

Then:

```powershell
docker compose build
```

Start:

```powershell
docker compose up -d
```

Check:

```powershell
docker compose ps
```

Check logs:

```powershell
docker compose logs -f llm
```

Check LLM:

```powershell
curl.exe http://127.0.0.1:8080/health
```

Check API:

```powershell
curl.exe http://127.0.0.1:8000/health
```

Test the agent:

```powershell
$body = @{
    text = "نريد نطلع مؤشر شهري عن المنشآت النشطة، لكن تعريف المنشأة النشطة غير متفق عليه."
    language = "ar"
} | ConvertTo-Json

Invoke-RestMethod `
    -Uri http://127.0.0.1:8000/analyze `
    -Method POST `
    -ContentType "application/json" `
    -Body $body
```

Monitor GPU:

```powershell
nvidia-smi -l 1
```

---

# 113. Expected Result

The expected end state is:

```text
User
 │
 │ Arabic / English / Mixed
 ▼
FastAPI
 │
 ▼
Methodology Agent
 │
 ▼
Qwen3-4B-Instruct-2507
 │
 ▼
Structured Methodology Interpretation
 │
 ├── Requirements
 ├── Definitions
 ├── Indicators
 ├── Data Sources
 ├── Constraints
 ├── Decisions
 └── Missing Information
             │
             ▼
       English Question
```

Example:

```text
Input:

نريد مؤشر شهري عن المنشآت النشطة.
البيانات من السجل التجاري، لكن تعريف المنشأة النشطة غير متفق عليه.

Output:

Requirement:
Monthly active-establishment indicator

Data source:
Business Register

Gap:
Definition of active establishment

Question:
How should an establishment be defined as active?

Reason:
The definition is required to determine which establishments
are included in the indicator.
```

---

# 114. Final Design Principle

The most important architectural principle is:

> **The LLM is a reasoning component of the Methodology Agent, not the Methodology Agent itself.**

The Methodology Agent consists of:

```text
LLM
+
structured state
+
methodology rules
+
terminology
+
gap detection
+
question prioritization
+
validation
+
human approval
+
provenance
```

Therefore, replacing:

```text
Qwen3-4B
```

with:

```text
Qwen3-8B
Qwen3-30B
another open model
vLLM
another inference runtime
```

must not require rewriting the methodology logic.

---

# 115. Final Deliverables

The coding agent/developer must produce:

```text
methodology-agent/
├── README.md
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── .gitignore
├── .dockerignore
├── requirements.txt
│
├── app/
│   ├── main.py
│   ├── api/
│   ├── agent/
│   ├── llm/
│   ├── models/
│   └── core/
│
├── prompts/
│   ├── system.md
│   ├── extraction.md
│   └── question_generation.md
│
├── models/
│   └── Qwen3-4B-Instruct-2507-Q4_K_M.gguf
│
├── tests/
│   ├── test_bilingual.py
│   ├── test_extraction.py
│   └── test_questions.py
│
├── scripts/
│   ├── download_model.ps1
│   └── benchmark.ps1
│
└── BENCHMARK.md
```

The model file itself should normally **not** be committed to Git; document the exact repository, filename, revision and checksum instead.

---

# 116. One-Line Expected Outcome

> **A fully local, Dockerized, open-source Arabic/English statistical methodology agent running on the laptop's RTX GPU, capable of converting bilingual business discussion into structured methodology requirements, identifying missing information, and generating precise English methodology questions, while remaining portable to CPU-only VDI and larger future GPU infrastructure.**
