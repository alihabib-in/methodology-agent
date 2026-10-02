"""Agent contracts (Phase B).

Every agent must expose a structured contract so the orchestrator can decide
what it runs, what it consumes, what it must produce, and whether it may modify
authoritative case state. Agents never own state; they return structured results
that the orchestrator validates and persists.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field


class AgentContract(BaseModel):
    id: str
    version: str = "1.0"
    purpose: str = ""
    input_schema: dict = Field(default_factory=dict)
    output_schema: dict = Field(default_factory=dict)
    required_tools: list[str] = Field(default_factory=list)
    required_context: list[str] = Field(default_factory=list)
    approval_required: bool = False
    failure_policy: str = "retry_once"
    can_modify_case: bool = False
    can_propose_case_updates: bool = True


class AgentResult(BaseModel):
    """Structured output of a single agent execution."""

    agent_id: str
    outputs: dict = Field(default_factory=dict)
    proposed_case_updates: dict = Field(default_factory=dict)
    recommendations: list[dict] = Field(default_factory=list)
    status: str = "succeeded"


class Agent(ABC):
    contract: AgentContract

    @abstractmethod
    def run(self, inputs: dict[str, Any]) -> AgentResult:
        """Execute the agent and return a structured result."""
