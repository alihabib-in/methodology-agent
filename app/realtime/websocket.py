"""WebSocket endpoint for session-scoped real-time events."""

from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from starlette.concurrency import run_in_threadpool

from app.core.logging import get_logger
from app.realtime.broker import EventBroker
from app.realtime.events import STATE_SNAPSHOT, build_envelope
from app.realtime.service import build_session_snapshot

logger = get_logger(__name__)

router = APIRouter()


@router.websocket("/ws/{session_id}")
async def session_ws(websocket: WebSocket, session_id: str) -> None:
    broker: EventBroker = websocket.app.state.realtime_broker
    agent = websocket.app.state.agent

    await websocket.accept()
    sub = broker.subscribe(session_id)

    try:
        snapshot = await run_in_threadpool(build_session_snapshot, agent, session_id)
        if snapshot is not None:
            envelope = build_envelope(
                STATE_SNAPSHOT, session_id=session_id, payload=snapshot, sequence=0
            )
            await websocket.send_json(envelope.model_dump())

        while True:
            event = await sub.queue.get()
            await websocket.send_json(event)
    except WebSocketDisconnect:
        pass
    except Exception:  # noqa: BLE001
        logger.exception("websocket error for session %s", session_id)
    finally:
        broker.unsubscribe(sub)
