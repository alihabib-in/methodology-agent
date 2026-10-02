"""Agent execution abstraction (Phase B).

The orchestrator never runs agents directly; it dispatches through an
``Executor``. This keeps execution swappable:

- ``InProcessExecutor`` — synchronous, in-process (the POC default).
- ``ArqExecutor`` (future) — enqueue jobs to `arq` workers backed by Redis for
  long-running agents (international research, DOCX generation). Added when the
  first long-running agent lands in Phase E; the interface below is already the
  stable seam, so no orchestrator changes are required.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from app.workflow.contracts import Agent, AgentResult


class Executor(ABC):
    @abstractmethod
    def execute(self, agent: Agent, inputs: dict[str, Any]) -> AgentResult:
        """Run an agent and return its structured result."""


class InProcessExecutor(Executor):
    def execute(self, agent: Agent, inputs: dict[str, Any]) -> AgentResult:
        return agent.run(inputs)
