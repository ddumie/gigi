from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from backend.database import Base


class User(Base):
    """사용자 계정 테이블"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    nickname = Column(String, unique=True, nullable=False)
    is_first_login = Column(Boolean, default=True)      # 첫 로그인 시 모달 표시 후 False
    is_active = Column(Boolean, default=True)            # 탈퇴/정지 시 False
    created_at = Column(DateTime(timezone=True), server_default=func.now())
