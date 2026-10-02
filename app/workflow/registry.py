"""Agent registry (Phase B).

Agents are registerable and discoverable by id. New methodology agents must be
added through this registry rather than hard-coded into the workflow engine.
"""

from __future__ import annotations

from app.workflow.contracts import Agent, AgentContract


class AgentRegistry:
    def __init__(self) -> None:
        self._agents: dict[str, Agent] = {}

    def register(self, agent: Agent) -> None:
        self._agents[agent.contract.id] = agent

    def get(self, agent_id: str) -> Agent | None:
        return self._agents.get(agent_id)

    def contract(self, agent_id: str) -> AgentContract | None:
        agent = self._agents.get(agent_id)
        return agent.contract if agent else None

    def ids(self) -> list[str]:
        return list(self._agents.keys())
