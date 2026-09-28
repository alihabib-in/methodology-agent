"""Standalone evaluation harness for the SCAD Methodology AI Portal.

Processes prerecorded multilingual (Arabic/English) meeting transcripts through
the portal's methodology pipeline and produces transparent, evidence-linked
evaluation artifacts (state history, gaps, questions, conflicts, candidate
methodology scope, and HTML/Markdown/JSON reports).

Run from the repository root:

    python -m evaluation.cli run --input evaluation/data/meeting_001 --mode mock
    python -m evaluation.cli review --run evaluation/output/M-001
"""
