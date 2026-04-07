from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, String
from sqlalchemy.sql import func
from backend.database import Base


class Routine(Base):
    """개인 습관과 모임 연동 습관을 함께 저장한다."""

    __tablename__ = "routines"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=True, index=True)
    title = Column(String, nullable=False)
    category = Column(String, nullable=False)            # 운동, 복약, 식단, 수면, 기타
    time = Column(String)                                # "07:00"
    repeat_type = Column(String, default="매일")         # 매일, 평일, 주말, 주1회, 주3회
    description = Column(String, default="")
    is_ai_recommended = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)            # 비활성화 시 False
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class RoutineCheck(Base):
    """습관 일일 체크 기록."""

    __tablename__ = "routine_checks"

    id = Column(Integer, primary_key=True, index=True)
    routine_id = Column(Integer, ForeignKey("routines.id"), nullable=False, index=True)
    checked_date = Column(Date, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
