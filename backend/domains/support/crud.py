from fastapi import HTTPException
from sqlalchemy.orm import Session
from . import models, schemas
from neighbor.models import GroupSearchPost
import secrets, string

# 메모
# 모임 구해요에서 온 모임에는 GroupSearchPost에서 가져온 habit_title과 frequency를 받아다 출력


# 초대코드 생성 (4자리의 숫자 or 알파벳 소문자)
def generate_invitecode(length = 4):
    d4code = string.ascii_lowercase + string.digits
    return ''.join(secrets.choice(d4code) for _ in range(length))

# 초대코드 생성 (중복 방지)
def create_unique_invitecode(db: Session, prefix="GIGI-", length=4, max_attempts=10):
    for _ in range(max_attempts):
        code_suffix = generate_invitecode(length)
        code = f"{prefix}{code_suffix}"
        existing = db.query(models.InviteCode).filter(models.InviteCode.code == code).first()
        if not existing:
            return code
    raise ValueError("초대코드 생성에 실패했습니다. 다시 시도해주세요.")

# 그룹 생성
def create_group(db: Session, group: schemas.GroupCreate, user_id: int):
    # group 생성
    db_group = models.Group(
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
    code = create_unique_invitecode(db)
    invite = models.InviteCode(
        code=code,
        group_id=db_group.id,
        created_by=user_id,
        is_active=True
    )
    db.add(invite)
    db.commit()
    db.refresh(invite)

    return db_group

# 모임 읽어오기
def get_group(db: Session, group_id: int, user_id: int):
    groupprofile = db.query(models.GroupProfile).filter(models.GroupProfile.group_id == group_id, models.GroupProfile.user_id == user_id).first()
    invite = db.query(models.InviteCode).filter(models.InviteCode.group_id == group_id).first()
    members = db.query(models.GroupMember).filter(models.GroupMember.group_id == group_id).all()

    # 습관 조회 (Group의 post_id가 None이 아닌 경우만.)
    group = db.query(models.Group).filter(models.Group.id == group_id).first()
    habit_info = None
    if group and group.post_id:
        post_info = db.query(GroupSearchPost).filter(GroupSearchPost.post_id == group.post_id).first()
        if post_info:
            habit_info = {
                "habit_title": post_info.habit_title,
                "frequency": post_info.frequency
            }
    return group, groupprofile, invite, members, habit_info

# 초대코드로 그룹 ID 조회
def get_group_id_by_code(db: Session, invite_code: str):
    invite = db.query(models.InviteCode).filter(
        models.InviteCode.code == invite_code,
        models.InviteCode.is_active == True
    ).first()
    if not invite:
        return None
    return invite.group_id

# 모임 구해요의 post_id로 가입하기 (그룹 없으면 그룹도 생성)
def get_or_create_group_id_by_post(db: Session, post_id: int, user_id: int):
    group = db.query(models.Group).filter(models.Group.post_id == post_id).first()
    if not group:
        # GroupSearchPost에서 값 가져와서 넣기
        post_info = db.query(GroupSearchPost).filter(GroupSearchPost.post_id == post_id).first()
        if not post_info:
            return None
        
        group_setting = schemas.GroupCreate(
            name=post_info.title,
            group_type=post_info.group_type,
        )

        group = create_group(db, group_setting, user_id)
        group.post_id = post_id
        db.commit()
        db.refresh(group)

    return group.id

# 모임 참가
def add_group_member(db: Session, group_id: int, user_id: int):
    new_member = models.GroupMember(
        group_id = group_id,
        user_id = user_id
    )
    db.add(new_member)
    db.commit()
    db.refresh(new_member)

    return new_member

# 모임 탈퇴
def remove_group_member(db: Session, group_id: int, user_id: int):
    member = db.query(models.GroupMember).filter(
        models.GroupMember.group_id == group_id,
        models.GroupMember.user_id == user_id
    ).first()
    if not member:
        return None
    db.delete(member)
    db.commit()
    return True

# 모임 정보 수정
def update_group_profile(db: Session, group_id: int, user_id: int, group: schemas.GroupCreate):
    groupprofile = db.query(models.GroupProfile).filter(
        models.GroupProfile.group_id == group_id,
        models.GroupProfile.user_id == user_id
    ).first()
    if not groupprofile:
        return None
    
    groupprofile.name = group.name
    groupprofile.group_type = group.group_type
    db.commit()
    db.refresh(groupprofile)
    return groupprofile