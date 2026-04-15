import logging
from datetime import date
from sqlalchemy.orm import Session
from backend.domains.onboarding.models import UserPreference

logger = logging.getLogger(__name__)


# 온보딩 DB CRUD
def get_preferences(db: Session, user_id: int):
    """user_id로 사용자 선호도 조회, 없으면 None 반환"""
    return db.query(UserPreference).filter(UserPreference.user_id == user_id).first()


def save_preferences(db: Session, user_id: int, age_group: str | None, health_interests: list[str] | None):
    """나이대, 관심사 저장 또는 수정"""
    try:
        db_pref = get_preferences(db, user_id)
        if db_pref:
            db_pref.age_group = age_group
            db_pref.health_interests = health_interests
        else:
            db_pref = UserPreference(user_id=user_id, age_group=age_group, health_interests=health_interests)
            db.add(db_pref)
        db.commit()
        db.refresh(db_pref)
        return db_pref
    except Exception as e:
        db.rollback()
        logger.error(f"선호도 저장 중 오류 발생: {e}", exc_info=True)
        raise ValueError("선호도 저장 중 오류가 발생했습니다.")


def incre_recommend_count(db: Session, user_id: int):
    """AI 재추천 횟수 증가 (+1), 날짜 바뀌면 자동 초기화 (하루 3회 제한)"""
    try:
        db_pref = get_preferences(db, user_id)
        if db_pref is None:
            return None
        today = date.today()
        # 날짜가 바뀌면 횟수 초기화(3회)
        if db_pref.last_recommend_date != today:
            db_pref.recommend_count = 0
        db_pref.recommend_count += 1
        db_pref.last_recommend_date = today
        db.commit()
        db.refresh(db_pref)
        return db_pref
    except Exception as e:
        db.rollback()
        logger.error(f"재추천 횟수 증가 중 오류 발생: {e}", exc_info=True)
        raise ValueError("재추천 횟수 업데이트 중 오류가 발생했습니다.")
    