from typing import List

from pydantic import BaseModel

from models.project import ProjectCondition


class RoadProfilePoint(BaseModel):
    label: str
    value: float


class ConditionBreakdownItem(BaseModel):
    label: str
    value: float
    color: str


class Report(BaseModel):
    id: str
    title: str
    category: str
    created: str
    note: str


class AnalyticsData(BaseModel):
    confidence: float
    quality: float
    roadCondition: ProjectCondition
    defectsDetected: int
    analyzedDistance: str
    roadProfile: List[RoadProfilePoint]
    conditionBreakdown: List[ConditionBreakdownItem]
    reports: List[Report]
