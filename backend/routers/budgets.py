from fastapi import APIRouter, HTTPException
from lib.db import db
from lib.seed import DEFAULT_BUDGET
from models.budget import BudgetData, MaterialCost

router = APIRouter(prefix="/projects", tags=["budgets"])

COST_PER_HIGH = 85000
COST_PER_MEDIUM = 45000
COST_PER_LOW = 18000
BASE_MAINTENANCE = 250000


@router.get("/{project_id}/budget", response_model=BudgetData)
async def get_budget(project_id: str):
    project = await db.projects.find_one({"id": project_id})
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    stored = await db.video_analysis.find_one({"project_id": project_id})

    if not stored:
        return BudgetData(**DEFAULT_BUDGET)

    boxes = stored["result"].get("boxes", [])

    high = sum(1 for b in boxes if b.get("severity") == "high")
    medium = sum(1 for b in boxes if b.get("severity") == "medium")
    low = sum(1 for b in boxes if b.get("severity") == "low")

    patching = high * COST_PER_HIGH
    resurfacing = medium * COST_PER_MEDIUM
    preventive = low * COST_PER_LOW
    maintenance = BASE_MAINTENANCE
    total_value = patching + resurfacing + preventive + maintenance

    def fmt(n: int) -> str:
        if n >= 100000:
            return f"\u20b9{round(n / 100000, 1)}L"
        return f"\u20b9{round(n / 1000)}K"

    materials = [
        {"name": "Patching", "amount": fmt(patching), "value": patching, "color": "#edb06c"},
        {"name": "Resurfacing", "amount": fmt(resurfacing), "value": resurfacing, "color": "#b8e986"},
        {"name": "Preventive", "amount": fmt(preventive), "value": preventive, "color": "#6cb8ed"},
        {"name": "Maintenance", "amount": fmt(maintenance), "value": maintenance, "color": "#9b8fe8"},
    ]

    materials = [m for m in materials if m["value"] > 0] or [
        {"name": "Maintenance", "amount": fmt(maintenance), "value": maintenance, "color": "#9b8fe8"}
    ]

    return BudgetData(
        total=fmt(total_value),
        totalValue=total_value,
        change="+0% vs last estimate",
        materials=[MaterialCost(**m) for m in materials],
        lenders=DEFAULT_BUDGET.get("lenders", []),
    )