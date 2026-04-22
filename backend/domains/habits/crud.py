from datetime import date, timedelta
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from backend.domains.habits.models import Habit, HabitCheck
from backend.domains.habits.schemas import HabitCreate, HabitUpdate


# ── Habit ──


async def has_any_habit(db: AsyncSession, user_id: int) -> bool:
    """활성/비활성 포함, 해당 유저의 습관 레코드가 하나라도 있는지 확인한다."""
    result = await db.execute(
        select(func.count()).select_from(Habit).where(Habit.user_id == user_id)
    )
    return result.scalar() > 0


async def get_habit(db: AsyncSession, habit_id: int, user_id: int) -> Habit | None:
    result = await db.execute(
        select(Habit).where(
            Habit.id == habit_id,
            Habit.user_id == user_id,
            Habit.is_active == True,
        )
    )
    return result.scalar_one_or_none()


async def get_habits(db: AsyncSession, user_id: int, category: str | None = None) -> list[Habit]:
    stmt = select(Habit).where(Habit.user_id == user_id, Habit.is_active == True)
    if category:
        stmt = stmt.where(Habit.category == category)
    stmt = stmt.order_by(Habit.created_at.asc())
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def create_habit(db: AsyncSession, user_id: int, habit_in: HabitCreate) -> Habit:
    habit = Habit(user_id=user_id, **habit_in.model_dump())
    db.add(habit)
    await db.commit()
    await db.refresh(habit)
    return habit


async def create_group_habit(
    db: AsyncSession,
    user_id: int,
    group_id: int,
    title: str,
    category: str,
    repeat_type: str,
) -> Habit:
    """모임 참여 시 그룹 습관을 자동으로 생성한다 (Flow A/B 공통)."""
    habit = Habit(
        user_id     = user_id,
        group_id    = group_id,
        title       = title,
        category    = category,
        repeat_type = repeat_type,
    )
    db.add(habit)
    await db.commit()
    await db.refresh(habit)
    return habit


async def update_habit(db: AsyncSession, habit: Habit, habit_in: HabitUpdate) -> Habit:
    for field, value in habit_in.model_dump(exclude_unset=True).items():
        setattr(habit, field, value)
    await db.commit()
    await db.refresh(habit)
    return habit


async def toggle_visibility(db: AsyncSession, habit: Habit) -> Habit:
    """모임 내 습관 공개/숨기기를 토글한다."""
    habit.is_hidden_from_group = not habit.is_hidden_from_group
    await db.commit()
    await db.refresh(habit)
    return habit


async def deactivate_habit(db: AsyncSession, habit: Habit) -> Habit:
    """소프트 삭제 — is_active=False로 변경한다."""
    habit.is_active = False
    await db.commit()
    return habit


# ── HabitCheck ──


async def get_check(db: AsyncSession, habit_id: int, checked_date: date) -> HabitCheck | None:
    result = await db.execute(
        select(HabitCheck).where(
            HabitCheck.habit_id == habit_id,
            HabitCheck.checked_date == checked_date,
        )
    )
    return result.scalar_one_or_none()


async def get_checks_in_range(
    db: AsyncSession, habit_id: int, start: date, end: date
) -> list[HabitCheck]:
    result = await db.execute(
        select(HabitCheck).where(
            HabitCheck.habit_id == habit_id,
            HabitCheck.checked_date >= start,
            HabitCheck.checked_date <= end,
        )
    )
    return list(result.scalars().all())


async def get_today_checks_for_user(db: AsyncSession, user_id: int, today: date) -> list[HabitCheck]:
    """오늘 탭에서 사용 — 해당 유저의 오늘 체크 전체 조회."""
    result = await db.execute(
        select(HabitCheck)
        .join(Habit, Habit.id == HabitCheck.habit_id)
        .where(
            Habit.user_id == user_id,
            Habit.is_active == True,
            HabitCheck.checked_date == today,
        )
    )
    return list(result.scalars().all())


async def check_habit(db: AsyncSession, habit_id: int, checked_date: date) -> HabitCheck:
    """체크 ON — 이미 체크된 경우 기존 레코드를 반환한다."""
    existing = await get_check(db, habit_id, checked_date)
    if existing:
        return existing
    check = HabitCheck(habit_id = habit_id, checked_date = checked_date)
    db.add(check)
    await db.commit()
    await db.refresh(check)
    return check


async def uncheck_habit(db: AsyncSession, habit_id: int, checked_date: date) -> bool:
    """체크 OFF — 체크 레코드가 없으면 False 반환."""
    existing = await get_check(db, habit_id, checked_date)
    if not existing:
        return False
    await db.delete(existing)
    await db.commit()
    return True


# ── 통계 (오늘 탭 전달용) ──


async def count_checked_today(db: AsyncSession, user_id: int, today: date) -> tuple[int, int]:
    """(오늘 체크 수, 오늘 전체 활성 습관 수) 반환."""
    result = await db.execute(
        select(func.count(Habit.id)).where(
            Habit.user_id == user_id,
            Habit.is_active == True,
        )
    )
    total = result.scalar_one()

    result = await db.execute(
        select(func.count(HabitCheck.id))
        .join(Habit, Habit.id == HabitCheck.habit_id)
        .where(
            Habit.user_id == user_id,
            Habit.is_active == True,
            HabitCheck.checked_date == today,
        )
    )
    checked = result.scalar_one()

    return checked, total


async def get_weekly_checked_dates(db: AsyncSession, user_id: int, today: date) -> list[date]:
    """최근 7일간 체크된 날짜 목록 반환 (미니 달력용)."""
    start = today - timedelta(days=6)
    result = await db.execute(
        select(HabitCheck.checked_date)
        .join(Habit, Habit.id == HabitCheck.habit_id)
        .where(
            Habit.user_id == user_id,
            Habit.is_active == True,
            HabitCheck.checked_date >= start,
            HabitCheck.checked_date <= today,
        )
        .distinct()
    )
    return list(result.scalars().all())
