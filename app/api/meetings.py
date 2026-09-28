"""Meeting/session endpoints: session-scoped methodology state + answer loop."""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from app.agent.methodology_agent import MethodologyAgent
from app.core.db import session_scope
from app.knowledge import repository
from app.models.methodology_state import MethodologyState
from app.realtime import events as rt

router = APIRouter()


class AnalyzeRequest(BaseModel):
    text: str
    language: str | None = None


class AnswerRequest(BaseModel):
    answer: str
    language: str | None = None


class ApproveRequest(BaseModel):
    concept: str
    statement: str
    domain: str | None = None


def _agent(request: Request) -> MethodologyAgent:
    return request.app.state.agent


@router.post("/meetings")
def create_meeting(request: Request):
    with session_scope() as session:
        meeting = repository.create_meeting(session)
        meeting_id = meeting.id
    request.app.state.realtime_broker.publish(
        rt.MEETING_CREATED, session_id=meeting_id, payload={"meeting_id": meeting_id}
    )
    return {"meeting_id": meeting_id}


@router.post("/meetings/{meeting_id}/analyze")
def analyze_meeting(meeting_id: str, body: AnalyzeRequest, request: Request):
    agent = _agent(request)
    broker = request.app.state.realtime_broker

    with session_scope() as session:
        meeting = repository.get_meeting(session, meeting_id)
        if meeting is None:
            raise HTTPException(status_code=404, detail="meeting not found")
        state = repository.load_meeting_state(meeting)

    broker.publish(
        rt.AI_STATUS_CHANGED,
        session_id=meeting_id,
        payload={"status": "analyzing"},
    )

    result = agent.analyze(body.text, body.language, state=state)

    if not result.get("parse_error"):
        _save_state(meeting_id, result["methodology_state"])
        _publish_analysis(meeting_id, result, broker)
    else:
        broker.publish(
            rt.SYSTEM_ERROR,
            session_id=meeting_id,
            payload={"error": result.get("error")},
        )

    return result


@router.post("/meetings/{meeting_id}/answer")
def answer_meeting(meeting_id: str, body: AnswerRequest, request: Request):
    agent = _agent(request)
    broker = request.app.state.realtime_broker

    with session_scope() as session:
        meeting = repository.get_meeting(session, meeting_id)
        if meeting is None:
            raise HTTPException(status_code=404, detail="meeting not found")
        state = repository.load_meeting_state(meeting)

    broker.publish(
        rt.ANSWER_RECEIVED,
        session_id=meeting_id,
        payload={"answer": body.answer},
    )
    broker.publish(
        rt.AI_STATUS_CHANGED,
        session_id=meeting_id,
        payload={"status": "processing_answer"},
    )

    result = agent.answer(body.answer, state, body.language)

    if not result.get("parse_error"):
        _save_state(meeting_id, result["methodology_state"])
        broker.publish(
            rt.ANSWER_INTERPRETED,
            session_id=meeting_id,
            payload={"answer": body.answer},
        )
        _publish_analysis(meeting_id, result, broker)
    else:
        broker.publish(
            rt.SYSTEM_ERROR,
            session_id=meeting_id,
            payload={"error": result.get("error")},
        )

    return result


@router.get("/meetings/{meeting_id}/state")
def get_meeting_state(meeting_id: str, request: Request):
    agent = _agent(request)
    with session_scope() as session:
        meeting = repository.get_meeting(session, meeting_id)
        if meeting is None:
            raise HTTPException(status_code=404, detail="meeting not found")
        state = repository.load_meeting_state(meeting)
        status = meeting.status

    gaps = agent.gap_detector.detect(state)
    questions = agent.question_generator.generate_many(state, gaps)

    return {
        "meeting_id": meeting_id,
        "status": status,
        "methodology_state": state.model_dump(),
        "gaps": gaps,
        "questions": [q.model_dump() for q in questions],
        "recommended_question": questions[0].model_dump() if questions else None,
    }


@router.post("/meetings/{meeting_id}/approve")
def approve_meeting(meeting_id: str, body: ApproveRequest, request: Request):
    with session_scope() as session:
        meeting = repository.get_meeting(session, meeting_id)
        if meeting is None:
            raise HTTPException(status_code=404, detail="meeting not found")
        item = repository.create_knowledge(
            session,
            concept=body.concept,
            statement=body.statement,
            domain=body.domain,
            source="meeting",
            evidence=meeting_id,
            meeting_id=meeting_id,
        )
        item_id = item.id
        concept = item.concept

    request.app.state.realtime_broker.publish(
        rt.KNOWLEDGE_CANDIDATE,
        session_id=meeting_id,
        payload={"knowledge_id": item_id, "concept": concept},
    )
    return {"knowledge_id": item_id, "status": "candidate", "concept": concept}


def _save_state(meeting_id: str, state_dict: dict) -> None:
    new_state = MethodologyState.model_validate(state_dict)
    with session_scope() as session:
        meeting = repository.get_meeting(session, meeting_id)
        if meeting is not None:
            repository.save_meeting_state(session, meeting, new_state)


def _publish_analysis(meeting_id: str, result: dict, broker) -> None:
    state = result["methodology_state"]
    broker.publish(
        rt.METHODOLOGY_UPDATED,
        session_id=meeting_id,
        payload={"methodology_state": state},
    )
    objective = state.get("objective")
    if objective:
        broker.publish(
            rt.OBJECTIVE_UPDATED,
            session_id=meeting_id,
            payload={"objective": objective},
        )
    broker.publish(
        rt.AI_STATUS_CHANGED,
        session_id=meeting_id,
        payload={"status": "detecting_gaps"},
    )
    for gap in result["gaps"][:5]:
        broker.publish(
            rt.GAP_DETECTED,
            session_id=meeting_id,
            payload={"gap": gap},
        )
    broker.publish(
        rt.AI_STATUS_CHANGED,
        session_id=meeting_id,
        payload={"status": "generating_question"},
    )
    question = result.get("recommended_question")
    if question:
        broker.publish(
            rt.QUESTION_GENERATED,
            session_id=meeting_id,
            payload={"question": question},
        )
    broker.publish(
        rt.AI_STATUS_CHANGED,
        session_id=meeting_id,
        payload={"status": "ready"},
    )
