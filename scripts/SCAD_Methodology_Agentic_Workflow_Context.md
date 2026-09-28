# SCAD Methodology Agentic Workflow

## Context and Architecture Specification for an LLM Coding Agent

**Document purpose:** Provide a self-contained technical context for
implementing the future SCAD Methodology Agentic Workflow Platform.

**Audience:** LLM coding agents, solution architects, backend/frontend
developers, AI engineers, and methodology-system developers.

**Status:** Target architecture / implementation context. The existing
Methodology Discussion Portal is the current implementation baseline.
The multi-agent workflow described here is the intended future
evolution.

------------------------------------------------------------------------

# 1. Overview

## 1.1 Purpose

The SCAD Methodology Agentic Workflow is an orchestrated, human-governed
multi-agent system for taking a **methodology request** from its initial
business description through structured methodology development.

The initial request will normally arrive through one of two channels:

1.  A bilingual business meeting, primarily Arabic and/or English,
    handled by the existing Methodology Discussion Portal.
2.  One or more requirement documents, normally Word documents,
    describing the business need for a methodology.

The system must not assume that an indicator card, detailed statistical
definition, classification, frequency, unit, or complete methodology
already exists at intake.

The initial task is to understand:

> **What methodology does SCAD need to develop?**

The resulting **Methodology Case** becomes the controlled starting point
for the downstream autonomous workflow.

The overall lifecycle is:

``` text
Meeting / Requirement Document
              |
              v
     Requirement Understanding
              |
              v
       Methodology Case
              |
      Human Confirmation
              |
              v
      Agentic Workflow
              |
    +---------+----------+
    |                    |
    v                    v
International       SCAD Input /
Research            Current Practice
    |                    |
    +---------+----------+
              |
              v
    Standardized Methodology
              |
              v
       Targeted Q&A
              |
              v
    SCAD-Specific Methodology
              |
              v
       Compliance / QA
              |
              v
       Gap Assessment
              |
              v
       Approved Outputs
```

## 1.2 Architectural principle

The platform follows this principle:

> **Agents own tasks; the platform owns workflow state and authoritative
> case state.**

Individual LLM agents must not become independent systems of record.

The workflow orchestrator controls:

-   what agent runs;
-   why it runs;
-   what inputs it receives;
-   what outputs it must produce;
-   which prerequisites are satisfied;
-   whether human approval is required;
-   whether an agent should be retried;
-   whether another agent must be triggered;
-   what artifact/version is produced;
-   and when the workflow can advance.

The Methodology Case is the shared business object representing the
current understanding of the requested methodology.

## 1.3 Existing portal as the current baseline

The existing Methodology Discussion Portal is the first major capability
of this platform.

It already provides:

-   bilingual meeting support;
-   methodology requirement elicitation;
-   structured methodology state;
-   extraction of facts/inferences;
-   deterministic gap detection;
-   prioritized questions;
-   human-in-the-loop approval;
-   knowledge persistence;
-   RAG;
-   evaluation/replay.

The current portal deliberately separates the LLM from deterministic
agent control. The existing architecture uses a `MethodologyAgent` that
orchestrates extraction, state management, gap detection, and question
generation. The LLM is a reasoning component rather than the complete
definition of the agent.

The future architecture must preserve these principles.

## 1.4 What the workflow is not

The platform is not intended to be:

-   a collection of independent chatbots;
-   an uncontrolled swarm of agents;
-   a system where every agent maintains a separate methodology state;
-   a system where inferred information silently becomes fact;
-   a fully autonomous system that publishes methodology without human
    approval;
-   a system that assumes indicator cards exist at intake;
-   a replacement for deterministic validation and governance.

The intended architecture is a **central orchestrator with specialized
agents operating over shared case state, evidence, artifacts, and
workflow state**.

------------------------------------------------------------------------

# 2. Core Domain Model

## 2.1 Methodology Case

A `MethodologyCase` is the central business object.

It represents:

> The methodology that SCAD is asking the platform to develop and the
> current controlled understanding of that request.

A case is source-independent.

It can be created from:

-   a meeting;
-   a Word requirement document;
-   multiple Word documents;
-   a meeting plus documents;
-   future supported intake channels.

The case should not be defined as a "meeting record" or a "document
record".

Conceptually:

``` text
MethodologyCase
|
+-- Identity
|   +-- case_id
|   +-- title
|   +-- status
|   +-- created_at
|   +-- updated_at
|
+-- Request
|   +-- objective
|   +-- business_need
|   +-- requested_scope
|   +-- expected_outcome
|
+-- Subject
|   +-- domain
|   +-- topic
|   +-- population/scope if known
|
+-- Requirements
|   +-- explicit_requirements
|   +-- constraints
|   +-- known_preferences
|
+-- Unknowns
|   +-- missing_information
|   +-- ambiguities
|   +-- conflicts
|
+-- Evidence References
|
+-- Decisions
|
+-- Workflow State
|   +-- current_stage
|   +-- completed_stages
|   +-- pending_actions
|
+-- Artifacts
|   +-- research reports
|   +-- methodology documents
|   +-- assessment reports
|   +-- indicator cards
|   +-- QA reports
```

The Case should initially be relatively lightweight. Detailed
statistical constructs can be developed by downstream agents.

For example, at intake the system may know:

``` text
Objective:
Develop a methodology for measuring AI infrastructure and computing capacity.

Known topics:
- Accelerators / GPUs
- Compute capacity
- Data centres
- Power

Unknown:
- Formal definitions
- Coverage
- Statistical units
- Frequency
- Data sources
- Classifications
```

The system must not invent the missing elements merely to populate the
case.

## 2.2 Source

A `Source` represents an original input.

Examples:

``` text
Source
- type: meeting
- type: word_document
- type: pdf_document (future)
- type: user_input (future)
```

A source contains:

-   source identifier;
-   source type;
-   original file/transcript reference;
-   metadata;
-   language;
-   timestamps/page references where applicable;
-   access/security metadata.

## 2.3 Evidence

Evidence is extracted information that can be traced back to a source.

Example:

``` json
{
  "evidence_id": "E001",
  "source_id": "DOC-001",
  "type": "business_requirement",
  "statement": "SCAD requires a methodology for measuring AI infrastructure capacity.",
  "location": "Section 1, paragraph 2",
  "language": "en",
  "provenance": {
    "source_type": "word_document",
    "source_location": "Section 1"
  }
}
```

Evidence and case state must remain conceptually separate.

``` text
SOURCE
   |
   v
EVIDENCE
   |
   v
CASE STATE
```

This provides traceability and prevents an agent from rewriting the
original source into an untraceable conclusion.

## 2.4 Facts, inferences, proposals and decisions

The system must preserve epistemic status.

Information may be:

-   `unknown`
-   `inferred`
-   `proposed`
-   `confirmed`
-   `rejected`
-   `conflicting`

The workflow must not treat an inferred or proposed value as confirmed
simply because an LLM generated it.

A useful pattern is:

``` text
Evidence
   |
   v
Agent interpretation
   |
   v
Proposal / inference
   |
   v
Validation / human review
   |
   v
Confirmed case state
```

## 2.5 Artifacts

Agents may produce documents or structured artifacts.

Examples:

-   international research report;
-   standardized methodology;
-   SCAD current-practice assessment;
-   question set;
-   Q&A record;
-   SCAD-specific methodology;
-   indicator cards;
-   compliance report;
-   gap assessment report.

Every artifact should have:

-   `artifact_id`;
-   `case_id`;
-   `agent_id`;
-   `workflow_stage`;
-   version;
-   creation timestamp;
-   status;
-   input references;
-   evidence references;
-   approval status.

------------------------------------------------------------------------

# 3. Agent Roles

## 3.1 Agent: Methodology Requirement Elicitation Agent

### Purpose

Convert a business meeting into a structured understanding of the
methodology request.

This is the existing Methodology Discussion Portal capability.

### Inputs

-   live meeting/transcript;
-   Arabic and English discussion;
-   meeting metadata;
-   optionally previously known case context.

### Responsibilities

-   understand Arabic, English and code-switching;
-   identify the business objective;
-   identify the methodology being requested;
-   extract explicit requirements;
-   distinguish facts from inference;
-   identify missing information;
-   identify contradictions;
-   ask high-priority questions;
-   maintain methodology state;
-   produce a structured requirement summary;
-   obtain human confirmation where required.

### Outputs

-   evidence records;
-   requirement extraction;
-   structured Methodology Case proposal;
-   unresolved questions;
-   confirmed answers;
-   meeting journal;
-   methodology request summary.

### Dependencies

-   transcription;
-   LLM;
-   deterministic state manager;
-   gap detector;
-   question generator;
-   PostgreSQL;
-   optional approved RAG context.

### Important constraint

This agent does not develop the full methodology.

Its primary responsibility is to establish:

> **What methodology does SCAD need?**

------------------------------------------------------------------------

# 3.2 Agent: Requirement Document Analysis Agent

### Purpose

Create a Methodology Case from Word requirement document(s).

### Inputs

-   one or more Word documents;
-   document metadata;
-   optional existing case context.

### Responsibilities

-   parse documents;
-   identify the stated business need;
-   identify explicit requirements;
-   extract scope and constraints;
-   identify requested outputs;
-   identify ambiguities;
-   preserve document/page/section provenance;
-   distinguish explicit statements from inferred interpretation;
-   produce a structured case proposal.

### Outputs

-   extracted evidence;
-   requirement summary;
-   Methodology Case proposal;
-   unresolved questions;
-   source-to-case traceability.

### Dependencies

-   document parser;
-   LLM extraction service;
-   evidence/provenance service;
-   Methodology Case service.

### Important constraint

The agent must not assume that detailed indicator definitions exist.

If a document says:

> "Develop indicators for AI infrastructure"

that is a requirement to develop the indicators, not evidence that the
indicators are already defined.

------------------------------------------------------------------------

# 3.3 Agent: Methodology Case Consolidation Agent

### Purpose

Combine evidence from meetings and/or documents into one coherent
Methodology Case.

### Inputs

-   evidence from intake agents;
-   existing case state;
-   previous decisions;
-   user corrections.

### Responsibilities

-   consolidate overlapping requirements;
-   detect contradictions;
-   preserve source references;
-   identify unresolved issues;
-   maintain status of each important field;
-   prepare the case for human confirmation.

### Outputs

-   consolidated Methodology Case;
-   conflict list;
-   unresolved requirements;
-   evidence mappings.

### Dependencies

-   case state service;
-   evidence store;
-   deterministic validation.

### Human gate

The case should normally reach:

``` text
REQUIREMENTS_REVIEW
```

before downstream methodology development begins.

------------------------------------------------------------------------

# 3.4 Agent: International Research Agent

### Purpose

Identify international standards, frameworks, methodologies, NSO
practices, and other authoritative sources relevant to the requested
methodology.

### Inputs

-   confirmed Methodology Case;
-   approved case scope;
-   research constraints.

### Responsibilities

-   identify relevant international standards;
-   search relevant statistical organizations;
-   identify methodological manuals;
-   identify classifications and frameworks;
-   identify relevant quality frameworks;
-   identify comparable national practices;
-   collect source metadata;
-   summarize relevance;
-   extract evidence;
-   identify methodological differences;
-   preserve URLs/source provenance.

### Outputs

-   International Evidence Package;
-   source register;
-   research findings;
-   unresolved research questions;
-   research report artifact.

### Dependencies

-   web research tools where permitted;
-   document retrieval;
-   approved internal knowledge;
-   evidence store.

### Important constraint

Research findings are not automatically authoritative case facts.

They remain sourced evidence and recommendations until incorporated into
an approved methodology.

------------------------------------------------------------------------

# 3.5 Agent: Standardized Methodology Development Agent

### Purpose

Develop a generic, internationally informed methodology before
incorporating SCAD-specific requirements.

### Inputs

-   confirmed Methodology Case;
-   International Evidence Package;
-   approved standards and sources.

### Responsibilities

-   synthesize international evidence;
-   establish conceptual definitions;
-   identify relevant statistical concepts;
-   propose scope and coverage;
-   develop measurement concepts;
-   define methodological processes;
-   identify data-source considerations;
-   identify classifications;
-   identify quality considerations;
-   document unresolved issues;
-   maintain source annotations.

### Outputs

-   Standardized Methodology document;
-   structured methodology specification;
-   unresolved methodological issues;
-   evidence mappings.

### Dependencies

-   International Research Agent;
-   document generation;
-   approved evidence;
-   methodology schema.

### Human gate

The standardized methodology should normally be presented for explicit
human review before SCAD-specific development proceeds.

------------------------------------------------------------------------

# 3.6 Agent: SCAD Input / Current Practice Analysis Agent

### Purpose

Analyze SCAD-provided material after the standardized methodology
exists.

### Inputs

-   SCAD documents;
-   current methodology documents;
-   existing indicator cards if they become available later;
-   standardized methodology;
-   Methodology Case.

### Responsibilities

-   read SCAD material;
-   identify current practice;
-   map current practice to the standardized methodology;
-   identify implemented versus missing components;
-   identify SCAD-specific constraints;
-   identify existing terminology;
-   identify evidence of current processes.

### Outputs

-   SCAD Current Practice Assessment;
-   mapping matrix;
-   identified gaps;
-   SCAD evidence package;
-   questions requiring clarification.

### Dependencies

-   document analysis;
-   standardized methodology;
-   evidence store.

------------------------------------------------------------------------

# 3.7 Agent: Methodology Q&A / Clarification Agent

### Purpose

Resolve missing information required to develop the SCAD-specific
methodology.

### Inputs

-   standardized methodology;
-   SCAD current-practice assessment;
-   Methodology Case;
-   identified gaps/unknowns.

### Responsibilities

-   identify information that genuinely requires SCAD input;
-   avoid asking questions already answered by evidence;
-   prioritize questions;
-   formulate clear questions;
-   record responses;
-   map responses to methodology fields;
-   detect conflicts between responses and previous evidence.

### Outputs

-   question set;
-   answers;
-   updated evidence;
-   updated case state;
-   unresolved questions.

### Dependencies

-   gap detection;
-   case state;
-   human interaction.

### Important constraint

The agent should ask only targeted questions needed to resolve material
uncertainty.

------------------------------------------------------------------------

# 3.8 Agent: Indicator Conceptualization Agent

### Purpose

Develop the indicator structure once sufficient methodological
understanding exists.

This is downstream from the initial Methodology Case.

### Inputs

-   approved standardized methodology;
-   approved SCAD requirements;
-   SCAD-specific methodology;
-   research evidence;
-   confirmed definitions and concepts.

### Responsibilities

-   identify candidate indicators;
-   determine whether multiple indicators are required;
-   propose indicator names;
-   develop definitions;
-   identify units;
-   identify population/coverage;
-   identify numerator/denominator where relevant;
-   identify frequency;
-   identify data sources;
-   identify classifications;
-   identify derivation rules;
-   identify quality considerations.

### Outputs

-   indicator specifications;
-   indicator card drafts;
-   indicator-to-methodology traceability.

### Important constraint

Indicator cards are outputs of the methodology-development process and
should not be assumed to exist at intake.

------------------------------------------------------------------------

# 3.9 Agent: SCAD-Specific Methodology Development Agent

### Purpose

Develop the final SCAD-specific methodology.

### Inputs

-   Methodology Case;
-   approved standardized methodology;
-   SCAD current-practice assessment;
-   Q&A results;
-   approved indicator specifications;
-   relevant evidence.

### Responsibilities

-   adapt standardized methodology to SCAD;
-   incorporate confirmed SCAD-specific information;
-   document Abu Dhabi/SCAD exceptions;
-   mark unresolved information;
-   use the approved SCAD document template;
-   preserve required formatting;
-   integrate indicator concepts;
-   maintain traceability.

### Outputs

-   SCAD-specific methodology document;
-   structured methodology;
-   annotations;
-   unresolved confirmation items.

### Annotation conventions

Where applicable, use:

``` text
[Aligned with: source]
[Abu Dhabi exception]
[To be confirmed by SCAD]
```

### Human gate

Final SCAD methodology requires human review and approval.

------------------------------------------------------------------------

# 3.10 Agent: Compliance and QA Agent

### Purpose

Verify that outputs satisfy methodological, structural, provenance, and
document requirements.

### Inputs

-   methodology artifact;
-   source evidence;
-   case state;
-   workflow requirements;
-   template rules.

### Responsibilities

-   check completeness;
-   check internal consistency;
-   check terminology;
-   check evidence traceability;
-   check unsupported claims;
-   check unresolved fields;
-   check required annotations;
-   check template compliance;
-   check source citations;
-   identify conflicts;
-   validate that human approvals have occurred where required.

### Outputs

-   QA report;
-   validation findings;
-   blocking issues;
-   non-blocking issues;
-   approval recommendation as a technical status only.

The QA agent must not silently modify authoritative methodology state.

------------------------------------------------------------------------

# 3.11 Agent: Gap Assessment Agent

### Purpose

Compare current SCAD methodology/practice against the standardized
methodology and produce a formal gap assessment.

### Inputs

-   standardized methodology;
-   SCAD current-practice assessment;
-   approved SCAD methodology;
-   evidence;
-   decisions.

### Responsibilities

-   identify methodological gaps;
-   classify gaps;
-   identify missing processes;
-   identify missing data;
-   identify missing definitions;
-   identify differences from international practice;
-   provide evidence for each gap;
-   distinguish confirmed gaps from assumptions.

### Outputs

-   Gap Assessment Report;
-   gap register;
-   recommendations/actions as documented findings;
-   evidence references.

------------------------------------------------------------------------

# 3.12 Cross-Cutting Agent: Document Generation Agent

### Purpose

Create and modify formal documents.

### Inputs

-   structured artifact specification;
-   official SCAD template;
-   approved content;
-   formatting rules.

### Responsibilities

-   generate DOCX;
-   preserve template formatting;
-   add required sections;
-   maintain headings and styles;
-   insert tables where appropriate;
-   create cover/title content;
-   perform structural validation.

### Important constraint

Document generation should be downstream from structured methodology
state.

The DOCX should not become the only source of truth.

------------------------------------------------------------------------

# 3.13 Cross-Cutting Agent: Knowledge Management Agent

### Purpose

Maintain reusable approved methodology knowledge.

### Responsibilities

-   persist approved findings;
-   manage knowledge lifecycle;
-   attach provenance;
-   classify knowledge;
-   index approved knowledge;
-   expose approved knowledge to future agents.

Only approved/published knowledge should become authoritative reusable
RAG knowledge.

------------------------------------------------------------------------

# 4. Workflow Orchestration

## 4.1 Orchestrator responsibilities

The orchestrator is the control plane.

It does not perform the specialized methodology work itself.

It manages:

``` text
Case
Workflow
Stages
Agent Tasks
Dependencies
Approvals
Artifacts
Events
Retries
Failures
Audit Trail
```

## 4.2 Workflow state

Example:

``` yaml
workflow:
  case_id: METH-2026-0042

  current_stage: STANDARDIZED_METHODOLOGY

  stages:
    - requirement_intake
    - case_confirmation
    - international_research
    - standardized_methodology
    - scad_input_analysis
    - clarification
    - indicator_development
    - scad_methodology
    - compliance
    - gap_assessment
    - completion
```

## 4.3 Stage states

Each stage should have explicit status:

``` text
PENDING
READY
RUNNING
WAITING_FOR_AGENT
WAITING_FOR_HUMAN
COMPLETED
FAILED
BLOCKED
CANCELLED
```

## 4.4 Agent task

An agent execution should be represented as a task.

Example:

``` json
{
  "task_id": "TASK-0042-003",
  "case_id": "METH-2026-0042",
  "agent": "international_research_agent",
  "stage": "international_research",
  "status": "READY",
  "inputs": [
    "case:METH-2026-0042"
  ],
  "required_outputs": [
    "source_register",
    "evidence_package",
    "research_report"
  ],
  "approval_required": false
}
```

## 4.5 Agent communication

Agents should communicate through structured task outputs and shared
state rather than informal agent-to-agent chat.

Preferred pattern:

``` text
Agent A
   |
   v
Structured Output
   |
   v
Orchestrator
   |
   +--> validate
   +--> persist
   +--> update case
   +--> determine next task
   |
   v
Agent B
```

Direct agent-to-agent calls may be allowed as an implementation
optimization, but the orchestrator must remain aware of the resulting
state transition.

## 4.6 Event-driven execution

The workflow should emit events such as:

``` text
CASE_CREATED
CASE_UPDATED
CASE_READY_FOR_REVIEW
CASE_APPROVED
STAGE_STARTED
AGENT_STARTED
AGENT_COMPLETED
AGENT_FAILED
ARTIFACT_CREATED
ARTIFACT_UPDATED
APPROVAL_REQUESTED
APPROVAL_GRANTED
APPROVAL_REJECTED
QUESTION_REQUESTED
QUESTION_ANSWERED
WORKFLOW_BLOCKED
WORKFLOW_COMPLETED
```

The existing real-time event architecture can be extended for these
workflow events.

------------------------------------------------------------------------

# 5. Methodology Request Handling

## 5.1 What is a methodology request?

A methodology request is a business request that indicates SCAD needs to
develop, revise, standardize, formalize, assess, or document a
statistical methodology.

Examples:

``` text
"We need a methodology for measuring AI infrastructure."

"Can you develop a standard methodology for this indicator?"

"We need to establish how this statistic should be measured."

"SCAD currently produces this statistic but needs a formal methodology."

"We need to develop a methodology for measuring graduate outcomes."
```

The system should not rely on exact keywords.

Recognition should use semantic understanding plus deterministic rules.

## 5.2 Request recognition pipeline

``` text
Input
  |
  v
Source Classification
  |
  v
Content Extraction
  |
  v
Requirement Detection
  |
  v
Methodology Request Classification
  |
  +---- not methodology request ----> General workflow
  |
  +---- methodology request ---------> Create Methodology Case
```

## 5.3 Meeting recognition

For meetings, the existing portal should detect whether the discussion
contains a methodology-development request.

Signals may include:

-   explicit request to develop methodology;
-   request to define measurement;
-   request to standardize an indicator;
-   request to establish statistical concepts;
-   discussion of definitions, scope, sources, frequency,
    classifications;
-   explicit request for a methodology document.

The classifier should return structured output:

``` json
{
  "is_methodology_request": true,
  "confidence": 0.94,
  "request_type": "new_methodology",
  "evidence_ids": ["E001", "E004"],
  "reason": "Business team explicitly requests development of a methodology for..."
}
```

The confidence value is not a substitute for human confirmation where
required.

## 5.4 Document recognition

For Word documents:

``` text
DOCX
 |
 v
Parse document
 |
 v
Extract sections / paragraphs
 |
 v
Requirement analysis
 |
 v
Methodology request classification
 |
 v
Evidence creation
 |
 v
Methodology Case proposal
```

The system should preserve:

-   filename;
-   document ID;
-   section;
-   heading;
-   paragraph;
-   page where available;
-   original text;
-   extracted evidence.

## 5.5 Selecting the initial workflow

Once a methodology request is confirmed, the orchestrator should select
the initial workflow.

Minimum workflow:

``` text
Requirement Intake
        |
        v
Methodology Case
        |
        v
Human Confirmation
        |
        v
International Research
        |
        v
Standardized Methodology
```

Additional stages are activated based on case conditions.

For example:

``` text
IF SCAD input documents are required
    -> activate SCAD Input Analysis

IF standardized methodology reveals missing SCAD information
    -> activate Clarification

IF methodology requires indicators
    -> activate Indicator Conceptualization

IF SCAD-specific methodology is required
    -> activate SCAD Methodology Agent

IF final methodology is complete
    -> activate Compliance / QA

IF gap assessment is requested/required
    -> activate Gap Assessment
```

## 5.6 Dynamic workflow selection

The orchestrator should not hard-code every future workflow branch.

Use workflow definitions.

Example:

``` yaml
workflow_definition:
  name: methodology_development

  triggers:
    - methodology_request_confirmed

  stages:

    requirement_case:
      agent: methodology_case_agent

    international_research:
      agent: international_research_agent
      depends_on:
        - requirement_case

    standardized_methodology:
      agent: standardized_methodology_agent
      depends_on:
        - international_research
      approval: required

    scad_input_analysis:
      agent: scad_input_agent
      condition: scad_documents_available
      depends_on:
        - standardized_methodology

    clarification:
      agent: methodology_qa_agent
      condition: unresolved_scad_requirements
      depends_on:
        - scad_input_analysis

    indicator_development:
      agent: indicator_agent
      condition: indicators_required
      depends_on:
        - standardized_methodology
        - clarification

    scad_methodology:
      agent: scad_methodology_agent
      depends_on:
        - standardized_methodology
        - scad_input_analysis
        - clarification

    compliance:
      agent: compliance_agent
      depends_on:
        - scad_methodology

    gap_assessment:
      agent: gap_assessment_agent
      condition: gap_assessment_required
      depends_on:
        - scad_methodology
        - standardized_methodology
```

------------------------------------------------------------------------

# 6. End-to-End Workflow

## Step 1: Intake

The system receives:

``` text
Meeting
OR
Word document(s)
```

The intake layer creates a `Source`.

## Step 2: Requirement extraction

The appropriate intake agent extracts evidence.

For a meeting:

``` text
Meeting
 -> Transcription
 -> Methodology Requirement Elicitation Agent
 -> Evidence
```

For documents:

``` text
DOCX
 -> Document Parser
 -> Requirement Document Analysis Agent
 -> Evidence
```

## Step 3: Methodology request detection

The system determines:

``` text
Is this a methodology request?
```

If no, route to the appropriate non-methodology workflow.

If yes, continue.

## Step 4: Create Methodology Case

The Case Consolidation Agent converts evidence into a structured case.

## Step 5: Human confirmation

The system presents:

``` text
What we understand you are asking SCAD to develop:
-----------------------------------------------
Title
Objective
Business need
Scope
Known requirements
Known constraints
Unknowns
Questions
-----------------------------------------------
```

Human actions:

``` text
CONFIRM
EDIT
REQUEST MORE INFORMATION
CANCEL
```

No downstream autonomous methodology development should start before the
required confirmation.

## Step 6: International research

The orchestrator creates an International Research Agent task.

The agent produces:

-   source register;
-   evidence;
-   findings;
-   research report.

The orchestrator validates and persists the results.

## Step 7: Standardized methodology

The Standardized Methodology Agent consumes the approved research
package.

It creates the generic methodology.

## Step 8: Human approval

The methodology is submitted for review.

Possible outcomes:

``` text
APPROVED
REQUEST_CHANGES
REJECTED
```

If changes are requested:

``` text
Human feedback
     |
     v
Agent task
     |
     v
Revised artifact
     |
     v
Approval again
```

## Step 9: SCAD input analysis

If SCAD-specific input documents are available or required, the SCAD
Input Agent analyzes them.

## Step 10: Clarification

If material information is missing, the Q&A Agent generates targeted
questions.

The workflow enters:

``` text
WAITING_FOR_HUMAN
```

until answers are provided.

## Step 11: Indicator development

Once enough methodology information exists, the Indicator Agent develops
candidate indicators and indicator cards.

Indicator cards are downstream outputs, not initial intake requirements.

## Step 12: SCAD-specific methodology

The SCAD Methodology Agent produces the SCAD-specific methodology using:

``` text
Methodology Case
+
International Research
+
Standardized Methodology
+
SCAD Evidence
+
Human Answers
+
Approved Indicator Specifications
```

## Step 13: Compliance / QA

The QA Agent validates the result.

Blocking issues prevent completion.

## Step 14: Gap assessment

Where required, the Gap Assessment Agent compares:

``` text
International / Standardized Methodology
             VS
SCAD Current Practice
```

and produces the formal gap assessment.

## Step 15: Final approval

Final outputs require human approval.

## Step 16: Knowledge publication

Approved reusable findings may enter the institutional knowledge base.

Only approved knowledge should be exposed as authoritative RAG
knowledge.

------------------------------------------------------------------------

# 7. Human-in-the-Loop Model

Human involvement is a governance mechanism, not a failure of autonomy.

Recommended mandatory gates:

``` text
Methodology Request
        |
        v
Case Confirmation
        |
        v
Standardized Methodology
        |
     APPROVAL
        |
        v
SCAD Methodology
        |
     APPROVAL
        |
        v
Final Outputs
```

Agents may work autonomously between gates.

The system should clearly distinguish:

``` text
Agent-generated
Human-reviewed
Human-confirmed
Approved knowledge
```

------------------------------------------------------------------------

# 8. Example Scenario

## 8.1 Business request

A Social Statistics team asks:

> "We need SCAD to develop a methodology for measuring graduate
> employment outcomes. We currently have different data sources and
> definitions and need a standardized approach."

This request could arrive through a meeting.

## 8.2 Meeting processing

The Methodology Requirement Elicitation Agent identifies:

``` text
Methodology request: YES

Requested methodology:
Graduate employment outcomes

Business need:
Standardize measurement across data sources

Known issues:
- Different definitions
- Multiple data sources
- Need standardized approach

Unknown:
- Target population
- Reference period
- Employment definition
- Required indicators
- Data sources
- Frequency
```

Evidence is linked to transcript segments.

## 8.3 Methodology Case

The case becomes:

``` yaml
case_id: METH-2026-0042

title: Graduate Employment Outcomes Methodology

objective:
  Develop a standardized methodology for measuring graduate employment outcomes.

business_need:
  Establish consistent concepts and measurement across relevant data sources.

known_requirements:
  - Standardized approach
  - Multiple data sources must be considered

unknowns:
  - Target population
  - Employment definition
  - Reference period
  - Indicators
  - Frequency
```

The business team confirms the case.

## 8.4 International research

The orchestrator starts:

``` text
International Research Agent
```

It researches:

-   international statistical standards;
-   relevant NSOs;
-   graduate outcome methodologies;
-   labour/statistical frameworks;
-   relevant classifications.

It creates the evidence package.

## 8.5 Standardized methodology

The Standardized Methodology Agent consumes the research and produces:

``` text
Graduate Employment Outcomes
Standardized Methodology
```

It identifies that several concepts must be clarified:

-   graduate cohort;
-   employment status;
-   reference period;
-   employment classification;
-   data sources;
-   outcome measures.

Human approval is requested.

## 8.6 SCAD input

SCAD uploads available current-practice documents.

The SCAD Input Agent maps current practice against the standardized
methodology.

It discovers:

``` text
Employment status definition:
Not formally standardized.

Graduate population:
Defined differently by source.

Reference period:
Not consistent.

Administrative data:
Available.

Survey data:
Available.
```

## 8.7 Q&A

The Q&A Agent creates targeted questions:

``` text
1. Which graduate cohorts should be included?

2. What reference period should define employment outcome?

3. Should self-employment be classified as employment?

4. Which administrative source should be authoritative where sources conflict?
```

SCAD answers the questions.

The answers become confirmed case evidence.

## 8.8 Indicator development

The Indicator Agent now develops candidate indicators.

For example:

``` text
Graduate Employment Rate
Graduate Unemployment Rate
Graduate Labour Force Participation Rate
```

The agent develops the corresponding indicator specifications.

These did not exist at intake; they were developed as part of the
methodology workflow.

## 8.9 SCAD methodology

The SCAD Methodology Agent combines:

``` text
International evidence
+
Standardized methodology
+
SCAD practice
+
SCAD answers
+
Indicator specifications
```

and creates the SCAD-specific methodology document.

## 8.10 QA

The Compliance Agent verifies:

``` text
[PASS] Required sections
[PASS] Source traceability
[PASS] Definitions
[PASS] Indicator consistency
[PASS] SCAD annotations
[PASS] Template compliance
[WARNING] One unresolved data-source issue
```

The workflow remains blocked until the blocking issue is resolved.

## 8.11 Gap assessment

The Gap Assessment Agent compares current SCAD practice against the
standardized methodology and creates the final Gap Assessment Report.

## 8.12 Completion

After human approval:

``` text
Methodology Case
        |
        +-- Approved Standardized Methodology
        |
        +-- Approved SCAD Methodology
        |
        +-- Approved Indicator Cards
        |
        +-- Compliance Report
        |
        +-- Gap Assessment Report
        |
        +-- Approved reusable knowledge
```

The case is marked:

``` text
COMPLETED
```

------------------------------------------------------------------------

# 9. Implementation Guidance for the Coding Agent

## 9.1 Build the platform incrementally

Do not attempt to implement every agent initially.

Recommended order:

``` text
Phase A
Methodology Case + Evidence model

Phase B
Workflow / Agent orchestration framework

Phase C
Existing meeting intake integration

Phase D
Word document requirement intake

Phase E
International Research Agent

Phase F
Standardized Methodology Agent

Phase G
SCAD Input + Q&A

Phase H
Indicator Agent

Phase I
SCAD Methodology Agent

Phase J
Compliance + Gap Assessment
```

## 9.2 Preserve existing portal architecture

The current portal already contains important capabilities that should
be reused rather than rewritten:

-   `MethodologyAgent`;
-   `MethodologyState`;
-   deterministic state management;
-   gap detection;
-   question prioritization;
-   PostgreSQL persistence;
-   Qdrant knowledge retrieval;
-   WebSocket/event infrastructure;
-   meeting/Jitsi integration;
-   evaluation harness;
-   HITL knowledge lifecycle.

The new orchestration layer should sit above these capabilities.

## 9.3 Do not create multiple competing states

There should be one authoritative case state.

Avoid:

``` text
Research Agent State
Methodology Agent State
SCAD Agent State
QA Agent State
```

Instead:

``` text
                  Methodology Case
                        |
       +----------------+----------------+
       |                |                |
   Research         SCAD Analysis       QA
    Agent             Agent            Agent
       |                |                |
       +----------------+----------------+
                        |
                 Orchestrator
```

Agents may maintain temporary execution state, but persistent business
truth belongs to the platform.

## 9.4 Do not let LLMs control workflow transitions directly

LLMs may recommend:

``` text
"More SCAD information is required."
```

The orchestrator determines whether the workflow actually transitions
to:

``` text
WAITING_FOR_HUMAN
```

Similarly, an LLM may report that an artifact is complete, but
deterministic validation must determine whether required outputs exist.

## 9.5 Every agent should have a contract

Each agent should expose:

``` text
Agent Metadata
    name
    version
    purpose
    input_schema
    output_schema
    required_tools
    required_context
    approval_requirements
    failure_policy
```

Example:

``` yaml
agent:
  id: international_research_agent
  version: 1.0

  input:
    - methodology_case
    - approved_context

  output:
    - source_register
    - evidence_package
    - research_report

  approval_required: false

  can_modify_case: false

  can_propose_case_updates: true
```

## 9.6 Treat provenance as mandatory

Every significant agent-generated statement should be traceable to:

-   source evidence;
-   research source;
-   human response;
-   previous approved artifact;
-   or explicit agent inference.

Do not allow unexplained claims into final methodology documents.

------------------------------------------------------------------------

# 10. Recommended Target Architecture

``` text
                         USER
                          |
              +-----------+-----------+
              |                       |
           Meeting                 Documents
              |                       |
              v                       v
       Requirement              Requirement
       Elicitation              Document Agent
          Agent                       |
              |                       |
              +-----------+-----------+
                          |
                          v
                    EVIDENCE STORE
                          |
                          v
                 METHODOLOGY CASE
                          |
                  Human Confirmation
                          |
                          v
                  WORKFLOW ENGINE
                          |
          +---------------+----------------+
          |               |                |
          v               v                v
      Research       SCAD Input         Future
       Agent           Agent           Agents
          |               |
          v               v
    International      Current
      Evidence         Practice
          |               |
          +-------+-------+
                  |
                  v
       Standardized Methodology
                  |
            Human Approval
                  |
                  v
             Q&A Agent
                  |
                  v
         Indicator Agent
                  |
                  v
       SCAD Methodology Agent
                  |
                  v
          Compliance Agent
                  |
                  v
       Gap Assessment Agent
                  |
                  v
          Human Approval
                  |
                  v
          APPROVED OUTPUTS
                  |
                  v
       APPROVED KNOWLEDGE BASE
```

------------------------------------------------------------------------

# 11. Non-Negotiable Design Principles

1.  **Methodology Case is source-independent.** A meeting is an intake
    channel, not the case itself.

2.  **Requirement documents and meetings converge into the same Case
    model.**

3.  **The initial case describes the requested methodology, not the
    final statistical design.**

4.  **Indicator cards are downstream outputs.** Do not require indicator
    cards at intake.

5.  **Evidence and Case State are separate.**

6.  **Every important conclusion should have provenance.**

7.  **Inference is not fact.**

8.  **Agents perform specialized tasks; the orchestrator controls
    workflow.**

9.  **There must be one authoritative persistent case state.**

10. **LLMs do not independently control workflow transitions.**

11. **Human approval is required at defined governance gates.**

12. **Only approved knowledge becomes authoritative reusable
    knowledge.**

13. **Agents should communicate through structured contracts and
    persisted state.**

14. **Workflow stages must be observable and auditable.**

15. **The architecture must support adding future agents without
    redesigning the core case model.**

16. **The existing Methodology Discussion Portal should be extended, not
    discarded.**

17. **The platform should preserve uncertainty and conflicting evidence
    rather than forcing premature decisions.**

18. **Final documents are artifacts generated from structured state;
    they are not the sole system of record.**

------------------------------------------------------------------------

# 12. Summary for the Coding Agent

The target system is a **SCAD Methodology Agentic Workflow Platform**.

The platform starts when SCAD provides a methodology requirement through
a meeting or requirement document.

The system:

``` text
1. Ingests the source
2. Extracts evidence
3. Detects a methodology request
4. Creates a Methodology Case
5. Obtains human confirmation
6. Starts the appropriate workflow
7. Runs specialized agents in dependency order
8. Persists structured state and evidence
9. Requests human input when required
10. Produces methodology artifacts
11. Validates outputs
12. Produces indicator cards as a downstream output
13. Performs gap assessment where required
14. Obtains final approval
15. Publishes approved reusable knowledge
```

The core architectural abstraction is:

``` text
                INPUT
                  |
                  v
              EVIDENCE
                  |
                  v
          METHODOLOGY CASE
                  |
                  v
           ORCHESTRATOR
                  |
        +---------+---------+
        |         |         |
        v         v         v
      AGENT     AGENT     AGENT
        |         |         |
        +---------+---------+
                  |
                  v
        STRUCTURED ARTIFACTS
                  |
                  v
           HUMAN APPROVAL
                  |
                  v
       APPROVED KNOWLEDGE
```

The coding agent should implement this as a **platform capability**, not
as a collection of hard-coded sequential scripts. New methodology agents
must be registerable, discoverable, executable, observable, and governed
through the same orchestration framework.
