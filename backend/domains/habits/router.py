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
)

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
