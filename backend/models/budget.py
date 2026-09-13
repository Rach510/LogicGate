from typing import List, Optional

from pydantic import BaseModel


class MaterialCost(BaseModel):
    name: str
    amount: str
    value: float
    color: str


class LenderOption(BaseModel):
    name: str
    subtitle: str
    rate: str
    term: str
    highlight: Optional[bool] = None


class BudgetData(BaseModel):
    """Mirrors frontend/src/types/index.ts BudgetData."""

    total: str
    totalValue: float
    change: str
    materials: List[MaterialCost]
    lenders: List[LenderOption]
