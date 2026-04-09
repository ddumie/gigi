from pydantic import BaseModel

class PreferenceRequest(BaseModel):
    """온보딩 1,2 : 나이대, 관심사 저장"""
    age_group : str | None
    health_interests : list[str] | None

class AIHabitItem(BaseModel):
    """AI추천습관 단일항목"""
    title: str
    category: str
    description: str

class AIRecommendResponse(BaseModel):
    """AI추천습관 응답"""
    habits: list[AIHabitItem]
    can_retry: bool #재추전 가능한지 아닌지 여부 확인(1-True, 2-False)

class SelectRequest(BaseModel):
    """AI추천습관 선택 후 등록요청"""
    selected_habits: list[AIHabitItem] #사용자가 선택한 습관
