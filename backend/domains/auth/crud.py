from sqlalchemy import select
from sqlalchemy.orm import Session
from backend.domains.auth.models import User


def get_user_by_email(db: Session, email: str) -> User | None:
    """이메일로 유저 조회 (로그인, 이메일 중복 확인에 사용)"""
    return db.execute(select(User).where(User.email == email)).scalar_one_or_none()


def get_user_by_nickname(db: Session, nickname: str) -> User | None:
    """닉네임으로 유저 조회 (닉네임 중복 확인에 사용)"""
    return db.execute(select(User).where(User.nickname == nickname)).scalar_one_or_none()


def get_user_by_id(db: Session, user_id: int) -> User | None:
    """ID로 유저 조회 (GET /me 등에 사용)"""
    return db.get(User, user_id)


def create_user(db: Session, email: str, password_hash: str, nickname: str, name: str, profile_image: str | None = None) -> User:
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
        db.commit()
        db.refresh(user)
        return user
    except Exception:
        db.rollback()
        raise


def update_profile(
    db: Session,
    user: User,
    nickname: str | None = None,
    name: str | None = None,
    profile_image: str | None = None,
    age_group: str | None = None,
    health_interests: list[str] | None = None
) -> User:
    """프로필 수정 (PUT /mypage/profile)"""
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
        db.commit()
        db.refresh(user)
        return user
    except Exception:
        db.rollback()
        raise


def update_password(db: Session, user: User, new_password_hash: str) -> User:
    """비밀번호 변경"""
    user.password_hash = new_password_hash
    try:
        db.commit()
        db.refresh(user)
        return user
    except Exception:
        db.rollback()
        raise


def deactivate_user(db: Session, user: User) -> None:
    """회원탈퇴 (소프트 삭제 — is_active = False)"""
    user.is_active = False
    try:
        db.commit()
        db.refresh(user)
    except Exception:
        db.rollback()
        raise
