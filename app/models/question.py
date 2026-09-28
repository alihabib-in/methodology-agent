from pydantic import BaseModel, Field


class MethodologyQuestion(BaseModel):
    question: str
    domain: str = "general"
    reason: str | None = None
    priority: float = Field(default=0.0, ge=0.0, le=1.0)
    status: str = "candidate"
