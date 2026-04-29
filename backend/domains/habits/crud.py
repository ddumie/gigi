import logging
from datetime import date, timedelta
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from backend.domains.habits.models import Habit, HabitCheck
from backend.domains.habits.schemas import HabitCreate, HabitUpdate


logger = logging.getLogger(__name__)


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
    stmt = stmt.order_by(Habit.created_at.desc())
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def create_habit(db: AsyncSession, user_id: int, habit_in: HabitCreate) -> Habit:
    try:
        habit = Habit(user_id=user_id, **habit_in.model_dump())
        db.add(habit)
        await db.commit()
        await db.refresh(habit)
        return habit
    except Exception as e:
        await db.rollback()
        logger.error(f"습관 생성 중 오류 발생: {e}", exc_info=True)
        raise ValueError("습관 생성 중 오류가 발생했습니다.")


async def create_group_habit(
    db: AsyncSession,
    user_id: int,
    group_id: int,
    title: str,
    category: str,
    repeat_type: str,
) -> Habit:
    """모임 참여 시 그룹 습관을 자동으로 생성한다 (Flow A/B 공통)."""
    try:
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
    except Exception as e:
        await db.rollback()
        logger.error(f"모임 습관 생성 중 오류 발생: {e}", exc_info=True)
        raise ValueError("모임 습관 생성 중 오류가 발생했습니다.")


async def update_habit(db: AsyncSession, habit: Habit, habit_in: HabitUpdate) -> Habit:
    try:
        for field, value in habit_in.model_dump(exclude_unset=True).items():
            setattr(habit, field, value)
        await db.commit()
        await db.refresh(habit)
        return habit
    except Exception as e:
        await db.rollback()
        logger.error(f"습관 수정 중 오류 발생: {e}", exc_info=True)
        raise ValueError("습관 수정 중 오류가 발생했습니다.")


async def toggle_visibility(db: AsyncSession, habit: Habit) -> Habit:
    """모임 내 습관 공개/숨기기를 토글한다."""
    try:
        habit.is_hidden_from_group = not habit.is_hidden_from_group
        await db.commit()
        await db.refresh(habit)
        return habit
    except Exception as e:
        await db.rollback()
        logger.error(f"습관 공개 설정 변경 중 오류 발생: {e}", exc_info=True)
        raise ValueError("습관 공개 설정 변경 중 오류가 발생했습니다.")


async def deactivate_habit(db: AsyncSession, habit: Habit) -> Habit:
    """소프트 삭제 — is_active=False로 변경한다."""
    try:
        habit.is_active = False
        await db.commit()
        return habit
    except Exception as e:
        await db.rollback()
        logger.error(f"습관 삭제 중 오류 발생: {e}", exc_info=True)
        raise ValueError("습관 삭제 중 오류가 발생했습니다.")


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


async def get_checks_bulk(
    db: AsyncSession, habit_ids: set[int], start: date, end: date
) -> set[tuple[int, date]]:
    """여러 습관의 지정 기간 체크 기록을 한 번에 조회한다."""
    result = await db.execute(
        select(HabitCheck.habit_id, HabitCheck.checked_date)
        .where(
            HabitCheck.habit_id.in_(habit_ids),
            HabitCheck.checked_date >= start,
            HabitCheck.checked_date <= end,
        )
    )
    return {(row.habit_id, row.checked_date) for row in result}


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
    try:
        check = HabitCheck(habit_id = habit_id, checked_date = checked_date)
        db.add(check)
        await db.commit()
        await db.refresh(check)
        return check
    except Exception as e:
        await db.rollback()
        logger.error(f"습관 체크 중 오류 발생: {e}", exc_info=True)
        raise ValueError("습관 체크 중 오류가 발생했습니다.")


async def uncheck_habit(db: AsyncSession, habit_id: int, checked_date: date) -> bool:
    """체크 OFF — 체크 레코드가 없으면 False 반환."""
    existing = await get_check(db, habit_id, checked_date)
    if not existing:
        return False
    try:
        await db.delete(existing)
        await db.commit()
        return True
    except Exception as e:
        await db.rollback()
        logger.error(f"습관 체크 해제 중 오류 발생: {e}", exc_info=True)
        raise ValueError("습관 체크 해제 중 오류가 발생했습니다.")


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


async def get_monthly_check_counts(
    db: AsyncSession, user_id: int, year: int, month: int
) -> dict[date, int]:
    """이번 달 각 날짜에 체크된 습관 수를 {date: count}로 반환 (미니 달력 진행률용)."""
    start = date(year, month, 1)
    # 다음 달 1일 - 1일 = 이번 달 마지막 날
    if month == 12:
        end = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        end = date(year, month + 1, 1) - timedelta(days=1)

    result = await db.execute(
        select(HabitCheck.checked_date, func.count(HabitCheck.id))
        .join(Habit, Habit.id == HabitCheck.habit_id)
        .where(
            Habit.user_id == user_id,
            Habit.is_active == True,
            HabitCheck.checked_date >= start,
            HabitCheck.checked_date <= end,
        )
        .group_by(HabitCheck.checked_date)
    )
    return {row[0]: row[1] for row in result.all()}
