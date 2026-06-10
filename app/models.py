from datetime import date, datetime
from typing import Optional
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
    birth_date: Optional[date] = None
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
