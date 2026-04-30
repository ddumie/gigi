from datetime import date

from pydantic import BaseModel


class TodayHabitItem(BaseModel):
    id:          int
    title:       str | None = None
    category:    str | None = None
    time:        str | None = None
    repeat_type: str | None = None
    description: str | None = None
    is_checked:  bool
    is_group:    bool = False


class DailyProgress(BaseModel):
    date:    date
    checked: int
    total:   int


class TodayStat(BaseModel):
    checked_count:       int
    total_count:         int
    completion_rate:     int
    weekly_average:      int
    streak_days:         int
    weekly_checked_dates: list[date]
    monthly_progress:    list[DailyProgress] = []


class TodayDashboardResponse(BaseModel):
    habits: list[TodayHabitItem]
    stats:  TodayStat
