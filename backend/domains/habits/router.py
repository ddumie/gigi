from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.domains.auth.router import get_current_user
from backend.domains.auth.models import User
from backend.domains.habits import service
from backend.domains.habits.schemas import (
    HabitCreate,
    HabitUpdate,
    HabitResponse,
    HabitCheckRequest,
    HabitCheckResponse,
    HabitAIRecommendRequest,
    HabitAIRecommendResponse,
    HabitAISelectRequest,
)
from backend.domains.onboarding.service import get_ai_recommendations
from backend.domains.habits.models import Habit

router = APIRouter()


@router.get("/", response_model=list[HabitResponse])
def list_habits(
    category:     str | None = Query(None, description="카테고리 필터"),
    db:           Session    = Depends(get_db),
    current_user: User       = Depends(get_current_user),
):
    return service.get_habits(db, current_user.id, category)


@router.post("/", response_model=HabitResponse, status_code=status.HTTP_201_CREATED)
def create_habit(
    data:         HabitCreate,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user),
):
    return service.create_habit(db, current_user.id, data)


@router.put("/{habit_id}", response_model=HabitResponse)
def update_habit(
    habit_id:     int,
    data:         HabitUpdate,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user),
):
    try:
        return service.update_habit(db, current_user.id, habit_id, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/{habit_id}")
def delete_habit(
    habit_id:     int,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user),
):
    try:
        service.deactivate_habit(db, current_user.id, habit_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return {"message": "삭제되었습니다"}


@router.post(
    "/{habit_id}/check",
    response_model=HabitCheckResponse,
    status_code=status.HTTP_201_CREATED,
)
def check_habit(
    habit_id:     int,
    body:         HabitCheckRequest,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user),
):
    try:
        return service.check_habit(db, current_user.id, habit_id, body.checked_date)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/{habit_id}/check")
def uncheck_habit(
    habit_id:     int,
    checked_date: date    = Query(default_factory=date.today),
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user),
):
    try:
        service.uncheck_habit(db, current_user.id, habit_id, checked_date)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return {"message": "체크가 해제되었습니다"}

# 온보딩 이후에 다른 항목에 대해서 추천받고싶을 때
# AI 추천 습관 받기
@router.post("/ai-recommend", response_model=HabitAIRecommendResponse)
def recommend_habits(
    request: HabitAIRecommendRequest,
    current_user: User = Depends(get_current_user),
):
    """관심사 기반 AI 습관 추천 (온보딩 완료 후 추가 추천용)"""
    try:
        habits = get_ai_recommendations(None, request.health_interests)
    except ValueError:
        raise HTTPException(status_code=502, detail="맞춤 습관 추천 중 오류가 발생했습니다.")
    return HabitAIRecommendResponse(habits=habits)


# AI 추천 습관 선택 후 등록
@router.post("/ai-recommend/select", status_code=status.HTTP_201_CREATED)
def select_habits(
    request: HabitAISelectRequest,
    db: Session = Depends(get_db),
    current_user: User    = Depends(get_current_user),
):
    """AI가 추천한 습관을 선택해서 등록(추가등록)"""
    if not request.selected_habits:
        raise HTTPException(status_code=400, detail="습관을 하나 이상 선택해주세요.")
    try:
        for item in request.selected_habits:
            db.add(Habit(
                user_id=current_user.id,
                title=item.title,
                category=item.category,
                description=item.description,
                repeat_type="매일",
                is_ai_recommended=True,
            ))
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="습관 저장 중 오류가 발생했습니다.")
    return {"message": "선택한 습관이 등록되었습니다."}
