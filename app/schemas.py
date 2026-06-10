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


class PlanExercise(BaseModel):
    name: str
    sets: Optional[int] = None
    reps: Optional[str] = None         # e.g. "8-12"
    target_weight: Optional[str] = None
    rest: Optional[str] = None
    notes: Optional[str] = None


class PlanSession(BaseModel):
    week: int = 1
    day: int = 1
    title: str
    focus: Optional[str] = None
    exercises: list[PlanExercise] = Field(default_factory=list)


class PlanProposal(BaseModel):
    label: str
    sessions: list[PlanSession] = Field(default_factory=list)


class PlanGenResponse(BaseModel):
    plans: list[PlanProposal] = Field(default_factory=list)


class AdaptedPlanResponse(BaseModel):
    plan: PlanProposal
