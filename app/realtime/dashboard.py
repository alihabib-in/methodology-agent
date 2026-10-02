"""Dashboard WebSocket endpoint: live broadcast of every workflow event.

Used by the control-room dashboard to watch agents and orchestration in real
time, across all cases. Subscribes to the broker's global broadcast channel.
"""

from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.logging import get_logger
from app.realtime.broker import EventBroker

logger = get_logger(__name__)

router = APIRouter()


@router.websocket("/ws/dashboard")
async def dashboard_ws(websocket: WebSocket) -> None:
    broker: EventBroker = websocket.app.state.realtime_broker

    await websocket.accept()
    subscription = broker.subscribe_all()

    try:
        while True:
            event = await subscription.queue.get()
            await websocket.send_json(event)
    except WebSocketDisconnect:
        pass
    except Exception:  # noqa: BLE001
        logger.exception("dashboard websocket error")
    finally:
        broker.unsubscribe(subscription)
