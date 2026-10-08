# Demo — Multi-Agent Methodology Orchestration

A single-screen demo of the agent workflow: a transcript is turned into a
meeting case, a chain of agents processes it, and a human approval gate pauses
the workflow before it produces the final consolidated output.

Built with **Streamlit** (Python) so it runs fast and deterministically — the
agents here are mock/stub implementations that mirror the production FastAPI
workflow, and are structured so the real agents can be plugged in later.

## Folder structure

```
demo/
├── app.py           # Streamlit single-screen UI
├── agents.py        # Agent interface + deterministic mock agents
├── orchestrator.py  # workflow graph + approval-gate state machine
├── transcript.py    # transcript loading/parsing
└── README.md        # this file
transcript/
└── sample_meeting.md   # sample bilingual-style meeting transcript
```

## Run the demo

```bash
pip install streamlit
streamlit run demo/app.py
```

Then open the printed URL (usually http://localhost:8501).

## Agent flow

| # | Stage | Agent | Approval gate |
|---|---|---|---|
| 1 | requirement_case | Elicitation | — |
| 2 | international_research | Research | — |
| 3 | standardized_methodology | Standardized Methodology | ✅ |
| 4 | scad_input_analysis | SCAD Input | — |
| 5 | clarification | Clarification / Q&A | — |
| 6 | indicator_development | Indicator | — |
| 7 | scad_methodology | SCAD Methodology | ✅ |
| 8 | compliance | Compliance / QA | — |
| 9 | gap_assessment | Gap Assessment | — |

1. **Create Meeting Case** parses the transcript (`[hh:mm:ss] Speaker: …`) and
   runs the *Elicitation* agent, producing the structured meeting case.
2. The orchestrator runs subsequent agents in order, pausing at the two
   **human approval gates** (`standardized_methodology` and
   `scad_methodology`).
3. At each gate the UI shows the agent's proposal, questions, and proposed
   sections, with **Approve / Modify / Reject** actions. The workflow does not
   proceed until the human responds.
4. After the final gate, the remaining agents run and the **final consolidated
   output** (objective, sections, indicators, annotations, gap matrix,
   recommendations, decisions, open questions) is rendered on the same screen.

## How each agent is invoked

- `DemoWorkflow.start()` invokes the first agent (`elicitation`) to create the
  case.
- `DemoWorkflow.advance()` walks the `STAGES` list in `orchestrator.py`, calling
  `AGENTS[agent_key].run(context)` for each stage, and stops when it reaches an
  `approval_required` stage (setting `wf.gate`).
- The UI's **Approve / Modify / Reject** buttons call `DemoWorkflow.approve(…)`
  and then `advance()` again.

Agents never mutate workflow state — they only return a `{"summary": …,
"questions": …, …}` dict. The orchestrator owns state and transitions.

## Plugging in the real agents

The mock agents in `demo/agents.py` implement the same roles as the production
agents under `app/agents/`. To use the real (LLM-backed) agents, replace each
mock `run()` with an HTTP call to the running FastAPI backend:

```python
# e.g. create a real case from the transcript
POST http://127.0.0.1:8000/cases          {"text": transcript, "language": "auto"}
# then advance / approve the real workflow
POST http://127.0.0.1:8000/cases/{id}/advance
POST http://127.0.0.1:8000/cases/{id}/stages/{stage}/approve   {"decision": "approved"}
```

The orchestrator only consumes the returned dictionaries, so the swap is
isolated to `agents.py`.
