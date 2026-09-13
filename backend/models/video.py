from typing import List, Literal

from pydantic import BaseModel

Severity = Literal["low", "medium", "high"]


class MeasurementOverlay(BaseModel):
    roadWidth: float
    leftLane: float
    kerbToKerb: float
    confidence: float
    quality: float
    frame: int


class BoundingBox(BaseModel):
    x: float
    y: float
    width: float
    height: float
    label: str
    severity: Severity


class DetectionPoint(BaseModel):
    x: float
    y: float
    label: str


class VideoOverlayMetadata(BaseModel):
    """Mirrors frontend/src/types/index.ts VideoOverlayMetadata."""

    duration: str
    fps: int
    resolution: str
    analyzedFrames: int
    activeMeasurements: MeasurementOverlay
    boxes: List[BoundingBox]
    points: List[DetectionPoint]
