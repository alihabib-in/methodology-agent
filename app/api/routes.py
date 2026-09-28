from fastapi import APIRouter, Request
from pydantic import BaseModel

from app.agent.methodology_agent import MethodologyAgent

router = APIRouter()


class AnalyzeRequest(BaseModel):
    text: str
    language: str | None = None


class StateRequest(BaseModel):
    text: str | None = None
    language: str | None = None


def _get_agent(request: Request) -> MethodologyAgent:
    return request.app.state.agent


@router.post("/analyze")
def analyze(request: AnalyzeRequest, http_request: Request):
    agent = _get_agent(http_request)
    return agent.analyze(text=request.text, language=request.language)


@router.post("/extract")
def extract(request: AnalyzeRequest, http_request: Request):
    agent = _get_agent(http_request)
    return agent.extract(request.text, request.language).model_dump()


@router.post("/question")
def question(request: AnalyzeRequest, http_request: Request):
    agent = _get_agent(http_request)
    result = agent.analyze(text=request.text, language=request.language)
    if result.get("parse_error"):
        return result
    return {
        "gaps": result["gaps"],
        "recommended_question": result["recommended_question"],
    }


@router.post("/methodology-state")
def methodology_state(request: StateRequest, http_request: Request):
    agent = _get_agent(http_request)
    if request.text:
        agent.analyze(text=request.text, language=request.language)
    return agent.get_state().model_dump()
