from fastapi import HTTPException
from sqlalchemy.orm import Session
from . import models, schemas
import secrets, string

# 초대코드 생성 (4자리의 숫자 or 알파벳 소문자)
def generate_invitecode(length = 4):
    d4code = string.ascii_lowercase + string.digits
    return ''.join(secrets.choice(d4code) for _ in range(length))

# 그룹 생성
def create_group(db: Session, group: schemas.GroupCreate, user_id: int):
    # group 생성
    db_group = models.Group(
        habit = group.habit,
        level_name = "seed",
        total_support_count = 0,
        support_streak = 0
    )
    db.add(db_group)
    db.commit()
    db.refresh(db_group)

    # group_profile 생성
    db_group_profile = models.GroupProfile(
        group_id = db_group.id,
        user_id = user_id,
        name = group.name,
        group_type = group.group_type
    )
    db.add(db_group_profile)
    db.commit()
    db.refresh(db_group_profile)

    # 초대코드 생성
    code_suffix = generate_invitecode()
    code = f"GIGI-{code_suffix}"
    invite = models.InviteCode(
        code = code,
        group_id = db_group.id,
        created_by = user_id,
        is_active = True
    )
    db.add(invite)
    db.commit()
    db.refresh(invite)

    return db_group

# 모임 읽어오기
def get_group(db: Session, group_id: int, user_id: int):
    groupprofile = db.query(models.GroupProfile).filter(models.GroupProfile.group_id == group_id)

    if not groupprofile:
        raise HTTPException(status_code = 404, detail= "모임을 찾을 수 없습니다.")
    
    invite = db.query(models.InviteCode).filter(models.InviteCode.group_id == group_id)

    if not invite:
        raise HTTPException(status_code=404, detail="초대코드를 찾을 수 없습니다.")    

    return groupprofile, invite

# 모임 참가
def participate_group(db: Session, ):