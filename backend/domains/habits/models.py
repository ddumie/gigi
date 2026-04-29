from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.sql import func
from backend.database import Base

HABIT_CATEGORIES = ("운동", "복약", "식단", "수면", "기타")
HABIT_REPEAT_TYPES = ("매일", "평일", "주말", "주1회", "주3회")


class Habit(Base):
    """개인 습관과 모임 연동 습관을 함께 저장한다."""

    __tablename__ = "habits_list"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=True, index=True)
    # group_id 있는 경우 title/category/repeat_type은 GroupSearchPost에서 가져와 보여주므로 nullable
    title = Column(String, nullable=True)
    category = Column(String, nullable=True)             # 운동, 복약, 식단, 수면, 기타
    time = Column(String)                                # "07:00"
    repeat_type = Column(String, nullable=True, default="매일")  # 매일, 평일, 주말, 주1회, 주3회
    description = Column(String, default="")
    is_ai_recommended = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)            # 비활성화 시 False
    is_hidden_from_group = Column(Boolean, default=False)  # 모임 내 습관 목록에서 숨김
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class HabitCheck(Base):
    """습관 일일 체크 기록."""

    __tablename__ = "habit_checks"
    __table_args__ = (
        UniqueConstraint("habit_id", "checked_date", name="uq_habit_checks_habit_id_checked_date"),
    )

    id = Column(Integer, primary_key=True, index=True)
    habit_id = Column(Integer, ForeignKey("habits_list.id", ondelete="SET NULL"), nullable=True, index=True)
    checked_date = Column(Date, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
