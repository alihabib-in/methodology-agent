from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.agent.methodology_agent import MethodologyAgent
from app.agents.document_analysis import DocumentAnalysisAgent
from app.agents.elicitation import ElicitationAgent
from app.agents.compliance import ComplianceAgent
from app.agents.gap_assessment import GapAssessmentAgent
from app.agents.indicator import IndicatorConceptualizationAgent
from app.agents.methodology_qa import MethodologyQAAgent
from app.agents.scad_input import SCADInputAgent
from app.agents.scad_methodology import SCADMethodologyAgent
from app.agents.standardized_methodology import StandardizedMethodologyAgent
from app.api import cases, health, knowledge, meeting, meetings, routes, tts
from app.core.config import settings
from app.core.logging import configure_logging, get_logger
from app.llm.client import LLMClient
from app.meeting.service import MeetingService
from app.realtime.broker import EventBroker
from app.realtime import dashboard as dashboard_ws
from app.realtime import websocket as realtime_ws
from app.research.agent import InternationalResearchAgent
from app.workflow.registry import AgentRegistry
from app.workflow.service import WorkflowService

configure_logging()
logger = get_logger(__name__)

app = FastAPI(
    title="Bilingual Methodology Agent",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    # Handled here (inside the middleware stack) so the response carries CORS
    # headers and the browser can read the error instead of misreporting CORS.
    logger.exception("unhandled error on %s", request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "internal server error", "type": type(exc).__name__},
    )

llm_client = LLMClient(
    base_url=settings.llm_base_url,
    model=settings.llm_model,
    timeout=settings.llm_timeout_seconds,
    temperature=settings.llm_temperature,
)

agent = MethodologyAgent(llm_client)
meeting_service = MeetingService()
realtime_broker = EventBroker()

app.state.agent = agent
app.state.meeting_service = meeting_service
app.state.realtime_broker = realtime_broker

agent_registry = AgentRegistry()
agent_registry.register(ElicitationAgent(agent))
agent_registry.register(DocumentAnalysisAgent(agent))
agent_registry.register(InternationalResearchAgent(agent.llm))
agent_registry.register(StandardizedMethodologyAgent(agent.llm))
agent_registry.register(SCADInputAgent(agent.llm))
agent_registry.register(MethodologyQAAgent(agent.llm))
agent_registry.register(IndicatorConceptualizationAgent(agent.llm))
agent_registry.register(SCADMethodologyAgent(agent.llm))
agent_registry.register(ComplianceAgent(agent.llm))
agent_registry.register(GapAssessmentAgent(agent.llm))
app.state.agent_registry = agent_registry
app.state.workflow_service = WorkflowService(agent_registry, broker=realtime_broker)


@app.on_event("startup")
def _startup() -> None:
    from app.core.db import init_db

    init_db()


app.include_router(health.router)
app.include_router(routes.router)
app.include_router(meetings.router)
app.include_router(knowledge.router)
app.include_router(meeting.router)
app.include_router(dashboard_ws.router)
app.include_router(realtime_ws.router)
app.include_router(tts.router)
app.include_router(cases.router)
