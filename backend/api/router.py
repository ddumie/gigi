from fastapi import APIRouter
from backend.domains.auth.router import router as auth_router
from backend.domains.onboarding.router import router as onboarding_router
from backend.domains.habits.router import router as habits_router
from backend.domains.today.router import router as today_router
from backend.domains.support.router import router as support_router
from backend.domains.neighbor.router import router as neighbor_router
from backend.domains.settings.router import router as settings_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth_router, prefix="/auth", tags=["인증"])
api_router.include_router(onboarding_router, prefix="/onboarding", tags=["온보딩"])
api_router.include_router(habits_router, prefix="/habits", tags=["습관"])
api_router.include_router(today_router, prefix="/today", tags=["오늘"])
api_router.include_router(support_router, prefix="/support", tags=["지지"])
api_router.include_router(neighbor_router, prefix="/neighbor", tags=["이웃"])
api_router.include_router(settings_router, prefix="/settings", tags=["설정"])
