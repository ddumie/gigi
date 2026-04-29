import logging
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database import get_async_db
from backend.domains.auth.router import get_current_user
from backend.domains.auth.models import User
from backend.domains.habits import service
from backend.domains.habits.crud import has_any_habit, get_active_habit_titles
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

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=list[HabitResponse])
async def list_habits(
    category:     str | None = Query(None, description="카테고리 필터"),
    db:           AsyncSession    = Depends(get_async_db),
    current_user: User       = Depends(get_current_user),
):
    habits = await service.get_habits(db, current_user.id, category)
    return [await service.build_habit_response(db, h) for h in habits]


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_habit(
    data:         HabitCreate,
    db:           AsyncSession = Depends(get_async_db),
    current_user: User    = Depends(get_current_user),
):
    is_first = not await has_any_habit(db, current_user.id)
    habit = await service.create_habit(db, current_user.id, data)
    payload = await service.build_habit_response(db, habit)
    return {**payload, "is_first_habit": is_first}


@router.put("/{habit_id}", response_model=HabitResponse)
async def update_habit(
    habit_id:     int,
    data:         HabitUpdate,
    db:           AsyncSession = Depends(get_async_db),
    current_user: User    = Depends(get_current_user),
):
    try:
        habit = await service.update_habit(db, current_user.id, habit_id, data)
        return await service.build_habit_response(db, habit)
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


@router.patch("/{habit_id}/visibility")
async def toggle_habit_visibility(
    habit_id:     int,
    db:           AsyncSession = Depends(get_async_db),
    current_user: User    = Depends(get_current_user),
):
    """모임 내 습관 공개/숨기기를 토글한다."""
    try:
        habit = await service.get_habit_or_raise(db, current_user.id, habit_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    from backend.domains.habits.crud import toggle_visibility
    updated = await toggle_visibility(db, habit)
    return {"id": updated.id, "is_hidden_from_group": updated.is_hidden_from_group}


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
    checked_date: date | None = Query(default=None),
    db:           AsyncSession = Depends(get_async_db),
    current_user: User    = Depends(get_current_user),
):
    if checked_date is None:
        checked_date = date.today()
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
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    """관심사 기반 AI 습관 추천 (온보딩 완료 후 추가 추천용)"""
    if current_user.is_first_login:
        raise HTTPException(status_code=403, detail="온보딩을 먼저 완료해주세요.")
    try:
        existing_titles = await get_active_habit_titles(db, current_user.id)
        habits = await get_ai_recommendations(None, request.health_interests, existing_titles)
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
    is_first = not await has_any_habit(db, current_user.id)
    try:
        await service.save_ai_selected_habits(db, current_user.id, request.selected_habits)
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"message": "선택한 습관이 등록되었습니다.", "is_first_habit": is_first}
