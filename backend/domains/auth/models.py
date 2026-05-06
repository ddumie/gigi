from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.sql import func
from backend.database import Base

# 유저 테이블
class User(Base):
    __tablename__ = "users"

    id            = Column(Integer, primary_key=True, index=True)                             # PK, 자동 증가 정수
    email         = Column(String(255), unique=True, nullable=False, index=True)              # 로그인 식별자, 중복 불가
    password_hash = Column(String(255), nullable=False)                                       # bcrypt 해시, 평문 저장 금지
    nickname      = Column(String(50), unique=True, nullable=False, index=True)               # 화면 표시용 이름, 중복 불가
    name          = Column(String(50), nullable=False)                                        # 실명, 중복 허용

    # 온보딩 정보
    age_group        = Column(String(20), nullable=True)                                      # 나이대 ("40대이하" | "50대" | "60대" | "70대이상")
    health_interests = Column(ARRAY(String), nullable=True, default=list)                     # 건강 관심사 목록 (예: ["혈압·혈당", "관절·근력"])

    # 상태값
    is_first_login = Column(Boolean, default=True)                                            # True면 온보딩 미완료 상태
    is_active      = Column(Boolean, default=True)                                            # False면 탈퇴/정지 (소프트 삭제)

    # 이미지
    profile_image = Column(String(500), nullable=True)                                        # 프로필 이미지 URL, 선택

    # 타임스탬프
    created_at = Column(DateTime(timezone=True), server_default=func.now())                   # 가입 시각, DB 서버 시간 자동 기록
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())  # 마지막 수정 시각