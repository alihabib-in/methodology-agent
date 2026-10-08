"""Single-screen demo of the multi-agent methodology orchestration.

Run from the repository root:

    pip install streamlit
    streamlit run demo/app.py

Flow: pick a transcript → "Create Meeting Case" → the orchestrator runs agents
until it reaches a human approval gate → approve/modify/reject → continues until
the next gate → produces the final consolidated output.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure this script's directory is importable so the sibling demo modules
# (orchestrator, agents, transcript) resolve regardless of how the app is
# launched (streamlit run demo/app.py, AppTest, etc.).
sys.path.insert(0, str(Path(__file__).resolve().parent))

import streamlit as st

from orchestrator import DemoWorkflow, STAGES
from transcript import extract_title, list_transcripts, load_transcript, parse_transcript

TRANSCRIPT_DIR = Path(__file__).resolve().parent.parent / "transcript"

_STATUS = {
    "pending": ("#9aa0a6", "⬜"),
    "running": ("#1a73e8", "🔄"),
    "completed": ("#188038", "✅"),
    "waiting": ("#f29900", "⏸️"),
    "rejected": ("#d93025", "❌"),
}

st.set_page_config(page_title="Methodology Orchestration Demo", layout="wide")

st.title("Multi-Agent Methodology Orchestration")
st.caption("Transcript → meeting case → agents → human approval → final output")


def status_badge(status: str) -> str:
    color, icon = _STATUS.get(status, _STATUS["pending"])
    label = status.replace("_", " ").title()
    return (
        f"<span style='display:inline-block;padding:2px 10px;border-radius:12px;"
        f"background:{color}22;color:{color};font-weight:600'>"
        f"{icon} {label}</span>"
    )


def render_stages(wf: DemoWorkflow) -> None:
    st.subheader("Workflow stages")
    for stage_id, _agent_key, approval in STAGES:
        status = wf.stage_status[stage_id]
        label = wf.stage_label(stage_id)
        gate = " · approval gate" if approval else ""
        st.markdown(
            f"{status_badge(status)} &nbsp; **{label}**<span style='color:#80868b'>"
            f"{gate}</span>",
            unsafe_allow_html=True,
        )


def render_approval(wf: DemoWorkflow) -> None:
    if wf.gate is None:
        return
    output = wf.stage_outputs.get(wf.gate, {})
    stage_label = wf.stage_label(wf.gate)

    with st.container(border=True):
        st.markdown("### 🛑 Human Approval Required")
        st.markdown(f"**Stage:** {stage_label}")
        st.markdown(f"**Proposal:** {output.get('summary', '')}")

        if output.get("questions"):
            st.markdown("**Needs your confirmation:**")
            for q in output["questions"]:
                st.markdown(f"- {q}")

        if output.get("sections"):
            with st.expander("View proposed sections"):
                for s in output["sections"]:
                    st.markdown(f"- {s}")

        if output.get("annotations"):
            st.markdown("**Annotations:**")
            for a in output["annotations"]:
                st.markdown(f"- `{a}`")

        col1, col2, col3 = st.columns(3)
        if col1.button("✅ Approve", type="primary", use_container_width=True):
            wf.approve("approve")
            wf.advance()
            st.rerun()
        if col2.button("✏️ Modify & Approve", use_container_width=True):
            wf.approve("modify")
            wf.advance()
            st.rerun()
        if col3.button("❌ Reject", use_container_width=True):
            wf.approve("reject")
            st.rerun()


def render_final_output(wf: DemoWorkflow) -> None:
    out = wf.consolidated_output()
    st.subheader("📦 Final consolidated output")

    st.markdown(f"**Objective:** {out['case'].get('objective', '')}")
    st.markdown(
        f"**Statistical unit:** {out['case'].get('statistical_unit', '')} · "
        f"**Reference period:** {out['case'].get('reference_period', '')} · "
        f"**Frequency:** {out['case'].get('frequency', '')} · "
        f"**Scope:** {out['case'].get('geographic_scope', '')}"
    )

    if out["standardized_sections"]:
        with st.expander("Standardized methodology sections"):
            for s in out["standardized_sections"]:
                st.markdown(f"- {s}")

    if out["indicators"]:
        st.markdown("**Indicator cards:**")
        for i in out["indicators"]:
            st.markdown(
                f"- `{i['code']}` **{i['name']}** — {i['measurement_unit']}, "
                f"{i['publication_frequency']}"
            )

    if out["scad_sections"]:
        with st.expander("SCAD-specific methodology sections"):
            for s in out["scad_sections"]:
                st.markdown(f"- {s}")

    if out["annotations"]:
        st.markdown("**Annotations:** " + ", ".join(f"`{a}`" for a in out["annotations"]))

    if out["gap_matrix"]:
        st.markdown("**Gap assessment:**")
        for g in out["gap_matrix"]:
            st.markdown(f"- {g['dimension']} — `{g['gap_level']}`")

    if out["recommendations"]:
        st.markdown("**Recommendations:**")
        for r in out["recommendations"]:
            st.markdown(f"- {r}")

    if out["decisions"]:
        st.markdown("**Decisions:**")
        for d in out["decisions"]:
            st.markdown(f"- {d}")

    if out["open_questions"]:
        st.markdown("**Open questions (pending business sign-off):**")
        for q in out["open_questions"]:
            st.markdown(f"- {q}")


# --- session state -----------------------------------------------------------

if "wf" not in st.session_state:
    st.session_state.wf = None

# --- transcript selection ----------------------------------------------------

transcripts = list_transcripts(str(TRANSCRIPT_DIR))
if not transcripts:
    st.error(f"No transcripts found in `{TRANSCRIPT_DIR}`.")
    st.stop()

selected = st.selectbox("Transcript", transcripts)

col_create, col_reset = st.columns([4, 1])
if col_create.button("🚀 Create Meeting Case", type="primary", use_container_width=True):
    text = load_transcript(selected)
    turns = parse_transcript(text)
    if not turns:
        st.error("No parseable speaker turns found in the transcript.")
    else:
        wf = DemoWorkflow(turns, title=extract_title(text))
        wf.start()
        wf.advance()  # run agents up to the first approval gate
        st.session_state.wf = wf

if col_reset.button("Reset"):
    st.session_state.wf = None
    st.rerun()

wf = st.session_state.wf
if wf is None:
    st.info("Select a transcript and click **Create Meeting Case** to start.")
    st.stop()

# --- the single-screen flow --------------------------------------------------

render_stages(wf)

if any(s == "rejected" for s in wf.stage_status.values()):
    st.error("❌ Workflow stopped: a stage was rejected by the reviewer.")
elif wf.done:
    render_final_output(wf)
    st.success("✅ Workflow completed — final output ready.")
elif wf.gate is not None:
    render_approval(wf)
