"""Compliance / QA report schema (Phase J)."""

from __future__ import annotations

from pydantic import BaseModel, Field


class QAFinding(BaseModel):
    severity: str = "non_blocking"  # blocking | non_blocking
    item: str = ""
    status: str = "pass"  # pass | fail | warning
    detail: str = ""


class QAReport(BaseModel):
    checklist: list[QAFinding] = Field(default_factory=list)
    blocking_issues: list[str] = Field(default_factory=list)
    non_blocking_issues: list[str] = Field(default_factory=list)
    approval_recommendation: str = "recommended"  # recommended | changes_required | not_recommended
    summary: str = ""
