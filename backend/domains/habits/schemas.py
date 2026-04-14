from datetime import date, datetime
from pydantic import BaseModel, Field, field_validator

from backend.domains.habits.models import HABIT_CATEGORIES, HABIT_REPEAT_TYPES


# ── Habit 요청 ──


class HabitCreate(BaseModel):
    title:            str        = Field(..., min_length=1, max_length=100)
    category:         str        = Field(..., description=" | ".join(HABIT_CATEGORIES))
    time:             str | None = Field(None, description="예: 07:00")
    repeat_type:      str        = Field("매일", description=" | ".join(HABIT_REPEAT_TYPES))
    description:      str        = ""
    is_ai_recommended: bool      = False
    group_id:         int | None = None

    @field_validator("category")
    @classmethod
    def validate_category(cls, v):
        if v not in HABIT_CATEGORIES:
            raise ValueError(f"카테고리는 {', '.join(HABIT_CATEGORIES)} 중 하나여야 합니다")
        return v

    @field_validator("repeat_type")
    @classmethod
    def validate_repeat_type(cls, v):
        if v not in HABIT_REPEAT_TYPES:
            raise ValueError(f"반복 유형은 {', '.join(HABIT_REPEAT_TYPES)} 중 하나여야 합니다")
        return v


class HabitUpdate(BaseModel):
    title:       str | None = Field(None, min_length=1, max_length=100)
    category:    str | None = Field(None, description=" | ".join(HABIT_CATEGORIES))
    time:        str | None = None
    repeat_type: str | None = Field(None, description=" | ".join(HABIT_REPEAT_TYPES))
    description: str | None = None

    @field_validator("category")
    @classmethod
    def validate_category(cls, v):
        if v is not None and v not in HABIT_CATEGORIES:
            raise ValueError(f"카테고리는 {', '.join(HABIT_CATEGORIES)} 중 하나여야 합니다")
        return v

    @field_validator("repeat_type")
    @classmethod
    def validate_repeat_type(cls, v):
        if v is not None and v not in HABIT_REPEAT_TYPES:
            raise ValueError(f"반복 유형은 {', '.join(HABIT_REPEAT_TYPES)} 중 하나여야 합니다")
        return v


# ── Habit 응답 ──


class HabitResponse(BaseModel):
    id:               int
    user_id:          int
    group_id:         int | None
    title:            str
    category:         str
    time:             str | None
    repeat_type:      str
    description:      str
    is_ai_recommended: bool
    is_active:        bool
    created_at:       datetime
    updated_at:       datetime | None

    model_config = {"from_attributes": True}


# ── HabitCheck 요청 / 응답 ──


class HabitCheckRequest(BaseModel):
    checked_date: date = Field(default_factory=date.today)


class HabitCheckResponse(BaseModel):
    id:           int
    habit_id:     int
    checked_date: date
    created_at:   datetime

    model_config = {"from_attributes": True}
