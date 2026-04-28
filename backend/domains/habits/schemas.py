from datetime import date, datetime
from pydantic import BaseModel, Field, field_validator

from backend.domains.habits.models import HABIT_CATEGORIES, HABIT_REPEAT_TYPES
from backend.domains.onboarding.schemas import AIHabitItem

# 요일 피커로 들어오는 임의 조합 검증용 (예: "월수금", "화목")
_VALID_DAYS = set("월화수목금토일")


def _is_valid_repeat_type(v: str) -> bool:
    """
    허용 형식:
      1) 기존 프리셋: 매일/평일/주말/주1회/주3회
      2) 요일 조합 문자열: 월,화,수,목,금,토,일 중 1~7자, 중복 없음
    """
    if v in HABIT_REPEAT_TYPES:
        return True
    if not v or len(v) > 7:
        return False
    if any(ch not in _VALID_DAYS for ch in v):
        return False
    if len(set(v)) != len(v):  # 중복 요일 금지
        return False
    return True


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
        if not _is_valid_repeat_type(v):
            raise ValueError(
                f"반복 유형은 {', '.join(HABIT_REPEAT_TYPES)} 또는 요일 조합(예: 월수금)이어야 합니다"
            )
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
        if v is not None and not _is_valid_repeat_type(v):
            raise ValueError(
                f"반복 유형은 {', '.join(HABIT_REPEAT_TYPES)} 또는 요일 조합(예: 월수금)이어야 합니다"
            )
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
    is_hidden_from_group: bool
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
 

# ── AI 추천 요청 / 응답 ──


class HabitAIRecommendRequest(BaseModel):
    """AI 습관 추천 요청(온보딩 완료 후 추가 추천용)"""
    health_interests: list[str] = Field(..., description="관심사 카테고리 목록")


class HabitAIRecommendResponse(BaseModel):
    """AI 습관 추천 결과 응답"""
    habits: list[AIHabitItem]


class HabitAISelectRequest(BaseModel):
    """AI 추천 습관 선택 후 등록 요청"""
    selected_habits: list[AIHabitItem]
