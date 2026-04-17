from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from backend.domains.habits import crud
from backend.domains.habits.models import Habit, HabitCheck
from backend.domains.habits.schemas import HabitCreate, HabitUpdate


async def get_habit_or_raise(db: AsyncSession, user_id: int, habit_id: int) -> Habit:
    """습관 조회 + 소유권 검증. 없으면 ValueError."""
    habit = await crud.get_habit(db, habit_id, user_id)
    if not habit:
        raise ValueError("습관을 찾을 수 없습니다")
    return habit


async def get_habits(
    db: AsyncSession, user_id: int, category: str | None = None
) -> list[Habit]:
    return await crud.get_habits(db, user_id, category)


async def create_habit(db: AsyncSession, user_id: int, data: HabitCreate) -> Habit:
    return await crud.create_habit(db, user_id, data)


async def update_habit(
    db: AsyncSession, user_id: int, habit_id: int, data: HabitUpdate
) -> Habit:
    habit = await get_habit_or_raise(db, user_id, habit_id)
    return await crud.update_habit(db, habit, data)


async def deactivate_habit(db: AsyncSession, user_id: int, habit_id: int) -> Habit:
    habit = await get_habit_or_raise(db, user_id, habit_id)
    return await crud.deactivate_habit(db, habit)


async def check_habit(
    db: AsyncSession, user_id: int, habit_id: int, checked_date: date
) -> HabitCheck:
    await get_habit_or_raise(db, user_id, habit_id)
    return await crud.check_habit(db, habit_id, checked_date)


async def uncheck_habit(
    db: AsyncSession, user_id: int, habit_id: int, checked_date: date
) -> None:
    await get_habit_or_raise(db, user_id, habit_id)
    if not await crud.uncheck_habit(db, habit_id, checked_date):
        raise ValueError("체크 기록이 없습니다")
