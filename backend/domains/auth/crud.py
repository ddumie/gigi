from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.domains.auth.models import User


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    """이메일로 유저 조회 (로그인, 이메일 중복 확인에 사용)"""
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_nickname(db: AsyncSession, nickname: str) -> User | None:
    """닉네임으로 유저 조회 (닉네임 중복 확인에 사용)"""
    result = await db.execute(select(User).where(User.nickname == nickname))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: int) -> User | None:
    """ID로 유저 조회 (GET /me 등에 사용)"""
    return await db.get(User, user_id)


async def create_user(db: AsyncSession, email: str, password_hash: str, nickname: str, name: str, profile_image: str | None = None) -> User:
    """유저 생성 (회원가입)"""
    user = User(
        email=email,
        password_hash=password_hash,
        nickname=nickname,
        name=name,
        profile_image=profile_image,
    )
    try:
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user
    except Exception:
        await db.rollback()
        raise


async def update_profile(
    db: AsyncSession,
    user: User,
    nickname: str | None = None,
    name: str | None = None,
    profile_image: str | None = None,
    age_group: str | None = None,
    health_interests: list[str] | None = None
) -> User:
    """프로필 수정"""
    updated = False

    if nickname is not None:
        user.nickname = nickname
        updated = True
    if name is not None:
        user.name = name
        updated = True
    if profile_image is not None:
        user.profile_image = profile_image
        updated = True
    if age_group is not None:
        user.age_group = age_group
        updated = True
    if health_interests is not None:
        user.health_interests = health_interests
        updated = True

    if not updated:
        return user

    try:
        await db.commit()
        await db.refresh(user)
        return user
    except Exception:
        await db.rollback()
        raise


async def update_password(db: AsyncSession, user: User, new_password_hash: str) -> User:
    """비밀번호 변경"""
    user.password_hash = new_password_hash
    try:
        await db.commit()
        await db.refresh(user)
        return user
    except Exception:
        await db.rollback()
        raise


async def deactivate_user(db: AsyncSession, user: User) -> None:
    """회원탈퇴 (소프트 삭제 — is_active = False, 이메일/닉네임 익명화)"""
    user.is_active = False
    user.email = f"deleted_{user.id}@deleted.com"
    user.nickname = f"deleted_{user.id}"
    try:
        await db.commit()
        await db.refresh(user)
    except Exception:
        await db.rollback()
        raise
