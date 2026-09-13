import uuid
from datetime import datetime, timezone

from pydantic import BaseModel, Field


class AiRoadBriefRequest(BaseModel):
    project_id: str
    project_name: str
    route: str
    condition: str
    confidence: float
    quality: float
    defects_detected: int
    road_width: float
    left_lane: float
    kerb_to_kerb: float
    budget_total: str


class AiRoadBrief(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str
    model: str = "gpt-5.4"
    content: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
