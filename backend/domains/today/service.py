from datetime import date, timedelta

from sqlalchemy.orm import Session

from backend.domains.habits import crud as habits_crud
from backend.domains.habits import service as habits_service
from backend.domains.today.schemas import (
    TodayDashboardResponse,
    TodayHabitItem,
    TodayStat,
)


# ── 연속 달성일 계산 ──

def _calc_streak(db: Session, user_id: int, today: date) -> int:
    """오늘부터 역순으로 모든 활성 습관을 완료한 연속 일수를 계산한다."""
    habits = habits_crud.get_habits(db, user_id)
    if not habits:
        return 0

    habit_ids = {h.id for h in habits}
    total     = len(habit_ids)
    streak    = 0

    for days_ago in range(30):
        check_date  = today - timedelta(days=days_ago)
        day_checked = 0
        for h_id in habit_ids:
            if habits_crud.get_check(db, h_id, check_date):
                day_checked += 1

        if day_checked == total:
            streak += 1
        else:
            # 오늘이 아직 미완료면 어제부터 카운트 시작
            if days_ago == 0:
                continue
            break

    return streak


# ── 이번 주 평균 달성률 ──

def _calc_weekly_average(db: Session, user_id: int, today: date) -> int:
    """최근 7일간의 일별 달성률 평균을 계산한다."""
    habits = habits_crud.get_habits(db, user_id)
    if not habits:
        return 0

    habit_ids  = {h.id for h in habits}
    total      = len(habit_ids)
    daily_rates = []

    for days_ago in range(7):
        check_date  = today - timedelta(days=days_ago)
        day_checked = 0
        for h_id in habit_ids:
            if habits_crud.get_check(db, h_id, check_date):
                day_checked += 1
        daily_rates.append(round(day_checked / total * 100))

    return round(sum(daily_rates) / len(daily_rates)) if daily_rates else 0


# ── 대시보드 ──

def get_today_dashboard(
    db: Session, user_id: int, today: date
) -> TodayDashboardResponse:
    habits       = habits_crud.get_habits(db, user_id)
    today_checks = habits_crud.get_today_checks_for_user(db, user_id, today)
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

    checked, total = habits_crud.count_checked_today(db, user_id, today)
    weekly_dates   = habits_crud.get_weekly_checked_dates(db, user_id, today)
    rate           = round(checked / total * 100) if total > 0 else 0
    weekly_avg     = _calc_weekly_average(db, user_id, today)
    streak         = _calc_streak(db, user_id, today)

    stats = TodayStat(
        checked_count        = checked,
        total_count          = total,
        completion_rate      = rate,
        weekly_average       = weekly_avg,
        streak_days          = streak,
        weekly_checked_dates = weekly_dates,
    )

    return TodayDashboardResponse(habits=habit_items, stats=stats)


# ── 체크 토글 ──

def toggle_habit_check(
    db: Session, user_id: int, habit_id: int, checked_date: date
) -> dict:
    """체크 상태를 토글한다. 현재 체크되어 있으면 해제, 아니면 체크."""
    habits_service.get_habit_or_raise(db, user_id, habit_id)
    existing = habits_crud.get_check(db, habit_id, checked_date)
    if existing:
        habits_crud.uncheck_habit(db, habit_id, checked_date)
        return {"is_checked": False}
    else:
        habits_crud.check_habit(db, habit_id, checked_date)
        return {"is_checked": True}
