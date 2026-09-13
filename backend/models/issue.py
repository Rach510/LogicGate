import uuid
from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field

from models.project import RoadLocation


class IssueReportRequest(BaseModel):
    """Mirrors frontend/src/types/index.ts IssueReport."""

    description: str
    category: str
    location: Optional[RoadLocation] = None
    attachmentName: Optional[str] = None
    project_id: Optional[str] = None


class IssueReportResponse(BaseModel):
    id: str
    status: str


class IssueReportDocument(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    description: str
    category: str
    location: Optional[RoadLocation] = None
    attachmentName: Optional[str] = None
    project_id: Optional[str] = None
    status: str = "submitted"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
