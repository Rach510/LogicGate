import uuid
from datetime import datetime, timezone
from typing import Literal, Optional

from pydantic import BaseModel, Field

ProjectStatus = Literal["Ready", "Processing", "Needs review"]
ProjectCondition = Literal["Good", "Minor defects", "Moderate defects", "Severe defects"]


class RoadLocation(BaseModel):
    latitude: float
    longitude: float
    address: Optional[str] = None
    heading: Optional[float] = None
    streetViewAvailable: bool = False
    panoramaId: Optional[str] = None


class ProjectCreate(BaseModel):
    name: str
    fileName: str
    location: Optional[RoadLocation] = None


class Project(BaseModel):
    """Mirrors frontend/src/types/index.ts Project — field names are camelCase to match."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    route: str
    updated: str = "Just now"
    status: ProjectStatus = "Processing"
    condition: ProjectCondition = "Good"
    coverage: str = "0 km covered"
    location: RoadLocation


class ProjectDocument(BaseModel):
    """Internal Mongo representation — adds bookkeeping fields not sent to the frontend."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    route: str
    status: ProjectStatus = "Processing"
    condition: ProjectCondition = "Good"
    coverage: str = "0 km covered"
    location: RoadLocation
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def to_project(self, updated_label: str) -> Project:
        return Project(
            id=self.id,
            name=self.name,
            route=self.route,
            updated=updated_label,
            status=self.status,
            condition=self.condition,
            coverage=self.coverage,
            location=self.location,
        )
