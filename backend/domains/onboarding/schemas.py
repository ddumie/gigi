from pydantic import BaseModel, field_validator, Field


class PreferenceRequest(BaseModel):
    """온보딩 1,2 : 나이대, 관심사 저장"""
    age_group: str | None = None
    health_interests: list[str] | None = None


class AIHabitItem(BaseModel):
    """AI추천습관 단일항목"""
    title: str = Field(..., min_length=1)
    category: str
    description: str = Field(..., min_length=1)

    @field_validator("category")
    @classmethod
    def category_must_be_valid(cls, v):
        """카테고리 유효성 검사(유효한 습관 카테고리인지 검증)"""
        habit_categories = ["운동", "복약", "식단", "수면", "기타"]
        if v not in habit_categories:
            raise ValueError(f"유효하지 않은 카테고리입니다. {habit_categories} 중 하나여야 합니다.")
        return v


class AIRecommendResponse(BaseModel):
    """AI추천습관 응답"""
    habits: list[AIHabitItem]
    can_retry: bool  # 재추천 가능한지 아닌지 여부 확인(1-True, 2-False)


class SelectRequest(BaseModel):
    """AI추천습관 선택 후 등록요청"""
    selected_habits: list[AIHabitItem]  # 사용자가 선택한 습관
