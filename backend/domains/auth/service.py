import asyncio
import secrets
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage

import aiosmtplib
import jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

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

async def hash_password(password: str) -> str:
    """평문 비밀번호 → bcrypt 해시"""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, pwd_context.hash, password)


async def verify_password(plain: str, hashed: str) -> bool:
    """평문과 해시 비교"""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, pwd_context.verify, plain, hashed)


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

async def get_current_user(token: str, db: AsyncSession) -> User:
    """
    JWT 토큰 검증 → 현재 유저 반환
    router.py에서 인증이 필요한 엔드포인트에 사용
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = int(payload["sub"])
    except jwt.ExpiredSignatureError:
        raise ValueError("토큰이 만료되었습니다")
    except (jwt.InvalidTokenError, KeyError, ValueError, TypeError):
        raise ValueError("유효하지 않은 토큰입니다")

    user = await crud.get_user_by_id(db, user_id)
    if not user or not user.is_active:
        raise ValueError("유효하지 않은 계정입니다")
    return user


# ──────────────────────────────────────────
# 회원가입
# ──────────────────────────────────────────

async def register(db: AsyncSession, data: RegisterRequest) -> User:
    """
    회원가입
    1. 이메일 중복 확인
    2. 닉네임 중복 확인
    3. 비밀번호 해싱
    4. 유저 생성
    """
    if await crud.get_user_by_email(db, data.email):
        raise ValueError("이미 사용 중인 이메일입니다")

    if await crud.get_user_by_nickname(db, data.nickname):
        raise ValueError("이미 사용 중인 닉네임입니다")

    password_hash = await hash_password(data.password)
    return await crud.create_user(
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

async def login(db: AsyncSession, data: LoginRequest) -> tuple[str, User]:
    """
    로그인
    1. 이메일로 유저 조회
    2. 계정 잠금 여부 확인
    3. 비밀번호 검증
    4. JWT 발급
    반환: (access_token, user)
    """
    user = await crud.get_user_by_email(db, data.email)
    if not user or not user.is_active:
        raise ValueError("이메일 또는 비밀번호가 올바르지 않습니다")

    now = datetime.now(timezone.utc)
    if user.locked_until and user.locked_until > now:
        remaining = int((user.locked_until - now).total_seconds() / 60) + 1
        raise ValueError(f"로그인 시도 횟수를 초과했습니다. {remaining}분 후 다시 시도해주세요.")

    if not await verify_password(data.password, user.password_hash):
        await crud.increment_login_fail(db, user)
        raise ValueError("이메일 또는 비밀번호가 올바르지 않습니다")

    await crud.reset_login_fail(db, user)
    token = create_access_token(user.id)
    return token, user


# ──────────────────────────────────────────
# 중복 확인
# ──────────────────────────────────────────

async def check_email(db: AsyncSession, email: str) -> bool:
    """이메일 사용 가능 여부 반환 (True = 사용 가능)"""
    return await crud.get_user_by_email(db, email) is None


async def check_nickname(db: AsyncSession, nickname: str) -> bool:
    """닉네임 사용 가능 여부 반환 (True = 사용 가능)"""
    return await crud.get_user_by_nickname(db, nickname) is None


# ──────────────────────────────────────────
# 닉네임 변경
# ──────────────────────────────────────────

async def update_nickname(db: AsyncSession, user: User, nickname: str) -> User:
    """닉네임 변경"""
    existing = await crud.get_user_by_nickname(db, nickname)
    if existing and existing.id != user.id:
        raise ValueError("이미 사용 중인 닉네임입니다")
    return await crud.update_profile(db, user, nickname=nickname)


# ──────────────────────────────────────────
# 비밀번호 변경
# ──────────────────────────────────────────

async def change_password(db: AsyncSession, user: User, data: PasswordChangeRequest) -> None:
    """
    비밀번호 변경
    1. 현재 비밀번호 확인
    2. 새 비밀번호 해싱
    3. 업데이트
    """
    if not await verify_password(data.current_password, user.password_hash):
        raise ValueError("현재 비밀번호가 올바르지 않습니다")

    new_hash = await hash_password(data.new_password)
    await crud.update_password(db, user, new_hash)


# ──────────────────────────────────────────
# 비밀번호 찾기 / 재설정
# ──────────────────────────────────────────

async def send_reset_email(to_email: str, reset_url: str) -> None:
    """비밀번호 재설정 이메일 발송 (Gmail SMTP)"""
    if not settings.MAIL_USERNAME or not settings.MAIL_PASSWORD or not settings.MAIL_FROM:
        raise RuntimeError("이메일 설정이 구성되지 않았습니다. .env를 확인해주세요.")

    msg = EmailMessage()
    msg["From"] = settings.MAIL_FROM
    msg["To"] = to_email
    msg["Subject"] = "[지지 GIGI] 비밀번호 재설정 안내"
    msg.set_content(
        f"안녕하세요, 지지 GIGI입니다.\n\n"
        f"비밀번호 재설정을 요청하셨습니다.\n"
        f"아래 링크를 클릭하여 비밀번호를 재설정해주세요.\n\n"
        f"{reset_url}\n\n"
        f"이 링크는 30분간 유효합니다.\n"
        f"본인이 요청하지 않으셨다면 이 이메일을 무시해주세요.\n\n"
        f"감사합니다.\n지지 GIGI 팀"
    )
    await aiosmtplib.send(
        msg,
        hostname="smtp.gmail.com",
        port=587,
        start_tls=True,
        username=settings.MAIL_USERNAME,
        password=settings.MAIL_PASSWORD,
    )


async def forgot_password(db: AsyncSession, email: str) -> None:
    """
    비밀번호 재설정 요청
    - 이메일이 없으면 조용히 종료 (이메일 존재 여부 외부 노출 방지)
    - 토큰 생성 → DB 저장 → 이메일 발송
    """
    user = await crud.get_user_by_email(db, email)
    if not user or not user.is_active:
        return

    token = secrets.token_urlsafe(32)
    expires = datetime.now(timezone.utc) + timedelta(minutes=30)
    await crud.save_reset_token(db, user, token, expires)

    reset_url = f"{settings.FRONTEND_URL}/pages/auth/reset-password.html?token={token}"
    try:
        await send_reset_email(user.email, reset_url)
    except Exception:
        await crud.clear_reset_token(db, user)
        raise


async def reset_password(db: AsyncSession, token: str, new_password: str) -> None:
    """
    비밀번호 재설정
    1. 토큰으로 유저 조회
    2. 만료 시간 확인
    3. 비밀번호 변경 후 토큰 삭제
    """
    user = await crud.get_user_by_reset_token(db, token)
    if not user or not user.is_active:
        raise ValueError("유효하지 않은 링크입니다")

    now = datetime.now(timezone.utc)
    if not user.password_reset_expires or user.password_reset_expires < now:
        raise ValueError("링크가 만료되었습니다. 다시 요청해주세요.")

    new_hash = await hash_password(new_password)
    await crud.update_password(db, user, new_hash)
    await crud.clear_reset_token(db, user)
