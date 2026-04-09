from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.sql import func
from backend.database import Base


class UserPreference(Base):
    """사용자 온보딩 설정 (초기 수집: onboarding / 이후 수정: settings)"""
    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    age_group = Column(String)                           # 40대 이하, 50대, 60대, 70대 이상
    health_interests = Column(ARRAY(String))             # ["운동·체력", "복약 관리", "식단·영양" 등]
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    recommend_count = Column(Integer, default=0, nullable=False)