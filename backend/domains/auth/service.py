from datetime import datetime, timedelta, timezone

import jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from backend.config import settings
from backend.domains.auth import crud
from backend.domains.auth.models import User
from backend.domains.auth.schemas import (
    RegisterRequest,
    LoginRequest,
    PasswordChangeRequest,
)

# bcrypt 해싱 설정
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ──────────────────────────────────────────
# 비밀번호 유틸
# ──────────────────────────────────────────

def hash_password(password: str) -> str:
    """평문 비밀번호 → bcrypt 해시"""
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """평문과 해시 비교"""
    return pwd_context.verify(plain, hashed)


# ──────────────────────────────────────────
# JWT 유틸
# ──────────────────────────────────────────

def create_access_token(user_id: int) -> str:
    """JWT access token 생성"""
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


# ──────────────────────────────────────────
# 토큰 검증
# ──────────────────────────────────────────

def get_current_user(token: str, db: Session) -> User:
    """
    JWT 토큰 검증 → 현재 유저 반환
    router.py에서 인증이 필요한 엔드포인트에 사용
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = int(payload["sub"])
    except jwt.ExpiredSignatureError:
        raise ValueError("토큰이 만료되었습니다")
    except jwt.InvalidTokenError:
        raise ValueError("유효하지 않은 토큰입니다")

    user = crud.get_user_by_id(db, user_id)
    if not user or not user.is_active:
        raise ValueError("유효하지 않은 계정입니다")
    return user


# ──────────────────────────────────────────
# 회원가입
# ──────────────────────────────────────────

def register(db: Session, data: RegisterRequest) -> User:
    """
    회원가입
    1. 이메일 중복 확인
    2. 닉네임 중복 확인
    3. 비밀번호 해싱
    4. 유저 생성
    """
    if crud.get_user_by_email(db, data.email):
        raise ValueError("이미 사용 중인 이메일입니다")

    if crud.get_user_by_nickname(db, data.nickname):
        raise ValueError("이미 사용 중인 닉네임입니다")

    password_hash = hash_password(data.password)
    return crud.create_user(
        db,
        email=data.email,
        password_hash=password_hash,
        nickname=data.nickname,
        name=data.name,
        profile_image=data.profile_image,
    )


# ──────────────────────────────────────────
# 로그인
# ──────────────────────────────────────────

def login(db: Session, data: LoginRequest) -> tuple[str, User]:
    """
    로그인
    1. 이메일로 유저 조회
    2. 비밀번호 검증
    3. JWT 발급
    반환: (access_token, user)
    """
    user = crud.get_user_by_email(db, data.email)
    if not user or not verify_password(data.password, user.password_hash):
        raise ValueError("이메일 또는 비밀번호가 올바르지 않습니다")

    if not user.is_active:
        raise ValueError("탈퇴하거나 정지된 계정입니다")

    token = create_access_token(user.id)
    return token, user


# ──────────────────────────────────────────
# 중복 확인
# ──────────────────────────────────────────

def check_email(db: Session, email: str) -> bool:
    """이메일 사용 가능 여부 반환 (True = 사용 가능)"""
    return crud.get_user_by_email(db, email) is None


def check_nickname(db: Session, nickname: str) -> bool:
    """닉네임 사용 가능 여부 반환 (True = 사용 가능)"""
    return crud.get_user_by_nickname(db, nickname) is None


# ──────────────────────────────────────────
# 비밀번호 변경
# ──────────────────────────────────────────

def change_password(db: Session, user: User, data: PasswordChangeRequest) -> User:
    """
    비밀번호 변경
    1. 현재 비밀번호 확인
    2. 새 비밀번호 해싱
    3. 업데이트
    """
    if not verify_password(data.current_password, user.password_hash):
        raise ValueError("현재 비밀번호가 올바르지 않습니다")

    new_hash = hash_password(data.new_password)
    return crud.update_password(db, user, new_hash)
