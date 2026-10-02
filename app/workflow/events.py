"""Workflow event type constants (Phase B).

Mirrors the spec §4.6 event vocabulary. These will be fed into the existing
real-time ``EventBroker`` when the workflow layer is wired to the API.
"""

CASE_CREATED = "case.created"
CASE_UPDATED = "case.updated"
CASE_READY_FOR_REVIEW = "case.ready_for_review"
CASE_APPROVED = "case.approved"

STAGE_STARTED = "stage.started"
STAGE_COMPLETED = "stage.completed"
STAGE_SKIPPED = "stage.skipped"
STAGE_BLOCKED = "stage.blocked"

AGENT_STARTED = "agent.started"
AGENT_COMPLETED = "agent.completed"
AGENT_FAILED = "agent.failed"

ARTIFACT_CREATED = "artifact.created"
ARTIFACT_UPDATED = "artifact.updated"

APPROVAL_REQUESTED = "approval.requested"
APPROVAL_GRANTED = "approval.granted"
APPROVAL_REJECTED = "approval.rejected"

QUESTION_REQUESTED = "question.requested"
QUESTION_ANSWERED = "question.answered"

WORKFLOW_BLOCKED = "workflow.blocked"
WORKFLOW_COMPLETED = "workflow.completed"
