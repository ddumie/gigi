from datetime import date, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from backend.domains.habits import crud as habits_crud
from backend.domains.habits import service as habits_service
from backend.domains.today.schemas import (
    DailyProgress,
    TodayDashboardResponse,
    TodayHabitItem,
    TodayStat,
)


# ── 연속 달성일 계산 ──

async def _calc_streak(db: AsyncSession, user_id: int, today: date) -> int:
    """오늘부터 역순으로 모든 활성 습관을 완료한 연속 일수를 계산한다."""
    habits = await habits_crud.get_habits(db, user_id)
    if not habits:
        return 0

    habit_ids = {h.id for h in habits}
    total     = len(habit_ids)
    start     = today - timedelta(days=29)
    checks    = await habits_crud.get_checks_bulk(db, habit_ids, start, today)

    streak = 0
    for days_ago in range(30):
        check_date  = today - timedelta(days=days_ago)
        day_checked = sum(1 for h_id in habit_ids if (h_id, check_date) in checks)
        if day_checked == total:
            streak += 1
        else:
            if days_ago == 0:
                continue
            break

    return streak


# ── 이번 주 평균 달성률 ──

async def _calc_weekly_average(db: AsyncSession, user_id: int, today: date) -> int:
    """최근 7일간의 일별 달성률 평균을 계산한다."""
    habits = await habits_crud.get_habits(db, user_id)
    if not habits:
        return 0

    habit_ids   = {h.id for h in habits}
    total       = len(habit_ids)
    start       = today - timedelta(days=6)
    checks      = await habits_crud.get_checks_bulk(db, habit_ids, start, today)
    daily_rates = []

    for days_ago in range(7):
        check_date  = today - timedelta(days=days_ago)
        day_checked = sum(1 for h_id in habit_ids if (h_id, check_date) in checks)
        daily_rates.append(round(day_checked / total * 100))

    return round(sum(daily_rates) / len(daily_rates)) if daily_rates else 0


# ── 대시보드 ──

async def get_today_dashboard(
    db: AsyncSession, user_id: int, today: date
) -> TodayDashboardResponse:
    habits       = await habits_crud.get_habits(db, user_id)
    today_checks = await habits_crud.get_today_checks_for_user(db, user_id, today)
    checked_ids  = {check.habit_id for check in today_checks}

    habit_items = [
        TodayHabitItem(
            id          = h.id,
            title       = h.title,
            category    = h.category,
            time        = h.time,
            repeat_type = h.repeat_type,
            is_checked  = h.id in checked_ids,
            is_group    = h.group_id is not None,
        )
        for h in habits
    ]

    checked, total = await habits_crud.count_checked_today(db, user_id, today)
    weekly_dates   = await habits_crud.get_weekly_checked_dates(db, user_id, today)
    rate           = round(checked / total * 100) if total > 0 else 0
    weekly_avg     = await _calc_weekly_average(db, user_id, today)
    streak         = await _calc_streak(db, user_id, today)

    # 이번 달 일별 진행률 (미니 달력 셀 채움 + 클릭 툴팁용)
    # total은 "그 날 시점에 이미 존재했던 활성 습관 수"로 계산 (등록 전 날짜는 0)
    monthly_counts = await habits_crud.get_monthly_check_counts(db, user_id, today.year, today.month)
    last_day       = (date(today.year + (1 if today.month == 12 else 0),
                            1 if today.month == 12 else today.month + 1, 1) - timedelta(days=1)).day
    habit_created_dates = [h.created_at.date() for h in habits if h.created_at]

    monthly_progress = []
    for d in range(1, last_day + 1):
        day       = date(today.year, today.month, d)
        day_total = sum(1 for cd in habit_created_dates if cd <= day)
        monthly_progress.append(
            DailyProgress(
                date    = day,
                checked = monthly_counts.get(day, 0),
                total   = day_total,
            )
        )

    stats = TodayStat(
        checked_count        = checked,
        total_count          = total,
        completion_rate      = rate,
        weekly_average       = weekly_avg,
        streak_days          = streak,
        weekly_checked_dates = weekly_dates,
        monthly_progress     = monthly_progress,
    )

    return TodayDashboardResponse(habits=habit_items, stats=stats)


# ── 체크 토글 ──

async def toggle_habit_check(
    db: AsyncSession, user_id: int, habit_id: int, checked_date: date
) -> dict:
    """체크 상태를 토글한다. 현재 체크되어 있으면 해제, 아니면 체크."""
    await habits_service.get_habit_or_raise(db, user_id, habit_id)
    existing = await habits_crud.get_check(db, habit_id, checked_date)
    if existing:
        await habits_crud.uncheck_habit(db, habit_id, checked_date)
        return {"is_checked": False}
    else:
        await habits_crud.check_habit(db, habit_id, checked_date)
        return {"is_checked": True}
