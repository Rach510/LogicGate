from fastapi import APIRouter, HTTPException
from lib.db import db
from lib.seed import DEFAULT_ANALYTICS
from models.analytics import AnalyticsData, RoadProfilePoint, ConditionBreakdownItem

router = APIRouter(prefix="/projects", tags=["analytics"])


@router.get("/{project_id}/analytics", response_model=AnalyticsData)
async def get_analytics(project_id: str):
    project = await db.projects.find_one({"id": project_id})
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    stored = await db.video_analysis.find_one({"project_id": project_id})

    if not stored:
        payload = dict(DEFAULT_ANALYTICS)
        payload["roadCondition"] = project.get("condition", payload["roadCondition"])
        payload["analyzedDistance"] = project.get("coverage", payload["analyzedDistance"]).replace(" covered", "")
        return AnalyticsData(**payload)

    result = stored["result"]
    measurements = result.get("activeMeasurements", {})
    boxes = result.get("boxes", [])

    confidence = measurements.get("confidence", 70)
    quality = measurements.get("quality", 70)
    defects = len(boxes)

    if quality >= 85:
        condition = "Good"
    elif quality >= 65:
        condition = "Minor defects"
    elif quality >= 45:
        condition = "Moderate defects"
    else:
        condition = "Severe defects"

    high = sum(1 for b in boxes if b.get("severity") == "high")
    medium = sum(1 for b in boxes if b.get("severity") == "medium")
    low = sum(1 for b in boxes if b.get("severity") == "low")
    total = max(defects, 1)

    road_profile = [
        RoadProfilePoint(label="Surface", value=round(quality * 0.95, 1)),
        RoadProfilePoint(label="Structure", value=round(quality * 0.90, 1)),
        RoadProfilePoint(label="Drainage", value=round(quality * 1.02, 1)),
        RoadProfilePoint(label="Markings", value=round(quality * 0.85, 1)),
        RoadProfilePoint(label="Edges", value=round(quality * 0.92, 1)),
    ]

    condition_breakdown = [
        ConditionBreakdownItem(label="Good", value=round((1 - high / total) * 60, 1), color="#b8e986"),
        ConditionBreakdownItem(label="Fair", value=round(medium / total * 30, 1), color="#edb06c"),
        ConditionBreakdownItem(label="Poor", value=round(high / total * 10, 1), color="#ed6c6c"),
    ]

    return AnalyticsData(
        confidence=confidence,
        quality=quality,
        roadCondition=condition,
        defectsDetected=defects,
        analyzedDistance=project.get("coverage", "0 km").replace(" covered", ""),
        roadProfile=road_profile,
        conditionBreakdown=condition_breakdown,
        reports=DEFAULT_ANALYTICS.get("reports", []),
    )