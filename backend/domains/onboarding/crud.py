from sqlalchemy.orm import Session
from backend.domains.onboarding.models import UserPreference

#온보딩 DB CRUD
def get_preferences(db: Session, user_id: int):
    """사용자 조회"""
    return db.query(UserPreference).filter(UserPreference.user_id == user_id).first()

def save_preferences(db: Session, user_id: int, age_group: str | None, health_interests: list[str] | None):
    """나이대, 관심사 저장 또는 수정"""
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
트
def incre_recommend_count(db: Session, user_id: int):
    """AI 재추천 횟수 증가(+1)"""
    db_pref = get_preferences(db, user_id)
    db_pref.recommend_count += 1 #일단 1회 추천가능으로 되어있음(0-처음 추천, 1-재추천 사용, 2-재추천 불가)
    db.commit()
    db.refresh(db_pref)
    return db_pref
