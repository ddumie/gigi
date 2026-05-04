from pydantic import BaseModel, field_validator, Field
from backend.domains.habits.models import HABIT_CATEGORIES


class PreferenceRequest(BaseModel):
    """온보딩 1,2 : 나이대, 관심사, 글씨크기 저장"""
    age_group: str | None = None
    health_interests: list[str] | None = None
    font_size: str | None = None  # 보통, 큼, 아주큼


class PreferenceResponse(BaseModel):
    """온보딩 저장 선호도 조회"""
    age_group: str | None = None
    health_interests: list[str] | None = None
    font_size: str | None = None


class AIHabitItem(BaseModel):
    """AI추천습관 단일항목"""
    title: str = Field(..., min_length=1)
    category: str
    description: str = Field(..., min_length=1)
    repeat_type: str = "매일"

    @field_validator("category")
    @classmethod
    def category_must_be_valid(cls, v):
        """카테고리 유효성 검사(유효한 습관 카테고리인지 검증)"""
        if v not in HABIT_CATEGORIES:
            raise ValueError(f"유효하지 않은 카테고리입니다. {HABIT_CATEGORIES} 중 하나여야 합니다.")
        return v


class AIRecommendResponse(BaseModel):
    """AI추천습관 응답"""
    habits: list[AIHabitItem]
    can_retry: bool  # 재추천 가능한지 아닌지 여부 확인(1-True, 2-False)


class SelectRequest(BaseModel):
    """AI추천습관 선택 후 등록요청"""
    selected_habits: list[AIHabitItem]  # 사용자가 선택한 습관
