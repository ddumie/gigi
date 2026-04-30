from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_async_db
from backend.domains.auth import crud, service
from backend.domains.auth.models import User
from backend.domains.onboarding.models import UserPreference
from backend.domains.auth.schemas import (
    RegisterRequest,
    LoginRequest,
    CheckResponse,
    TokenResponse,
    UserResponse,
    PasswordChangeRequest,
    NicknameUpdateRequest,
)

router = APIRouter()
bearer_scheme = HTTPBearer(auto_error=False)


# ──────────────────────────────────────────
# 인증 의존성
# ──────────────────────────────────────────

async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_async_db),
) -> User:
    """Authorization: Bearer {token} 헤더에서 유저 추출"""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="인증 토큰이 필요합니다",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        return await service.get_current_user(credentials.credentials, db)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_optional_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_async_db),
) -> User | None:
    """토큰이 없으면 None 반환 (비로그인 허용 엔드포인트용)"""
    if credentials is None:
        return None
    try:
        return await service.get_current_user(credentials.credentials, db)
    except Exception:
        return None


# ──────────────────────────────────────────
# 회원가입
# ──────────────────────────────────────────

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(data: RegisterRequest, db: AsyncSession = Depends(get_async_db)):
    """회원가입 → JWT + 유저 정보 반환"""
    try:
        user = await service.register(db, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))

    token = service.create_access_token(user.id)
    return TokenResponse(access_token=token, user=UserResponse.model_validate(user))


# ──────────────────────────────────────────
# 로그인
# ──────────────────────────────────────────

@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_async_db)):
    """로그인 → JWT + 유저 정보 반환"""
    try:
        token, user = await service.login(db, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

    return TokenResponse(access_token=token, user=UserResponse.model_validate(user))


# ──────────────────────────────────────────
# 내 정보 조회
# ──────────────────────────────────────────

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_async_db)):
    """현재 로그인 유저 정보 반환"""
    user_data = UserResponse.model_validate(current_user)
    pref = (await db.execute(select(UserPreference).where(UserPreference.user_id == current_user.id))).scalar_one_or_none()
    if pref:
        user_data.health_interests = pref.health_interests
    return user_data


# ──────────────────────────────────────────
# 중복 확인
# ──────────────────────────────────────────

@router.get("/check/email", response_model=CheckResponse)
async def check_email(email: str = Query(...), db: AsyncSession = Depends(get_async_db)):
    """이메일 중복 확인"""
    available = await service.check_email(db, email)
    message = "사용 가능한 이메일입니다" if available else "이미 사용 중인 이메일입니다"
    return CheckResponse(available=available, message=message)


@router.get("/check/nickname", response_model=CheckResponse)
async def check_nickname(nickname: str = Query(...), db: AsyncSession = Depends(get_async_db)):
    """닉네임 중복 확인"""
    available = await service.check_nickname(db, nickname)
    message = "사용 가능한 닉네임입니다" if available else "이미 사용 중인 닉네임입니다"
    return CheckResponse(available=available, message=message)


# ──────────────────────────────────────────
# 닉네임 변경
# ──────────────────────────────────────────

@router.patch("/nickname")
async def update_nickname(
    data: NicknameUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """닉네임 변경 (로그인 필요)"""
    try:
        user = await service.update_nickname(db, current_user, data.nickname)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    return {"message": "닉네임이 변경되었습니다.", "nickname": user.nickname}


# ──────────────────────────────────────────
# 비밀번호 변경
# ──────────────────────────────────────────

@router.put("/password")
async def change_password(
    data: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """비밀번호 변경 (로그인 필요)"""
    try:
        await service.change_password(db, current_user, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return {"message": "비밀번호가 변경되었습니다."}


# ──────────────────────────────────────────
# 회원탈퇴
# ──────────────────────────────────────────

@router.delete("/me", status_code=status.HTTP_200_OK)
async def delete_me(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """회원탈퇴 (소프트 삭제 — is_active = False)"""
    try:
        await crud.deactivate_user(db, current_user)
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="회원탈퇴 처리 중 오류가 발생했습니다.")
    return {"message": "회원탈퇴가 완료되었습니다."}
