from typing import Optional
from pydantic import BaseModel, Field


class NutritionEstimate(BaseModel):
    description: str
    calories: int = 0
    protein_g: float = 0
    carbs_g: float = 0
    fat_g: float = 0


class NutritionListResponse(BaseModel):
    items: list[NutritionEstimate] = Field(default_factory=list)
