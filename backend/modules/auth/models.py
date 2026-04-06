from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from backend.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    nickname = Column(String, nullable=False)
    account_type = Column(String, nullable=False)  # "senior" / "family"
    is_active = Column(Boolean, default=True)       # 탈퇴/정지 시 False
    created_at = Column(DateTime(timezone=True), server_default=func.now())