from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.domains.auth.router import get_current_user
from backend.domains.auth.models import User
from backend.domains.habits.schemas import HabitCheckRequest
from backend.domains.today import service
from backend.domains.today.schemas import TodayDashboardResponse

router = APIRouter()


@router.get("/", response_model=TodayDashboardResponse)
def get_today_dashboard(
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user),
):
    today = date.today()
    return service.get_today_dashboard(db, current_user.id, today)


@router.post("/habits/{habit_id}/toggle")
def toggle_habit_check(
    habit_id:     int,
    body:         HabitCheckRequest,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user),
):
    try:
        return service.toggle_habit_check(
            db, current_user.id, habit_id, body.checked_date
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
