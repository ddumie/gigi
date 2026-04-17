from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from backend.domains.onboarding import crud, service
from backend.domains.onboarding.schemas import PreferenceRequest, AIRecommendResponse, SelectRequest
from backend.domains.auth.service import get_current_user
from backend.database import get_async_db

router = APIRouter()
bearer = HTTPBearer()


# 유저쪽 헤더에서 토큰 추출 후 현재 유저 반환
async def get_current_user_dep(
        credentials: HTTPAuthorizationCredentials = Depends(bearer),
        db: AsyncSession = Depends(get_async_db)):
    """Authorization 헤더 토큰으로 현재 유저 반환"""
    try:
        return get_current_user(credentials.credentials, db)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


# 나이대, 관심사 저장
@router.post("/preferences")
async def save_preferences(request: PreferenceRequest, db: AsyncSession = Depends(get_async_db), current_user = Depends(get_current_user_dep)):
    """나이대, 관심사 저장"""
    try:
        await crud.save_preferences(db, current_user.id, request.age_group, request.health_interests)
    except ValueError:
        raise HTTPException(status_code=500, detail="선호도 저장 중 오류가 발생했습니다.")
    return {"message": "선호도가 저장되었습니다."}


# AI습관 추천(선호도 조회, 횟수체크)
@router.post("/ai-recommend", response_model=AIRecommendResponse)
async def recommend_habits(db: AsyncSession = Depends(get_async_db), current_user = Depends(get_current_user_dep)):
    """AI습관 추천 (처음 온보딩 설정 시 하루 3회 제한)"""
    pref = await crud.get_preferences(db, current_user.id)
    if pref is None:
        raise HTTPException(status_code=404, detail="먼저 선호도를 저장해주세요.")
    if pref.recommend_count >= 3:
        raise HTTPException(status_code=400, detail="오늘 추천 횟수를 모두 사용했습니다. 내일 다시 시도해주세요.")
    try:
        habits, updated_pref = await service.recommend_habits_and_count(db, current_user.id, pref.age_group, pref.health_interests)
    except ValueError:
        raise HTTPException(status_code=502, detail="맞춤 습관 추천 중 오류가 발생했습니다.")
    return AIRecommendResponse(habits=habits, can_retry=(updated_pref.recommend_count < 3))


# 사용자가 선택한 습관 등록
@router.post("/ai-recommend/select")
async def select_habits(request: SelectRequest, db: AsyncSession = Depends(get_async_db), current_user = Depends(get_current_user_dep)):
    """AI가 추천한 습관을 사용자가 선택해서 등록"""
    if not current_user.is_first_login:
        raise HTTPException(status_code=400, detail="이미 온보딩이 완료된 사용자입니다.")
    if not request.selected_habits:
        raise HTTPException(status_code=400, detail="습관을 하나 이상 선택해주세요.")
    try:
        await service.save_selected_habits(db, current_user.id, request.selected_habits)
    except ValueError:
        raise HTTPException(status_code=500, detail="습관 저장 중 오류가 발생했습니다.")
    return {"message": "선택한 습관이 등록되었습니다."}
