from datetime import date, timedelta

from sqlalchemy import select, func, and_
from sqlalchemy.orm import Session

from backend.domains.habits.models import Habit, HabitCheck
from backend.domains.habits.schemas import HabitCreate, HabitUpdate


# ── Habit ──


def get_habit(db: Session, habit_id: int, user_id: int) -> Habit | None:
    return db.execute(
        select(Habit).where(
            Habit.id == habit_id,
            Habit.user_id == user_id,
            Habit.is_active == True,
        )
    ).scalar_one_or_none()


def get_habits(db: Session, user_id: int, category: str | None = None) -> list[Habit]:
    stmt = select(Habit).where(Habit.user_id == user_id, Habit.is_active == True)
    if category:
        stmt = stmt.where(Habit.category == category)
    stmt = stmt.order_by(Habit.created_at.asc())
    return list(db.execute(stmt).scalars().all())


def create_habit(db: Session, user_id: int, habit_in: HabitCreate) -> Habit:
    habit = Habit(user_id=user_id, **habit_in.model_dump())
    db.add(habit)
    db.commit()
    db.refresh(habit)
    return habit


def create_group_habit(
    db: Session,
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
    db.commit()
    db.refresh(habit)
    return habit


def update_habit(db: Session, habit: Habit, habit_in: HabitUpdate) -> Habit:
    for field, value in habit_in.model_dump(exclude_unset=True).items():
        setattr(habit, field, value)
    db.commit()
    db.refresh(habit)
    return habit


def deactivate_habit(db: Session, habit: Habit) -> Habit:
    """소프트 삭제 — is_active=False로 변경한다."""
    habit.is_active = False
    db.commit()
    return habit


# ── HabitCheck ──


def get_check(db: Session, habit_id: int, checked_date: date) -> HabitCheck | None:
    return db.execute(
        select(HabitCheck).where(
            HabitCheck.habit_id == habit_id,
            HabitCheck.checked_date == checked_date,
        )
    ).scalar_one_or_none()


def get_checks_in_range(
    db: Session, habit_id: int, start: date, end: date
) -> list[HabitCheck]:
    return list(
        db.execute(
            select(HabitCheck).where(
                HabitCheck.habit_id == habit_id,
                HabitCheck.checked_date >= start,
                HabitCheck.checked_date <= end,
            )
        ).scalars().all()
    )


def get_today_checks_for_user(db: Session, user_id: int, today: date) -> list[HabitCheck]:
    """오늘 탭에서 사용 — 해당 유저의 오늘 체크 전체 조회."""
    return list(
        db.execute(
            select(HabitCheck)
            .join(Habit, Habit.id == HabitCheck.habit_id)
            .where(
                Habit.user_id == user_id,
                Habit.is_active == True,
                HabitCheck.checked_date == today,
            )
        ).scalars().all()
    )


def check_habit(db: Session, habit_id: int, checked_date: date) -> HabitCheck:
    """체크 ON — 이미 체크된 경우 기존 레코드를 반환한다."""
    existing = get_check(db, habit_id, checked_date)
    if existing:
        return existing
    check = HabitCheck(habit_id = habit_id, checked_date = checked_date)
    db.add(check)
    db.commit()
    db.refresh(check)
    return check


def uncheck_habit(db: Session, habit_id: int, checked_date: date) -> bool:
    """체크 OFF — 체크 레코드가 없으면 False 반환."""
    existing = get_check(db, habit_id, checked_date)
    if not existing:
        return False
    db.delete(existing)
    db.commit()
    return True


# ── 통계 (오늘 탭 전달용) ──


def count_checked_today(db: Session, user_id: int, today: date) -> tuple[int, int]:
    """(오늘 체크 수, 오늘 전체 활성 습관 수) 반환."""
    total = db.execute(
        select(func.count(Habit.id)).where(
            Habit.user_id == user_id,
            Habit.is_active == True,
        )
    ).scalar_one()

    checked = db.execute(
        select(func.count(HabitCheck.id))
        .join(Habit, Habit.id == HabitCheck.habit_id)
        .where(
            Habit.user_id == user_id,
            Habit.is_active == True,
            HabitCheck.checked_date == today,
        )
    ).scalar_one()

    return checked, total


def get_weekly_checked_dates(db: Session, user_id: int, today: date) -> list[date]:
    """최근 7일간 체크된 날짜 목록 반환 (미니 달력용)."""
    start = today - timedelta(days=6)
    rows = db.execute(
        select(HabitCheck.checked_date)
        .join(Habit, Habit.id == HabitCheck.habit_id)
        .where(
            Habit.user_id == user_id,
            Habit.is_active == True,
            HabitCheck.checked_date >= start,
            HabitCheck.checked_date <= today,
        )
        .distinct()
    ).scalars().all()
    return list(rows)
