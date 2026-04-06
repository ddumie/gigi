from fastapi import APIRouter
from backend.modules.auth.router import router as auth_router
from backend.modules.routine.router import router as routine_router
from backend.modules.onboarding.router import router as onboarding_router
from backend.modules.group.router import router as group_router
from backend.modules.support.router import router as support_router
from backend.modules.community.router import router as community_router
from backend.modules.mypage.router import router as mypage_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth_router, prefix="/auth", tags=["인증"])
api_router.include_router(routine_router, prefix="/routines", tags=["루틴"])
api_router.include_router(onboarding_router, prefix="/onboarding", tags=["온보딩"])
api_router.include_router(group_router, prefix="/groups", tags=["그룹"])
api_router.include_router(support_router, prefix="/groups", tags=["지지하기"])
api_router.include_router(community_router, prefix="/community", tags=["커뮤니티"])
api_router.include_router(mypage_router, prefix="/mypage", tags=["마이페이지"])