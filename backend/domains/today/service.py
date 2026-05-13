import calendar
from datetime import date, timedelta

DAY_MAP = {0: '월', 1: '화', 2: '수', 3: '목', 4: '금', 5: '토', 6: '일'}

def _is_habit_for_today(repeat_type: str | None, today: date) -> bool:
    if not repeat_type or repeat_type == '매일':
        return True
    today_day = DAY_MAP[today.weekday()]
    if repeat_type == '평일':
        return today.weekday() < 5
    if repeat_type == '주말':
        return today.weekday() >= 5
    return today_day in repeat_type

from sqlalchemy.ext.asyncio import AsyncSession

from backend.domains.habits import crud as habits_crud
from backend.domains.habits import service as habits_service
from backend.domains.today.schemas import (
    DailyProgress,
    TodayDashboardResponse,
    TodayHabitItem,
    TodayStat,
)


# ── 습관 메타 수집 (날짜별 예정 습관 판정에 필요) ──

async def _collect_habit_metas(db: AsyncSession, habits: list) -> list[dict]:
    """각 습관의 repeat_type/생성일을 모아둔다. 모임 습관은 Post 값으로 해석."""
    from backend.domains.habits import service as habits_service
    metas = []
    for h in habits:
        meta = await habits_service.resolve_habit_meta(db, h)
        metas.append({
            "id":           h.id,
            "repeat_type":  meta["repeat_type"],
            "created_date": h.created_at.date() if h.created_at else date.min,
        })
    return metas


def _scheduled_on(metas: list[dict], check_date: date) -> list[dict]:
    """그 날짜에 예정된 습관만 필터 (생성일 이후 + repeat_type 매치)."""
    return [
        m for m in metas
        if m["created_date"] <= check_date
        and _is_habit_for_today(m["repeat_type"], check_date)
    ]


# ── 연속 달성일 계산 ──

async def _calc_streak(db: AsyncSession, user_id: int, today: date) -> int:
    """오늘부터 역순으로 그 날 예정된 습관을 모두 완료한 연속 일수를 계산한다.

    예정된 습관이 0개인 날(예: 주말 전용만 있는 화요일)은 streak를 깨지 않고 건너뛴다.
    """
    habits = await habits_crud.get_habits(db, user_id)
    if not habits:
        return 0

    metas     = await _collect_habit_metas(db, habits)
    habit_ids = {m["id"] for m in metas}
    start     = today - timedelta(days=29)
    checks    = await habits_crud.get_checks_bulk(db, habit_ids, start, today)

    streak = 0
    for days_ago in range(30):
        check_date = today - timedelta(days=days_ago)
        scheduled  = _scheduled_on(metas, check_date)
        if not scheduled:
            # 그 날 예정된 습관 없음 → streak 유지하고 건너뛰기
            continue
        total       = len(scheduled)
        day_checked = sum(1 for m in scheduled if (m["id"], check_date) in checks)
        if day_checked == total:
            streak += 1
        else:
            if days_ago == 0:
                # 오늘은 아직 미완료여도 streak 깨지 않음
                continue
            break

    return streak


# ── 이번 주 평균 달성률 ──

async def _calc_weekly_average(db: AsyncSession, user_id: int, today: date) -> int:
    """최근 7일간 일별 달성률 평균. 예정 습관 없는 날은 평균에서 제외."""
    habits = await habits_crud.get_habits(db, user_id)
    if not habits:
        return 0

    metas       = await _collect_habit_metas(db, habits)
    habit_ids   = {m["id"] for m in metas}
    start       = today - timedelta(days=6)
    checks      = await habits_crud.get_checks_bulk(db, habit_ids, start, today)
    daily_rates = []

    for days_ago in range(7):
        check_date = today - timedelta(days=days_ago)
        scheduled  = _scheduled_on(metas, check_date)
        if not scheduled:
            continue  # 예정 습관 없는 날은 평균 계산에서 제외
        total       = len(scheduled)
        day_checked = sum(1 for m in scheduled if (m["id"], check_date) in checks)
        daily_rates.append(round(day_checked / total * 100))

    return round(sum(daily_rates) / len(daily_rates)) if daily_rates else 0


# ── 대시보드 ──

async def get_today_dashboard(
    db: AsyncSession, user_id: int, today: date
) -> TodayDashboardResponse:
    habits       = await habits_crud.get_habits(db, user_id)
    today_checks = await habits_crud.get_today_checks_for_user(db, user_id, today)
    checked_ids  = {check.habit_id for check in today_checks}

    habit_items = []
    for h in habits:
        meta = await habits_service.resolve_habit_meta(db, h)
        if not _is_habit_for_today(meta["repeat_type"], today):
            continue
        habit_items.append(
            TodayHabitItem(
                id          = h.id,
                title       = meta["title"],
                category    = meta["category"],
                time        = h.time,
                repeat_type = meta["repeat_type"],
                description = h.description or None,
                is_checked  = h.id in checked_ids,
                is_group    = h.group_id is not None,
            )
        )

    checked, total = await habits_crud.count_checked_today(db, user_id, today)
    weekly_dates   = await habits_crud.get_weekly_checked_dates(db, user_id, today)
    rate           = round(checked / total * 100) if total > 0 else 0
    weekly_avg     = await _calc_weekly_average(db, user_id, today)
    streak         = await _calc_streak(db, user_id, today)

    # 이번 달 일별 진행률 (미니 달력 셀 채움 + 클릭 툴팁용)
    # total은 "그 날 시점에 이미 존재했던 활성 습관 수"로 계산 (등록 전 날짜는 0)
    monthly_counts = await habits_crud.get_monthly_check_counts(db, user_id, today.year, today.month)
    last_day       = calendar.monthrange(today.year, today.month)[1]
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
