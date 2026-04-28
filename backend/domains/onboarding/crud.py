import logging
from datetime import date
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.domains.onboarding.models import UserPreference


logger = logging.getLogger(__name__)


# 온보딩 DB CRUD
async def get_preferences(db: AsyncSession, user_id: int):
    """user_id로 사용자 선호도 조회, 없으면 None 반환"""
    result = await db.execute(select(UserPreference).filter(UserPreference.user_id == user_id))
    return result.scalars().first()


async def save_preferences(db: AsyncSession, user_id: int, age_group: str | None, health_interests: list[str] | None, font_size: str | None = None):
    """나이대, 관심사, 글씨크기 저장 또는 수정"""
    try:
        db_pref = await get_preferences(db, user_id)
        if db_pref:
            db_pref.age_group = age_group
            db_pref.health_interests = health_interests
            if font_size is not None:
                db_pref.font_size = font_size
        else:
            db_pref = UserPreference(user_id=user_id, age_group=age_group, health_interests=health_interests, font_size=font_size)
            db.add(db_pref)
        await db.commit()
        await db.refresh(db_pref)
        return db_pref
    except Exception as e:
        await db.rollback()
        logger.error(f"선호도 저장 중 오류 발생: {e}", exc_info=True)
        raise ValueError("선호도 저장 중 오류가 발생했습니다.")


async def increment_recommend_count(db: AsyncSession, user_id: int):
    """AI 재추천 횟수 증가 (+1), 날짜가 바뀌면 자동 초기화 (하루 15회 제한)"""
    try:
        db_pref = await get_preferences(db, user_id)
        if db_pref is None:
            return None
        today = date.today()
        # 날짜가 바뀌면 횟수 초기화
        if db_pref.last_recommend_date != today:
            db_pref.recommend_count = 0
        # 하루 15회 초과 시 예외 발생
        if db_pref.recommend_count >= 15:
            raise ValueError("하루 재추천 횟수를 초과했습니다.")
        db_pref.recommend_count += 1
        db_pref.last_recommend_date = today
        await db.commit()
        await db.refresh(db_pref)
        return db_pref
    except Exception as e:
        await db.rollback()
        logger.error(f"재추천 횟수 증가 중 오류 발생: {e}", exc_info=True)
        raise ValueError("재추천 횟수 업데이트 중 오류가 발생했습니다.")
    