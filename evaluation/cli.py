"""Command-line interface for the evaluation harness.

Usage:
    python -m evaluation.cli run --input evaluation/data/meeting_001 --mode mock
    python -m evaluation.cli review --run evaluation/output/M-001
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from .adapters import build_adapter
from .config import EvalConfig
from .engine import EvaluationEngine
from .exporters import write_outputs
from .transcript_loader import load_transcript
from .transcript_normalizer import normalize_transcript


def _cmd_run(args: argparse.Namespace) -> None:
    config = EvalConfig(
        mode=args.mode,
        llm_base_url=args.llm_base_url,
        llm_model=args.llm_model,
        llm_timeout=args.llm_timeout,
        batch_size=args.batch_size,
        use_rag=args.use_rag,
        output_dir=args.output_dir,
    )
    transcript = normalize_transcript(load_transcript(args.input))
    adapter = build_adapter(config)
    state = EvaluationEngine(adapter, config).run(transcript)

    out_dir = config.output_for(transcript.meeting_id)
    files = write_outputs(transcript, state, out_dir)

    print(f"Evaluation complete -> {out_dir}")
    for f in files:
        print(f"  - {f.name}")
    print(f"\nReadiness: {state.candidate_scope.readiness_score}% "
          f"({state.candidate_scope.readiness_status}); "
          f"gaps={len(state.gaps)}, conflicts={len(state.conflicts)}, "
          f"questions={len(state.questions)}")


_SCOPE_FIELDS = ["objective", "population", "statistical_unit", "reference_period", "geographic_scope"]


def _cmd_review(args: argparse.Namespace) -> None:
    run_dir = Path(args.run)
    scope_path = run_dir / "candidate_scope.json"
    if not scope_path.exists():
        raise SystemExit(f"No candidate_scope.json in {run_dir}")

    scope = json.loads(scope_path.read_text(encoding="utf-8"))
    print("=" * 44)
    print("CANDIDATE METHODOLOGY")
    print("=" * 44)
    for field in _SCOPE_FIELDS:
        print(f"\n{field.replace('_', ' ').title()}:\n  {scope.get(field) or '(not set)'}")
    print("\nIndicators:", ", ".join(scope.get("indicators", [])) or "(none)")
    print("Data sources:", ", ".join(scope.get("data_sources", [])) or "(none)")
    print("Open questions:", len(scope.get("open_questions", [])))
    print("Readiness:", f"{scope.get('readiness_score', 0)}% ({scope.get('readiness_status')})")
    print("=" * 44)
    print("[1] Approve   [2] Reject   [3] Edit   [4] Return for revision")

    choice = input("Choose an action [1-4]: ").strip()
    decision = {"1": "approved", "2": "rejected", "3": "edit", "4": "return_for_revision"}.get(choice)
    if decision is None:
        raise SystemExit("Invalid choice")

    edits = []
    if decision == "edit":
        for field in _SCOPE_FIELDS:
            current = scope.get(field) or ""
            new = input(f"{field.replace('_', ' ').title()} [current: {current}]: ").strip()
            if new and new != current:
                edits.append({"field": field, "before": current, "after": new})
                scope[field] = new

    reviewer = input("Reviewer name: ").strip() or "evaluator"
    reason = input("Reason (optional): ").strip()

    result = {
        "decision": decision,
        "reviewer": reviewer,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "reason": reason,
        "edits": edits,
        "source_type": "human",
        "scope_after": scope,
    }
    (run_dir / "review.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nDecision '{decision}' recorded -> {run_dir / 'review.json'}")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="evaluation", description="Methodology Portal evaluation harness")
    sub = parser.add_subparsers(dest="command")

    run = sub.add_parser("run", help="Run the evaluation pipeline over a transcript")
    run.add_argument("--input", required=True, help="Transcript file, folder, or meeting dir")
    run.add_argument("--mode", choices=["production", "local", "mock"], default="mock")
    run.add_argument("--batch-size", type=int, default=5)
    run.add_argument("--llm-base-url", default=os.environ.get("LLM_BASE_URL", "http://localhost:8080/v1"))
    run.add_argument("--llm-model", default=os.environ.get("LLM_MODEL", "qwen3-4b-instruct-2507"))
    run.add_argument("--llm-timeout", type=float, default=float(os.environ.get("LLM_TIMEOUT_SECONDS", 120)))
    run.add_argument("--use-rag", action="store_true")
    run.add_argument("--output-dir", default="evaluation/output")

    review = sub.add_parser("review", help="Simulated human review of a run")
    review.add_argument("--run", required=True, help="Path to a run output directory")

    args = parser.parse_args(argv)
    if args.command == "run":
        _cmd_run(args)
    elif args.command == "review":
        _cmd_review(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
