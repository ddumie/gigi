from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.sql import func
from backend.database import Base


class UserPreference(Base):
    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    age_group = Column(String)                       # "50대", "60대", "70대"
    health_interests = Column(ARRAY(String))         # ["운동·체력", "복약 관리"]
    exercise_time = Column(String)                   # "아침 (6~9시)"
    created_at = Column(DateTime(timezone=True), server_default=func.now())