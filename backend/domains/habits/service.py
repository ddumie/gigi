from datetime import date

from sqlalchemy.orm import Session

from backend.domains.habits import crud
from backend.domains.habits.models import Habit, HabitCheck
from backend.domains.habits.schemas import HabitCreate, HabitUpdate


def get_habit_or_raise(db: Session, user_id: int, habit_id: int) -> Habit:
    """습관 조회 + 소유권 검증. 없으면 ValueError."""
    habit = crud.get_habit(db, habit_id, user_id)
    if not habit:
        raise ValueError("습관을 찾을 수 없습니다")
    return habit


def get_habits(
    db: Session, user_id: int, category: str | None = None
) -> list[Habit]:
    return crud.get_habits(db, user_id, category)


def create_habit(db: Session, user_id: int, data: HabitCreate) -> Habit:
    return crud.create_habit(db, user_id, data)


def update_habit(
    db: Session, user_id: int, habit_id: int, data: HabitUpdate
) -> Habit:
    habit = get_habit_or_raise(db, user_id, habit_id)
    return crud.update_habit(db, habit, data)


def deactivate_habit(db: Session, user_id: int, habit_id: int) -> Habit:
    habit = get_habit_or_raise(db, user_id, habit_id)
    return crud.deactivate_habit(db, habit)


def check_habit(
    db: Session, user_id: int, habit_id: int, checked_date: date
) -> HabitCheck:
    get_habit_or_raise(db, user_id, habit_id)
    return crud.check_habit(db, habit_id, checked_date)


def uncheck_habit(
    db: Session, user_id: int, habit_id: int, checked_date: date
) -> None:
    get_habit_or_raise(db, user_id, habit_id)
    if not crud.uncheck_habit(db, habit_id, checked_date):
        raise ValueError("체크 기록이 없습니다")
