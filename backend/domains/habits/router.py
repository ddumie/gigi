from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database import get_async_db
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
async def list_habits(
    category:     str | None = Query(None, description="카테고리 필터"),
    db:           AsyncSession    = Depends(get_async_db),
    current_user: User       = Depends(get_current_user),
):
    return await service.get_habits(db, current_user.id, category)


@router.post("/", response_model=HabitResponse, status_code=status.HTTP_201_CREATED)
async def create_habit(
    data:         HabitCreate,
    db:           AsyncSession = Depends(get_async_db),
    current_user: User    = Depends(get_current_user),
):
    return await service.create_habit(db, current_user.id, data)


@router.put("/{habit_id}", response_model=HabitResponse)
async def update_habit(
    habit_id:     int,
    data:         HabitUpdate,
    db:           AsyncSession = Depends(get_async_db),
    current_user: User    = Depends(get_current_user),
):
    try:
        return await service.update_habit(db, current_user.id, habit_id, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/{habit_id}")
async def delete_habit(
    habit_id:     int,
    db:           AsyncSession = Depends(get_async_db),
    current_user: User    = Depends(get_current_user),
):
    try:
        await service.deactivate_habit(db, current_user.id, habit_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return {"message": "삭제되었습니다"}


@router.post(
    "/{habit_id}/check",
    response_model=HabitCheckResponse,
    status_code=status.HTTP_201_CREATED,
)
async def check_habit(
    habit_id:     int,
    body:         HabitCheckRequest,
    db:           AsyncSession = Depends(get_async_db),
    current_user: User    = Depends(get_current_user),
):
    try:
        return await service.check_habit(db, current_user.id, habit_id, body.checked_date)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/{habit_id}/check")
async def uncheck_habit(
    habit_id:     int,
    checked_date: date    = Query(default_factory=date.today),
    db:           AsyncSession = Depends(get_async_db),
    current_user: User    = Depends(get_current_user),
):
    try:
        await service.uncheck_habit(db, current_user.id, habit_id, checked_date)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return {"message": "체크가 해제되었습니다"}

# 온보딩 이후에 다른 항목에 대해서 추천받고싶을 때
# AI 추천 습관 받기
@router.post("/ai-recommend", response_model=HabitAIRecommendResponse)
async def recommend_habits(
    request: HabitAIRecommendRequest,
    current_user: User = Depends(get_current_user),
):
    """관심사 기반 AI 습관 추천 (온보딩 완료 후 추가 추천용)"""
    if current_user.is_first_login:
        raise HTTPException(status_code=403, detail="온보딩을 먼저 완료해주세요.")
    try:
        habits = await get_ai_recommendations(None, request.health_interests)
    except ValueError:
        raise HTTPException(status_code=502, detail="맞춤 습관 추천 중 오류가 발생했습니다.")
    return HabitAIRecommendResponse(habits=habits)


# AI 추천 습관 선택 후 등록
@router.post("/ai-recommend/select", status_code=status.HTTP_201_CREATED)
async def select_habits(
    request: HabitAISelectRequest,
    db: AsyncSession = Depends(get_async_db),
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
        await db.commit()
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="습관 저장 중 오류가 발생했습니다.")
    return {"message": "선택한 습관이 등록되었습니다."}
