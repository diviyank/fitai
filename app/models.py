from datetime import datetime
from datetime import date as DateType
from typing import Optional, Dict, Any
from sqlalchemy import JSON
from sqlmodel import SQLModel, Field, Column


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    password_hash: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class UserSession(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    token: str = Field(index=True, unique=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime


class Profile(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True, unique=True)
    sex: str = "homme"
    birth_date: Optional[DateType] = None
    height_cm: Optional[float] = None
    activity_level: str = "modere"
    language: str = "fr"
    units: str = "metric"
    medical_conditions: str = ""
    preferences: str = ""
    equipment: str = ""
    days_per_week: int = 3
    session_length_min: int = 45
    calorie_target_override: Optional[int] = None
    use_llm_directly: bool = True


class BodyMetric(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    date: DateType = Field(index=True)
    weight_kg: Optional[float] = None
    steps: Optional[int] = None
    body_fat_pct: Optional[float] = None
    measurements_json: dict = Field(default_factory=dict, sa_column=Column(JSON))
    energy: Optional[int] = None
    sleep_hours: Optional[float] = None
    soreness: Optional[int] = None
    notes: str = ""


class Goal(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    type: str = "general"  # see enums.GOAL_TYPES
    target_value: Optional[float] = None
    target_date: Optional[DateType] = None
    baseline_value: Optional[float] = None
    status: str = "active"  # active | achieved | abandoned
    notes: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)


class FoodLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    date: DateType = Field(index=True)
    meal_slot: Optional[str] = None  # see enums.MEAL_SLOTS
    description: str
    calories: Optional[int] = None
    protein_g: Optional[float] = None
    carbs_g: Optional[float] = None
    fat_g: Optional[float] = None
    source: str = "manual"  # manual | llm
