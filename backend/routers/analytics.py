from fastapi import APIRouter, HTTPException
from lib.db import db
from models.analytics import AnalyticsData, RoadProfilePoint, ConditionBreakdownItem, Report

router = APIRouter(prefix="/projects", tags=["analytics"])


def _condition_from_quality(quality: float) -> str:
    if quality >= 85:
        return "Good"
    if quality >= 65:
        return "Minor defects"
    if quality >= 45:
        return "Moderate defects"
    return "Severe defects"


def _parse_coverage_km(value: str | None) -> float:
    if not value:
        return 0.0
    try:
        return float(str(value).replace("km", "").replace("covered", "").strip())
    except ValueError:
        return 0.0


@router.get("/{project_id}/analytics", response_model=AnalyticsData)
async def get_analytics(project_id: str):
    project = await db.projects.find_one({"id": project_id})
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    stored = await db.video_analysis.find_one({"project_id": project_id})
    if not stored:
        return AnalyticsData(
            confidence=0,
            quality=0,
            roadCondition="Good",
            defectsDetected=0,
            analyzedDistance="0 km",
            roadProfile=[],
            conditionBreakdown=[ConditionBreakdownItem(label="Awaiting analysis", value=100, color="#60716a")],
            reports=[],
        )

    result = stored.get("result", {})
    measurements = result.get("activeMeasurements", {}) or {}
    boxes = result.get("boxes", []) or []
    confidence = float(measurements.get("confidence", 0) or 0)
    quality = float(measurements.get("quality", 0) or 0)
    defects = len(boxes)
    condition = _condition_from_quality(quality)

    high = sum(1 for b in boxes if b.get("severity") == "high")
    medium = sum(1 for b in boxes if b.get("severity") == "medium")
    low = sum(1 for b in boxes if b.get("severity") == "low")
    defect_pressure = min(60.0, high * 7.0 + medium * 4.0 + low * 1.5)
    residual = max(0.0, 100.0 - defect_pressure)
    poor = min(residual, high * 3.5)
    moderate = min(max(0.0, residual - poor), medium * 3.5)
    minor = min(max(0.0, residual - poor - moderate), low * 2.0 + medium * 0.8)
    good = max(0.0, 100.0 - poor - moderate - minor)

    raw_breakdown = [good, minor, moderate, poor]
    total = sum(raw_breakdown) or 1
    breakdown = [round(v / total * 100.0, 1) for v in raw_breakdown]
    breakdown[-1] = round(100.0 - sum(breakdown[:-1]), 1)

    detection_confidence = float(result.get("detectionConfidence", 0) or 0)
    boundary_confidence = float(result.get("boundaryConfidence", 0) or 0)
    max_detection = float(result.get("maxDetectionConfidence", 0) or 0)
    width_stability = float(result.get("widthStability", boundary_confidence) or boundary_confidence)

    if detection_confidence <= 0 and boxes:
        detection_confidence = sum(float(b.get("confidence", 0) or 0) for b in boxes) / len(boxes)
    if max_detection <= 0 and boxes:
        max_detection = max(float(b.get("confidence", 0) or 0) for b in boxes)
    if boundary_confidence <= 0:
        boundary_confidence = min(95.0, max(35.0, quality))
    if width_stability <= 0:
        width_stability = boundary_confidence

    road_profile = [
        RoadProfilePoint(label="Capture", value=round(quality, 1)),
        RoadProfilePoint(label="Geometry", value=round(boundary_confidence, 1)),
        RoadProfilePoint(label="Detection", value=round(detection_confidence, 1)),
        RoadProfilePoint(label="Best detection", value=round(max_detection, 1)),
        RoadProfilePoint(label="Overall", value=round(confidence, 1)),
        RoadProfilePoint(label="Width stability", value=round(width_stability, 1)),
    ]

    reports: list[Report] = []
    for issue in await db.issues.find({"project_id": project_id}).sort("created_at", -1).to_list(20):
        reports.append(Report(
            id=str(issue.get("id", "issue")),
            title=issue.get("category", "Field issue"),
            category=issue.get("category", "Road survey"),
            created=str(issue.get("created_at", ""))[:19].replace("T", " "),
            note=issue.get("description", "Reported from field review."),
        ))

    distance_km = float(result.get("estimatedDistanceKm", _parse_coverage_km(project.get("coverage"))))
    return AnalyticsData(
        confidence=round(confidence, 1),
        quality=round(quality, 1),
        roadCondition=condition,
        defectsDetected=defects,
        analyzedDistance=f"{distance_km:.2f} km" if distance_km else "0 km",
        roadProfile=road_profile,
        conditionBreakdown=[
            ConditionBreakdownItem(label="Good", value=breakdown[0], color="#b8e986"),
            ConditionBreakdownItem(label="Minor defects", value=breakdown[1], color="#f6c76d"),
            ConditionBreakdownItem(label="Moderate defects", value=breakdown[2], color="#e89d5c"),
            ConditionBreakdownItem(label="Severe defects", value=breakdown[3], color="#ed6f61"),
        ],
        reports=reports,
    )
