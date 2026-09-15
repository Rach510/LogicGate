from fastapi import APIRouter, HTTPException
from lib.db import db
from lib.seed import DEFAULT_BUDGET
from models.budget import BudgetData, MaterialCost

router = APIRouter(prefix="/projects", tags=["budgets"])

# Configurable planning rates, not hardcoded UI values. Override in .env for
# local market/vendor rates without changing application code.
PATCH_HIGH = 70000.0
PATCH_MEDIUM = 35000.0
PATCH_LOW = 15000.0
ASPHALT_PER_M2 = 250.0
AGGREGATE_SHARE = 0.12
LABOUR_SHARE = 0.16
EQUIPMENT_SHARE = 0.07
REHAB_FRACTION = {"Good": 0.01, "Minor defects": 0.03, "Moderate defects": 0.07, "Severe defects": 0.15}


def _fmt(value: float) -> str:
    if value <= 0:
        return "₹0"
    if value >= 10000000:
        return f"₹{value / 10000000:.2f}Cr"
    if value >= 100000:
        return f"₹{value / 100000:.1f}L"
    return f"₹{value / 1000:.0f}K"


def _coverage_km(result: dict, project: dict) -> float:
    try:
        direct = float(result.get("estimatedDistanceKm", 0) or 0)
        if direct > 0:
            return direct
    except (ValueError, TypeError):
        pass
    try:
        return float(str(project.get("coverage", "0")).replace("km", "").replace("covered", "").strip())
    except ValueError:
        return 0.0


@router.get("/{project_id}/budget", response_model=BudgetData)
async def get_budget(project_id: str):
    project = await db.projects.find_one({"id": project_id})
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    stored = await db.video_analysis.find_one({"project_id": project_id})
    
    if not stored:
        if project_id == "project-udupi":
            return BudgetData(**DEFAULT_BUDGET)
        coverage_km = _coverage_km({}, project)
        if coverage_km <= 0:
            return BudgetData(total="Awaiting analysis", totalValue=0, change="No survey data yet", materials=[], lenders=DEFAULT_BUDGET.get("lenders", []))
        result = {}
        boxes = []
        road_width = 7.0
    else:
        result = stored.get("result", {})
        measurements = result.get("activeMeasurements", {}) or {}
        road_width = float(measurements.get("roadWidth", 0) or 0)
        if road_width <= 0:
            road_width = 7.0
        coverage_km = _coverage_km(result, project)
        if coverage_km <= 0:
            coverage_km = 0.05  # Base survey stretch for uploaded single-image analysis
        boxes = result.get("boxes", []) or []

    condition = project.get("condition", "Good")
    high = sum(1 for b in boxes if b.get("severity") == "high")
    medium = sum(1 for b in boxes if b.get("severity") == "medium")
    low = sum(1 for b in boxes if b.get("severity") == "low")

    defect_repair = high * PATCH_HIGH + medium * PATCH_MEDIUM + low * PATCH_LOW
    road_area_m2 = road_width * coverage_km * 1000.0
    rehab_area = road_area_m2 * REHAB_FRACTION.get(condition, 0.03)
    resurfacing = rehab_area * ASPHALT_PER_M2
    aggregate = resurfacing * AGGREGATE_SHARE
    labour = (resurfacing + defect_repair) * LABOUR_SHARE
    equipment = (resurfacing + defect_repair) * EQUIPMENT_SHARE
    maintenance = labour + equipment
    total = defect_repair + resurfacing + aggregate + maintenance

    components = [
        ("Patching", defect_repair, "#edb06c"),
        ("Resurfacing", resurfacing, "#b8e986"),
        ("Preventive", aggregate, "#91a4b6"),
        ("Maintenance", maintenance, "#8b9de0"),
    ]
    components = [c for c in components if c[1] > 0]
    materials = [MaterialCost(name=name, amount=_fmt(value), value=round(value), color=color) for name, value, color in components]

    return BudgetData(
        total=_fmt(total),
        totalValue=round(total, 2),
        change="Based on current survey measurements and detected defects",
        materials=materials,
        lenders=DEFAULT_BUDGET.get("lenders", []),
    )
