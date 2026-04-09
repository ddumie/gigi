from sqlalchemy.orm import Session
from . import crud, schemas, models

# 초대코드로 모임 가입
def invited_group_service(db: Session, invite_code: str, user_id: int):
    group_id = crud.get_group_id_by_code(db, invite_code)
    if not group_id:
        raise ValueError("초대코드가 잘못 되었거나 만료 되었습니다.")
    return join_group_service(db, group_id, user_id)

# 모임 생성
def create_group_service(db: Session, group: schemas.GroupCreate, user_id: int):
    return crud.create_group(db, group, user_id)

# 모임 관리
def group_info_service(db: Session, group_id: int, user_id: int):
    group, groupprofile, invite, members, habit_info = crud.get_group(db, group_id, user_id)
    if not group:
        raise ValueError("모임을 찾을 수 없습니다.")
    if not groupprofile:
        raise ValueError("모임 설정을 찾을 수 없습니다.")
    if not invite:
        raise ValueError("초대코드를 찾을 수 없습니다.")
    if not members:
        raise ValueError("해당 그룹에 맴버가 없습니다.")
    return group, groupprofile, invite, members, habit_info

# 모임 구해요로 모임 가입하기
def join_by_post_service(db: Session, post_id: int, user_id: int):
    group_id = crud.get_or_create_group_id_by_post(db, post_id, user_id)
    if not group_id:
        raise ValueError("해당 post_id에 연결 된 그룹을 찾을 수 없습니다.")
    return join_group_service(db, group_id, user_id)

# 가져온 그룹 id로 가입하기
def join_group_service(db: Session, group_id: int, user_id: int):
    # 모임 존재 확인
    group = db.query(models.Group).filter(models.Group.id == group_id).first()
    if not group:
        raise ValueError("모임을 찾을 수 없습니다.")

    # 중복가입 확인
    existing_member = db.query(models.GroupMember).filter(
        models.GroupMember.group_id == group_id,
        models.GroupMember.user_id == user_id
    ).first()
    if existing_member:
        raise ValueError("이미 모임에 가입 된 사용자입니다.")

    return crud.add_group_member(db, group_id, user_id)    

# 모임 탈퇴하기
def leave_group_service(db: Session, group_id: int, user_id: int):
    # 모임 확인
    group = db.query(models.Group).filter(models.Group.id == group_id).first()
    if not group:
        raise ValueError("모임을 찾을 수 없습니다.")
    
    # 가입 여부 확인
    member = db.query(models.GroupMember).filter(
        models.GroupMember.group_id == group_id,
        models.GroupMember.user_id == user_id
    ).first()
    if not member:
        raise ValueError("가입된 사용자가 아닙니다.")
    
    # 탈퇴처리
    return crud.remove_group_member(db, group_id, user_id)

# 모임 정보 수정
def update_group_profile_service(db: Session, group_id: int, user_id: int, group: schemas.GroupCreate):
    updated_profile = crud.update_group_profile(db, group_id, user_id, group)
    if not updated_profile:
        raise ValueError("해당 사용자에 대한 그룹 프로필을 찾을 수 없습니다.")
    return updated_profile