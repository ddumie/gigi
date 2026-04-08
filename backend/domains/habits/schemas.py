from datetime import date, datetime
from pydantic import BaseModel, Field

from backend.domains.habits.models import HABIT_CATEGORIES, HABIT_REPEAT_TYPES


# ── Habit 요청 ──


class HabitCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    category: str = Field(..., description=" | ".join(HABIT_CATEGORIES))
    time: str | None = Field(None, description="예: 07:00")
    repeat_type: str = Field("매일", description=" | ".join(HABIT_REPEAT_TYPES))
    description: str = ""
    is_ai_recommended: bool = False
    group_id: int | None = None


class HabitUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=100)
    category: str | None = Field(None, description=" | ".join(HABIT_CATEGORIES))
    time: str | None = None
    repeat_type: str | None = Field(None, description=" | ".join(HABIT_REPEAT_TYPES))
    description: str | None = None


# ── Habit 응답 ──


class HabitResponse(BaseModel):
    id: int
    user_id: int
    group_id: int | None
    title: str
    category: str
    time: str | None
    repeat_type: str
    description: str
    is_ai_recommended: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime | None

    model_config = {"from_attributes": True}


# ── HabitCheck 요청 / 응답 ──


class HabitCheckRequest(BaseModel):
    checked_date: date = Field(default_factory=date.today)


class HabitCheckResponse(BaseModel):
    id: int
    habit_id: int
    checked_date: date
    created_at: datetime

    model_config = {"from_attributes": True}
