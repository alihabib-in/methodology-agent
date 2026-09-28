# Multilingual Methodology Portal Evaluation Harness

## Python Evaluation Program — Coding Agent Implementation Prompt

### 1. Mission

Create a **standalone Python evaluation harness** for the SCAD Methodology AI Portal.

The purpose of this program is to allow the development team to test and understand the portal's **methodology-processing algorithm and final outputs** using prerecorded multilingual meeting transcripts before moving the containerized application to a higher-configuration server.

The evaluation harness must simulate the important parts of the portal workflow:

```text
Meeting Transcript
        ↓
Arabic / English understanding
        ↓
Existing Knowledge Retrieval
        ↓
Objective Detection
        ↓
Methodology State
        ↓
Gap Detection
        ↓
Question Generation
        ↓
Answer / Evidence Processing
        ↓
Methodology State Update
        ↓
Gap Re-evaluation
        ↓
Candidate Methodology Scope
        ↓
Human Review Simulation
        ↓
Knowledge Candidate Extraction
        ↓
Final Structured Output
```

The primary goal is **evaluation and transparency**, not production deployment.

The program should allow a human evaluator to understand:

> "Given these meeting conversations, what did the portal understand, what gaps did it identify, what questions did it generate, what assumptions did it make, how did the methodology state evolve, and what final methodology did it produce?"

---

# 2. Important Constraints

The evaluation program must:

* run independently from Jitsi
* process prerecorded transcript files
* support Arabic
* support English
* support mixed Arabic/English meetings
* preserve original transcript text
* produce structured intermediate outputs
* produce a final methodology candidate
* expose the reasoning/evidence chain without exposing hidden chain-of-thought
* support local LLM inference
* support the existing portal LLM gateway where practical
* support deterministic/mock mode
* work from the existing repository
* reuse existing methodology services/models/prompts where practical
* not duplicate existing production logic unnecessarily
* not require cloud AI services
* not require internet access
* not require a GPU
* be runnable from the developer VDI

The program must be useful even if the production frontend and Jitsi are not running.

---

# 3. First Step — Inspect Existing Repository

Before implementing anything:

Inspect the existing repository thoroughly.

Identify:

```text
backend/
frontend/
methodology/
knowledge/
rag/
LLM gateway
prompts
Pydantic models
database models
WebSocket/event models
API endpoints
existing methodology agent
gap detection
question generation
candidate scope
knowledge extraction
```

Determine which existing production services can be reused directly.

Create:

```text
docs/EVALUATION_HARNESS_ASSESSMENT.md
```

Document:

1. Existing methodology pipeline
2. Existing LLM gateway
3. Existing prompts
4. Existing state model
5. Existing gap model
6. Existing question model
7. Existing candidate-scope model
8. Existing knowledge model
9. Components reusable by the evaluation harness
10. Components that need adapters
11. Missing functionality
12. Recommended integration approach

Do not rebuild existing production logic if it can be invoked safely.

---

# 4. Evaluation Harness Architecture

Create a standalone evaluation package, preferably:

```text
evaluation/
├── README.md
├── __init__.py
├── cli.py
├── config.py
├── runner.py
├── transcript_loader.py
├── transcript_normalizer.py
├── methodology_engine.py
├── evaluation_state.py
├── evidence_tracker.py
├── report_generator.py
├── exporters.py
├── models/
│   ├── transcript.py
│   ├── events.py
│   ├── methodology.py
│   ├── gaps.py
│   ├── questions.py
│   ├── knowledge.py
│   └── evaluation.py
├── adapters/
│   ├── llm_adapter.py
│   ├── production_adapter.py
│   └── mock_adapter.py
└── tests/
```

Adapt this structure to the existing repository.

Do not blindly create all files if equivalent components already exist.

---

# 5. Input: Meeting Transcript Dataset

The program must accept a folder of meeting transcripts.

Example:

```text
evaluation/data/
├── meeting_001/
│   ├── metadata.json
│   └── transcript.json
│
├── meeting_002/
│   ├── metadata.json
│   └── transcript.json
│
└── meeting_003/
    ├── metadata.json
    └── transcript.json
```

Also support a simple:

```text
.txt
.md
.json
.csv
```

format where practical.

---

# 6. Recommended Transcript JSON Format

Support structured transcripts such as:

```json
{
  "meeting_id": "M-001",
  "title": "Active Establishment Indicator",
  "language_mix": ["ar", "en"],
  "segments": [
    {
      "segment_id": "S001",
      "speaker_id": "business_01",
      "timestamp_start": "00:00:04",
      "timestamp_end": "00:00:12",
      "language": "ar",
      "text": "نريد مؤشر عن المنشآت النشطة."
    },
    {
      "segment_id": "S002",
      "speaker_id": "methodologist_01",
      "timestamp_start": "00:00:14",
      "timestamp_end": "00:00:22",
      "language": "en",
      "text": "What exactly do you mean by active?"
    },
    {
      "segment_id": "S003",
      "speaker_id": "business_01",
      "timestamp_start": "00:00:25",
      "timestamp_end": "00:00:34",
      "language": "ar",
      "text": "المنشأة التي لديها نشاط اقتصادي خلال الفترة."
    }
  ]
}
```

The program must preserve:

* speaker
* timestamp
* original language
* original text

Never overwrite the original transcript.

If the JSON format is unavailable, fallback to process normal text transcript format.

```
Introduction
0:00
good afternoon everyone and welcome to the first of the 13 webinars that are
0:05
part of the 2020 M us webinars program my name is Catalina Justine I'm
0:10
professor of statistics a diversity of Pisa in Italy and today I will act as the webinar facilitator as this is a
0:17
live event I would like to specify that today I'm connected from my house as all the other members of the emos
```
---

# 7. Mixed-Language Support

The evaluator must explicitly test scenarios such as:

```text
Arabic → Arabic → English → Arabic → English
```

and:

```text
Arabic sentence containing English statistical terminology
```

Example:

```text
نحتاج monthly indicator للمنشآت النشطة.
```

The pipeline must not assume that an entire meeting has one language.

Language should be treated at the segment level.

---

# 8. Transcript Normalization

Create an internal normalized representation.

Example:

```python
TranscriptSegment(
    meeting_id="M-001",
    segment_id="S001",
    speaker_id="business_01",
    timestamp_start="00:00:04",
    timestamp_end="00:00:12",
    language="ar",
    original_text="نريد مؤشر عن المنشآت النشطة.",
    normalized_text="We need an indicator about active establishments."
)
```

Important:

The normalized text is supplementary.

The original Arabic must always remain available as evidence.

Do not translate everything before processing unless required by the selected model/pipeline.

The LLM should ideally support multilingual reasoning directly.

---

# 9. Evaluation Modes

Support at least three modes.

## Mode A — Production Logic

Use the actual methodology services from the portal.

Example:

```bash
python -m evaluation.cli run \
  --input evaluation/data/meeting_001 \
  --mode production
```

This should exercise as much of the actual methodology pipeline as possible.

---

## Mode B — Local LLM

Use the locally configured LLM gateway.

Example:

```bash
python -m evaluation.cli run \
  --input evaluation/data/meeting_001 \
  --mode local
```

No cloud API.

---

## Mode C — Mock

Use deterministic mock outputs.

Example:

```bash
python -m evaluation.cli run \
  --input evaluation/data/meeting_001 \
  --mode mock
```

Mock mode is for testing application logic.

It must never silently substitute for the real LLM.

---

# 10. Core Evaluation Pipeline

For each meeting execute:

```text
STEP 1
Load transcript

STEP 2
Validate transcript

STEP 3
Normalize language representation

STEP 4
Extract initial objective

STEP 5
Retrieve existing knowledge

STEP 6
Initialize methodology state

STEP 7
Process transcript incrementally

STEP 8
Identify requirements

STEP 9
Identify gaps

STEP 10
Generate questions

STEP 11
Determine whether transcript contains an answer

STEP 12
Interpret answer/evidence

STEP 13
Update methodology state

STEP 14
Recalculate gaps

STEP 15
Repeat until transcript is exhausted

STEP 16
Generate candidate methodology scope

STEP 17
Extract knowledge candidates

STEP 18
Perform consistency/conflict checks

STEP 19
Generate final evaluation report
```

---

# 11. Important: Process Transcript Incrementally

Do NOT simply send the entire transcript to the LLM once and ask:

> "Generate the final methodology."

That defeats the purpose of evaluating the portal algorithm.

The evaluator should simulate the real meeting progression.

Conceptually:

```text
Segment 1
  ↓
State update

Segments 2–5
  ↓
State update

Segments 6–10
  ↓
New gap

Segments 11–15
  ↓
Question answered

...
```

This allows us to understand how the methodology evolves.

---

# 12. Evaluation State

Maintain a complete state object.

Example:

```json
{
  "meeting_id": "M-001",
  "objective": {},
  "requirements": [],
  "constraints": [],
  "definitions": [],
  "business_rules": [],
  "data_sources": [],
  "gaps": [],
  "questions": [],
  "answers": [],
  "insights": [],
  "assumptions": [],
  "unknowns": [],
  "candidate_scope": {},
  "knowledge_candidates": [],
  "state_version": 12
}
```

Every meaningful state change must create a version.

---

# 13. State History

The evaluator must preserve the full methodology evolution.

Example:

```text
VERSION 1
Objective identified

VERSION 2
Population identified

VERSION 3
Reference period gap detected

VERSION 4
Question generated

VERSION 5
Reference period = monthly

VERSION 6
Statistical unit identified

VERSION 7
Candidate methodology ready
```

Create:

```text
evaluation/output/M-001/state_history.json
```

---

# 14. Evidence Tracking

This is extremely important.

Every extracted methodology fact must have evidence.

Example:

```json
{
  "concept": "reference_period",
  "value": "monthly",
  "status": "confirmed",
  "confidence": 0.96,
  "evidence": [
    {
      "segment_id": "S021",
      "speaker_id": "business_01",
      "timestamp_start": "00:04:21",
      "timestamp_end": "00:04:27",
      "original_text": "نريد المؤشر بشكل شهري",
      "language": "ar"
    }
  ]
}
```

This lets the evaluator answer:

> Why did the system decide that the reference period is monthly?

The system should be able to trace every important conclusion back to transcript evidence.

---

# 15. Evidence Categories

Each piece of methodology information should be classified as:

```text
confirmed
inferred
assumption
proposed
unknown
contradicted
rejected
```

Never treat:

```text
inferred
assumption
proposed
```

as equivalent to:

```text
confirmed
```

This distinction must appear in the final report.

---

# 16. Objective Detection

The system should determine:

```text
What is the business trying to achieve?
```

Example:

```json
{
  "objective": "Develop a monthly indicator measuring active establishments.",
  "status": "confirmed",
  "confidence": 0.92,
  "evidence": [...]
}
```

If the objective changes during the meeting:

```text
Initial objective
       ↓
Refined objective
       ↓
Final objective
```

preserve the history.

---

# 17. Methodology Gap Detection

Evaluate the transcript against a methodology checklist.

At minimum:

```text
Objective
Population
Statistical unit
Reference period
Geographic scope
Indicators
Dimensions
Definitions
Data sources
Business rules
Classification
Quality requirements
Frequency
Disaggregation
Constraints
Assumptions
Output requirements
```

For each:

```json
{
  "concept": "statistical_unit",
  "status": "open",
  "priority": 0.88,
  "reason": "The discussion refers to establishments and companies interchangeably."
}
```

---

# 18. Gap Priority

Use the existing production logic if available.

Otherwise implement:

```text
priority =
methodology_impact
× information_gap
× uncertainty
× downstream_dependency
```

Normalize to:

```text
0.0 – 1.0
```

The report must explain why the question was prioritized.

Do not expose hidden chain-of-thought.

Instead provide concise operational rationale.

---

# 19. Question Generation

For each important unresolved gap, generate:

```json
{
  "question_id": "Q001",
  "question": "What should be the reference period for this indicator?",
  "target_gap": "reference_period",
  "priority": 0.91,
  "why_asked": "The reference period is required to define how the indicator is measured.",
  "expected_information": "measurement frequency/reference period"
}
```

Questions must be in English.

The meeting transcript may be Arabic.

---

# 20. Detect Answers in the Conversation

This is an important evaluation feature.

The system should determine whether later transcript segments already answer a previously generated question.

Example:

```text
Question:
What should be the reference period?

Later transcript:
"نريد المؤشر بشكل شهري."
```

The system should recognize:

```text
Answer detected
reference_period = monthly
```

rather than generating another redundant question.

---

# 21. Question Lifecycle

Track:

```text
candidate
presented
asked
answered
skipped
deferred
rejected
superseded
```

Example:

```json
{
  "question_id": "Q001",
  "status_history": [
    {
      "status": "candidate",
      "timestamp": "..."
    },
    {
      "status": "presented",
      "timestamp": "..."
    },
    {
      "status": "answered",
      "timestamp": "..."
    }
  ]
}
```

---

# 22. Answer Interpretation

Convert answers into structured information.

Example:

```json
{
  "interpretations": [
    {
      "concept": "reference_period",
      "value": "monthly",
      "status": "confirmed",
      "confidence": 0.96,
      "evidence": [...]
    }
  ],
  "new_requirements": [],
  "new_constraints": [],
  "new_definitions": [],
  "new_business_rules": [],
  "open_questions": []
}
```

Use Pydantic models.

LLM output must never be accepted blindly.

---

# 23. Contradiction Detection

The evaluator must intentionally test contradictions.

Example:

Early meeting:

```text
"The indicator should be monthly."
```

Later:

```text
"We actually need this quarterly."
```

The system should NOT silently overwrite monthly.

Expected:

```text
CONFLICT DETECTED

Existing:
Monthly

New:
Quarterly

Status:
Needs human resolution
```

The final report must identify unresolved contradictions.

---

# 24. Candidate Methodology Scope

At the end of processing generate:

```json
{
  "objective": "",
  "population": "",
  "statistical_unit": "",
  "reference_period": "",
  "geographic_scope": "",
  "indicators": [],
  "dimensions": [],
  "data_sources": [],
  "definitions": [],
  "business_rules": [],
  "quality_requirements": [],
  "constraints": [],
  "assumptions": [],
  "open_questions": [],
  "readiness_score": 0.0,
  "readiness_status": "in_progress"
}
```

Every populated field should be traceable to evidence.

---

# 25. Readiness Evaluation

Calculate or reuse existing readiness logic.

Possible states:

```text
insufficient
in_progress
ready_for_review
approved
rejected
```

The evaluator should show:

```text
Methodology Readiness: 82%

Complete:
✓ Objective
✓ Population
✓ Statistical unit
✓ Reference period

Incomplete:
○ Geographic scope
○ Quality requirements

Conflicts:
⚠ Definition of active establishment
```

Do not claim "ready" merely because the LLM generated a complete-looking document.

Readiness must reflect unresolved gaps and conflicts.

---

# 26. Knowledge Extraction

After candidate methodology generation, identify reusable organizational knowledge.

Example:

```json
{
  "knowledge_type": "definition",
  "concept": "active_establishment",
  "statement": "...",
  "status": "candidate",
  "confidence": 0.94,
  "evidence": [...]
}
```

Potential knowledge types:

```text
definition
business_rule
statistical_unit
population_definition
indicator_definition
dimension_definition
data_source
quality_rule
classification
methodological_principle
process_rule
constraint
terminology
```

Do not automatically mark knowledge as approved.

---

# 27. Human Approval Simulation

The evaluation harness should support a simulated human-review stage.

Example:

```bash
python -m evaluation.cli review \
  --run evaluation/output/M-001
```

Display:

```text
====================================
CANDIDATE METHODOLOGY
====================================

Objective:
...

Population:
...

Statistical Unit:
...

Reference Period:
...

Open Questions:
...

Conflicts:
...

Knowledge Candidates:
...

====================================
```

Allow the evaluator to:

```text
[1] Approve
[2] Reject
[3] Edit
[4] Return for revision
```

This is a simulation of the real portal workflow.

---

# 28. Interactive Review

Where practical, support editing from the CLI.

Example:

```text
Reference period:
Current: Monthly

Enter new value or press ENTER to keep:
>
```

Any manual modification must be recorded as:

```text
source_type = human
```

and must include:

```text
before
after
user/reviewer
timestamp
reason
```

---

# 29. Final Output

Generate several outputs.

## Human-readable report

```text
evaluation/output/M-001/report.html
```

Prefer HTML because it can present a rich interactive evaluation report.

Also generate:

```text
evaluation/output/M-001/report.md
```

---

# 30. Final Report Structure

The report should contain:

## Executive Summary

* meeting title
* languages detected
* duration
* number of speakers
* number of transcript segments
* final objective
* methodology readiness
* unresolved gaps
* unresolved conflicts

---

## 1. Meeting Understanding

Show:

```text
Languages:
Arabic 72%
English 28%
```

If language percentages can be calculated reliably from transcript segments.

---

## 2. Objective Evolution

Example:

```text
Initial:
Develop an establishment indicator

Refined:
D
```
