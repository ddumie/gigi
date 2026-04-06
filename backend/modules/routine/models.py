from sqlalchemy import Column, Integer, String, Date, DateTime, Boolean, ForeignKey
from sqlalchemy.sql import func
from backend.database import Base


class Routine(Base):
    __tablename__ = "routines"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String, nullable=False)
    category = Column(String, nullable=False)       # 운동, 복약, 식단, 수면, 기타
    time = Column(String)                            # "07:00"
    repeat_type = Column(String, default="매일")     # 매일, 평일, 주말, 주1회, 주3회
    description = Column(String, default="")
    is_ai_recommended = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)        # 비활성화 시 False
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class RoutineCheck(Base):
    __tablename__ = "routine_checks"

    id = Column(Integer, primary_key=True, index=True)
    routine_id = Column(Integer, ForeignKey("routines.id"), nullable=False, index=True)
    checked_date = Column(Date, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())