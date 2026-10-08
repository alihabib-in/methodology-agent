# AI Agents

This document describes the AI agents that power the methodology-documentation
workflow: what each agent does, how agents are connected to one another, and a
worked example. It covers only the agents — for the full platform (services,
realtime, data model) see `docs/PORTAL_OVERVIEW.md`.

---

## 1. Overview

The system is a **central orchestrator + specialized agents**, not a swarm of
independent chatbots. The platform (workflow engine) owns state and decides what
runs; each agent is a worker that receives structured inputs and returns
structured outputs. Agents never write to each other directly — they communicate
through the orchestrator.

Two architectural rules govern the agents:

1. **Agents own tasks; the platform owns state.** An agent returns a result; the
   workflow engine validates it, persists it, and hands it to the next agent.
2. **The LLM is a reasoning component, not the agent.** Deterministic code does
   extraction-state-gap-question logic, data retrieval, and validation; the LLM
   is called only where fuzzy reasoning is required.

---

## 2. The agent network (workflow graph)

The workflow is declared as data in `app/workflow/definitions_registry.py`.
Each node is a stage bound to an agent; arrows are dependencies (an agent runs
only after its dependencies complete). Approval gates pause for a human.

```
                       ┌──────────────────────────────┐
                       │  Intake (no workflow stage)  │
                       │  Elicitation  /  Document    │
                       │  Analysis agent              │
                       └──────────────┬───────────────┘
                                      │  creates the case
                                      ▼
                       ┌──────────────────────────────┐
                       │  requirement_case            │  ← human confirm
                       └──────────────┬───────────────┘
                                      ▼
                       ┌──────────────────────────────┐
                       │  case_analysis               │  Case Analysis agent
                       │  (produces the Case Brief)   │
                       └──────────────┬───────────────┘
                                      ▼
                       ┌──────────────────────────────┐
                       │  data_acquisition            │  Data Acquisition agent
                       │  (fetches real datasets)     │
                       └───────┬──────────────┬───────┘
                               │              │
                  ┌────────────▼───┐          │
                  │ international  │          │  International Research agent
                  │ _research      │          │
                  └───────┬────────┘          │
                          │                   │
          ┌───────────────▼───────────────────▼──────┐
          │  standardized_methodology   ★ approval   │  Standardized Methodology agent
          └───────┬───────────────┬─────────────────┘
                  │               │
        ┌─────────▼────────┐      │
        │ scad_input       │      │  SCAD Input agent (conditional)
        │ _analysis        │      │
        └─────────┬────────┘      │
        ┌─────────▼────────┐      │
        │ clarification    │      │  Q&A agent (conditional)
        └─────────┬────────┘      │
                  │               │
        ┌─────────▼────────────────▼────────┐
        │ indicator_development             │  Indicator agent (conditional)
        └─────────┬─────────────────────────┘
                  │
        ┌─────────▼─────────────────────────────────┐
        │ scad_methodology         ★ approval       │  SCAD Methodology agent
        └───────┬───────────────────────┬───────────┘
                │                       │
      ┌─────────▼────────┐    ┌─────────▼────────────┐
      │ compliance       │    │ gap_assessment       │  Compliance + Gap agents
      └──────────────────┘    └──────────────────────┘
```

---

## 3. How agents are connected

**Three connection mechanisms:**

| Mechanism | Where | Description |
|---|---|---|
| **Dependencies** | `definitions_registry.py` (`depends_on`) | An agent runs only after its dependencies are `COMPLETED`. The engine injects each dependency's output into the agent's inputs, keyed by the dependency's stage id (e.g. `standardized_methodology` receives `inputs["international_research"]` and `inputs["data_acquisition"]`). |
| **Case context injection** | `workflow/service.py` (`advance_case`) | The case's problem statement (`objective`, `domain`, `topic`, `title`, `explicit_requirements`, `constraints`) is injected into **every** agent's inputs, so all agents are contextually aware. |
| **Approval gates** | `definitions_registry.py` (`approval_required`) | A stage whose agent runs successfully but has `approval_required=True` enters `WAITING_FOR_HUMAN` instead of `COMPLETED`. Downstream agents stay blocked until a human approves (via `POST /cases/{id}/stages/{stage}/approve`). |

**Conditional stages** run only when a boolean fact is true: `scad_input_analysis`
(`scad_documents_available`), `clarification` (`unresolved_scad_requirements`),
`indicator_development` (`indicators_required`), `gap_assessment`
(`gap_assessment_required`).

**Failure handling:** if an agent returns `status="failed"` it is marked
`FAILED`, and (since the engine treats `FAILED`/`SKIPPED` stages as satisfied)
the workflow continues so a single agent cannot wedge the pipeline.

---

## 4. Agent catalog

### 4.1 Intake agents (no workflow stage)

**Elicitation agent** — `app/agents/elicitation.py`
- ID: `methodology_requirement_elicitation_agent`
- **What it does:** converts a bilingual (Arabic/English) meeting/discussion into a structured case proposal. It wraps the deterministic reasoning pipeline (`app/agent/methodology_agent.py`: extract → state → gap → question).
- **Inputs:** `text`, `language`
- **Outputs:** `summary`, `extraction`, `methodology_state`, `gaps`, `recommended_question`
- **Consumed by:** the `POST /cases` endpoint, which turns its output into a `MethodologyCase` (via `case/consolidation.py`).

**Document Analysis agent** — `app/agents/document_analysis.py`
- ID: `requirement_document_analysis_agent`
- **What it does:** the same as Elicitation, but for a Word document (parsed by `document_parser.py`).
- **Inputs:** `text`, `language`, `filename`
- **Consumed by:** the `POST /cases/intake-document` endpoint.

### 4.2 Case Analysis agent

`app/agents/case_analysis.py` — ID `case_analysis_agent`
- **What it does:** analyzes the confirmed case and produces an **execution brief** that prepares all downstream agents: the statistical domain, the standards/portals to research, the key concepts to define, and the sector classification.
- **Inputs:** `objective`, `title`, `domain`, `topic`, `explicit_requirements`, `constraints`
- **Outputs:** `case_brief` = `{ objective, domain, topic, research_scope[], key_concepts[], sector_classification[], section_priorities[], agent_brief{} }`, `reasoning`
- **Consumed by:** `data_acquisition` and `international_research`.

### 4.3 Data Acquisition agent

`app/agents/data_acquisition.py` — ID `data_acquisition_agent`
- **What it does:** discovers and retrieves **real data** from public portals. It derives search queries (topic taxonomy + LLM + deterministic fallback), searches World Bank and Eurostat, and fetches the most relevant datasets.
- **Inputs:** `objective`, `case_analysis` (the brief)
- **Outputs:** `evidence_package` = `{ objective, queries[], datasets[], retrieved_at }`, `datasets`, `reasoning`
- **Consumed by:** `international_research`, `standardized_methodology`, `scad_methodology` (datasets are cited factually in the methodology documents).

### 4.4 International Research agent

`app/research/agent.py` — ID `international_research_agent`
- **What it does:** identifies authoritative international standards, frameworks, classifications, and NSO practices, using the case brief's `research_scope` to stay on-topic. A credibility policy (`app/research/sources.py`) discards user-generated content.
- **Inputs:** `objective`, `domain`, `topic`, `case_analysis`
- **Outputs:** `source_register[]`, `findings[]`, `research_report`, `unresolved_questions[]`, `reasoning`
- **Consumed by:** `standardized_methodology`.

### 4.5 Standardized Methodology agent

`app/agents/standardized_methodology.py` — ID `standardized_methodology_agent` — **★ approval gate**
- **What it does:** synthesizes the research + retrieved data into a generic, internationally-informed methodology (12 sections, independent of SCAD constraints).
- **Inputs:** `objective`, `domain`, `international_research`, `data_acquisition`
- **Outputs:** `methodology` (12 sections), `source_refs[]`, `reasoning`
- **Consumed by:** `scad_input_analysis`, `indicator_development`, `scad_methodology`, `gap_assessment`.

### 4.6 SCAD Input agent

`app/agents/scad_input.py` — ID `scad_input_agent` — **conditional** (`scad_documents_available`)
- **What it does:** reads SCAD current-practice documents (uploaded per case) and maps them against the standardized methodology, producing a current-practice assessment and the gaps.
- **Inputs:** `objective`, `standardized_methodology`, `scad_documents[]`
- **Outputs:** `current_practice[]`, `mapping_matrix[]`, `gaps[]`, `questions[]`, `reasoning`
- **Consumed by:** `clarification`, `scad_methodology`.

### 4.7 Q&A / Clarification agent

`app/agents/methodology_qa.py` — ID `methodology_qa_agent` — **conditional** (`unresolved_scad_requirements`)
- **What it does:** generates prioritized, non-leading questions for the remaining uncertainty, avoiding what evidence already resolved.
- **Inputs:** `objective`, `scad_input_analysis`
- **Outputs:** `question_set[]`, `reasoning`
- **Consumed by:** `indicator_development`, `scad_methodology`.

### 4.8 Indicator agent

`app/agents/indicator.py` — ID `indicator_agent` — **conditional** (`indicators_required`)
- **What it does:** develops candidate indicator specifications in SCAD's "Indicator Information Card" format (41 fields).
- **Inputs:** `objective`, `standardized_methodology`, `scad_input_analysis`, `clarification`
- **Outputs:** `indicators[]`, `traceability[]`, `reasoning`
- **Consumed by:** `scad_methodology`.

### 4.9 SCAD Methodology agent

`app/agents/scad_methodology.py` — ID `scad_methodology_agent` — **★ approval gate**
- **What it does:** produces the final SCAD-specific methodology document (7 sections + subsections), adapting the standardized methodology to SCAD practice, applying annotations (`[Aligned with: …]`, `[Abu Dhabi exception]`, `[To be confirmed by SCAD]`), and following SCAD's official tone/formatting (loaded from the reference corpus).
- **Inputs:** `objective`, `standardized_methodology`, `scad_input_analysis`, `clarification`, `indicator_development`, `data_acquisition`
- **Outputs:** `methodology` (7 sections), `source_refs[]`, `indicator_codes[]`, `reasoning`
- **Consumed by:** `compliance`, `gap_assessment`.

### 4.10 Compliance / QA agent

`app/agents/compliance.py` — ID `compliance_agent`
- **What it does:** validates the SCAD methodology for completeness, consistency, provenance, annotations, and citations. Read-only — never modifies methodology state.
- **Inputs:** `scad_methodology`, `standardized_methodology`
- **Outputs:** `qa_report` (checklist, blocking/non-blocking issues), `approval_recommendation`, `reasoning`
- **Consumed by:** (terminal — reported to the user).

### 4.11 Gap Assessment agent

`app/agents/gap_assessment.py` — ID `gap_assessment_agent` — **conditional** (`gap_assessment_required`)
- **What it does:** compares the SCAD methodology against the standardized (international) methodology and produces a formal gap assessment.
- **Inputs:** `objective`, `standardized_methodology`, `scad_methodology`
- **Outputs:** `gap_assessment` (matrix, priority areas, recommendations), `gap_register[]`, `reasoning`
- **Consumed by:** (terminal — reported to the user).

### 4.12 Cross-cutting: Document Generation

`app/agents/document_generation.py` (not a workflow agent)
- **What it does:** renders structured artifacts to DOCX/XLSX — the standardized methodology, the SCAD methodology (with the SCAD template styles), the gap-assessment table, and the transposed indicator-card spreadsheet.

---

## 5. Worked example — "AI Adoption Index in Abu Dhabi"

A user creates a case from the discussion *"Develop a methodology for the AI
Adoption Index in Abu Dhabi, based on the 2025 AI survey."*

1. **Elicitation** extracts the objective: *"Develop a methodology for the AI
   Adoption Index in Abu Dhabi based on the 2025 AI survey."* → a `MethodologyCase`
   is created and set to `requirements_review`.
2. **Human confirms** the case (`POST /cases/{id}/confirm`).
3. **Case Analysis** produces the brief: domain `digital economy`, topic `AI
   adoption`, `research_scope = [OECD.AI, ITU benchmarks, Singapore/UK AI
   indices]`, `key_concepts = [AI adoption, technology integration, …]`.
4. **Data Acquisition** derives queries (`internet users`, `broadband
   subscriptions`, `research & development expenditure`, …) and fetches real
   data — e.g. *Individuals using the Internet, male: 100% (2024)* and *Secure
   Internet servers: 46,058 (2024)* from the World Bank.
5. **International Research** finds `OECD.AI`, `ITU AI benchmarks`, `UK AI
   Strategy`, plus `ISIC Rev.4`/`GSBPM`.
6. **Standardized Methodology** writes the 12-section generic methodology,
   citing the internet/ICT figures. → **approval gate**.
7. **Indicator** (after approval) produces SCAD cards: `IND-001 AI Adoption by
   Sector`, `IND-002 AI Use Case Distribution`, `IND-003 AI Capability Type
   Distribution`.
8. **SCAD Methodology** writes the 7-section SCAD-specific document with
   annotations, listing the retrieved datasets as sources. → **approval gate**.
9. **Compliance** reports blocking/non-blocking findings.
10. **Gap Assessment** compares SCAD practice vs. the international methodology.

The result is a complete, auditable methodology document backed by real data.

---

## 6. Supporting components (the reasoning pipeline)

The intake agents delegate to **`MethodologyAgent`** (`app/agent/methodology_agent.py`),
which composes four deterministic parts — only the Extractor calls the LLM:

```
MethodologyAgent
 ├─ Extractor          (LLM)   text → ExtractionResult (validated JSON)
 ├─ StateManager      (pure)   ExtractionResult → MethodologyState (never downgrades a confirmed field)
 ├─ GapDetector       (pure)   MethodologyState → priority-sorted gaps
 └─ QuestionGenerator (pure)   top gap → one English methodology question
```

All workflow agents call the LLM through a shared, retry-capable client
(`app/llm/client.py`) and a JSON helper (`app/agent/extractor.py::chat_json`)
that retries on truncation, so transient LLM failures do not cascade.
