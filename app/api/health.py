from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/health")
def health(request: Request):
    agent = request.app.state.agent
    llm_status = agent.llm.health()
    return {
        "status": "healthy",
        "llm": "available" if llm_status["available"] else "unavailable",
        "model": llm_status["model"],
    }
