from typing import List, Literal
from pydantic import BaseModel

Severity = Literal["low", "medium", "high"]
MediaType = Literal["image", "video"]

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
    confidence: float = 0.0

class DetectionPoint(BaseModel):
    x: float
    y: float
    label: str

class RoadBoundary(BaseModel):
    leftTopX: float
    leftBottomX: float
    rightTopX: float
    rightBottomX: float
    confidence: float = 0.0

class VideoOverlayMetadata(BaseModel):
    duration: str
    fps: int
    resolution: str
    analyzedFrames: int
    activeMeasurements: MeasurementOverlay
    boxes: List[BoundingBox]
    points: List[DetectionPoint]
    mediaType: MediaType = "video"
    mediaUrl: str | None = None
    roadBoundary: RoadBoundary | None = None
