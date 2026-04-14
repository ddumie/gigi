from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.domains.onboarding import crud, service
from backend.domains.onboarding.schemas import PreferenceRequest, AIRecommendResponse, SelectRequest
from backend.domains.auth.service import get_current_user
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

router = APIRouter()
bearer = HTTPBearer()


# 유저쪽 헤더에서 토큰 추출 후 현재 유저 반환
def get_current_user_dep(
        credentials: HTTPAuthorizationCredentials = Depends(bearer),
        db: Session = Depends(get_db)):
    """Authorization 헤더 토큰으로 현재 유저 반환"""
    try:
        return get_current_user(credentials.credentials, db)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


# 나이대, 관심사 저장
@router.post("/preferences")
def save_preferences(request: PreferenceRequest, db: Session = Depends(get_db), current_user = Depends(get_current_user_dep)):
    """나이대, 관심사 저장"""
    try:
        crud.save_preferences(db, current_user.id, request.age_group, request.health_interests)
    except ValueError:
        raise HTTPException(status_code=500, detail="선호도 저장 중 오류가 발생했습니다.")
    return {"message": "선호도가 저장되었습니다."}


# AI습관 추천
@router.post("/ai-recommend", response_model=AIRecommendResponse)
def recommend_habits(db: Session = Depends(get_db), current_user = Depends(get_current_user_dep)):
    """AI습관 추천(재추천 1회 제한)"""
    # 추천흐름 3단계
    # 1단계: DB에서 선호도 조회
    try:
        pref = crud.get_preferences(db, current_user.id)
    except Exception:
        raise HTTPException(status_code=500, detail="서버 오류가 발생했습니다.")
    if pref is None:
        raise HTTPException(status_code=404, detail="먼저 선호도를 저장해주세요.")
    if pref.recommend_count >= 2:
        raise HTTPException(status_code=400, detail="재추천은 1회만 가능합니다. 더 이상 추천받을 수 없습니다.")

    # 2단계: Gemini AI 호출(Gemini가 습관추천에 성공하면 카운트 +1, 실패하면 에러반환(카운트 증가X))
    try:
        habits = service.get_ai_recommendations(pref.age_group, pref.health_interests)
    except ValueError:
        raise HTTPException(status_code=502, detail="AI추천 중 오류가 발생했습니다.")

    # 3단계: DB에 카운트 증가
    try:
        updated_pref = crud.incre_recommend_count(db, current_user.id)
    except ValueError:
        raise HTTPException(status_code=500, detail="재추천 횟수 업데이트 중 오류가 발생했습니다.")
    if updated_pref is None:
        raise HTTPException(status_code=404, detail="선호도 정보를 찾을 수 없습니다.")
    return AIRecommendResponse(habits=habits, can_retry=(updated_pref.recommend_count < 2))


# 사용자가 선택한 습관 등록
@router.post("/ai-recommend/select")
def select_habits(request: SelectRequest, db: Session = Depends(get_db), current_user = Depends(get_current_user_dep)):
    """AI가 추천한 습관을 사용자가 선택해서 등록"""
    if not current_user.is_first_login:
        raise HTTPException(status_code=400, detail="이미 온보딩이 완료된 사용자입니다.")
    if not request.selected_habits:
        raise HTTPException(status_code=400, detail="습관을 하나 이상 선택해주세요.")
    try:
        service.save_selected_habits(db, current_user.id, request.selected_habits)
    except ValueError:
        raise HTTPException(status_code=500, detail="습관 저장 중 오류가 발생했습니다.")
    return {"message": "선택한 습관이 등록되었습니다."}
