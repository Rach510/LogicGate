import glob
import os
import pytest
from lib.cv_analysis import analyze_image
from lib.road_damage_ai import predict_damage, CLASS_NAMES
from lib.seed import DEFAULT_BUDGET
from models.budget import BudgetData, MaterialCost


def test_pothole_detection_on_damaged_road():
    """Verify that potholes are detected on the uploaded heavily damaged road."""
    target = "backend/uploads/e5d9c8a3-11db-4a99-8707-c4593e554cd0.jpg"
    if not os.path.exists(target):
        pytest.skip("Test image not found")
    with open(target, "rb") as f:
        data = f.read()
    res = analyze_image(data)
    assert res["defects_detected"] > 0
    potholes = [b for b in res["boxes"] if b.label == "Pothole"]
    assert len(potholes) >= 3, f"Expected at least 3 potholes, got {len(potholes)}"
    assert any(b.severity in ("medium", "high") for b in potholes)


def test_no_false_positives_on_clean_road():
    """Verify that a clean pristine asphalt road detects 0 defects."""
    clean = "backend/uploads/383ab1e9-e98f-438c-9a4d-00762edfd7c4.jpg"
    if not os.path.exists(clean):
        pytest.skip("Clean test image not found")
    with open(clean, "rb") as f:
        data = f.read()
    res = analyze_image(data)
    assert res["defects_detected"] == 0
    assert len(res["boxes"]) == 0


def test_budget_components_structure():
    """Verify default and dynamic budget structures have the expected 4 components."""
    budget = BudgetData(**DEFAULT_BUDGET)
    assert budget.totalValue > 0
    assert len(budget.materials) == 4
    names = {m.name for m in budget.materials}
    assert names == {"Patching", "Resurfacing", "Preventive", "Maintenance"}
    total_val = sum(m.value for m in budget.materials)
    assert total_val == budget.totalValue
